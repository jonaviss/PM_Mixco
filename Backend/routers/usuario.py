from fastapi import APIRouter, HTTPException, Depends
from database import supabase, verificar_contrasena
from routers.dependencies import obtener_usuario_actual
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import bcrypt

router = APIRouter(prefix="/usuario", tags=["Perfil"])


class PerfilUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None


class PasswordChange(BaseModel):
    contrasena_actual: str
    contrasena_nueva: str = Field(..., min_length=6)


@router.put("/perfil")
async def actualizar_perfil(
    payload: PerfilUpdate,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    cui = usuario_actual["sub"]
    try:
        update_data = payload.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "No se enviaron campos para actualizar.")
        supabase.table("usuarios").update(update_data).eq("cui", cui).execute()
        return {"mensaje": "Perfil actualizado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.put("/cambiar-contrasena")
async def cambiar_contrasena(
    payload: PasswordChange,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    cui = usuario_actual["sub"]
    try:
        res = supabase.table("usuarios") \
            .select("contrasena_hash") \
            .eq("cui", cui) \
            .execute()
        if not res.data:
            raise HTTPException(404, "Usuario no encontrado.")
        if not verificar_contrasena(payload.contrasena_actual, res.data[0]["contrasena_hash"]):
            raise HTTPException(400, "La contraseña actual no es correcta.")
        contrasena_hash = bcrypt.hashpw(
            payload.contrasena_nueva.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        supabase.table("usuarios").update({"contrasena_hash": contrasena_hash}).eq("cui", cui).execute()
        return {"mensaje": "Contraseña actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
