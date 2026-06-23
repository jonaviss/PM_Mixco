from typing import List, Dict, Any, Optional
from database import supabase
from datetime import datetime


def find_lotes_disponibles(producto_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("lotes") \
        .select("*") \
        .eq("producto_id", producto_id) \
        .gt("cantidad_restante", 0) \
        .order("fecha_compra", desc=False) \
        .execute()
    return res.data or []


def update_lote_cantidad(lote_id: str, cantidad_restante: int) -> None:
    supabase.table("lotes").update({"cantidad_restante": cantidad_restante}).eq("id", lote_id).execute()


def create_lote_auto(producto_id: str, cantidad_inicial: int, costo_unitario: float) -> None:
    lote_data = {
        "producto_id": producto_id,
        "cantidad_inicial": cantidad_inicial,
        "cantidad_restante": cantidad_inicial,
        "costo_unitario": costo_unitario,
        "fecha_compra": datetime.now().isoformat()
    }
    supabase.table("lotes").insert(lote_data).execute()
