from fastapi import APIRouter, HTTPException, status, Depends
from database import supabase, verificar_contrasena
from routers.dependencies import obtener_usuario_actual
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import bcrypt

router = APIRouter(prefix="/admin", tags=["Administración"])


class UsuarioCreate(BaseModel):
    cui: str = Field(..., min_length=13, max_length=13)
    nombre_completo: str
    contrasena: str = Field(..., min_length=6)
    correo: Optional[str] = None
    rango_id: int
    modulos_ids: List[int] = Field(default_factory=list)


class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None
    activo: Optional[bool] = None
    contrasena: Optional[str] = None


class UsuarioAccesosUpdate(BaseModel):
    rango_id: int
    modulos_ids: List[int] = Field(default_factory=list)


def requiere_admin(payload: Dict[str, Any]):
    if payload.get("rango") not in ["administrador", "super_admin"]:
        raise HTTPException(403, "Solo administradores pueden acceder a este módulo.")
    return payload


@router.get("/roles")
async def listar_roles(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    requiere_admin(usuario_actual)
    try:
        res = supabase.table("rangos").select("*").execute()
        return (res.data or [])
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/modulos")
async def listar_modulos(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    requiere_admin(usuario_actual)
    try:
        res = supabase.table("modulos").select("*").execute()
        return (res.data or [])
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/usuarios")
async def listar_usuarios(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    requiere_admin(usuario_actual)
    try:
        res = supabase.table("usuarios").select("cui, nombre_completo, correo, activo, created_at").order("created_at", desc=True).execute()
        usuarios = res.data or []
        for u in usuarios:
            res_accesos = supabase.table("accesos_usuarios") \
                .select("rango_id, rangos(nombre), modulo_id, modulos(nombre)") \
                .eq("usuario_cui", u["cui"]) \
                .execute()
            if res_accesos.data:
                u["rango_id"] = res_accesos.data[0]["rango_id"]
                u["rango_nombre"] = res_accesos.data[0]["rangos"]["nombre"]
                u["modulos"] = [
                    {"id": a["modulo_id"], "nombre": a["modulos"]["nombre"]}
                    for a in res_accesos.data if a.get("modulos")
                ]
            else:
                u["rango_id"] = None
                u["rango_nombre"] = "cliente"
                u["modulos"] = []
        return usuarios
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
async def crear_usuario(payload: UsuarioCreate, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    requiere_admin(usuario_actual)
    try:
        res_exist = supabase.table("usuarios").select("cui").eq("cui", payload.cui).execute()
        if res_exist.data:
            raise HTTPException(400, f"El CUI {payload.cui} ya está registrado.")
        contrasena_hash = bcrypt.hashpw(payload.contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        usuario_data = {
            "cui": payload.cui,
            "nombre_completo": payload.nombre_completo,
            "contrasena_hash": contrasena_hash,
            "activo": True,
            "correo": payload.correo or None
        }
        res = supabase.table("usuarios").insert(usuario_data).execute()
        nuevo = res.data[0]
        for modulo_id in payload.modulos_ids:
            supabase.table("accesos_usuarios").insert({
                "usuario_cui": payload.cui,
                "rango_id": payload.rango_id,
                "modulo_id": modulo_id
            }).execute()
        return {"mensaje": "Usuario creado exitosamente", "cui": nuevo["cui"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.put("/usuarios/{cui}")
async def actualizar_usuario(cui: str, payload: UsuarioUpdate, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    requiere_admin(usuario_actual)
    try:
        res_exist = supabase.table("usuarios").select("cui").eq("cui", cui).execute()
        if not res_exist.data:
            raise HTTPException(404, "Usuario no encontrado.")
        update_data = payload.model_dump(exclude_none=True)
        if "contrasena" in update_data:
            update_data["contrasena_hash"] = bcrypt.hashpw(
                update_data.pop("contrasena").encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
        if not update_data:
            raise HTTPException(400, "No se enviaron campos para actualizar.")
        supabase.table("usuarios").update(update_data).eq("cui", cui).execute()
        return {"mensaje": "Usuario actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.put("/usuarios/{cui}/toggle-activo")
async def toggle_activo_usuario(cui: str, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    requiere_admin(usuario_actual)
    try:
        res = supabase.table("usuarios").select("activo").eq("cui", cui).execute()
        if not res.data:
            raise HTTPException(404, "Usuario no encontrado.")
        nuevo_estado = not res.data[0]["activo"]
        supabase.table("usuarios").update({"activo": nuevo_estado}).eq("cui", cui).execute()
        return {"mensaje": f"Usuario {'activado' if nuevo_estado else 'desactivado'}", "activo": nuevo_estado}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/usuarios/{cui}/reset-password")
async def reset_password_usuario(cui: str, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    requiere_admin(usuario_actual)
    try:
        res_exist = supabase.table("usuarios").select("cui").eq("cui", cui).execute()
        if not res_exist.data:
            raise HTTPException(404, "Usuario no encontrado.")
        DEFAULT_PASSWORD = "PalabraMiel2026"
        contrasena_hash = bcrypt.hashpw(DEFAULT_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        supabase.table("usuarios").update({"contrasena_hash": contrasena_hash}).eq("cui", cui).execute()
        return {"mensaje": f"Contraseña reiniciada a: {DEFAULT_PASSWORD}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.put("/usuarios/{cui}/accesos")
async def actualizar_accesos(cui: str, payload: UsuarioAccesosUpdate, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    requiere_admin(usuario_actual)
    try:
        res_exist = supabase.table("usuarios").select("cui").eq("cui", cui).execute()
        if not res_exist.data:
            raise HTTPException(404, "Usuario no encontrado.")
        supabase.table("accesos_usuarios").delete().eq("usuario_cui", cui).execute()
        for modulo_id in payload.modulos_ids:
            supabase.table("accesos_usuarios").insert({
                "usuario_cui": cui,
                "rango_id": payload.rango_id,
                "modulo_id": modulo_id
            }).execute()
        return {"mensaje": "Accesos actualizados correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
