from typing import List, Optional, Dict, Any
from database import supabase


def list_productos(incluir_inactivos: bool = False) -> List[Dict[str, Any]]:
    query = supabase.table("inventario_libreria").select("*, proveedores(nombre, id)")
    if not incluir_inactivos:
        query = query.eq("estado", True)
    res = query.execute()
    return res.data or []


def find_producto_by_id(producto_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("inventario_libreria").select("*").eq("id", producto_id).execute()
    return res.data[0] if res.data else None


def find_producto_basico(producto_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("inventario_libreria") \
        .select("id, nombre, stock, precio, costo_promedio") \
        .eq("id", producto_id) \
        .execute()
    return res.data[0] if res.data else None


def create_producto(data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("inventario_libreria").insert(data).execute()
    return res.data[0]


def update_producto(producto_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    res = supabase.table("inventario_libreria").update(data).eq("id", producto_id).execute()
    return res.data[0] if res.data else None


def update_producto_stock(producto_id: str, nuevo_stock: int) -> None:
    supabase.table("inventario_libreria").update({"stock": nuevo_stock}).eq("id", producto_id).execute()


def get_producto_stock(producto_id: str) -> Optional[int]:
    res = supabase.table("inventario_libreria").select("stock").eq("id", producto_id).execute()
    return res.data[0]["stock"] if res.data else None


def get_producto_costo_promedio(producto_id: str) -> Optional[float]:
    res = supabase.table("inventario_libreria").select("costo_promedio").eq("id", producto_id).execute()
    return res.data[0].get("costo_promedio", 0) if res.data else None
