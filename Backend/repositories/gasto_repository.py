from typing import List, Dict, Any, Optional
from database import supabase


def create_gasto(data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("gastos").insert(data).execute()
    return res.data[0]


def update_gasto(gasto_id: str, data: Dict[str, Any]) -> None:
    supabase.table("gastos").update(data).eq("id", gasto_id).execute()


def delete_gasto(gasto_id: str) -> None:
    supabase.table("gastos").delete().eq("id", gasto_id).execute()


def find_gasto_by_id(gasto_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("gastos").select("*").eq("id", gasto_id).execute()
    return res.data[0] if res.data else None


def list_gastos(inicio: str, fin: str, pagina: int, por_pagina: int) -> dict:
    offset = (pagina - 1) * por_pagina
    res = supabase.table("gastos") \
        .select("*", count="exact") \
        .gte("fecha_gasto", inicio) \
        .lte("fecha_gasto", fin) \
        .order("fecha_gasto", desc=True) \
        .range(offset, offset + por_pagina - 1) \
        .execute()
    return {"data": res.data or [], "total": res.count or 0}


def sum_gastos_periodo(inicio: str, fin: str) -> float:
    res = supabase.table("gastos") \
        .select("monto") \
        .gte("fecha_gasto", inicio) \
        .lte("fecha_gasto", fin) \
        .execute()
    return sum(float(g["monto"]) for g in (res.data or []))
