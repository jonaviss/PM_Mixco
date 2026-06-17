"""
Módulo de gestión de librería.
Maneja inventario, ventas (contado y crédito), abonos simples y distribuidos.
Incluye FIFO para consumo de lotes y creación automática de lotes para productos creados desde inventario.
"""

import os
import base64
import httpx
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends, Query
from database import supabase
from schemas import ProductoLibreriaCreate, VentaLibreriaCreate, PagoLibreriaCreate, AbonoDistribuidoCreate, ProductoLibreriaUpdate
from routers.dependencies import obtener_usuario_actual
from routers.pdf_libreria import generar_pdf_comprobante
from typing import Dict, Any, Optional
from datetime import datetime

router = APIRouter()

# ======================== FUNCIÓN AUXILIAR FIFO (CORREGIDA) ========================
async def consumir_lote_fifo(producto_id: str, cantidad_vendida: int) -> float:
    """
    Consume la cantidad vendida de los lotes más antiguos (FIFO).
    Si no hay lotes, usa el costo_promedio del producto.
    Retorna el costo total de la venta.
    """
    if cantidad_vendida <= 0:
        return 0.0

    costo_total = 0.0
    restante = cantidad_vendida

    # Buscar lotes disponibles
    res_lotes = supabase.table("lotes").select("*").eq("producto_id", producto_id).gt("cantidad_restante", 0).order("fecha_compra", desc=False).execute()
    lotes = res_lotes.data or []

    # Consumir lotes FIFO
    for lote in lotes:
        if restante <= 0:
            break
        disponible = lote["cantidad_restante"]
        descontar = min(disponible, restante)
        costo_total += descontar * lote["costo_unitario"]
        nuevo_restante = disponible - descontar
        supabase.table("lotes").update({"cantidad_restante": nuevo_restante}).eq("id", lote["id"]).execute()
        restante -= descontar

    # Si aún falta stock (no hay suficientes lotes), usar costo_promedio
    if restante > 0:
        res_prod = supabase.table("inventario_libreria").select("costo_promedio").eq("id", producto_id).execute()
        if not res_prod.data:
            raise HTTPException(404, f"Producto {producto_id} no encontrado")
        costo_promedio = res_prod.data[0].get("costo_promedio", 0)
        costo_total += restante * costo_promedio
        # Opcional: registrar en bitácora que no había lotes suficientes

    return costo_total

# ======================== NOTIFICACIONES ASÍNCRONAS ========================
async def despachar_correo_libreria(datos: dict):
    """Genera PDF y envía correo (código existente)"""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[ALERTA] RESEND_API_KEY no configurada. Correo abortado.")
        return
    tipo = datos.get("tipo_notificacion", "venta_contado")
    if tipo == "venta_credito":
        titulo_recibo = "Notificacion de Cargo a Credito"
    elif tipo == "venta_contado":
        titulo_recibo = "Comprobante de Compra en Efectivo"
    else:
        titulo_recibo = "Comprobante de Abono Recibido"
    monto = datos.get("monto", 0)
    hermano = datos.get("hermano", {})
    nombre_hermano = hermano.get("nombre_completo", "Hermano")
    try:
        pdf_bytes = generar_pdf_comprobante(datos)
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        adjunto = [{
            "filename": f"comprobante_{datos.get('id_transaccion', 'tx')[:8]}.pdf",
            "content": pdf_base64,
            "type": "application/pdf"
        }]
    except Exception as e:
        print(f"[ERROR] Falla al generar PDF: {e}")
        adjunto = []
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 24px;
                border: 1px solid #e8e4d9; border-radius: 12px; background-color: #fafaf8;">
        <h2 style="color: #755b00; text-align: center; margin-bottom: 4px;">PALABRA MIEL MIXCO</h2>
        <p style="text-align: center; color: #7a7565; font-size: 13px; margin-top: 0;">{titulo_recibo}</p>
        <hr style="border: none; border-top: 2px solid #C9A227; margin: 16px 0;">
        <p style="font-size: 14px; color: #1c1c1a;">Estimado(a) <strong>{nombre_hermano}</strong>,</p>
        <p style="font-size: 14px; color: #4d4635; margin-top: 8px;">
            Se ha registrado una transacción en el módulo de Librería por un monto de
            <strong style="color: #755b00;">Q{monto:.2f}</strong>.
        </p>
        <p style="font-size: 14px; color: #4d4635; margin-top: 8px;">
            Adjunto encontrará el comprobante en formato PDF con el detalle completo
            de la transacción y el estado de su cuenta.
        </p>
        <div style="background: #f0edea; border-radius: 8px; padding: 12px; margin-top: 16px;
                    text-align: center; border: 1px solid #d1c5af;">
            <p style="font-size: 11px; color: #7a7565; margin: 0;">
                PM Mixco ERP v2.0.0 — Módulo Librería — Documento generado automáticamente
            </p>
        </div>
    </div>
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload_correo = {
        "from": "Libreria PM Mixco <onboarding@resend.dev>",
        "to": ["jonathanvisoni@gmail.com"],
        "subject": f"{titulo_recibo} — Q{monto:.2f} — PM Mixco",
        "html": html_content,
        "attachments": adjunto
    }
    async with httpx.AsyncClient() as client:
        respuesta = await client.post("https://api.resend.com/emails", json=payload_correo, headers=headers)
        if respuesta.status_code != 200:
            print(f"[ERROR] Falla al despachar correo via Resend: {respuesta.text}")

