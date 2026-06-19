"""
Módulo de dashboard para librería.
Provee KPIs y actividad reciente filtrados según el rango del usuario.
- Administrador: ve todo
- Encargado: ve todos los analistas
- Analista: ve solo sus propias operaciones
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from database import supabase
from routers.dependencies import obtener_usuario_actual
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

router = APIRouter()

ZONA_GT = pytz.timezone("America/Guatemala")


@router.get("/kpis")
async def obtener_kpis(
    cui: Optional[str] = Query(default=None),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    """
    Retorna KPIs del módulo de librería filtrados según el rango del usuario.

    - Analista: solo sus propias ventas (ignora el parámetro cui)
    - Encargado: puede filtrar por analista específico o ver todos los analistas
    - Administrador: ve todo, puede filtrar por cualquier usuario

    Args:
        cui: CUI opcional para filtrar por operador específico

    Returns:
        dict: KPIs de ventas del día, créditos pendientes y ventas del mes

    Raises:
        HTTPException 500: Si ocurre un error al consultar la base de datos
    """
    try:
        rango = usuario_actual.get("rango", "analista")
        cui_actual = usuario_actual.get("sub")

        ahora = datetime.now(ZONA_GT)
        inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        # El analista siempre ve solo sus propias operaciones
        # El backend ignora cualquier parámetro cui enviado por el analista
        if rango == "analista":
            cui_filtro = cui_actual
        elif cui and rango in ["encargado", "administrador", "super_admin"]:
            cui_filtro = cui
        else:
            cui_filtro = None

        # Ventas del día
        query_dia = supabase.table("libreria_ventas").select("total_venta, estado_pago").gte("created_at", inicio_dia)
        if cui_filtro:
            query_dia = query_dia.eq("digitado_por", cui_filtro)
        res_dia = query_dia.execute()

        ventas_dia = res_dia.data or []
        ventas_dia_total = sum(v["total_venta"] for v in ventas_dia)
        ventas_dia_cantidad = len(ventas_dia)

        # Créditos pendientes
        query_creditos = supabase.table("libreria_ventas").select("total_venta, total_pagado").in_("estado_pago", ["pendiente", "parcial"])
        if cui_filtro:
            query_creditos = query_creditos.eq("digitado_por", cui_filtro)
        res_creditos = query_creditos.execute()

        creditos = res_creditos.data or []
        creditos_pendientes_total = sum(v["total_venta"] - v["total_pagado"] for v in creditos)
        creditos_pendientes_cantidad = len(creditos)

        # Ventas del mes
        query_mes = supabase.table("libreria_ventas").select("total_venta").gte("created_at", inicio_mes)
        if cui_filtro:
            query_mes = query_mes.eq("digitado_por", cui_filtro)
        res_mes = query_mes.execute()

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
    cui: Optional[str] = Query(default=None),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    """
    Retorna actividad reciente de ventas filtrada según el rango del usuario.

    - Analista: solo sus propias ventas (ignora el parámetro cui)
    - Encargado: puede filtrar por analista o ver todos los analistas
    - Administrador: ve todo, puede filtrar por cualquier usuario

    Args:
        pagina: Número de página solicitada
        por_pagina: Registros por página
        cui: CUI opcional para filtrar por operador

    Returns:
        dict: Lista paginada de ventas con metadatos

    Raises:
        HTTPException 500: Si ocurre un error al consultar la base de datos
    """
    try:
        rango = usuario_actual.get("rango", "analista")
        cui_actual = usuario_actual.get("sub")

        # El analista siempre ve solo sus propias operaciones
        if rango == "analista":
            cui_filtro = cui_actual
        elif cui and rango in ["encargado", "administrador", "super_admin"]:
            cui_filtro = cui
        else:
            cui_filtro = None

        offset = (pagina - 1) * por_pagina

        # Total de registros
        query_total = supabase.table("libreria_ventas").select("id", count="exact")
        if cui_filtro:
            query_total = query_total.eq("digitado_por", cui_filtro)
        res_total = query_total.execute()

        total = res_total.count or 0
        total_paginas = max((total + por_pagina - 1) // por_pagina, 1)

        # Registros paginados
        query = supabase.table("libreria_ventas") \
            .select("id, comprador_cui, total_venta, total_pagado, estado_pago, created_at, digitado_por") \
            .order("created_at", desc=True) \
            .range(offset, offset + por_pagina - 1)

        if cui_filtro:
            query = query.eq("digitado_por", cui_filtro)

        res = query.execute()

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