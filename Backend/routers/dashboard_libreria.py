"""
Módulo de dashboard para librería.
Provee KPIs y actividad reciente para el panel de control del módulo.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from database import supabase
from routers.dependencies import obtener_usuario_actual
from typing import Dict, Any
from datetime import datetime
import pytz

router = APIRouter()

ZONA_GT = pytz.timezone("America/Guatemala")


@router.get("/kpis")
async def obtener_kpis(
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    """
    Retorna los KPIs principales del módulo de librería.

    Returns:
        dict: Ventas del día, créditos pendientes y ventas del mes

    Raises:
        HTTPException 500: Si ocurre un error al consultar la base de datos
    """
    try:
        ahora = datetime.now(ZONA_GT)
        inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        # Ventas del día (contado y crédito)
        res_dia = supabase.table("libreria_ventas") \
            .select("total_venta, estado_pago") \
            .gte("created_at", inicio_dia) \
            .execute()

        ventas_dia = res_dia.data or []
        ventas_dia_total = sum(v["total_venta"] for v in ventas_dia)
        ventas_dia_cantidad = len(ventas_dia)

        # Créditos pendientes (estado pendiente o parcial)
        res_creditos = supabase.table("libreria_ventas") \
            .select("total_venta, total_pagado") \
            .in_("estado_pago", ["pendiente", "parcial"]) \
            .execute()

        creditos = res_creditos.data or []
        creditos_pendientes_total = sum(
            v["total_venta"] - v["total_pagado"] for v in creditos
        )
        creditos_pendientes_cantidad = len(creditos)

        # Ventas del mes
        res_mes = supabase.table("libreria_ventas") \
            .select("total_venta") \
            .gte("created_at", inicio_mes) \
            .execute()

        ventas_mes = res_mes.data or []
        ventas_mes_total = sum(v["total_venta"] for v in ventas_mes)

        return {
            "ventas_dia_total": ventas_dia_total,
            "ventas_dia_cantidad": ventas_dia_cantidad,
            "creditos_pendientes_total": creditos_pendientes_total,
            "creditos_pendientes_cantidad": creditos_pendientes_cantidad,
            "ventas_mes_total": ventas_mes_total,
            "meta_mes": 50000
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actividad")
async def obtener_actividad(
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    """
    Retorna la actividad reciente de ventas con paginación.

    Args:
        pagina: Número de página solicitada
        por_pagina: Registros por página

    Returns:
        dict: Lista de ventas recientes con metadatos de paginación

    Raises:
        HTTPException 500: Si ocurre un error al consultar la base de datos
    """
    try:
        offset = (pagina - 1) * por_pagina

        # Total de registros
        res_total = supabase.table("libreria_ventas") \
            .select("id", count="exact") \
            .execute()

        total = res_total.count or 0
        total_paginas = (total + por_pagina - 1) // por_pagina

        # Registros paginados ordenados por fecha descendente
        res = supabase.table("libreria_ventas") \
            .select("id, comprador_cui, total_venta, total_pagado, estado_pago, created_at") \
            .order("created_at", desc=True) \
            .range(offset, offset + por_pagina - 1) \
            .execute()

        return {
            "data": res.data or [],
            "paginacion": {
                "pagina_actual": pagina,
                "por_pagina": por_pagina,
                "total_registros": total,
                "total_paginas": total_paginas,
                "tiene_siguiente": pagina < total_paginas,
                "tiene_anterior": pagina > 1
            },
            "ok": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))