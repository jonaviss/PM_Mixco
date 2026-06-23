from typing import List, Dict, Any, Optional
from database import supabase


def list_proveedores(estado: str = "activos") -> List[Dict[str, Any]]:
    q = supabase.table("proveedores").select("*")
    if estado == "activos":
        q = q.eq("activo", True)
    elif estado == "inactivos":
        q = q.eq("activo", False)
    res = q.order("nombre").execute()
    return res.data or []


def find_proveedor_by_id(proveedor_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("proveedores").select("*").eq("id", proveedor_id).execute()
    return res.data[0] if res.data else None


def find_proveedor_por_nombre(nombre: str, excluir_id: Optional[str] = None) -> bool:
    q = supabase.table("proveedores").select("id, nombre").ilike("nombre", nombre.strip().lower())
    if excluir_id:
        q = q.neq("id", excluir_id)
    res = q.execute()
    return len(res.data) > 0


def create_proveedor(data: Dict[str, Any]) -> Dict[str, Any]:
    data["activo"] = True
    res = supabase.table("proveedores").insert(data).execute()
    return res.data[0]


def update_proveedor(proveedor_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    res = supabase.table("proveedores").update(data).eq("id", proveedor_id).execute()
    return res.data[0] if res.data else None
