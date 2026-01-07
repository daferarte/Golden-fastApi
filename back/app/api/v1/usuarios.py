from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.usuario_service import UsuarioService
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.schemas.usuario_self_update import UsuarioSelfUpdate
from app.api import deps

router = APIRouter()
service = UsuarioService()

# Definimos quien puede gestionar usuarios
permitir_solo_duenos = deps.RoleChecker(["dueño"])

@router.post("/", response_model=UsuarioResponse, dependencies=[Depends(permitir_solo_duenos)])
def create_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    # Validar si el usuario ya existe
    existing = service.repository.get_by_username(db, data.nombre_usuario)
    if existing:
         raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    return service.create(db, data)

@router.get("/", response_model=list[UsuarioResponse], dependencies=[Depends(permitir_solo_duenos)])
def list_usuarios(db: Session = Depends(get_db)):
    return service.get_all(db)

@router.get("/me", response_model=UsuarioResponse)
def get_user_me(current_user = Depends(deps.get_current_active_user)):
    """Obtener el usuario logueado actualmente"""
    return current_user

@router.put("/me", response_model=UsuarioResponse)
def update_user_me(
    data: UsuarioSelfUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_active_user)
):
    """Actualizar datos propios (incluyendo contraseña)"""
    updated = service.update(db, current_user.id, data)
    return updated

@router.get("/{usuario_id}", response_model=UsuarioResponse, dependencies=[Depends(permitir_solo_duenos)])
def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = service.get_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.put("/{usuario_id}", response_model=UsuarioResponse, dependencies=[Depends(permitir_solo_duenos)])
def update_usuario(usuario_id: int, data: UsuarioUpdate, db: Session = Depends(get_db)):
    updated = service.update(db, usuario_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return updated

@router.delete("/{usuario_id}", dependencies=[Depends(permitir_solo_duenos)])
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    deleted = service.delete(db, usuario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Usuario eliminado correctamente"}
