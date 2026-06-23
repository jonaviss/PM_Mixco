from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException, BackgroundTasks
from schemas import VentaLibreriaCreate, VentaMultipleCreate
from repositories.venta_repository import (
    create_venta, find_venta_by_id, find_venta_basica, update_venta,
    search_ventas_por_uuid, search_ventas_por_cui, search_ventas_por_cuis,
    count_ventas_por_cui, count_ventas_por_cuis,
    list_all_ventas, find_ventas_con_filtros, create_venta_detalle,
    find_detalle_by_venta, find_detalle_completo, find_detalle_con_producto,
    find_detalle_para_cancelacion, find_primer_detalle, find_detalle_by_venta_ids
)
from repositories.inventario_repository import (
    find_producto_basico, update_producto_stock, get_producto_stock
)
from repositories.lote_repository import find_lotes_disponibles, update_lote_cantidad
from repositories.pago_repository import create_pago, calcular_deuda_comprador, find_pagos_by_venta, find_pagos_by_venta_ordenados
from repositories.common_repository import find_usuario_basico, find_usuario_nombre, find_usuarios_por_nombre
from services.notificacion_service import despachar_correo_libreria


async def consumir_lote_fifo(producto_id: str, cantidad_vendida: int) -> float:
    if cantidad_vendida <= 0:
        return 0.0
    costo_total = 0.0
    restante = cantidad_vendida
    lotes = find_lotes_disponibles(producto_id)
    for lote in lotes:
        if restante <= 0:
            break
        descontar = min(lote["cantidad_restante"], restante)
        costo_total += descontar * lote["costo_unitario"]
        nuevo_restante = lote["cantidad_restante"] - descontar
        update_lote_cantidad(lote["id"], nuevo_restante)
        restante -= descontar
    if restante > 0:
        from repositories.inventario_repository import get_producto_costo_promedio
        costo_promedio = get_producto_costo_promedio(producto_id) or 0
        costo_total += restante * costo_promedio
    return costo_total


async def registrar_venta_simple(
    payload: VentaLibreriaCreate, usuario_cui: str, background_tasks: BackgroundTasks
) -> dict:
    producto = find_producto_basico(payload.producto_id)
    if not producto:
        raise HTTPException(404, "Producto no encontrado")
    if producto["stock"] < payload.cantidad:
        raise HTTPException(400, "Existencias insuficientes en inventario.")

    precio_unitario = float(producto["precio"])
    total_venta = precio_unitario * payload.cantidad
    es_contado = payload.tipo_pago == "contado"
    estado_inicial = "pagado" if es_contado else "pendiente"
    monto_ingresado = total_venta if es_contado else 0.0

    costo_total = await consumir_lote_fifo(payload.producto_id, payload.cantidad)
    costo_unitario = costo_total / payload.cantidad if payload.cantidad > 0 else 0

    venta = create_venta({
        "comprador_cui": payload.comprador_cui,
        "total_venta": total_venta,
        "total_pagado": monto_ingresado,
        "estado_pago": estado_inicial,
        "digitado_por": usuario_cui
    })
    venta_id = venta["id"]

    create_venta_detalle({
        "venta_id": venta_id,
        "producto_id": payload.producto_id,
        "cantidad": payload.cantidad,
        "precio_unitario": precio_unitario,
        "subtotal": total_venta,
        "costo_unitario": costo_unitario
    })

    if es_contado:
        create_pago({
            "venta_id": venta_id,
            "monto_abonado": total_venta,
            "metodo_pago_id": 1,
            "digitado_por": usuario_cui
        })

    update_producto_stock(payload.producto_id, producto["stock"] - payload.cantidad)

    comprador = find_usuario_basico(payload.comprador_cui) or {"cui": payload.comprador_cui, "nombre_completo": "—", "correo": ""}
    deuda_total, cant_deudas = calcular_deuda_comprador(payload.comprador_cui)
    operador = find_usuario_nombre(usuario_cui) or usuario_cui

    background_tasks.add_task(despachar_correo_libreria, {
        "id_transaccion": venta_id,
        "tipo_notificacion": "venta_contado" if es_contado else "venta_credito",
        "monto": total_venta,
        "venta": {
            "id": venta_id,
            "comprador_cui": payload.comprador_cui,
            "total_venta": total_venta,
            "total_pagado": monto_ingresado,
            "saldo_pendiente": total_venta - monto_ingresado,
            "estado_pago": estado_inicial,
            "operador": operador
        },
        "productos": [{
            "nombre": producto["nombre"],
            "tipo_producto": producto.get("tipo_producto", "—"),
            "cantidad": payload.cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": total_venta
        }],
        "pagos": [],
        "hermano": comprador,
        "deuda_hermano": {"total": deuda_total, "cantidad": cant_deudas}
    })

    sin_correo = not comprador.get("correo")
    return {"mensaje": f"Transacción completada exitosamente.{' El comprador no tiene correo registrado, no se envió comprobante.' if sin_correo else ''}", "venta_id": venta_id, "sin_correo": sin_correo}


