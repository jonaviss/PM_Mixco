from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from schemas import PerfilUpdate, PasswordChange
from routers.dependencies import obtener_usuario_actual
from services.usuario_service import update_profile, change_password
from repositories.usuario_repository import find_user_by_cui

router = APIRouter(prefix="/usuario", tags=["Perfil"])


@router.get("/perfil")
def obtener_perfil(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    user = find_user_by_cui(usuario_actual["sub"])
    if not user:
        raise HTTPException(404, "Usuario no encontrado.")
    return {
        "cui": user["cui"],
        "nombre_completo": user.get("nombre_completo", ""),
        "correo": user.get("correo", ""),
        "telegram_chat_id": user.get("telegram_chat_id") or ""
    }


@router.put("/perfil")
def actualizar_perfil(
    payload: PerfilUpdate,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual),
):
    try:
        update_profile(usuario_actual["sub"], payload.nombre_completo, payload.correo, payload.telegram_chat_id)
        return {"mensaje": "Perfil actualizado correctamente"}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/cambiar-contrasena")
def cambiar_contrasena(
    payload: PasswordChange,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual),
):
    try:
        change_password(usuario_actual["sub"], payload.contrasena_actual, payload.contrasena_nueva)
        return {"mensaje": "Contraseña actualizada correctamente"}
    except ValueError as e:
        if "no es correcta" in str(e):
            raise HTTPException(400, str(e))
        raise HTTPException(404, str(e))
