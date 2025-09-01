from fastapi import APIRouter
from app.api.v1 import (
    cliente, sedes, membresias, ventas_membresias, asistencias,
    facturas, detalles_facturas, usuarios, roles, tipos_descuento, reportes_asistencia, acceso, dispositivo_router,
    uploads, reportes
)

api_router = APIRouter()

api_router.include_router(dispositivo_router.router, prefix="/dispositivo", tags=["Control Dispositivo"])
api_router.include_router(acceso.router, prefix="/acceso", tags=["Control de Acceso"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(cliente.router, prefix="/clientes", tags=["Clientes"])
api_router.include_router(sedes.router, prefix="/sedes", tags=["Sedes"])
api_router.include_router(membresias.router, prefix="/membresias", tags=["Membresías"])
api_router.include_router(ventas_membresias.router, prefix="/ventas-membresias", tags=["Ventas Membresías"])
api_router.include_router(asistencias.router, prefix="/asistencias", tags=["Asistencias"])
api_router.include_router(facturas.router, prefix="/facturas", tags=["Facturas"])
api_router.include_router(detalles_facturas.router, prefix="/detalles-facturas", tags=["Detalles Facturas"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(tipos_descuento.router, prefix="/tipos-descuento", tags=["Tipos Descuento"])
api_router.include_router(reportes_asistencia.router, prefix="/reportes-asistencia", tags=["Reportes Asistencia"])
api_router.include_router(reportes.router)