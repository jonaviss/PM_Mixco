from typing import List, Optional, Dict, Any
from database import supabase


def find_user_by_cui(cui: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("usuarios").select("*").eq("cui", cui).execute()
    return res.data[0] if res.data else None


def list_all_usuarios() -> List[Dict[str, Any]]:
    res = supabase.table("usuarios") \
        .select("cui, nombre_completo, correo, activo, created_at") \
        .order("created_at", desc=True) \
        .execute()
    return res.data or []


def find_accesos_by_cui(cui: str) -> List[Dict[str, Any]]:
    res = supabase.table("accesos_usuarios") \
        .select("rango_id, rangos(nombre), modulo_id, modulos(nombre)") \
        .eq("usuario_cui", cui) \
        .execute()
    return res.data or []


def create_usuario(data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("usuarios").insert(data).execute()
    return res.data[0]


def update_usuario(cui: str, data: Dict[str, Any]) -> None:
    supabase.table("usuarios").update(data).eq("cui", cui).execute()


def delete_accesos_by_cui(cui: str) -> None:
    supabase.table("accesos_usuarios").delete().eq("usuario_cui", cui).execute()


def create_acceso(usuario_cui: str, rango_id: int, modulo_id: int) -> None:
    supabase.table("accesos_usuarios").insert({
        "usuario_cui": usuario_cui,
        "rango_id": rango_id,
        "modulo_id": modulo_id
    }).execute()


def list_roles() -> List[Dict[str, Any]]:
    res = supabase.table("rangos").select("*").execute()
    return res.data or []


def list_modulos() -> List[Dict[str, Any]]:
    res = supabase.table("modulos").select("*").execute()
    return res.data or []


def find_user_hash(cui: str) -> Optional[str]:
    res = supabase.table("usuarios") \
        .select("contrasena_hash") \
        .eq("cui", cui) \
        .execute()
    return res.data[0]["contrasena_hash"] if res.data else None
