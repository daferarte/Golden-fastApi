import os, json, time, uuid, threading
import paho.mqtt.client as mqtt

# --- Configuración del Broker MQTT (por entorno) ---
MQTT_BROKER_IP = os.getenv("MQTT_BROKER_IP", "192.168.0.100")
MQTT_PORT      = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER      = os.getenv("MQTT_USER", "")         # ej. "backend"
MQTT_PASS      = os.getenv("MQTT_PASS", "")         # ej. "backendpass"
MQTT_TLS       = os.getenv("MQTT_TLS", "false").lower() in ("1","true","yes")

# Helpers de topics
def topic_cmd(sede, device):   return f"devices/{sede}/{device}/cmd"
def topic_ack(sede, device):   return f"devices/{sede}/{device}/cmd/ack"
def topic_state(s, d):         return f"devices/{s}/{d}/state"
def topic_event(s, d):         return f"devices/{s}/{d}/event"
def topic_config(s, d):        return f"devices/{s}/{d}/config"

class MQTTClient:
    """
    Cliente MQTT con:
    - Conexión/reconexión no bloqueante (loop_start)
    - Publicación JSON con QoS/retain (QoS 1 por defecto)
    - Suscripción idempotente
    - Envío de comando y espera de ACK por 'id' con timeout
    """
    def __init__(self):
        # API v2 de callbacks
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"fastapi_backend_service-{uuid.uuid4().hex[:6]}",
            userdata={}
        )

        if MQTT_USER:
            self.client.username_pw_set(MQTT_USER, MQTT_PASS)

        # TLS opcional
        if MQTT_TLS:
            import ssl
            self.client.tls_set(cert_reqs=ssl.CERT_NONE)
            self.client.tls_insecure_set(True)

        # Callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # Sincronización
        self._connected = threading.Event()
        self._lock = threading.RLock()
        self._subs = set()

        # Pendientes de ACK: cmd_id -> {"event": Event, "ok": None}
        self._pending = {}

    # ------------------ Ciclo de vida ------------------

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if int(reason_code) == 0:
            print("✅ Conectado exitosamente al Broker MQTT!")
            self._connected.set()
            # Re-suscribir lo que ya teníamos
            with self._lock:
                for t in list(self._subs):
                    self.client.subscribe(t, qos=1)
        else:
            print(f"❌ Falló la conexión al Broker MQTT, código: {reason_code}")

    def on_disconnect(self, client, userdata, reason_code, properties):
        print(f"🔌 Desconectado del Broker MQTT (rc={reason_code})")
        self._connected.clear()

    def on_message(self, client, userdata, msg):
        # Procesa ACKs: payload JSON con {"id": "...", "ok": true/false, ...}
        try:
            data = json.loads(msg.payload.decode())
        except Exception:
            return
        if msg.topic.endswith("/cmd/ack"):
            cmd_id = data.get("id")
            if not cmd_id:
                return
            with self._lock:
                pending = self._pending.get(cmd_id)
                if pending:
                    pending["ok"] = bool(data.get("ok"))
                    pending["event"].set()

    def connect(self, retries=999):
        """Conexión con reintentos y backoff; arranca loop de red."""
        backoff = 1.0
        for _ in range(retries):
            try:
                self.client.connect(MQTT_BROKER_IP, MQTT_PORT, keepalive=30)
                self.client.loop_start()  # maneja red en segundo plano
                if self._connected.wait(timeout=5.0):
                    return
            except Exception as e:
                print(f"🔥 Error al conectar con MQTT: {e}")
            time.sleep(backoff)
            backoff = min(backoff * 1.7, 10.0)
        raise RuntimeError("No se pudo conectar al broker MQTT")

    def disconnect(self):
        """Detiene loop y desconecta."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

    # ------------------ Utilidades ------------------

    def ensure_connected(self, timeout=5.0):
        if self._connected.is_set():
            return True
        return self._connected.wait(timeout=timeout)

    def ensure_sub(self, topic: str, qos: int = 1) -> bool:
        """Suscripción idempotente y segura (re-suscribe tras reconexión)."""
        with self._lock:
            if topic in self._subs:
                return True
            res, _ = self.client.subscribe(topic, qos=qos)
            if res == mqtt.MQTT_ERR_SUCCESS:
                self._subs.add(topic)
                return True
            print(f"⚠️ No se pudo suscribir a {topic} (rc={res})")
            return False

    def publish_json(self, topic: str, payload: dict, qos: int = 1, retain: bool = False) -> bool:
        """Publica JSON con QoS/retain configurables."""
        try:
            if not self.ensure_connected(timeout=3.0):
                print("⚠️ Publish abortado: MQTT no conectado")
                return False
            msg = json.dumps(payload)
            info = self.client.publish(topic, msg, qos=qos, retain=retain)
            info.wait_for_publish(timeout=5.0)
            ok = (info.rc == mqtt.MQTT_ERR_SUCCESS)
            if ok:
                print(f"✉️ {topic} QoS={qos} retain={retain}: {msg}")
            else:
                print(f"⚠️ Falló publish en {topic}, rc={info.rc}")
            return ok
        except Exception as e:
            print(f"🔥 Error durante publish: {e}")
            return False

    # Mantén compatibilidad con tu interfaz existente:
    def publish(self, topic: str, payload: dict) -> bool:
        """Compat: publica con QoS 1 y sin retain (comportamiento recomendado)."""
        return self.publish_json(topic, payload, qos=1, retain=False)

    # ------------------ Comandos con ACK ------------------

    def send_command_and_wait_ack(self, sede: str, device: str, action: str,
                                  payload: dict | None = None, timeout: float = 5.0) -> bool:
        """
        Publica en devices/<sede>/<device>/cmd y espera ACK en /cmd/ack.
        Devuelve True si ok==true en el ACK dentro del timeout.
        """
        cmd_id = f"c-{uuid.uuid4().hex[:8]}"
        t_cmd = topic_cmd(sede, device)
        t_ack = topic_ack(sede, device)

        # Suscribirse al ACK antes de publicar
        if not self.ensure_sub(t_ack, qos=1):
            raise RuntimeError("No se pudo suscribir al topic de ACK")

        body = {"id": cmd_id, "ts": int(time.time()), "action": action}
        if payload:
            body.update(payload)

        ev = threading.Event()
        with self._lock:
            self._pending[cmd_id] = {"event": ev, "ok": None}

        if not self.publish_json(t_cmd, body, qos=1, retain=False):
            with self._lock:
                self._pending.pop(cmd_id, None)
            raise RuntimeError("No se pudo publicar el comando")

        if not ev.wait(timeout=timeout):
            with self._lock:
                self._pending.pop(cmd_id, None)
            print("⏱️ Timeout esperando ACK")
            return False

        with self._lock:
            ok = self._pending.pop(cmd_id)["ok"]
        return bool(ok)

# Instancia única (Singleton)
mqtt_client = MQTTClient()
