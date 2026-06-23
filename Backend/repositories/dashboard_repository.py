from typing import List, Dict, Any, Optional
from database import supabase


def find_ventas_dia(inicio_dia: str, cui_filtro: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas").select("total_venta, estado_pago").gte("created_at", inicio_dia).neq("estado", "cancelada")
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return res.data or []


def find_creditos_pendientes(cui_filtro: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas").select("total_venta, total_pagado").in_("estado_pago", ["pendiente", "parcial"]).neq("estado", "cancelada")
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return res.data or []


def find_ventas_mes(inicio_mes: str, cui_filtro: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas").select("total_venta").gte("created_at", inicio_mes).neq("estado", "cancelada")
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return res.data or []


def find_ventas_pagadas_periodo(inicio: str, fin: str, cui_filtro: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas") \
        .select("id, total_venta") \
        .gte("created_at", inicio) \
        .lte("created_at", fin) \
        .eq("estado_pago", "pagado") \
        .neq("estado", "cancelada")
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return res.data or []


def find_detalle_por_venta_ids(venta_ids: List[str]) -> List[Dict[str, Any]]:
    if not venta_ids:
        return []
    res = supabase.table("libreria_ventas_detalle") \
        .select("venta_id, cantidad, precio_unitario, costo_unitario") \
        .in_("venta_id", venta_ids) \
        .execute()
    return res.data or []


def find_all_creditos_pendientes(cui_filtro: Optional[str] = None,
                                  pagina: int = 1, por_pagina: int = 10) -> dict:
    offset = (pagina - 1) * por_pagina
    q = supabase.table("libreria_ventas") \
        .select("id, comprador_cui, total_venta, total_pagado, estado_pago, created_at, digitado_por", count="exact") \
        .in_("estado_pago", ["pendiente", "parcial"]) \
        .neq("estado", "cancelada") \
        .order("created_at", desc=False) \
        .range(offset, offset + por_pagina - 1)
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return {"data": res.data or [], "total": res.count or 0}


def find_all_pagados(cui_filtro: Optional[str] = None,
                      pagina: int = 1, por_pagina: int = 10) -> dict:
    offset = (pagina - 1) * por_pagina
    q = supabase.table("libreria_ventas") \
        .select("id, comprador_cui, total_venta, total_pagado, estado_pago, created_at, digitado_por", count="exact") \
        .eq("estado_pago", "pagado") \
        .neq("estado", "cancelada") \
        .order("created_at", desc=True) \
        .range(offset, offset + por_pagina - 1)
    if cui_filtro:
        q = q.eq("digitado_por", cui_filtro)
    res = q.execute()
    return {"data": res.data or [], "total": res.count or 0}


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
