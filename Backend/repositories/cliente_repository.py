from typing import List, Dict, Any
from database import supabase


def find_ventas_by_comprador(cui: str) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_ventas") \
        .select("id, total_venta, total_pagado, estado_pago, created_at, digitado_por") \
        .eq("comprador_cui", cui) \
        .order("created_at", desc=True) \
        .execute()
    return res.data or []


def find_usuarios_by_cuis(cuis: List[str]) -> Dict[str, str]:
    if not cuis:
        return {}
    res = supabase.table("usuarios").select("cui, nombre_completo").in_("cui", cuis).execute()
    return {u["cui"]: u["nombre_completo"] for u in (res.data or [])}


def find_detalle_by_venta_ids(venta_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    if not venta_ids:
        return {}
    res = supabase.table("libreria_ventas_detalle") \
        .select("venta_id, cantidad, precio_unitario, subtotal, inventario_libreria(nombre, tipo_producto)") \
        .in_("venta_id", venta_ids) \
        .execute()
    agrupado = {}
    for d in (res.data or []):
        vid = d["venta_id"]
        if vid not in agrupado:
            agrupado[vid] = []
        prod_info = d.get("inventario_libreria") or {}
        agrupado[vid].append({
            "nombre": prod_info.get("nombre", "Producto"),
            "tipo_producto": prod_info.get("tipo_producto", "—"),
            "cantidad": d["cantidad"],
            "precio_unitario": float(d["precio_unitario"]),
            "subtotal": float(d["subtotal"])
        })
    return agrupado


def find_venta_ids_by_comprador(cui: str) -> List[str]:
    res = supabase.table("libreria_ventas") \
        .select("id") \
        .eq("comprador_cui", cui) \
        .execute()
    return [v["id"] for v in (res.data or [])]


def find_pagos_by_venta_ids(venta_ids: List[str]) -> List[Dict[str, Any]]:
    if not venta_ids:
        return []
    res = supabase.table("libreria_pagos") \
        .select("id, venta_id, monto_abonado, fecha_pago, digitado_por") \
        .in_("venta_id", venta_ids) \
        .order("fecha_pago", desc=True) \
        .execute()
    return res.data or []
