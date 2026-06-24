import io
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse
from schemas import (
    ProductoLibreriaCreate, ProductoLibreriaUpdate,
    VentaLibreriaCreate, VentaMultipleCreate,
    PagoLibreriaCreate, AbonoDistribuidoCreate
)
from routers.dependencies import obtener_usuario_actual, requiere_encargado, requiere_empleado
from routers.pdf_libreria import generar_pdf_comprobante

from services.inventario_service import (
    get_all_productos, register_producto, update_producto_info, toggle_producto_estado
)
from services.venta_service import (
    registrar_venta_simple, registrar_venta_multiple,
    buscar_ventas, get_reporte_ventas, obtener_detalle_venta_completo, cancelar_venta
)
from services.pago_service import (
    registrar_abono, distribuir_abono, obtener_pendientes, obtener_historial_cliente, anular_pago
)
from services.notificacion_service import despachar_correo_libreria
from repositories.common_repository import find_vendedores_por_modulo, find_usuarios_activos, find_all_usuarios_basico

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(requiere_empleado)])


@router.get("/productos")
async def listar_productos(
    incluir_inactivos: bool = False,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    busqueda: str = Query(""),
    categoria: str = Query(""),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    return get_all_productos(incluir_inactivos, pagina, por_pagina, busqueda, categoria)


@router.get("/productos/resumen")
async def listar_productos_resumen(
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    from services.inventario_service import get_todos_productos_sin_paginar
    return get_todos_productos_sin_paginar()


@router.get("/clientes")
async def listar_clientes(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return find_all_usuarios_basico()


@router.post("/productos", status_code=status.HTTP_201_CREATED)
def registrar_producto(
    payload: ProductoLibreriaCreate,
    usuario_actual=Depends(obtener_usuario_actual)
):
    requiere_encargado(usuario_actual)
    nuevo = register_producto(payload, usuario_actual["sub"])
    return {"mensaje": "Producto registrado", "data": nuevo}


@router.put("/productos/{producto_id}")
def actualizar_producto(
    producto_id: str,
    payload: ProductoLibreriaUpdate,
    usuario_actual=Depends(obtener_usuario_actual)
):
    requiere_encargado(usuario_actual)
    result = update_producto_info(producto_id, payload)
    return {"mensaje": "Producto actualizado", "data": result}


@router.put("/productos/{producto_id}/toggle-estado")
async def toggle_estado_producto(
    producto_id: str,
    usuario_actual=Depends(obtener_usuario_actual)
):
    requiere_encargado(usuario_actual)
    mensaje, estado = toggle_producto_estado(producto_id)
    return {"mensaje": mensaje, "estado": estado}


@router.post("/ventas", status_code=status.HTTP_201_CREATED)
async def registrar_venta(
    payload: VentaLibreriaCreate,
    background_tasks: BackgroundTasks,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    return await registrar_venta_simple(payload, usuario_actual["sub"], background_tasks)


@router.post("/ventas/multiple", status_code=status.HTTP_201_CREATED)
async def registrar_venta_multiple_endpoint(
    payload: VentaMultipleCreate,
    background_tasks: BackgroundTasks,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    return await registrar_venta_multiple(payload, usuario_actual["sub"], background_tasks)


@router.get("/ventas/buscar")
async def buscar_ventas_endpoint(
    q: str = Query("", min_length=0),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(30, ge=1, le=100),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    return await buscar_ventas(q, pagina, por_pagina)


@router.get("/ventas/reporte")
async def reporte_ventas(
    inicio: str,
    fin: str,
    operador_cui: Optional[str] = None,
    cliente_cui: Optional[str] = None,
    estado: Optional[str] = None,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    return await get_reporte_ventas(inicio, fin, operador_cui, cliente_cui, estado)


@router.get("/ventas/{venta_id}")
async def obtener_venta(
    venta_id: str,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    venta, productos, pagos, cliente, _, operador = await obtener_detalle_venta_completo(venta_id)
    return {
        "id": venta["id"],
        "comprador_cui": venta["comprador_cui"],
        "total_venta": venta["total_venta"],
        "total_pagado": venta["total_pagado"],
        "estado_pago": venta["estado_pago"],
        "created_at": venta["created_at"],
        "digitado_por": venta["digitado_por"],
        "productos": productos,
        "pagos": pagos,
        "usuarios": {"nombre_completo": cliente}
    }


@router.delete("/ventas/{venta_id}", status_code=status.HTTP_200_OK)
async def cancelar_venta_endpoint(
    venta_id: str,
    background_tasks: BackgroundTasks,
    motivo: str = Query("", min_length=0, max_length=500),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    return await cancelar_venta(venta_id, motivo, background_tasks)


@router.post("/pagos")
async def registrar_abono_endpoint(
    payload: PagoLibreriaCreate,
    background_tasks: BackgroundTasks,
    usuario_actual=Depends(obtener_usuario_actual)
):
    return await registrar_abono(payload, usuario_actual["sub"], background_tasks)


@router.post("/pagos/distribuir", status_code=status.HTTP_201_CREATED)
async def distribuir_abono_endpoint(
    payload: AbonoDistribuidoCreate,
    background_tasks: BackgroundTasks,
    usuario_actual=Depends(obtener_usuario_actual)
):
    return await distribuir_abono(payload, usuario_actual["sub"], background_tasks)


@router.get("/cobros/pendientes")
async def obtener_pendientes_endpoint(
    cui: str,
    usuario_actual=Depends(obtener_usuario_actual)
):
    return obtener_pendientes(cui)


@router.delete("/pagos/{pago_id}")
async def anular_pago_endpoint(
    pago_id: str,
    usuario_actual=Depends(obtener_usuario_actual)
):
    return anular_pago(pago_id)


@router.get("/clientes/{cui}/historial")
async def obtener_historial_cliente_endpoint(
    cui: str,
    usuario_actual=Depends(obtener_usuario_actual)
):
    return obtener_historial_cliente(cui)


@router.get("/ventas/{venta_id}/detalle")
async def obtener_detalle_venta(
    venta_id: str,
    usuario_actual=Depends(obtener_usuario_actual)
):
    venta, productos, pagos, cliente, _, operador = await obtener_detalle_venta_completo(venta_id)
    deuda_total, cant_deudas = 0.0, 0
    from repositories.pago_repository import calcular_deuda_comprador
    deuda_total, cant_deudas = calcular_deuda_comprador(venta["comprador_cui"])
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
        "deuda_hermano": {"total": deuda_total, "cantidad": cant_deudas},
        "ok": True
    }


@router.get("/usuarios/vendedores")
async def listar_vendedores(
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    accesos = find_vendedores_por_modulo()
    vendedores = []
    vistos = set()
    for u in accesos:
        cui = u["usuario_cui"]
        if cui and cui not in vistos:
            vistos.add(cui)
            vendedores.append({
                "cui": cui,
                "nombre_completo": u.get("usuarios", {}).get("nombre_completo", "—")
            })
    if not vendedores:
        vendedores = find_usuarios_activos()
    return vendedores


@router.get("/ventas/{venta_id}/pdf")
async def descargar_pdf_venta(
    venta_id: str,
    usuario_actual=Depends(obtener_usuario_actual)
):
    venta, productos, pagos, cliente, _, operador = await obtener_detalle_venta_completo(venta_id)
    tipo = "venta_contado" if venta["estado_pago"] == "pagado" and venta["total_pagado"] >= venta["total_venta"] else "venta_credito"
    datos_pdf = {
        "tipo_notificacion": tipo,
        "id_transaccion": venta_id,
        "monto": float(venta["total_venta"]),
        "venta": {
            "id": venta_id,
            "comprador_cui": venta["comprador_cui"],
            "total_venta": float(venta["total_venta"]),
            "total_pagado": float(venta["total_pagado"]),
            "saldo_pendiente": float(venta["total_venta"]) - float(venta["total_pagado"]),
            "estado_pago": venta["estado_pago"],
            "created_at": venta["created_at"],
            "operador": operador
        },
        "productos": productos,
        "pagos": pagos,
        "hermano": {"cui": venta["comprador_cui"], "nombre_completo": cliente},
        "deuda_hermano": {"total": 0, "cantidad": 0}
    }
    pdf_bytes = generar_pdf_comprobante(datos_pdf)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=recibo_{venta_id[:8]}.pdf"}
    )


@router.post("/ventas/{venta_id}/reenviar-correo")
async def reenviar_correo_venta(
    venta_id: str,
    background_tasks: BackgroundTasks,
    usuario_actual=Depends(obtener_usuario_actual)
):
    venta, productos, pagos, cliente, correo_cliente, operador = await obtener_detalle_venta_completo(venta_id)
    tipo = "venta_contado" if venta["estado_pago"] == "pagado" and venta["total_pagado"] >= venta["total_venta"] else "venta_credito"
    datos_pdf = {
        "tipo_notificacion": tipo,
        "id_transaccion": venta_id,
        "monto": float(venta["total_venta"]),
        "venta": {
            "id": venta_id,
            "comprador_cui": venta["comprador_cui"],
            "total_venta": float(venta["total_venta"]),
            "total_pagado": float(venta["total_pagado"]),
            "saldo_pendiente": float(venta["total_venta"]) - float(venta["total_pagado"]),
            "estado_pago": venta["estado_pago"],
            "created_at": venta["created_at"],
            "operador": operador
        },
        "productos": productos,
        "pagos": pagos,
        "hermano": {"cui": venta["comprador_cui"], "nombre_completo": cliente, "correo": correo_cliente},
        "deuda_hermano": {"total": 0, "cantidad": 0}
    }
    background_tasks.add_task(despachar_correo_libreria, datos_pdf)
    return {"mensaje": "Correo reenviado correctamente"}
