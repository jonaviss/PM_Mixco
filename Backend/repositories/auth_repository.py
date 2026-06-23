from typing import List, Optional, Dict, Any
from database import supabase


def find_active_user_by_cui(cui: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("usuarios") \
        .select("cui, nombre_completo, contrasena_hash, activo") \
        .eq("cui", cui) \
        .eq("activo", True) \
        .execute()
    return res.data[0] if res.data else None


def find_accesos_by_cui(cui: str) -> List[Dict[str, Any]]:
    res = supabase.table("accesos_usuarios") \
        .select("rango_id, rangos(nombre), modulo_id, modulos(nombre)") \
        .eq("usuario_cui", cui) \
        .execute()
    return res.data or []


def find_user_names_by_cui(cuis: List[str]) -> Dict[str, str]:
    if not cuis:
        return {}
    res = supabase.table("usuarios") \
        .select("cui, nombre_completo") \
        .in_("cui", cuis) \
        .execute()
    return {u["cui"]: u["nombre_completo"] for u in (res.data or [])}