async def registrar_venta_multiple(
    payload: VentaMultipleCreate, usuario_cui: str, background_tasks: BackgroundTasks
) -> dict:
    if not payload.productos:
        raise HTTPException(400, "La venta debe tener al menos un producto.")

    productos_detalle = []
    total_venta = 0.0
    stock_actual_dict = {}

    for item in payload.productos:
        prod = find_producto_basico(item.producto_id)
        if not prod:
            raise HTTPException(404, f"Producto {item.producto_id} no encontrado")
        if prod["stock"] < item.cantidad:
            raise HTTPException(400, f"Stock insuficiente para '{prod['nombre']}'. Disponible: {prod['stock']}")
        precio_unitario = float(prod["precio"])
        subtotal = precio_unitario * item.cantidad
        total_venta += subtotal
        productos_detalle.append({
            "producto": prod,
            "cantidad": item.cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": subtotal
        })
        stock_actual_dict[item.producto_id] = prod["stock"]

    es_contado = payload.tipo_pago == "contado"
    estado_inicial = "pagado" if es_contado else "pendiente"
    monto_ingresado = total_venta if es_contado else 0.0

    venta = create_venta({
        "comprador_cui": payload.comprador_cui,
        "total_venta": total_venta,
        "total_pagado": monto_ingresado,
        "estado_pago": estado_inicial,
        "digitado_por": usuario_cui
    })
    venta_id = venta["id"]

    productos_correo = []
    costo_total_venta = 0.0

    for det in productos_detalle:
        prod = det["producto"]
        pid = prod["id"]
        cantidad = det["cantidad"]
        precio_unitario = det["precio_unitario"]
        subtotal = det["subtotal"]

        costo_producto = await consumir_lote_fifo(pid, cantidad)
        costo_total_venta += costo_producto
        costo_unitario = costo_producto / cantidad if cantidad > 0 else 0

        create_venta_detalle({
            "venta_id": venta_id,
            "producto_id": pid,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": subtotal,
            "costo_unitario": costo_unitario
        })

        update_producto_stock(pid, stock_actual_dict[pid] - cantidad)

        productos_correo.append({
            "nombre": prod["nombre"],
            "tipo_producto": prod.get("tipo_producto", "—"),
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": subtotal
        })

    if es_contado:
        create_pago({
            "venta_id": venta_id,
            "monto_abonado": total_venta,
            "metodo_pago_id": 1,
            "digitado_por": usuario_cui
        })

    comprador = find_usuario_basico(payload.comprador_cui) or {"cui": payload.comprador_cui, "nombre_completo": "—", "correo": ""}
    deuda_total, cant_deudas = calcular_deuda_comprador(payload.comprador_cui)
    operador = find_usuario_nombre(usuario_cui) or usuario_cui

    background_tasks.add_task(despachar_correo_libreria, {
        "id_transaccion": venta_id,
        "tipo_notificacion": "venta_contado" if es_contado else "venta_credito",
        "monto": total_venta,
        "venta": {
            "id": venta_id,
            "comprador_cui": payload.comprador_cui,
            "total_venta": total_venta,
            "total_pagado": monto_ingresado,
            "saldo_pendiente": total_venta - monto_ingresado,
            "estado_pago": estado_inicial,
            "operador": operador
        },
        "productos": productos_correo,
        "pagos": [],
        "hermano": comprador,
        "deuda_hermano": {"total": deuda_total, "cantidad": cant_deudas}
    })

    sin_correo = not comprador.get("correo")
    return {"mensaje": f"Venta registrada exitosamente.{' El comprador no tiene correo registrado, no se envió comprobante.' if sin_correo else ''}", "venta_id": venta_id, "total": total_venta, "sin_correo": sin_correo}


