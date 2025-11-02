import os, json, time, uuid, threading, asyncio
import paho.mqtt.client as mqtt
from app.services.event_broadcast import broadcaster

# =====================================================
# 🔧 Configuración del Broker MQTT (una sola IP local)
# =====================================================
MQTT_BROKER_IP = os.getenv("MQTT_BROKER_IP", "192.168.101.21").strip()
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")
MQTT_TLS = os.getenv("MQTT_TLS", "false").lower() in ("1", "true", "yes")

# =====================================================
# 🔹 Helpers para formatear topics
# =====================================================
def topic_cmd(sede, device): return f"devices/{sede}/{device}/cmd"
def topic_ack(sede, device): return f"devices/{sede}/{device}/cmd/ack"
def topic_event(s, d): return f"devices/{s}/{d}/event"
def topic_state(s, d): return f"devices/{s}/{d}/state"
def topic_config(s, d): return f"devices/{s}/{d}/config"

# =====================================================
# 🚀 Cliente MQTT optimizado
# =====================================================
class MQTTClient:
    """
    Cliente MQTT:
    - Conexión estable y automática (loop_start)
    - Publicación JSON con QoS=1
    - Reenvía mensajes /event al WebSocket broadcaster
    """
    def __init__(self):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"fastapi-backend-{uuid.uuid4().hex[:6]}",
            userdata={}
        )

        if MQTT_USER:
            self.client.username_pw_set(MQTT_USER, MQTT_PASS)

        if MQTT_TLS:
            import ssl
            self.client.tls_set(cert_reqs=ssl.CERT_NONE)
            self.client.tls_insecure_set(True)

        # --- Callbacks ---
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # --- Estado y control ---
        self._connected = threading.Event()
        self._subs = set()
        self._lock = threading.RLock()
        self._pending = {}

    # =====================================================
    # 🧩 Callbacks principales
    # =====================================================
    def on_connect(self, client, userdata, flags, reason_code, properties):
        rc = getattr(reason_code, "value", reason_code)
        ok = int(rc) == 0 if isinstance(rc, int) else getattr(reason_code, "is_good", lambda: False)()

        if ok:
            print(f"✅ Conectado exitosamente al Broker MQTT en {MQTT_BROKER_IP}:{MQTT_PORT}")
            self._connected.set()
            with self._lock:
                for t in list(self._subs):
                    self.client.subscribe(t, qos=1)
        else:
            print(f"❌ Falló la conexión al broker ({reason_code})")

    def on_disconnect(self, client, userdata, reason_code, properties):
        print("🔌 Desconectado del Broker MQTT")
        self._connected.clear()

    def on_message(self, client, userdata, msg):
        """Procesa mensajes MQTT entrantes."""
        try:
            data = json.loads(msg.payload.decode())
        except Exception:
            return

        # --- ACKs de comandos ---
        if msg.topic.endswith("/cmd/ack"):
            cmd_id = data.get("id")
            if cmd_id in self._pending:
                with self._lock:
                    self._pending[cmd_id]["ok"] = bool(data.get("ok"))
                    self._pending[cmd_id]["event"].set()
            return

        # --- Eventos del gimnasio ---
        if msg.topic.endswith("/event"):
            print(f"📩 Evento MQTT recibido: {data}")
            try:
                asyncio.run(broadcaster.broadcast({
                    "topic": msg.topic,
                    "data": data
                }))
            except RuntimeError:
                # Si ya hay un loop corriendo (caso FastAPI), usar create_task
                asyncio.create_task(broadcaster.broadcast({
                    "topic": msg.topic,
                    "data": data
                }))

    # =====================================================
    # 🔌 Conexión y ciclo de vida
    # =====================================================
    def connect(self, retries=10):
        """Intenta conectar al broker con reintentos exponenciales."""
        backoff = 1.0
        for attempt in range(retries):
            try:
                print(f"🔗 Intentando conectar a {MQTT_BROKER_IP}:{MQTT_PORT} (intento {attempt+1}) ...")
                self.client.connect(MQTT_BROKER_IP, MQTT_PORT, keepalive=30)
                self.client.loop_start()
                return
            except Exception as e:
                print(f"⚠️ Error conectando a MQTT: {e}")
                time.sleep(backoff)
                backoff = min(backoff * 1.8, 10.0)
        raise RuntimeError("❌ No se pudo conectar al broker MQTT tras varios intentos")

    def disconnect(self):
        """Desconecta el cliente MQTT y detiene su loop."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

    # =====================================================
    # 🧠 Utilidades
    # =====================================================
    def ensure_connected(self, timeout=5.0) -> bool:
        return self._connected.wait(timeout=timeout)

    def ensure_sub(self, topic: str, qos: int = 1) -> bool:
        """Suscripción segura e idempotente."""
        with self._lock:
            if topic in self._subs:
                return True
            res, _ = self.client.subscribe(topic, qos=qos)
            if res == mqtt.MQTT_ERR_SUCCESS:
                self._subs.add(topic)
                print(f"📡 Suscrito a topic: {topic}")
                return True
            print(f"⚠️ No se pudo suscribir a {topic} (rc={res})")
            return False

    def publish_json(self, topic: str, payload: dict, qos: int = 1, retain: bool = False) -> bool:
        """Publica un mensaje JSON."""
        try:
            if not self.ensure_connected(timeout=3.0):
                print("⚠️ Publish abortado: MQTT no conectado")
                return False
            msg = json.dumps(payload)
            info = self.client.publish(topic, msg, qos=qos, retain=retain)
            info.wait_for_publish(timeout=3.0)
            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✉️ MQTT publish: {topic} -> {msg}")
                return True
            print(f"⚠️ Falló publish rc={info.rc}")
            return False
        except Exception as e:
            print(f"🔥 Error publicando MQTT: {e}")
            return False

    def publish(self, topic: str, payload: dict) -> bool:
        """Compatibilidad: publish por defecto con QoS=1."""
        return self.publish_json(topic, payload, qos=1, retain=False)

    # =====================================================
    # 📡 Comandos con ACK
    # =====================================================
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


# =====================================================
#  Singleton global
# =====================================================
mqtt_client = MQTTClient()
