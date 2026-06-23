from typing import List, Optional, Dict, Any
from database import supabase


def create_pago(data: Dict[str, Any]) -> Dict[str, Any]:
    res = supabase.table("libreria_pagos").insert(data).execute()
    return res.data[0]


def find_pagos_by_venta(venta_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_pagos").select("*").eq("venta_id", venta_id).execute()
    return res.data or []


def find_pagos_by_venta_ordenados(venta_id: str) -> List[Dict[str, Any]]:
    res = supabase.table("libreria_pagos") \
        .select("id, monto_abonado, fecha_pago, digitado_por") \
        .eq("venta_id", venta_id) \
        .order("fecha_pago", desc=False) \
        .execute()
    return res.data or []


def find_pago_by_id(pago_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("libreria_pagos").select("*").eq("id", pago_id).execute()
    return res.data[0] if res.data else None


def delete_pago(pago_id: str) -> None:
    supabase.table("libreria_pagos").delete().eq("id", pago_id).execute()


def sum_pagos_by_venta(venta_id: str) -> float:
    res = supabase.table("libreria_pagos").select("monto_abonado").eq("venta_id", venta_id).execute()
    return sum(float(p["monto_abonado"]) for p in (res.data or []))


def calcular_deuda_comprador(cui: str) -> tuple:
    res = supabase.table("libreria_ventas") \
        .select("total_venta, total_pagado") \
        .eq("comprador_cui", cui) \
        .in_("estado_pago", ["pendiente", "parcial"]) \
        .execute()
    rows = res.data or []
    deuda_total = sum(float(d["total_venta"]) - float(d["total_pagado"])
                      for d in rows if float(d["total_venta"]) - float(d["total_pagado"]) > 0)
    return deuda_total, len(rows)
