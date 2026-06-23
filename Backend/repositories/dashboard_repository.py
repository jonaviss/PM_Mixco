from typing import List, Dict, Any, Optional
from database import supabase


def find_ventas_dia(inicio_dia: str, cui_filtro: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas").select("total_venta, estado_pago").gte("created_at", inicio_dia)
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return res.data or []


def find_creditos_pendientes(cui_filtro: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas").select("total_venta, total_pagado").in_("estado_pago", ["pendiente", "parcial"])
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return res.data or []


def find_ventas_mes(inicio_mes: str, cui_filtro: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas").select("total_venta").gte("created_at", inicio_mes)
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return res.data or []


def count_actividad_total(cui_filtro: Optional[str] = None) -> int:
    q = supabase.table("libreria_ventas").select("id", count="exact")
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return res.count or 0


def find_actividad_paginada(offset: int, por_pagina: int, cui_filtro: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas") \
        .select("id, comprador_cui, total_venta, total_pagado, estado_pago, created_at, digitado_por") \
        .order("created_at", desc=True) \
        .range(offset, offset + por_pagina - 1)
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return res.data or []
