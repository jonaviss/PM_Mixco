"""
Módulo de gestión de librería.
Maneja inventario, ventas (contado y crédito) y abonos parciales.
"""

import os
import httpx
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from database import supabase
from schemas import ProductoLibreriaCreate, VentaLibreriaCreate, PagoLibreriaCreate
from routers.dependencies import obtener_usuario_actual
from typing import Dict, Any

router = APIRouter()


# --- NOTIFICACIONES ASÍNCRONAS ---

async def despachar_correo_libreria(datos: dict):
    """
    Construye la plantilla HTML y la envía mediante Resend.
    Funciona para ventas nuevas (contado/crédito) y abonos parciales.

    Args:
        datos: Diccionario con id_transaccion, tipo_notificacion,
               detalle_producto, cantidad y monto
    """
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[ALERTA] RESEND_API_KEY no configurada. Correo abortado.")
        return

    id_referencia = datos["id_transaccion"][:8]
    url_validacion = f"https://pm-mixco-erp.com/validar-transaccion/{datos['id_transaccion']}"
    qr_img_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url_validacion}"

    if datos["tipo_notificacion"] == "venta_credito":
        titulo_recibo = "Notificación de Cargo a Crédito"
        concepto_monto = "Monto de Deuda Adquirida"
        color_destaque = "#d97706"
    elif datos["tipo_notificacion"] == "venta_contado":
        titulo_recibo = "Comprobante de Compra en Efectivo"
        concepto_monto = "Total Pagado Neto"
        color_destaque = "#1e40af"
    else:
        titulo_recibo = "Comprobante de Abono Recibido"
        concepto_monto = "Monto del Abono Liquidado"
        color_destaque = "#059669"

    html_content = f'''
    <div style="font-family: Arial, sans-serif; max-width: 400px; margin: auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h2 style="color: #1e3a8a; text-align: center; margin-bottom: 5px;">PALABRA MIEL MIXCO</h2>
        <p style="text-align: center; color: #6b7280; font-size: 14px; margin-top: 0; font-weight: bold;">{titulo_recibo}</p>
        <hr style="border: none; border-top: 1px dashed #d1d5db; margin: 20px 0;">
        <p style="font-size: 15px; color: #374151; margin-bottom: 8px;"><strong>Detalle:</strong> {datos['detalle_producto']}</p>
        <p style="font-size: 15px; color: #374151; margin-top: 0; margin-bottom: 8px;"><strong>Cantidad:</strong> {datos['cantidad']} unidad(es)</p>
        <p style="font-size: 16px; margin-top: 15px;"><strong>{concepto_monto}:</strong> <span style="color: {color_destaque}; font-weight: bold;">Q{datos['monto']:.2f}</span></p>
        <p style="font-size: 13px; color: #6b7280; margin-top: 20px;"><strong>No. Operación:</strong> <span style="font-family: monospace;">{id_referencia}</span></p>
        <div style="text-align: center; margin-top: 30px;">
            <img src="{qr_img_url}" alt="Código QR" style="border-radius: 6px; border: 1px solid #e5e7eb; padding: 6px; background-color: #ffffff;">
            <p style="font-size: 11px; color: #9ca3af; margin-top: 10px; line-height: 1.4;">Escanee este código QR para validar la autenticidad de la transacción.</p>
        </div>
        <div style="background-color: #f8fafc; padding: 12px; border-radius: 6px; margin-top: 25px; text-align: center; border: 1px solid #f1f5f9;">
            <p style="font-size: 11px; color: #64748b; margin: 0; font-weight: 500;">PM Mixco ERP - Control de Gestión Institucional</p>
        </div>
    </div>
    '''

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    correo_destino = "jonathanvisoni@gmail.com"

    payload_correo = {
        "from": "Libreria PM Mixco <onboarding@resend.dev>",
        "to": [correo_destino],
        "subject": f"{titulo_recibo} - Q{datos['monto']:.2f} - PM Mixco",
        "html": html_content
    }

    async with httpx.AsyncClient() as client:
        respuesta = await client.post(
            "https://api.resend.com/emails",
            json=payload_correo,
            headers=headers
        )
        if respuesta.status_code != 200:
            print(f"[ERROR] Falla al despachar correo via Resend: {respuesta.text}")