async def buscar_ventas(q: str, pagina: int = 1, por_pagina: int = 30) -> dict:
    offset = (pagina - 1) * por_pagina
    if not q:
        ventas = list_all_ventas(por_pagina, offset)
        total = 0
    elif q.count("-") == 4 and len(q) == 36:
        ventas = search_ventas_por_uuid(q)
        total = len(ventas)
    elif q.isdigit():
        ventas = search_ventas_por_cui(q, por_pagina, offset)
        total = count_ventas_por_cui(q)
    else:
        cuis = find_usuarios_por_nombre(q)
        if not cuis:
            return {"ventas": [], "total": 0, "pagina": pagina, "por_pagina": por_pagina}
        ventas = search_ventas_por_cuis(cuis, por_pagina, offset)
        total = count_ventas_por_cuis(cuis)
    if ventas:
        ids = [v["id"] for v in ventas]
        detalle_map = find_detalle_by_venta_ids(ids)
        for v in ventas:
            v["productos"] = detalle_map.get(v["id"], [])
    return {"ventas": ventas, "total": total, "pagina": pagina, "por_pagina": por_pagina}


async def get_reporte_ventas(inicio: str, fin: str, operador_cui: Optional[str] = None,
                             cliente_cui: Optional[str] = None, estado: Optional[str] = None) -> dict:
    ventas = find_ventas_con_filtros(inicio, fin, operador_cui, cliente_cui, estado)
    ventas_detalle = []
    for v in ventas:
        detalle = find_detalle_con_producto(v["id"])
        productos = []
        for d in detalle:
            productos.append({
                "nombre": d.get("inventario_libreria", {}).get("nombre", "Producto no disponible"),
                "cantidad": d["cantidad"],
                "precio_unitario": d["precio_unitario"],
                "subtotal": d["subtotal"]
            })
        cliente = find_usuario_nombre(v["comprador_cui"]) or "—"
        ventas_detalle.append({
            "id": v["id"],
            "cliente": cliente,
            "total": v["total_venta"],
            "pagado": v["total_pagado"],
            "estado": v["estado_pago"],
            "created_at": v["created_at"],
            "productos": productos
        })

    dias = {}
    for v in ventas_detalle:
        fecha = v["created_at"].split("T")[0]
        if fecha not in dias:
            dias[fecha] = {"fecha": fecha, "cantidad": 0, "total": 0.0, "productos": 0, "ventas": []}
        dias[fecha]["cantidad"] += 1
        dias[fecha]["total"] += v["total"]
        dias[fecha]["productos"] += sum(p["cantidad"] for p in v["productos"])
        dias[fecha]["ventas"].append(v)

    ordenados = sorted(dias.values(), key=lambda x: x["fecha"])
    detalle = {d["fecha"]: d.pop("ventas") for d in ordenados}
    return {
        "dias": ordenados,
        "detalle": detalle,
        "resumen": {
            "total_ventas": sum(d["total"] for d in ordenados),
            "total_transacciones": sum(d["cantidad"] for d in ordenados),
            "total_productos": sum(d["productos"] for d in ordenados)
        }
    }


