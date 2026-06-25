import io
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from routers.dependencies import obtener_usuario_actual
from typing import Dict, Any
from services.cliente_service import obtener_mis_compras, obtener_mis_pagos, obtener_detalle_venta_cliente
from routers.pdf_libreria import generar_pdf_comprobante

router = APIRouter(prefix="/cliente", tags=["Cliente"])


@router.get("/compras")
async def mis_compras(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return obtener_mis_compras(usuario_actual["sub"])
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/pagos")
async def mis_pagos(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return obtener_mis_pagos(usuario_actual["sub"])
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/ventas/{venta_id}/detalle")
async def detalle_venta(
    venta_id: str,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    return await obtener_detalle_venta_cliente(usuario_actual["sub"], venta_id)


@router.get("/ventas/{venta_id}/pdf")
async def pdf_venta(
    venta_id: str,
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    data = await obtener_detalle_venta_cliente(usuario_actual["sub"], venta_id)
    venta = data["venta"]
    tipo = "venta_contado" if venta["estado_pago"] == "pagado" and venta["total_pagado"] >= venta["total_venta"] else "venta_credito"
    datos_pdf = {
        "tipo_notificacion": tipo,
        "id_transaccion": venta_id,
        "monto": float(venta["total_venta"]),
        "venta": venta,
        "productos": data["productos"],
        "pagos": data["pagos"],
        "hermano": {"cui": venta["comprador_cui"], "nombre_completo": venta.get("cliente", "—")},
        "deuda_hermano": {"total": 0, "cantidad": 0}
    }
    pdf_bytes = generar_pdf_comprobante(datos_pdf)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=recibo_{venta_id[:8]}.pdf"}
    )
