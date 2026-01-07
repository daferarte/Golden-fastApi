# app/services/acceso_service.py
from sqlalchemy.orm import Session
from datetime import datetime, date
from fastapi import HTTPException
from typing import Literal
from threading import Thread

from app.models.asistencia import Asistencia
from app.models.usuario import Usuario
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.venta_membresia_repository import VentaMembresiaRepository
from app.repositories.asistencia_repository import AsistenciaRepository
from app.utils.notifier import notificar_asistencia


class AccesoService:
    def __init__(self):
        self.cliente_repo = ClienteRepository()
        self.venta_repo = VentaMembresiaRepository()
        self.asistencia_repo = AsistenciaRepository()

    # -----------------------------------------------------
    # 🔸 Método interno: registra evento y dispara notificación
    # -----------------------------------------------------
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
    ) -> Asistencia:
        nueva_asistencia = Asistencia(
            id_cliente=cliente.id,
            id_venta=id_venta,
            id_sede=id_sede,
            fecha_hora_entrada=datetime.now(),
            tipo_acceso=tipo_acceso,
            motivo_error=None if permitido else mensaje,
        )
        db.add(nueva_asistencia)
        db.flush()  # Asigna el ID sin hacer commit

        # 🔔 Payload enriquecido
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
        if extra_data:
            payload.update(extra_data)

        # 🔸 Lanzar notificación en hilo aparte (no bloqueante)
        Thread(target=lambda: notificar_asistencia(payload)).start()

        return nueva_asistencia

    # -----------------------------------------------------
    # 🔹 Lógica principal
    # -----------------------------------------------------
    def verificar_acceso(
        self,
        db: Session,
        cliente_id: int,
        *,
        tipo_acceso: Literal["huella", "documento"] = "huella",
        id_sede: int = 1,
    ) -> dict:
        # 1️⃣ Buscar cliente
        cliente = self.cliente_repo.get_by_id(db, id_value=cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # 1.5️⃣ Verificar si es Usuario del Sistema (acceso ilimitado)
        usuario_sistema = db.query(Usuario).filter(Usuario.id_cliente == cliente.id, Usuario.activo == True).first()
        if usuario_sistema:
             self._registrar_evento(
                db,
                cliente,
                True,
                f"Acceso ADMINISTRATIVO concedido",
                tipo_acceso,
                id_sede=id_sede,
                extra_data={
                    "tipo_membresia": "STAFF",
                    "es_admin": True
                }
            )
             db.commit()
             return {
                "permitido": True,
                "mensaje": f"¡Hola Acceso Staff",
                "tipo_membresia": "ADMINISTRATIVO",
                "tiquetera": False,
                "sesiones_restantes": None,
                "dias_restantes": 9999,
                "asistencia_id": 0, # O el id real si lo devolvemos
            }

        # 2️⃣ Buscar membresía activa
        venta = self.venta_repo.find_active_for_client(db, cliente.id)
        if not venta:
            msg = f"no tiene una membresía activa."
            self._registrar_evento(db, cliente, False, msg, tipo_acceso)
            db.commit()
            return {"permitido": False, "mensaje": f"Acceso denegado. {msg}"}

        m = venta.membresia
        es_tiquetera = "tiquetera" in m.nombre_membresia.lower()
        dias_restantes = (
            (venta.fecha_fin.date() - date.today()).days if venta.fecha_fin else None
        )

        # 3️⃣ Validaciones
        motivos_error = []
        if venta.fecha_fin and venta.fecha_fin.date() < date.today():
            motivos_error.append("La membresía ha expirado.")
        if m.max_accesos_diarios and (
            self.asistencia_repo.count_today_for_client(db, cliente.id)
            >= m.max_accesos_diarios
        ):
            motivos_error.append("Ha excedido los accesos diarios permitidos.")
        if es_tiquetera and (
            not venta.sesiones_restantes or venta.sesiones_restantes <= 0
        ):
            motivos_error.append("No tiene sesiones disponibles.")

        # 4️⃣ Si hay errores → registrar intento fallido
        if motivos_error:
            msg = " ".join(motivos_error)
            self._registrar_evento(
                db,
                cliente,
                False,
                f"Acceso denegado. {msg}",
                tipo_acceso,
                venta.id,
                id_sede,
                extra_data={
                    "tipo_membresia": m.nombre_membresia,
                    "sesiones_restantes": venta.sesiones_restantes,
                    "dias_restantes": dias_restantes,
                },
            )
            db.commit()
            return {"permitido": False, "mensaje": msg}

        # 5️⃣ Registrar acceso exitoso
        nueva_asistencia = self._registrar_evento(
            db,
            cliente,
            True,
            f"Acceso permitido para {cliente.nombre}",
            tipo_acceso,
            venta.id,
            id_sede,
            extra_data={
                "tipo_membresia": m.nombre_membresia,
                "sesiones_restantes": venta.sesiones_restantes,
                "dias_restantes": dias_restantes,
            },
        )

        # 6️⃣ Actualizar sesiones (solo si tiquetera)
        if es_tiquetera and venta.sesiones_restantes is not None:
            venta.sesiones_restantes -= 1

        # ✅ Un solo commit al final
        db.commit()

        return {
            "permitido": True,
            "mensaje": f"¡Bienvenido, {cliente.nombre}!",
            "tipo_membresia": m.nombre_membresia,
            "tiquetera": es_tiquetera,
            "sesiones_restantes": venta.sesiones_restantes if es_tiquetera else None,
            "dias_restantes": dias_restantes,
            "asistencia_id": nueva_asistencia.id,
        }
