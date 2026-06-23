from typing import List, Dict, Any, Optional
from database import supabase


def create_compra(data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("compras").insert(data).execute()
    return res.data[0]


def find_compra_by_id(compra_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("compras").select("*, proveedores(nombre)").eq("id", compra_id).execute()
    return res.data[0] if res.data else None


def list_compras(proveedor_id: Optional[str] = None, estado: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("compras").select("*, proveedores(nombre)")
    if proveedor_id:
        q = q.eq("proveedor_id", proveedor_id)
    if estado:
        q = q.eq("estado", estado)
    res = q.order("fecha_compra", desc=True).execute()
    return res.data or []


def update_compra(compra_id: str, data: Dict[str, Any]) -> None:
    supabase.table("compras").update(data).eq("id", compra_id).execute()


def create_compra_detalle(data: Dict[str, Any]) -> None:
    supabase.table("compras_detalle").insert(data).execute()


def create_lote(data: Dict[str, Any]) -> None:
    supabase.table("lotes").insert(data).execute()


def find_compra_detalles(compra_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("compras_detalle") \
        .select("*, inventario_libreria(nombre)") \
        .eq("compra_id", compra_id) \
        .execute()
    return res.data or []


def find_pagos_proveedor(compra_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("pagos_proveedores").select("*").eq("compra_id", compra_id).execute()
    return res.data or []


def list_pagos_proveedores(compra_id: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("pagos_proveedores").select("*, compras(proveedor_id, proveedores(nombre))")
    if compra_id:
        q = q.eq("compra_id", compra_id)
    res = q.order("fecha_pago", desc=True).execute()
    return res.data or []


def create_pago_proveedor(data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("pagos_proveedores").insert(data).execute()
    return res.data[0]


def find_lotes_pendientes(producto_id: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("lotes") \
        .select("*, compras(proveedor_id, proveedores(nombre)), inventario_libreria(nombre, tipo_producto)") \
        .gt("cantidad_restante", 0)
    if producto_id:
        q = q.eq("producto_id", producto_id)
    res = q.order("fecha_compra", desc=False).execute()
    return res.data or []
