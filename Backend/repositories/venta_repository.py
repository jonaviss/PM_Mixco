from typing import List, Optional, Dict, Any
from database import supabase


def create_venta(data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("libreria_ventas").insert(data).execute()
    return res.data[0]


def find_venta_by_id(venta_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("libreria_ventas") \
        .select("*, usuarios!libreria_ventas_comprador_cui_fkey(nombre_completo, correo)") \
        .eq("id", venta_id) \
        .execute()
    return res.data[0] if res.data else None


def find_venta_basica(venta_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("libreria_ventas") \
        .select("id, comprador_cui, total_venta, total_pagado, estado_pago, created_at, digitado_por") \
        .eq("id", venta_id) \
        .execute()
    return res.data[0] if res.data else None


def update_venta(venta_id: str, data: Dict[str, Any]) -> None:
    supabase.table("libreria_ventas").update(data).eq("id", venta_id).execute()


def search_ventas_por_uuid(uuid: str) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_ventas") \
        .select("*, usuarios!libreria_ventas_comprador_cui_fkey(nombre_completo, correo)") \
        .eq("id", uuid) \
        .execute()
    return res.data or []


def search_ventas_por_cui(cui: str, limit: int = 0, offset: int = 0) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas") \
        .select("*, usuarios!libreria_ventas_comprador_cui_fkey(nombre_completo, correo)") \
        .eq("comprador_cui", cui) \
        .order("created_at", desc=True)
    if limit:
        q = q.limit(limit).offset(offset)
    res = q.execute()
    return res.data or []


def count_ventas_por_cui(cui: str) -> int:
    res = supabase.table("libreria_ventas") \
        .select("id", count="exact") \
        .eq("comprador_cui", cui) \
        .execute()
    return res.count or 0


def search_ventas_por_cuis(cuis: List[str], limit: int = 0, offset: int = 0) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas") \
        .select("*, usuarios!libreria_ventas_comprador_cui_fkey(nombre_completo, correo)") \
        .in_("comprador_cui", cuis) \
        .order("created_at", desc=True)
    if limit:
        q = q.limit(limit).offset(offset)
    res = q.execute()
    return res.data or []


def count_ventas_por_cuis(cuis: List[str]) -> int:
    res = supabase.table("libreria_ventas") \
        .select("id", count="exact") \
        .in_("comprador_cui", cuis) \
        .execute()
    return res.count or 0


def list_all_ventas(limit: int = 0, offset: int = 0) -> List[Dict[str, Any]]:
    q = supabase.table("libreria_ventas") \
        .select("*, usuarios!libreria_ventas_comprador_cui_fkey(nombre_completo, correo)") \
        .order("created_at", desc=True)
    if limit:
        q = q.limit(limit).offset(offset)
    res = q.execute()
    return res.data or []


def find_ventas_by_comprador(cui: str, estados: List[str]) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_ventas") \
        .select("id, total_venta, total_pagado, estado_pago, created_at") \
        .eq("comprador_cui", cui) \
        .in_("estado_pago", estados) \
        .order("created_at", desc=False) \
        .execute()
    return res.data or []


def find_ventas_by_comprador_all(cui: str) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_ventas") \
        .select("id, total_venta, total_pagado, estado_pago, created_at, digitado_por") \
        .eq("comprador_cui", cui) \
        .order("created_at", desc=True) \
        .execute()
    return res.data or []


def find_ventas_con_filtros(inicio: str, fin: str, operador_cui: Optional[str] = None,
                            cliente_cui: Optional[str] = None, estado: Optional[str] = None) -> List[Dict[str, Any]]:
    query = supabase.table("libreria_ventas") \
        .select("id, comprador_cui, total_venta, total_pagado, estado_pago, created_at, digitado_por") \
        .gte("created_at", inicio) \
        .lte("created_at", fin)
    if operador_cui:
        query = query.eq("digitado_por", operador_cui)
    if cliente_cui:
        query = query.eq("comprador_cui", cliente_cui)
    if estado:
        query = query.eq("estado_pago", estado)
    res = query.order("created_at", desc=False).execute()
    return res.data or []


def create_venta_detalle(data: Dict[str, Any]) -> None:
    supabase.table("libreria_ventas_detalle").insert(data).execute()


def find_detalle_by_venta(venta_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_ventas_detalle") \
        .select("*, inventario_libreria!inner(nombre)") \
        .eq("venta_id", venta_id) \
        .execute()
    return res.data or []


def find_detalle_by_venta_ids(venta_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    if not venta_ids:
        return {}
    res = supabase.table("libreria_ventas_detalle") \
        .select("*, inventario_libreria!inner(nombre)") \
        .in_("venta_id", venta_ids) \
        .execute()
    agrupado = {}
    for d in (res.data or []):
        agrupado.setdefault(d["venta_id"], []).append(d)
    return agrupado


def find_detalle_completo(venta_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_ventas_detalle") \
        .select("cantidad, precio_unitario, subtotal, costo_unitario, inventario_libreria(nombre, tipo_producto)") \
        .eq("venta_id", venta_id) \
        .execute()
    return res.data or []


def find_detalle_con_producto(venta_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_ventas_detalle") \
        .select("producto_id, cantidad, precio_unitario, subtotal, inventario_libreria(nombre)") \
        .eq("venta_id", venta_id) \
        .execute()
    return res.data or []


def find_detalle_para_cancelacion(venta_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_ventas_detalle") \
        .select("producto_id, cantidad") \
        .eq("venta_id", venta_id) \
        .execute()
    return res.data or []


def find_primer_detalle(venta_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("libreria_ventas_detalle") \
        .select("producto_id, inventario_libreria(nombre)") \
        .eq("venta_id", venta_id) \
        .limit(1) \
        .execute()
    return res.data[0] if res.data else None
