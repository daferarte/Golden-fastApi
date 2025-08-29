from sqlalchemy.orm import Session
from datetime import datetime
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.venta_membresia_repository import VentaMembresiaRepository
from app.repositories.asistencia_repository import AsistenciaRepository
from app.models.asistencia import Asistencia
from fastapi import HTTPException

class AccesoService:
    def __init__(self):
        # El servicio necesita acceder a varios repositorios
        self.cliente_repo = ClienteRepository()
        self.venta_repo = VentaMembresiaRepository()
        self.asistencia_repo = AsistenciaRepository()

    def verificar_acceso(self, db: Session, cliente_id: int) -> dict:
        """
        Verifica el acceso de un cliente por su ID y registra la asistencia si es válido.
        Devuelve un diccionario con el estado y un mensaje.
        """
        # --- CORRECCIÓN: Usar el nombre de argumento correcto 'id_value' ---
        cliente = self.cliente_repo.get_by_id(db, id_value=cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # 2. Validar que tenga una membresía activa (no vencida)
        venta_activa = self.venta_repo.find_active_for_client(db, cliente.id)
        if not venta_activa:
            return {"permitido": False, "mensaje": f"Acceso denegado. {cliente.nombre} no tiene una membresía activa."}

        # 3. Validar que aún tenga ingresos permitidos (si aplica)
        if venta_activa.sesiones_restantes is not None and venta_activa.sesiones_restantes <= 0:
            return {"permitido": False, "mensaje": f"Acceso denegado. {cliente.nombre} no tiene sesiones disponibles."}

        # 4. Validar que no sobrepase sus ingresos diarios
        membresia_info = venta_activa.membresia # Relación con el modelo Membresia
        
        if membresia_info.max_accesos_diarios is not None:
            accesos_hoy = self.asistencia_repo.count_today_for_client(db, cliente.id)
            if accesos_hoy >= membresia_info.max_accesos_diarios:
                return {"permitido": False, "mensaje": f"Acceso denegado. {cliente.nombre} ha excedido los accesos diarios."}

        # --- Si todas las validaciones pasan, el acceso es PERMITIDO ---
        
        # a. Registrar la nueva asistencia
        nueva_asistencia = Asistencia(
            id_cliente=cliente.id,
            id_venta=venta_activa.id,
            id_sede=1,  # Puedes hacer esto dinámico si tienes varias sedes
            fecha_hora_entrada=datetime.now(),
            tipo_acceso="huella"
        )
        db.add(nueva_asistencia)
        
        # b. Descontar una sesión si la membresía tiene un límite
        if venta_activa.sesiones_restantes is not None:
            venta_activa.sesiones_restantes -= 1
        
        db.commit()

        return {"permitido": True, "mensaje": f"¡Bienvenido, {cliente.nombre}!"}