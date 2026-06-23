from typing import Optional, Dict, Any
from database import supabase


def find_usuario_basico(cui: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("usuarios") \
        .select("cui, nombre_completo, correo") \
        .eq("cui", cui) \
        .execute()
    return res.data[0] if res.data else None


def find_usuario_nombre(cui: str) -> Optional[str]:
    res = supabase.table("usuarios") \
        .select("nombre_completo") \
        .eq("cui", cui) \
        .execute()
    return res.data[0]["nombre_completo"] if res.data else None


def find_usuarios_by_cuis(cuis: list) -> dict:
    res = supabase.table("usuarios") \
        .select("cui, nombre_completo") \
        .in_("cui", cuis) \
        .execute()
    return {u["cui"]: u["nombre_completo"] for u in (res.data or [])}


def find_usuarios_por_nombre(q: str) -> list:
    res = supabase.table("usuarios") \
        .select("cui") \
        .ilike("nombre_completo", f"%{q}%") \
        .execute()
    return [u["cui"] for u in (res.data or [])]


def get_configuracion_correo() -> dict:
    try:
        res = supabase.table("configuracion_correo").select("*").limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return {}


def find_vendedores_por_modulo() -> list:
    res = supabase.table("accesos_usuarios") \
        .select("usuario_cui, usuarios(nombre_completo)") \
        .eq("modulo_id", 1) \
        .execute()
    return res.data or []


def find_all_usuarios_basico() -> list:
    res = supabase.table("usuarios") \
        .select("cui, nombre_completo, correo, created_at") \
        .execute()
    return res.data or []


def find_usuarios_activos() -> list:
    res = supabase.table("usuarios") \
        .select("cui, nombre_completo") \
        .eq("activo", True) \
        .execute()
    return res.data or []