async def obtener_detalle_venta_completo(venta_id: str) -> Tuple[dict, list, list, str, str, str]:
    venta = find_venta_basica(venta_id)
    if not venta:
        raise HTTPException(404, "Venta no encontrada")

    detalle = find_detalle_completo(venta_id)
    productos = []
    for d in detalle:
        prod_info = d.get("inventario_libreria") or {}
        productos.append({
            "nombre": prod_info.get("nombre", "Producto no disponible"),
            "tipo_producto": prod_info.get("tipo_producto", "—"),
            "cantidad": d["cantidad"],
            "precio_unitario": float(d["precio_unitario"]),
            "subtotal": float(d["subtotal"]),
            "costo_unitario": float(d["costo_unitario"]) if d.get("costo_unitario") else None
        })

    pagos_raw = find_pagos_by_venta_ordenados(venta_id)
    pagos = []
    for p in pagos_raw:
        pagos.append({"id": p["id"], "monto_abonado": float(p["monto_abonado"]), "fecha_pago": p["fecha_pago"], "operador": "—"})

    comprador = find_usuario_basico(venta["comprador_cui"])
    cliente = comprador["nombre_completo"] if comprador else "—"
    correo = comprador.get("correo", "") if comprador else ""
    operador = find_usuario_nombre(venta["digitado_por"]) or venta.get("digitado_por", "—")

    return venta, productos, pagos, cliente, correo, operador


async def cancelar_venta(venta_id: str, motivo: str, background_tasks: BackgroundTasks) -> dict:
    venta = find_venta_by_id(venta_id)
    if not venta:
        raise HTTPException(404, "Venta no encontrada")
    if venta.get("estado") == "cancelada":
        raise HTTPException(400, "La venta ya fue cancelada anteriormente")

    detalles = find_detalle_para_cancelacion(venta_id)
    for det in detalles:
        stock_actual = get_producto_stock(det["producto_id"])
        if stock_actual is not None:
            update_producto_stock(det["producto_id"], stock_actual + det["cantidad"])

    update_data = {"estado": "cancelada", "estado_pago": "cancelada"}
    if motivo:
        update_data["motivo_cancelacion"] = motivo
    update_venta(venta_id, update_data)

    comprador = find_usuario_basico(venta["comprador_cui"]) or {"cui": venta["comprador_cui"], "nombre_completo": "—", "correo": ""}
    detalle = find_detalle_completo(venta_id)
    productos = []
    for d in detalle:
        prod_info = d.get("inventario_libreria") or {}
        productos.append({
            "nombre": prod_info.get("nombre", "Producto"),
            "tipo_producto": prod_info.get("tipo_producto", "—"),
            "cantidad": d["cantidad"],
            "precio_unitario": float(d["precio_unitario"]),
            "subtotal": float(d["subtotal"])
        })

    background_tasks.add_task(despachar_correo_libreria, {
        "id_transaccion": venta_id,
        "tipo_notificacion": "cancelacion",
        "monto": float(venta["total_venta"]),
        "motivo_cancelacion": motivo or "—",
        "venta": {
            "id": venta_id,
            "comprador_cui": venta["comprador_cui"],
            "total_venta": float(venta["total_venta"]),
            "total_pagado": float(venta["total_pagado"]),
            "saldo_pendiente": 0,
            "estado_pago": "cancelada",
            "created_at": venta["created_at"],
            "operador": "—"
        },
        "productos": productos,
        "pagos": [],
        "hermano": comprador,
        "deuda_hermano": {"total": 0, "cantidad": 0}
    })

    sin_correo = not comprador.get("correo")
    return {"mensaje": f"Venta cancelada exitosamente — stock restaurado y deuda liberada{' (sin correo del comprador, no se envió notificación)' if sin_correo else ''}", "venta_id": venta_id}
