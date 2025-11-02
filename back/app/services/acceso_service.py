# app/services/acceso_service.py
from sqlalchemy.orm import Session
from datetime import datetime, date
from fastapi import HTTPException
from typing import Literal
from app.models.asistencia import Asistencia
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.venta_membresia_repository import VentaMembresiaRepository
from app.repositories.asistencia_repository import AsistenciaRepository
from app.utils.notifier import notificar_asistencia


class AccesoService:
    def __init__(self):
        self.cliente_repo = ClienteRepository()
        self.venta_repo = VentaMembresiaRepository()
        self.asistencia_repo = AsistenciaRepository()

    # ============================================================
    # 🔹 Método auxiliar centralizado para registrar el evento
    # ============================================================
    def _registrar_evento(
        self,
        db: Session,
        cliente,
        permitido: bool,
        mensaje: str,
        tipo_acceso: str,
        id_venta: int | None = None,
        id_sede: int = 1,
        extra_data: dict | None = None,
    ):
        """
        Registra en la base de datos un evento de asistencia:
        - permitido=True → acceso exitoso.
        - permitido=False → intento fallido con motivo_error.
        También emite una notificación enriquecida.
        """
        nueva_asistencia = Asistencia(
            id_cliente=cliente.id,
            id_venta=id_venta,
            id_sede=id_sede,
            fecha_hora_entrada=datetime.now(),
            tipo_acceso=tipo_acceso,
            motivo_error=None if permitido else mensaje,
        )
        db.add(nueva_asistencia)
        db.commit()
        db.refresh(nueva_asistencia)

        # ============================================================
        # 🔔 Construir payload de notificación enriquecido
        # ============================================================
        payload = {
            "permitido": permitido,
            "mensaje": mensaje,
            "id_asistencia": nueva_asistencia.id,
            "nombre": f"{cliente.nombre} {cliente.apellido}".strip(),
            "documento": cliente.documento,
            "foto": cliente.fotografia,
            "hora": nueva_asistencia.fecha_hora_entrada.strftime("%H:%M:%S"),
            "tipo_acceso": tipo_acceso,
        }

        # Si hay datos extra (membresía, sesiones, vencimiento, etc.)
        if extra_data:
            payload.update(extra_data)

        try:
            notificar_asistencia(payload)
        except Exception as e:
            print(f"⚠️ No se pudo notificar asistencia vía MQTT: {e}")

        return nueva_asistencia

    # ============================================================
    # 🔹 Lógica principal de verificación de acceso
    # ============================================================
    def verificar_acceso(
        self,
        db: Session,
        cliente_id: int,
        *,
        tipo_acceso: Literal["huella", "documento"] = "huella",
        id_sede: int = 1,
    ) -> dict:
        # --- Validar existencia del cliente ---
        cliente = self.cliente_repo.get_by_id(db, id_value=cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # --- Buscar membresía activa ---
        venta_activa = self.venta_repo.find_active_for_client(db, cliente.id)
        if not venta_activa:
            mensaje = f"Acceso denegado. {cliente.nombre} no tiene una membresía activa."
            self._registrar_evento(db, cliente, False, mensaje, tipo_acceso)
            return {"permitido": False, "mensaje": mensaje}

        membresia_info = venta_activa.membresia
        es_tiquetera = "tiquetera" in membresia_info.nombre_membresia.lower()

        # --- Días restantes ---
        dias_restantes = None
        if venta_activa.fecha_fin:
            dias_restantes = (venta_activa.fecha_fin.date() - date.today()).days

        # --- Verificar vigencia ---
        if venta_activa.fecha_fin and venta_activa.fecha_fin.date() < datetime.now().date():
            mensaje = f"Acceso denegado. La membresía de {cliente.nombre} ha expirado."
            self._registrar_evento(
                db,
                cliente,
                False,
                mensaje,
                tipo_acceso,
                venta_activa.id,
                extra_data={
                    "tipo_membresia": membresia_info.nombre_membresia,
                    "sesiones_restantes": venta_activa.sesiones_restantes,
                    "dias_restantes": dias_restantes,
                },
            )
            return {"permitido": False, "mensaje": mensaje}

        # --- Límite de accesos diarios ---
        if membresia_info.max_accesos_diarios is not None:
            accesos_hoy = self.asistencia_repo.count_today_for_client(db, cliente.id)
            if accesos_hoy >= membresia_info.max_accesos_diarios:
                mensaje = f"Acceso denegado. {cliente.nombre} ha excedido los accesos diarios permitidos."
                self._registrar_evento(
                    db,
                    cliente,
                    False,
                    mensaje,
                    tipo_acceso,
                    venta_activa.id,
                    extra_data={
                        "tipo_membresia": membresia_info.nombre_membresia,
                        "sesiones_restantes": venta_activa.sesiones_restantes,
                        "dias_restantes": dias_restantes,
                    },
                )
                return {"permitido": False, "mensaje": mensaje}

        # --- Membresía tipo tiquetera ---
        if es_tiquetera and (venta_activa.sesiones_restantes is None or venta_activa.sesiones_restantes <= 0):
            mensaje = f"Acceso denegado. {cliente.nombre} no tiene sesiones disponibles."
            self._registrar_evento(
                db,
                cliente,
                False,
                mensaje,
                tipo_acceso,
                venta_activa.id,
                extra_data={
                    "tipo_membresia": membresia_info.nombre_membresia,
                    "sesiones_restantes": venta_activa.sesiones_restantes,
                    "dias_restantes": dias_restantes,
                },
            )
            return {"permitido": False, "mensaje": mensaje}

        # ----------------------------------------------------------
        # ✅ Si pasa todas las validaciones → acceso exitoso
        # ----------------------------------------------------------
        nueva_asistencia = self._registrar_evento(
            db=db,
            cliente=cliente,
            permitido=True,
            mensaje=f"Acceso permitido para {cliente.nombre}",
            tipo_acceso=tipo_acceso,
            id_venta=venta_activa.id,
            id_sede=id_sede,
            extra_data={
                "tipo_membresia": membresia_info.nombre_membresia,
                "sesiones_restantes": venta_activa.sesiones_restantes,
                "dias_restantes": dias_restantes,
            },
        )

        # --- Restar sesión si aplica ---
        if es_tiquetera and venta_activa.sesiones_restantes is not None:
            venta_activa.sesiones_restantes -= 1
            db.commit()

        # --- Respuesta final ---
        return {
            "permitido": True,
            "mensaje": f"¡Bienvenido, {cliente.nombre}!",
            "tipo_membresia": membresia_info.nombre_membresia,
            "tiquetera": es_tiquetera,
            "sesiones_restantes": venta_activa.sesiones_restantes if es_tiquetera else None,
            "dias_restantes": dias_restantes,
            "asistencia_id": nueva_asistencia.id,
        }
