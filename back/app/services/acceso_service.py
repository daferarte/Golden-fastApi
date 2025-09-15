# app/services/acceso_service.py
from sqlalchemy.orm import Session
from datetime import datetime
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.venta_membresia_repository import VentaMembresiaRepository
from app.repositories.asistencia_repository import AsistenciaRepository
from app.models.asistencia import Asistencia
from fastapi import HTTPException
from typing import Literal

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
        cliente = self.cliente_repo.get_by_id(db, id_value=cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        venta_activa = self.venta_repo.find_active_for_client(db, cliente.id)
        if not venta_activa:
            return {"permitido": False, "mensaje": f"Acceso denegado. {cliente.nombre} no tiene una membresía activa."}

        if venta_activa.sesiones_restantes is not None and venta_activa.sesiones_restantes <= 0:
            return {"permitido": False, "mensaje": f"Acceso denegado. {cliente.nombre} no tiene sesiones disponibles."}

        membresia_info = venta_activa.membresia
        if membresia_info.max_accesos_diarios is not None:
            accesos_hoy = self.asistencia_repo.count_today_for_client(db, cliente.id)
            if accesos_hoy >= membresia_info.max_accesos_diarios:
                return {"permitido": False, "mensaje": f"Acceso denegado. {cliente.nombre} ha excedido los accesos diarios."}

        nueva_asistencia = Asistencia(
            id_cliente=cliente.id,
            id_venta=venta_activa.id,
            id_sede=id_sede,
            fecha_hora_entrada=datetime.now(),
            tipo_acceso=tipo_acceso,   # <- aquí usamos el método real
        )
        db.add(nueva_asistencia)

        if venta_activa.sesiones_restantes is not None:
            venta_activa.sesiones_restantes -= 1
        
        db.commit()
        return {"permitido": True, "mensaje": f"¡Bienvenido, {cliente.nombre}!"}
