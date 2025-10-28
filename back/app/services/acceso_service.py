# app/services/acceso_service.py
from sqlalchemy.orm import Session
from datetime import datetime
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.venta_membresia_repository import VentaMembresiaRepository
from app.repositories.asistencia_repository import AsistenciaRepository
from app.models.asistencia import Asistencia
from fastapi import HTTPException
from typing import Literal
from app.utils.notifier import notificar_asistencia

class AccesoService:
    def __init__(self):
        self.cliente_repo = ClienteRepository()
        self.venta_repo = VentaMembresiaRepository()
        self.asistencia_repo = AsistenciaRepository()

    def verificar_acceso(
        self,
        db: Session,
        cliente_id: int,
        *,
        tipo_acceso: Literal["huella", "documento"] = "huella",
        id_sede: int = 1,
    ) -> dict:
        # ================================
        # 🔹 1. Validar existencia del cliente
        # ================================
        cliente = self.cliente_repo.get_by_id(db, id_value=cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # ================================
        # 🔹 2. Buscar membresía activa
        # ================================
        venta_activa = self.venta_repo.find_active_for_client(db, cliente.id)
        if not venta_activa:
            return {
                "permitido": False,
                "mensaje": f"Acceso denegado. {cliente.nombre} no tiene una membresía activa."
            }

        membresia_info = venta_activa.membresia

        # ================================
        # 🔹 3. Verificar vigencia de la membresía
        # ================================
        if venta_activa.fecha_fin and venta_activa.fecha_fin.date() < datetime.now().date():
            return {
                "permitido": False,
                "mensaje": f"Acceso denegado. La membresía de {cliente.nombre} ha expirado."
            }

        # ================================
        # 🔹 4. Validar accesos diarios
        # ================================
        if membresia_info.max_accesos_diarios is not None:
            accesos_hoy = self.asistencia_repo.count_today_for_client(db, cliente.id)
            if accesos_hoy >= membresia_info.max_accesos_diarios:
                return {
                    "permitido": False,
                    "mensaje": f"Acceso denegado. {cliente.nombre} ha excedido los accesos diarios permitidos."
                }

        # ================================
        # 🔹 5. Verificar membresía tipo “tiquetera”
        # ================================
        es_tiquetera = "tiquetera" in membresia_info.nombre_membresia.lower()
        if es_tiquetera and (venta_activa.sesiones_restantes is None or venta_activa.sesiones_restantes <= 0):
            return {
                "permitido": False,
                "mensaje": f"Acceso denegado. {cliente.nombre} no tiene sesiones disponibles."
            }

        # ================================
        # 🔹 6. Registrar asistencia
        # ================================
        nueva_asistencia = Asistencia(
            id_cliente=cliente.id,
            id_venta=venta_activa.id,
            id_sede=id_sede,
            fecha_hora_entrada=datetime.now(),
            tipo_acceso=tipo_acceso,
        )
        db.add(nueva_asistencia)
        db.flush()  # Importante: asigna ID y relaciones antes del commit

        # ================================
        # 🔹 7. Restar sesión si aplica
        # ================================
        if es_tiquetera and venta_activa.sesiones_restantes is not None:
            venta_activa.sesiones_restantes -= 1

        # ================================
        # 🔹 8. Guardar y notificar
        # ================================
        db.commit()
        db.refresh(nueva_asistencia)

        try:
            notificar_asistencia(nueva_asistencia)
        except Exception as e:
            print(f"⚠️ No se pudo notificar asistencia vía MQTT: {e}")

        # ================================
        # 🔹 9. Respuesta final
        # ================================
        return {
            "permitido": True,
            "mensaje": f"¡Bienvenido, {cliente.nombre}!",
            "tipo_membresia": membresia_info.nombre_membresia,
            "tiquetera": es_tiquetera,
            "sesiones_restantes": venta_activa.sesiones_restantes if es_tiquetera else None,
        }
