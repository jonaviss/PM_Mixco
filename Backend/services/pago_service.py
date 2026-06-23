from typing import List, Dict, Any, Optional
from fastapi import HTTPException, BackgroundTasks
from schemas import PagoLibreriaCreate, AbonoDistribuidoCreate
from repositories.pago_repository import create_pago, sum_pagos_by_venta, calcular_deuda_comprador, find_pago_by_id, delete_pago as repo_delete_pago
from repositories.venta_repository import (
    find_venta_basica, update_venta, find_ventas_by_comprador, find_primer_detalle
)
from repositories.common_repository import find_usuario_basico, find_usuario_nombre
from services.notificacion_service import despachar_correo_libreria


async def registrar_abono(
    payload: PagoLibreriaCreate, usuario_cui: str, background_tasks: BackgroundTasks
) -> dict:
    venta = find_venta_basica(payload.venta_id)
    if not venta:
        raise HTTPException(404, "Registro de venta no localizado.")
    if venta["estado_pago"] == "pagado":
        raise HTTPException(400, "La deuda asociada a esta venta ya fue liquidada.")

    comprador = find_usuario_basico(venta["comprador_cui"]) or {"cui": venta["comprador_cui"], "nombre_completo": "—", "correo": ""}

    pago = create_pago({
        "venta_id": payload.venta_id,
        "monto_abonado": payload.monto_abonado,
        "metodo_pago_id": payload.metodo_pago_id,
        "digitado_por": usuario_cui
    })

    total_acumulado = sum_pagos_by_venta(payload.venta_id)
    estado_nuevo = "pagado" if total_acumulado >= float(venta["total_venta"]) else "parcial"
    update_venta(payload.venta_id, {"total_pagado": total_acumulado, "estado_pago": estado_nuevo})

    det = find_primer_detalle(payload.venta_id)
    nombre_prod = "Abono a Cuenta Credito"
    if det and det.get("inventario_libreria"):
        nombre_prod = det["inventario_libreria"]["nombre"]

    background_tasks.add_task(despachar_correo_libreria, {
        "id_transaccion": pago["id"],
        "tipo_notificacion": "abono_parcial",
        "detalle_producto": f"Abono a cuenta ({nombre_prod})",
        "cantidad": 1,
        "monto": payload.monto_abonado,
        "hermano": comprador
    })

    return {"mensaje": "Abono aplicado correctamente", "estado_actual": estado_nuevo}


async def distribuir_abono(
    payload: AbonoDistribuidoCreate, usuario_cui: str, background_tasks: BackgroundTasks
) -> dict:
    ventas = find_ventas_by_comprador(payload.comprador_cui, ["pendiente", "parcial"])
    if not ventas:
        raise HTTPException(404, "Este cliente no tiene ventas pendientes de pago.")

    deuda_total = sum(float(v["total_venta"]) - float(v["total_pagado"])
                      for v in ventas if float(v["total_venta"]) - float(v["total_pagado"]) > 0)
    if float(payload.monto_abonado) > deuda_total:
        raise HTTPException(400, f"El monto ingresado (Q{payload.monto_abonado:.2f}) supera la deuda total (Q{deuda_total:.2f}).")

    monto_restante = float(payload.monto_abonado)
    ventas_pagadas = []

    for venta in ventas:
        if monto_restante <= 0:
            break
        pendiente = float(venta["total_venta"]) - float(venta["total_pagado"])
        if pendiente <= 0:
            continue
        abono = min(monto_restante, pendiente)
        create_pago({
            "venta_id": venta["id"],
            "monto_abonado": abono,
            "metodo_pago_id": payload.metodo_pago_id,
            "digitado_por": usuario_cui
        })
        nuevo_pagado = float(venta["total_pagado"]) + abono
        nuevo_estado = "pagado" if nuevo_pagado >= float(venta["total_venta"]) else "parcial"
        update_venta(venta["id"], {"total_pagado": nuevo_pagado, "estado_pago": nuevo_estado})
        ventas_pagadas.append({"venta_id": venta["id"], "abono_aplicado": abono, "estado": nuevo_estado})
        monto_restante -= abono

    if ventas_pagadas:
        comprador = find_usuario_basico(payload.comprador_cui) or {"cui": payload.comprador_cui, "nombre_completo": "—", "correo": ""}
        deuda_restante, cant_deudas = calcular_deuda_comprador(payload.comprador_cui)
        operador = find_usuario_nombre(usuario_cui) or usuario_cui
        background_tasks.add_task(despachar_correo_libreria, {
            "id_transaccion": ventas_pagadas[0]["venta_id"],
            "tipo_notificacion": "abono_parcial",
            "monto": float(payload.monto_abonado),
            "venta": {
                "id": ventas_pagadas[0]["venta_id"],
                "comprador_cui": payload.comprador_cui,
                "total_venta": float(payload.monto_abonado),
                "total_pagado": float(payload.monto_abonado),
                "saldo_pendiente": deuda_restante,
                "estado_pago": ventas_pagadas[0]["estado"],
                "operador": operador
            },
            "productos": [],
            "pagos": [{"monto_abonado": float(payload.monto_abonado), "fecha_pago": None, "operador": operador}],
            "hermano": comprador,
            "deuda_hermano": {"total": deuda_restante, "cantidad": cant_deudas}
        })

    return {
        "mensaje": f"Abono de Q{payload.monto_abonado:.2f} distribuido correctamente.",
        "ventas_actualizadas": ventas_pagadas,
        "saldo_restante": round(monto_restante, 2),
        "ok": True
    }


def anular_pago(pago_id: str) -> dict:
    pago = find_pago_by_id(pago_id)
    if not pago:
        raise HTTPException(404, "Cobro no encontrado")
    venta_id = pago["venta_id"]
    repo_delete_pago(pago_id)
    total_pagado = sum_pagos_by_venta(venta_id)
    venta = find_venta_basica(venta_id)
    if not venta:
        return {"mensaje": "Cobro anulado", "ok": True}
    total_venta = float(venta["total_venta"])
    if total_pagado <= 0:
        update_venta(venta_id, {"total_pagado": 0, "estado_pago": "pendiente"})
    elif total_pagado < total_venta:
        update_venta(venta_id, {"total_pagado": total_pagado, "estado_pago": "parcial"})
    else:
        update_venta(venta_id, {"total_pagado": total_pagado, "estado_pago": "pagado"})
    return {"mensaje": "Cobro anulado correctamente", "ok": True}


def obtener_pendientes(cui: str) -> dict:
    ventas = find_ventas_by_comprador(cui, ["pendiente", "parcial"])
    return {"ventas": ventas or [], "ok": True}


def obtener_historial_cliente(cui: str) -> dict:
    from repositories.venta_repository import find_ventas_by_comprador_all
    from repositories.common_repository import find_usuarios_by_cuis
    ventas = find_ventas_by_comprador_all(cui)
    cuis_op = list(set(v["digitado_por"] for v in ventas if v.get("digitado_por")))
    nombres = find_usuarios_by_cuis(cuis_op) if cuis_op else {}
    for v in ventas:
        v["nombre_operador"] = nombres.get(v.get("digitado_por"))
    return {"ventas": ventas, "ok": True}
