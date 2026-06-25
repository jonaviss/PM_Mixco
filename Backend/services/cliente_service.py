from typing import Dict, Any
from fastapi import HTTPException
from repositories.cliente_repository import (
    find_ventas_by_comprador, find_usuarios_by_cuis,
    find_detalle_by_venta_ids, find_venta_ids_by_comprador, find_pagos_by_venta_ids,
    find_venta_basica_by_comprador
)
from services.venta_service import obtener_detalle_venta_completo


async def obtener_detalle_venta_cliente(cui: str, venta_id: str) -> dict:
    venta = find_venta_basica_by_comprador(venta_id, cui)
    if not venta:
        raise HTTPException(404, "Venta no encontrada o no te pertenece")

    _, productos, pagos, cliente, _, operador = await obtener_detalle_venta_completo(venta_id)
    return {
        "venta": {
            "id": venta["id"],
            "comprador_cui": venta["comprador_cui"],
            "cliente": cliente,
            "total_venta": float(venta["total_venta"]),
            "total_pagado": float(venta["total_pagado"]),
            "saldo_pendiente": float(venta["total_venta"]) - float(venta["total_pagado"]),
            "estado_pago": venta["estado_pago"],
            "created_at": venta["created_at"],
            "operador": operador
        },
        "productos": productos,
        "pagos": pagos,
        "ok": True
    }


def obtener_mis_compras(cui: str) -> Dict[str, Any]:
    ventas = find_ventas_by_comprador(cui)
    cuis_operadores = list(set(v["digitado_por"] for v in ventas if v.get("digitado_por")))
    nombres = find_usuarios_by_cuis(cuis_operadores)
    venta_ids = [v["id"] for v in ventas]
    detalles_por_venta = find_detalle_by_venta_ids(venta_ids)
    for v in ventas:
        v["nombre_operador"] = nombres.get(v.get("digitado_por"), v.get("digitado_por", "—"))
        v["productos"] = detalles_por_venta.get(v["id"], [])
    return {"ventas": ventas, "ok": True}


def obtener_mis_pagos(cui: str) -> Dict[str, Any]:
    venta_ids = find_venta_ids_by_comprador(cui)
    if not venta_ids:
        return {"pagos": [], "ok": True}
    pagos = find_pagos_by_venta_ids(venta_ids)
    cuis_operadores = list(set(p["digitado_por"] for p in pagos if p.get("digitado_por")))
    nombres = find_usuarios_by_cuis(cuis_operadores)
    for p in pagos:
        p["operador"] = nombres.get(p.get("digitado_por"), "—")
        p["monto_abonado"] = float(p["monto_abonado"])
    return {"pagos": pagos, "ok": True}