# ======================== GESTIÓN DE INVENTARIO Y CLIENTES ========================
@router.get("/productos")
async def listar_productos(
    incluir_inactivos: bool = False,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    try:
        query = supabase.table("inventario_libreria").select("*, proveedores(nombre, id)")
        if not incluir_inactivos:
            query = query.eq("estado", True)
        res = query.execute()
        productos = res.data or []
        # Obtener nombres de creadores
        cuis = list(set(p.get("creado_por") for p in productos if p.get("creado_por")))
        nombres = {}
        if cuis:
            res_usuarios = supabase.table("usuarios").select("cui, nombre_completo").in_("cui", cuis).execute()
            nombres = {u["cui"]: u["nombre_completo"] for u in (res_usuarios.data or [])}
        for p in productos:
            p["creado_por_nombre"] = nombres.get(p.get("creado_por"), p.get("creado_por") or "—")
        return productos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clientes")
async def listar_clientes(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("usuarios").select("cui, nombre_completo, correo, created_at").execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/productos", status_code=status.HTTP_201_CREATED)
def registrar_producto(payload: ProductoLibreriaCreate, usuario_actual=Depends(obtener_usuario_actual)):
    if usuario_actual.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para registrar productos.")
    try:
        data = payload.model_dump(exclude_none=True)
        # Guardar creado_por
        data["creado_por"] = usuario_actual["sub"]
        res = supabase.table("inventario_libreria").insert(data).execute()
        nuevo_producto = res.data[0]
        producto_id = nuevo_producto["id"]

        # ===== NUEVO: Crear lote automático si el producto tiene stock y costo =====
        stock = data.get("stock", 0)
        costo_promedio = data.get("costo_promedio")
        if stock > 0 and costo_promedio is not None:
            lote_data = {
                "producto_id": producto_id,
                "compra_id": None,  # Sin compra asociada (creado desde inventario)
                "cantidad_inicial": stock,
                "cantidad_restante": stock,
                "costo_unitario": costo_promedio,
                "fecha_compra": datetime.now().isoformat()
            }
            supabase.table("lotes").insert(lote_data).execute()

        return {"mensaje": "Producto registrado", "data": nuevo_producto}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.put("/productos/{producto_id}")
def actualizar_producto(producto_id: str, payload: ProductoLibreriaUpdate, usuario_actual=Depends(obtener_usuario_actual)):
    if usuario_actual.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para modificar productos.")
    try:
        res_exist = supabase.table("inventario_libreria").select("id").eq("id", producto_id).execute()
        if not res_exist.data:
            raise HTTPException(404, "Producto no encontrado")
        update_data = payload.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "No se enviaron campos para actualizar.")
        res_update = supabase.table("inventario_libreria").update(update_data).eq("id", producto_id).execute()
        return {"mensaje": "Producto actualizado", "data": res_update.data[0]}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.put("/productos/{producto_id}/toggle-estado")
async def toggle_estado_producto(producto_id: str, usuario_actual=Depends(obtener_usuario_actual)):
    if usuario_actual.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para modificar productos.")
    try:
        res = supabase.table("inventario_libreria").select("estado").eq("id", producto_id).execute()
        if not res.data:
            raise HTTPException(404, "Producto no encontrado")
        nuevo_estado = not res.data[0]["estado"]
        update_res = supabase.table("inventario_libreria").update({"estado": nuevo_estado}).eq("id", producto_id).execute()
        mensaje = "Producto reactivado" if nuevo_estado else "Producto desactivado"
        return {"mensaje": mensaje, "estado": nuevo_estado, "data": update_res.data[0]}
    except Exception as e:
        raise HTTPException(500, str(e))

# ======================== VENTAS CON FIFO (CORREGIDO) ========================
@router.post("/ventas", status_code=status.HTTP_201_CREATED)
async def registrar_venta(
    payload: VentaLibreriaCreate,
    background_tasks: BackgroundTasks,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    try:
        res_producto = supabase.table("inventario_libreria") \
            .select("id, nombre, stock, precio, costo_promedio") \
            .eq("id", payload.producto_id) \
            .execute()
        if not res_producto.data:
            raise HTTPException(404, "Producto no encontrado")
        producto = res_producto.data[0]
        stock_actual = producto["stock"]
        if stock_actual < payload.cantidad:
            raise HTTPException(400, "Existencias insuficientes en inventario.")
        precio_unitario = float(producto["precio"])
        total_venta = precio_unitario * payload.cantidad
        es_contado = payload.tipo_pago == "contado"
        estado_inicial = "pagado" if es_contado else "pendiente"
        monto_ingresado = total_venta if es_contado else 0.0

        # Consumir lotes (corregido para manejar productos sin lotes)
        costo_total_venta = await consumir_lote_fifo(payload.producto_id, payload.cantidad)
        costo_unitario_venta = costo_total_venta / payload.cantidad if payload.cantidad > 0 else 0

        res_venta = supabase.table("libreria_ventas").insert({
            "comprador_cui": payload.comprador_cui,
            "total_venta": total_venta,
            "total_pagado": monto_ingresado,
            "estado_pago": estado_inicial,
            "digitado_por": usuario_actual["sub"]
        }).execute()
        venta_id = res_venta.data[0]["id"]

        supabase.table("libreria_ventas_detalle").insert({
            "venta_id": venta_id,
            "producto_id": payload.producto_id,
            "cantidad": payload.cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": total_venta,
            "costo_unitario": costo_unitario_venta
        }).execute()

        if es_contado:
            supabase.table("libreria_pagos").insert({
                "venta_id": venta_id,
                "monto_abonado": total_venta,
                "metodo_pago_id": 1,
                "digitado_por": usuario_actual["sub"]
            }).execute()

        # Actualizar stock (restar)
        supabase.table("inventario_libreria") \
            .update({"stock": stock_actual - payload.cantidad}) \
            .eq("id", payload.producto_id) \
            .execute()

        # Obtener datos para correo
        res_comprador = supabase.table("usuarios") \
            .select("cui, nombre_completo") \
            .eq("cui", payload.comprador_cui) \
            .execute()
        comprador = res_comprador.data[0] if res_comprador.data else {"cui": payload.comprador_cui, "nombre_completo": "—"}

        res_deuda = supabase.table("libreria_ventas") \
            .select("total_venta, total_pagado") \
            .eq("comprador_cui", payload.comprador_cui) \
            .in_("estado_pago", ["pendiente", "parcial"]) \
            .execute()
        deuda_data = res_deuda.data or []
        deuda_total = sum(float(d["total_venta"]) - float(d["total_pagado"]) for d in deuda_data if float(d["total_venta"]) - float(d["total_pagado"]) > 0)

        res_op = supabase.table("usuarios").select("nombre_completo").eq("cui", usuario_actual["sub"]).execute()
        nombre_op = res_op.data[0]["nombre_completo"] if res_op.data else usuario_actual["sub"]

        tipo_notif = "venta_contado" if es_contado else "venta_credito"
        background_tasks.add_task(despachar_correo_libreria, {
            "id_transaccion": venta_id,
            "tipo_notificacion": tipo_notif,
            "monto": total_venta,
            "venta": {
                "id": venta_id,
                "comprador_cui": payload.comprador_cui,
                "total_venta": total_venta,
                "total_pagado": monto_ingresado,
                "saldo_pendiente": total_venta - monto_ingresado,
                "estado_pago": estado_inicial,
                "operador": nombre_op
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
            "deuda_hermano": {"total": deuda_total, "cantidad": len(deuda_data)}
        })
        return {"mensaje": "Transacción completada exitosamente", "venta_id": venta_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ======================== GESTIÓN DE ABONOS ========================
@router.post("/pagos")
async def registrar_abono(payload: PagoLibreriaCreate, background_tasks: BackgroundTasks, usuario_actual=Depends(obtener_usuario_actual)):
    try:
        res_venta = supabase.table("libreria_ventas").select("id, total_venta, total_pagado, estado_pago").eq("id", payload.venta_id).execute()
        if not res_venta.data:
            raise HTTPException(404, "Registro de venta no localizado.")
        venta = res_venta.data[0]
        if venta["estado_pago"] == "pagado":
            raise HTTPException(400, "La deuda asociada a esta venta ya fue liquidada.")
        res_pago = supabase.table("libreria_pagos").insert({
            "venta_id": payload.venta_id,
            "monto_abonado": payload.monto_abonado,
            "metodo_pago_id": payload.metodo_pago_id,
            "digitado_por": usuario_actual["sub"]
        }).execute()
        pago_id = res_pago.data[0]["id"]
        res_pagos = supabase.table("libreria_pagos").select("monto_abonado").eq("venta_id", payload.venta_id).execute()
        total_acumulado = sum(float(p["monto_abonado"]) for p in res_pagos.data)
        estado_nuevo = "pagado" if total_acumulado >= float(venta["total_venta"]) else "parcial"
        supabase.table("libreria_ventas").update({"total_pagado": total_acumulado, "estado_pago": estado_nuevo}).eq("id", payload.venta_id).execute()
        res_detalle = supabase.table("libreria_ventas_detalle").select("producto_id, inventario_libreria(nombre)").eq("venta_id", payload.venta_id).limit(1).execute()
        nombre_prod = "Abono a Cuenta Credito"
        if res_detalle.data and res_detalle.data[0].get("inventario_libreria"):
            nombre_prod = res_detalle.data[0]["inventario_libreria"]["nombre"]
        background_tasks.add_task(despachar_correo_libreria, {
            "id_transaccion": pago_id,
            "tipo_notificacion": "abono_parcial",
            "detalle_producto": f"Abono a cuenta ({nombre_prod})",
            "cantidad": 1,
            "monto": payload.monto_abonado
        })
        return {"mensaje": "Abono aplicado correctamente", "estado_actual": estado_nuevo}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.post("/pagos/distribuir", status_code=status.HTTP_201_CREATED)
async def distribuir_abono(payload: AbonoDistribuidoCreate, background_tasks: BackgroundTasks, usuario_actual=Depends(obtener_usuario_actual)):
    try:
        res_ventas = supabase.table("libreria_ventas").select("id, total_venta, total_pagado, estado_pago, created_at").eq("comprador_cui", payload.comprador_cui).in_("estado_pago", ["pendiente", "parcial"]).order("created_at", desc=False).execute()
        ventas = res_ventas.data or []
        if not ventas:
            raise HTTPException(404, "Este cliente no tiene ventas pendientes de pago.")
        deuda_total = sum(float(v["total_venta"]) - float(v["total_pagado"]) for v in ventas if float(v["total_venta"]) - float(v["total_pagado"]) > 0)
        if float(payload.monto_abonado) > deuda_total:
            raise HTTPException(400, f"El monto ingresado (Q{payload.monto_abonado:.2f}) supera la deuda total (Q{deuda_total:.2f}).")
        monto_restante = float(payload.monto_abonado)
        ventas_pagadas = []
        for venta in ventas:
            if monto_restante <= 0:
                break
            total_venta = float(venta["total_venta"])
            total_pagado = float(venta["total_pagado"])
            pendiente_venta = total_venta - total_pagado
            if pendiente_venta <= 0:
                continue
            abono_aplicar = min(monto_restante, pendiente_venta)
            supabase.table("libreria_pagos").insert({
                "venta_id": venta["id"],
                "monto_abonado": abono_aplicar,
                "metodo_pago_id": payload.metodo_pago_id,
                "digitado_por": usuario_actual["sub"]
            }).execute()
            nuevo_pagado = total_pagado + abono_aplicar
            nuevo_estado = "pagado" if nuevo_pagado >= total_venta else "parcial"
            supabase.table("libreria_ventas").update({"total_pagado": nuevo_pagado, "estado_pago": nuevo_estado}).eq("id", venta["id"]).execute()
            ventas_pagadas.append({"venta_id": venta["id"], "abono_aplicado": abono_aplicar, "estado": nuevo_estado})
            monto_restante -= abono_aplicar
        if ventas_pagadas:
            res_comprador = supabase.table("usuarios").select("cui, nombre_completo").eq("cui", payload.comprador_cui).execute()
            comprador = res_comprador.data[0] if res_comprador.data else {"cui": payload.comprador_cui, "nombre_completo": "—"}
            res_deuda = supabase.table("libreria_ventas").select("total_venta, total_pagado").eq("comprador_cui", payload.comprador_cui).in_("estado_pago", ["pendiente", "parcial"]).execute()
            deuda_data = res_deuda.data or []
            deuda_total = sum(float(d["total_venta"]) - float(d["total_pagado"]) for d in deuda_data if float(d["total_venta"]) - float(d["total_pagado"]) > 0)
            res_op = supabase.table("usuarios").select("nombre_completo").eq("cui", usuario_actual["sub"]).execute()
            nombre_op = res_op.data[0]["nombre_completo"] if res_op.data else usuario_actual["sub"]
            background_tasks.add_task(despachar_correo_libreria, {
                "id_transaccion": ventas_pagadas[0]["venta_id"],
                "tipo_notificacion": "abono_parcial",
                "monto": float(payload.monto_abonado),
                "venta": {
                    "id": ventas_pagadas[0]["venta_id"],
                    "comprador_cui": payload.comprador_cui,
                    "total_venta": float(payload.monto_abonado),
                    "total_pagado": float(payload.monto_abonado),
                    "saldo_pendiente": deuda_total,
                    "estado_pago": ventas_pagadas[0]["estado"],
                    "operador": nombre_op
                },
                "productos": [],
                "pagos": [{"monto_abonado": float(payload.monto_abonado), "fecha_pago": None, "operador": nombre_op}],
                "hermano": comprador,
                "deuda_hermano": {"total": deuda_total, "cantidad": len(deuda_data)}
            })
        return {"mensaje": f"Abono de Q{payload.monto_abonado:.2f} distribuido correctamente.", "ventas_actualizadas": ventas_pagadas, "saldo_restante": round(monto_restante, 2), "ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# ======================== ENDPOINTS DE COBROS Y CLIENTES ========================
@router.get("/cobros/pendientes")
async def obtener_pendientes(cui: str, usuario_actual=Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("libreria_ventas").select("id, total_venta, total_pagado, estado_pago, created_at").eq("comprador_cui", cui).in_("estado_pago", ["pendiente", "parcial"]).order("created_at", desc=False).execute()
        return {"ventas": res.data or [], "ok": True}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.get("/clientes/{cui}/historial")
async def obtener_historial_cliente(cui: str, usuario_actual=Depends(obtener_usuario_actual)):
    try:
        res = supabase.table("libreria_ventas").select("id, total_venta, total_pagado, estado_pago, created_at, digitado_por").eq("comprador_cui", cui).order("created_at", desc=True).execute()
        ventas = res.data or []
        cuis_operadores = list(set(v["digitado_por"] for v in ventas if v.get("digitado_por")))
        nombres_operadores = {}
        if cuis_operadores:
            res_usuarios = supabase.table("usuarios").select("cui, nombre_completo").in_("cui", cuis_operadores).execute()
            nombres_operadores = {u["cui"]: u["nombre_completo"] for u in (res_usuarios.data or [])}
        for v in ventas:
            v["nombre_operador"] = nombres_operadores.get(v.get("digitado_por"))
        return {"ventas": ventas, "ok": True}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.get("/ventas/{venta_id}/detalle")
async def obtener_detalle_venta(venta_id: str, usuario_actual=Depends(obtener_usuario_actual)):
    try:
        res_venta = supabase.table("libreria_ventas").select("id, comprador_cui, total_venta, total_pagado, estado_pago, created_at, digitado_por").eq("id", venta_id).execute()
        if not res_venta.data:
            raise HTTPException(404, "Venta no encontrada.")
        venta = res_venta.data[0]
        res_detalle = supabase.table("libreria_ventas_detalle").select("cantidad, precio_unitario, subtotal, costo_unitario, inventario_libreria(nombre, tipo_producto)").eq("venta_id", venta_id).execute()
        productos = []
        for d in (res_detalle.data or []):
            producto_info = d.get("inventario_libreria") or {}
            productos.append({
                "nombre": producto_info.get("nombre", "Producto no disponible"),
                "tipo_producto": producto_info.get("tipo_producto", "—"),
                "cantidad": d["cantidad"],
                "precio_unitario": float(d["precio_unitario"]),
                "subtotal": float(d["subtotal"]),
                "costo_unitario": float(d["costo_unitario"]) if d.get("costo_unitario") else None
            })
        res_pagos = supabase.table("libreria_pagos").select("id, monto_abonado, fecha_pago, digitado_por").eq("venta_id", venta_id).order("fecha_pago", desc=False).execute()
        pagos = res_pagos.data or []
        cuis_pagos = list(set(p["digitado_por"] for p in pagos if p.get("digitado_por")))
        nombres_pagos = {}
        if cuis_pagos:
            res_op = supabase.table("usuarios").select("cui, nombre_completo").in_("cui", cuis_pagos).execute()
            nombres_pagos = {u["cui"]: u["nombre_completo"] for u in (res_op.data or [])}
        pagos_enriquecidos = []
        for p in pagos:
            cui_op = p.get("digitado_por")
            pagos_enriquecidos.append({
                "monto_abonado": float(p["monto_abonado"]),
                "fecha_pago": p["fecha_pago"],
                "operador": nombres_pagos.get(cui_op, cui_op or "—")
            })
        cui_venta = venta.get("digitado_por")
        nombre_operador_venta = "—"
        if cui_venta:
            res_op_venta = supabase.table("usuarios").select("nombre_completo").eq("cui", cui_venta).execute()
            if res_op_venta.data:
                nombre_operador_venta = res_op_venta.data[0]["nombre_completo"]
        comprador_cui = venta["comprador_cui"]
        res_deuda = supabase.table("libreria_ventas").select("total_venta, total_pagado").eq("comprador_cui", comprador_cui).in_("estado_pago", ["pendiente", "parcial"]).execute()
        deuda_data = res_deuda.data or []
        deuda_total = sum(float(d["total_venta"]) - float(d["total_pagado"]) for d in deuda_data if float(d["total_venta"]) - float(d["total_pagado"]) > 0)
        return {
            "venta": {
                "id": venta["id"],
                "comprador_cui": venta["comprador_cui"],
                "total_venta": float(venta["total_venta"]),
                "total_pagado": float(venta["total_pagado"]),
                "saldo_pendiente": float(venta["total_venta"]) - float(venta["total_pagado"]),
                "estado_pago": venta["estado_pago"],
                "created_at": venta["created_at"],
                "operador": nombre_operador_venta
            },
            "productos": productos,
            "pagos": pagos_enriquecidos,
            "deuda_hermano": {"total": deuda_total, "cantidad": len(deuda_data)},
            "ok": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))