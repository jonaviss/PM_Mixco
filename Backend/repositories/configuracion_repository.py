from typing import List, Dict, Any, Optional
from database import supabase
from datetime import datetime, timezone


def list_all(table: str) -> List[Dict[str, Any]]:
    res = supabase.table(table).select("*").order("nombre").execute()
    return res.data or []


def insert(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table(table).insert(data).execute()
    return res.data[0]


def update(table: str, id_column: str, id_value: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    res = supabase.table(table).update(data).eq(id_column, id_value).execute()
    return res.data[0] if res.data else None


def delete(table: str, id_column: str, id_value: Any) -> bool:
    res = supabase.table(table).delete().eq(id_column, id_value).execute()
    return len(res.data) > 0


def get_configuracion_correo_first() -> Optional[Dict[str, Any]]:
    res = supabase.table("configuracion_correo").select("*").limit(1).execute()
    return res.data[0] if res.data else None


def upsert_configuracion_correo(smtp_user: str, smtp_password: str) -> None:
    existing = get_configuracion_correo_first()
    data = {
        "smtp_user": smtp_user,
        "smtp_password": smtp_password,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if existing:
        supabase.table("configuracion_correo").update(data).eq("id", existing["id"]).execute()
    else:
        supabase.table("configuracion_correo").insert(data).execute()
