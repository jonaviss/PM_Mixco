from typing import Dict, Any, Optional
from fastapi import HTTPException
from schemas import CompraCreate, PagoProveedorCreate
from repositories.compra_repository import (
    create_compra, find_compra_by_id, list_compras, update_compra,
    create_compra_detalle, create_lote, find_compra_detalles,
    find_pagos_proveedor, list_pagos_proveedores, create_pago_proveedor,
    find_lotes_pendientes
)
from repositories.inventario_repository import find_producto_by_id
from repositories.common_repository import find_usuarios_by_cuis


def _requiere_permiso(usuario: Dict[str, Any]):
    if usuario.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para esta acción.")


def get_all_compras(proveedor_id: Optional[str] = None, estado: Optional[str] = None) -> list:
    return list_compras(proveedor_id, estado)


def register_compra(payload: CompraCreate, usuario_cui: str) -> Dict[str, Any]:
    total_compra = sum(d.cantidad * d.costo_unitario for d in payload.detalles)
    es_contado = payload.condicion_pago == "CONTADO"

    compra = create_compra({
        "proveedor_id": payload.proveedor_id,
        "fecha_compra": payload.fecha_compra.isoformat(),
        "fecha_factura": payload.fecha_factura.isoformat() if payload.fecha_factura else None,
        "factura": payload.factura,
        "observaciones": payload.observaciones,
        "total_compra": total_compra,
        "total_pagado": total_compra if es_contado else 0,
        "estado": "pagado" if es_contado else "pendiente"
    })
    compra_id = compra["id"]

    for detalle in payload.detalles:
        create_compra_detalle({
            "compra_id": compra_id,
            "producto_id": detalle.producto_id,
            "cantidad": detalle.cantidad,
            "costo_unitario": detalle.costo_unitario,
            "subtotal": detalle.cantidad * detalle.costo_unitario
        })
        create_lote({
            "producto_id": detalle.producto_id,
            "compra_id": compra_id,
            "cantidad_inicial": detalle.cantidad,
            "cantidad_restante": detalle.cantidad,
            "costo_unitario": detalle.costo_unitario,
            "fecha_compra": payload.fecha_compra.isoformat()
        })
        prod = find_producto_by_id(detalle.producto_id)
        if not prod:
            raise HTTPException(404, f"Producto {detalle.producto_id} no encontrado")
        stock_actual = prod.get("stock") or 0
        costo_promedio_actual = prod.get("costo_promedio") or 0
        nuevo_stock = stock_actual + detalle.cantidad
        nuevo_costo = (
            (stock_actual * costo_promedio_actual) + (detalle.cantidad * detalle.costo_unitario)
        ) / nuevo_stock if nuevo_stock > 0 else 0
        from repositories.inventario_repository import update_producto
        update_producto(detalle.producto_id, {"stock": nuevo_stock, "costo_promedio": nuevo_costo})

    if es_contado:
        create_pago_proveedor({
            "compra_id": compra_id,
            "monto": total_compra,
            "fecha_pago": payload.fecha_compra.isoformat(),
            "metodo_pago_id": 1,
            "referencia": "Pago al contado",
            "digitado_por": usuario_cui
        })

    return {"mensaje": "Compra registrada", "compra_id": compra_id, "total": total_compra}


def get_compra_detalle(compra_id: str) -> dict:
    compra = find_compra_by_id(compra_id)
    if not compra:
        raise HTTPException(404, "Compra no encontrada")
    detalles = find_compra_detalles(compra_id)
    pagos = find_pagos_proveedor(compra_id)
    cuis = list(set(p.get("digitado_por") for p in pagos if p.get("digitado_por")))
    nombres = find_usuarios_by_cuis(cuis) if cuis else {}
    pagos_con_nombre = []
    for p in pagos:
        pagos_con_nombre.append({
            "id": p["id"], "monto": p["monto"], "fecha_pago": p["fecha_pago"],
            "referencia": p.get("referencia"),
            "operador_cui": p.get("digitado_por"),
            "operador_nombre": nombres.get(p.get("digitado_por"), p.get("digitado_por") or "—")
        })
    return {"compra": compra, "detalles": detalles, "pagos": pagos_con_nombre}


def register_pago_proveedor(payload: PagoProveedorCreate, usuario_cui: str) -> Dict[str, Any]:
    compra = find_compra_by_id(payload.compra_id)
    if not compra:
        raise HTTPException(404, "Compra no encontrada")
    saldo = compra["total_compra"] - compra["total_pagado"]
    if payload.monto > saldo:
        raise HTTPException(400, f"El monto no puede exceder el saldo pendiente (Q{saldo:.2f})")
    pago = create_pago_proveedor({
        "compra_id": payload.compra_id,
        "monto": payload.monto,
        "fecha_pago": payload.fecha_pago.isoformat(),
        "metodo_pago_id": payload.metodo_pago_id,
        "referencia": payload.referencia,
        "digitado_por": usuario_cui
    })
    nuevo_pagado = compra["total_pagado"] + payload.monto
    nuevo_estado = "pagado" if nuevo_pagado >= compra["total_compra"] else "parcial"
    update_compra(payload.compra_id, {"total_pagado": nuevo_pagado, "estado": nuevo_estado})
    return {"mensaje": "Pago registrado", "pago_id": pago["id"], "saldo_restante": compra["total_compra"] - nuevo_pagado}


def get_lotes_pendientes(producto_id: Optional[str] = None) -> list:
    return find_lotes_pendientes(producto_id)