# --- GESTIÓN DE INVENTARIO Y CLIENTES ---

@router.get("/productos")
async def listar_productos(
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    """
    Retorna la lista de productos activos en inventario.

    Returns:
        list: Productos con estado activo

    Raises:
        HTTPException 500: Si ocurre un error al consultar la base de datos
    """
    try:
        res = supabase.table("inventario_libreria").select("*").eq("estado", True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clientes")
async def listar_clientes(
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    """
    Retorna la lista de hermanos para el buscador predictivo del POS.

    Returns:
        list: Usuarios con cui, nombre_completo y correo

    Raises:
        HTTPException 500: Si ocurre un error al consultar la base de datos
    """
    try:
        res = supabase.table("usuarios").select("cui, nombre_completo, correo").execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/productos", status_code=status.HTTP_201_CREATED)
def registrar_producto(
    payload: ProductoLibreriaCreate,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    """
    Registra un nuevo producto en el inventario de librería.

    Args:
        payload: Datos del producto a registrar
        usuario_actual: Payload del JWT del operador autenticado

    Returns:
        dict: Producto creado con su ID

    Raises:
        HTTPException 403: Si el usuario no tiene rango suficiente
        HTTPException 500: Si ocurre un error al insertar en la base de datos
    """
    if usuario_actual.get("rango") not in ["encargado", "administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para registrar productos."
        )

    try:
        data = payload.model_dump(exclude_none=True)
        res = supabase.table("inventario_libreria").insert(data).execute()
        return {"mensaje": "Producto registrado", "data": res.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- GESTIÓN DE VENTAS ---

@router.post("/ventas", status_code=status.HTTP_201_CREATED)
def registrar_venta(
    payload: VentaLibreriaCreate,
    background_tasks: BackgroundTasks,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    """
    Registra una nueva venta en librería (contado o crédito).

    Args:
        payload: Datos de la venta (producto, comprador, cantidad, tipo de pago)
        background_tasks: Manejador de tareas asíncronas para el correo
        usuario_actual: Payload del JWT del operador autenticado

    Returns:
        dict: ID de la venta creada y mensaje de confirmación

    Raises:
        HTTPException 404: Si el producto no existe
        HTTPException 400: Si el stock es insuficiente
        HTTPException 500: Si ocurre un error en la base de datos
    """
    try:
        # 1. Verificar producto y stock
        res_producto = supabase.table("inventario_libreria") \
            .select("id, nombre, stock, precio") \
            .eq("id", payload.producto_id) \
            .execute()

        if not res_producto.data:
            raise HTTPException(status_code=404, detail="Producto no encontrado.")

        producto = res_producto.data[0]
        stock_actual = producto["stock"]

        if stock_actual < payload.cantidad:
            raise HTTPException(status_code=400, detail="Existencias insuficientes en inventario.")

        # 2. Calcular montos
        precio_unitario = producto["precio"]
        total_venta = precio_unitario * payload.cantidad
        es_contado = payload.tipo_pago == "contado"
        estado_inicial = "pagado" if es_contado else "pendiente"
        monto_ingresado = total_venta if es_contado else 0.0

        # 3. Insertar cabecera de venta
        res_venta = supabase.table("libreria_ventas").insert({
            "comprador_cui": payload.comprador_cui,
            "total_venta": total_venta,
            "total_pagado": monto_ingresado,
            "estado_pago": estado_inicial
        }).execute()

        venta_id = res_venta.data[0]["id"]

        # 4. Insertar detalle de venta
        supabase.table("libreria_ventas_detalle").insert({
            "venta_id": venta_id,
            "producto_id": payload.producto_id,
            "cantidad": payload.cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": total_venta
        }).execute()

        # 5. Si es contado, registrar pago con el operador real del JWT
        if es_contado:
            supabase.table("libreria_pagos").insert({
                "venta_id": venta_id,
                "monto_abonado": total_venta,
                "metodo_pago_id": 1,
                "digitado_por": usuario_actual["sub"]
            }).execute()

        # 6. Descontar stock
        supabase.table("inventario_libreria") \
            .update({"stock": stock_actual - payload.cantidad}) \
            .eq("id", payload.producto_id) \
            .execute()

        # 7. Notificación por correo en segundo plano
        tipo_notif = "venta_contado" if es_contado else "venta_credito"
        background_tasks.add_task(
            despachar_correo_libreria,
            {
                "id_transaccion": venta_id,
                "tipo_notificacion": tipo_notif,
                "detalle_producto": producto["nombre"],
                "cantidad": payload.cantidad,
                "monto": total_venta
            }
        )

        return {"mensaje": "Transacción completada exitosamente", "venta_id": venta_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- GESTIÓN DE ABONOS PARCIALES ---

@router.post("/pagos")
async def registrar_abono(
    payload: PagoLibreriaCreate,
    background_tasks: BackgroundTasks,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    """
    Registra un abono parcial o total a una venta a crédito.

    Args:
        payload: Datos del abono (venta_id, monto, metodo_pago_id)
        background_tasks: Manejador de tareas asíncronas para el correo
        usuario_actual: Payload del JWT del operador autenticado

    Returns:
        dict: Estado actualizado de la venta y mensaje de confirmación

    Raises:
        HTTPException 404: Si la venta no existe
        HTTPException 400: Si la venta ya está pagada
        HTTPException 500: Si ocurre un error en la base de datos
    """
    try:
        # 1. Obtener venta
        res_venta = supabase.table("libreria_ventas") \
            .select("id, total_venta, total_pagado, estado_pago") \
            .eq("id", payload.venta_id) \
            .execute()

        if not res_venta.data:
            raise HTTPException(status_code=404, detail="Registro de venta no localizado.")

        venta = res_venta.data[0]

        if venta["estado_pago"] == "pagado":
            raise HTTPException(status_code=400, detail="La deuda asociada a esta venta ya fue liquidada.")

        # 2. Registrar abono con el operador real del JWT
        res_pago = supabase.table("libreria_pagos").insert({
            "venta_id": payload.venta_id,
            "monto_abonado": payload.monto_abonado,
            "metodo_pago_id": payload.metodo_pago_id,
            "digitado_por": usuario_actual["sub"]
        }).execute()

        pago_id = res_pago.data[0]["id"]

        # 3. Recalcular total acumulado de todos los abonos
        res_pagos = supabase.table("libreria_pagos") \
            .select("monto_abonado") \
            .eq("venta_id", payload.venta_id) \
            .execute()

        total_acumulado = sum(p["monto_abonado"] for p in res_pagos.data)
        estado_nuevo = "pagado" if total_acumulado >= venta["total_venta"] else "parcial"

        # 4. Actualizar estado de la venta
        supabase.table("libreria_ventas").update({
            "total_pagado": total_acumulado,
            "estado_pago": estado_nuevo
        }).eq("id", payload.venta_id).execute()

        # 5. Obtener nombre del producto para el correo
        res_detalle = supabase.table("libreria_ventas_detalle") \
            .select("producto_id, inventario_libreria(nombre)") \
            .eq("venta_id", payload.venta_id) \
            .limit(1) \
            .execute()

        nombre_prod = "Abono a Cuenta Credito"
        if res_detalle.data and res_detalle.data[0].get("inventario_libreria"):
            nombre_prod = res_detalle.data[0]["inventario_libreria"]["nombre"]

        # 6. Notificación por correo en segundo plano
        background_tasks.add_task(
            despachar_correo_libreria,
            {
                "id_transaccion": pago_id,
                "tipo_notificacion": "abono_parcial",
                "detalle_producto": f"Abono a cuenta ({nombre_prod})",
                "cantidad": 1,
                "monto": payload.monto_abonado
            }
        )

        return {"mensaje": "Abono aplicado correctamente", "estado_actual": estado_nuevo}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))