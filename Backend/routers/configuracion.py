from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from routers.dependencies import obtener_usuario_actual
from typing import Dict, Any
from datetime import datetime, timezone

router = APIRouter(prefix="/configuracion", tags=["Configuración"])

# ======================== TIPOS DE PRODUCTO ========================
@router.get("/tipos-producto")
async def listar_tipos_producto(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("tipos_producto").select("*").order("nombre").execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.post("/tipos-producto", status_code=201)
async def crear_tipo_producto(data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        nombre = data.get("nombre", "").strip()
        if not nombre:
            raise HTTPException(400, "El nombre es obligatorio")
        res = supabase.table("tipos_producto").insert({"nombre": nombre}).execute()
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.put("/tipos-producto/{tipo_id}")
async def actualizar_tipo_producto(tipo_id: int, data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("tipos_producto").update(data).eq("id", tipo_id).execute()
        if not res.data:
            raise HTTPException(404, "Tipo de producto no encontrado")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.delete("/tipos-producto/{tipo_id}")
async def eliminar_tipo_producto(tipo_id: int, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("tipos_producto").delete().eq("id", tipo_id).execute()
        if not res.data:
            raise HTTPException(404, "Tipo de producto no encontrado")
        return {"mensaje": "Tipo de producto eliminado"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# ======================== MÉTODOS DE PAGO ========================
@router.get("/metodos-pago")
async def listar_metodos_pago(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("cat_metodos_pago").select("*").order("nombre").execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.post("/metodos-pago", status_code=201)
async def crear_metodo_pago(data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        nombre = data.get("nombre", "").strip()
        if not nombre:
            raise HTTPException(400, "El nombre es obligatorio")
        res = supabase.table("cat_metodos_pago").insert({"nombre": nombre}).execute()
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.put("/metodos-pago/{metodo_id}")
async def actualizar_metodo_pago(metodo_id: int, data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("cat_metodos_pago").update(data).eq("id", metodo_id).execute()
        if not res.data:
            raise HTTPException(404, "Método de pago no encontrado")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.delete("/metodos-pago/{metodo_id}")
async def eliminar_metodo_pago(metodo_id: int, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("cat_metodos_pago").delete().eq("id", metodo_id).execute()
        if not res.data:
            raise HTTPException(404, "Método de pago no encontrado")
        return {"mensaje": "Método de pago eliminado"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# ======================== CONFIGURACIÓN DE CORREO ========================
@router.get("/correo")
async def obtener_configuracion_correo(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("configuracion_correo").select("*").limit(1).execute()
        config = res.data[0] if res.data else {}
        if config.get("smtp_password"):
            config["smtp_password"] = "********"
        return config
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.put("/correo")
async def actualizar_configuracion_correo(data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        smtp_user = data.get("smtp_user", "").strip()
        smtp_password = data.get("smtp_password", "").strip()
        if not smtp_user or not smtp_password:
            raise HTTPException(400, "Usuario y contraseña son obligatorios")
        res = supabase.table("configuracion_correo").select("*").limit(1).execute()
        if res.data:
            supabase.table("configuracion_correo").update({
                "smtp_user": smtp_user,
                "smtp_password": smtp_password,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", res.data[0]["id"]).execute()
        else:
            supabase.table("configuracion_correo").insert({
                "smtp_user": smtp_user,
                "smtp_password": smtp_password
            }).execute()
        return {"mensaje": "Configuración de correo actualizada"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
