from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
from schemas import UsuarioCreate, UsuarioUpdate, UsuarioAccesosUpdate
from routers.dependencies import requiere_admin
from services.usuario_service import (
    get_all_usuarios,
    create_new_usuario,
    update_existing_usuario,
    toggle_usuario_activo,
    reset_usuario_password,
    update_usuario_accesos,
)
from repositories.usuario_repository import list_roles, list_modulos

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.get("/roles")
def listar_roles(_: Dict[str, Any] = Depends(requiere_admin)):
    return list_roles()


@router.get("/modulos")
def listar_modulos(_: Dict[str, Any] = Depends(requiere_admin)):
    return list_modulos()


@router.get("/usuarios")
def listar_usuarios(_: Dict[str, Any] = Depends(requiere_admin)):
    return get_all_usuarios()


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
def crear_usuario(payload: UsuarioCreate, _: Dict[str, Any] = Depends(requiere_admin)):
    try:
        nuevo = create_new_usuario(payload)
        return {"mensaje": "Usuario creado exitosamente", "cui": nuevo["cui"]}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/usuarios/{cui}")
def actualizar_usuario(cui: str, payload: UsuarioUpdate, _: Dict[str, Any] = Depends(requiere_admin)):
    try:
        update_existing_usuario(cui, payload)
        return {"mensaje": "Usuario actualizado"}
    except ValueError as e:
        if "no encontrado" in str(e):
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))


@router.put("/usuarios/{cui}/toggle-activo")
def toggle_activo(cui: str, _: Dict[str, Any] = Depends(requiere_admin)):
    try:
        nuevo_estado = toggle_usuario_activo(cui)
        return {"mensaje": f"Usuario {'activado' if nuevo_estado else 'desactivado'}", "activo": nuevo_estado}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/usuarios/{cui}/reset-password")
def reset_password(cui: str, _: Dict[str, Any] = Depends(requiere_admin)):
    try:
        reset_usuario_password(cui)
        return {"mensaje": f"Contraseña reiniciada a: PalabraMiel2026"}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/usuarios/{cui}/accesos")
def actualizar_accesos(cui: str, payload: UsuarioAccesosUpdate, _: Dict[str, Any] = Depends(requiere_admin)):
    try:
        update_usuario_accesos(cui, payload.rango_id, payload.modulos_ids)
        return {"mensaje": "Accesos actualizados correctamente"}
    except ValueError as e:
        raise HTTPException(404, str(e))
