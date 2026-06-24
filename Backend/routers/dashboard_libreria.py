from fastapi import APIRouter, HTTPException, Depends, Query
from routers.dependencies import obtener_usuario_actual
from typing import Dict, Any, Optional
from services.dashboard_service import _resolver_cui_filtro, obtener_kpis, obtener_actividad, obtener_creditos_detallados, obtener_pagados_detallados

router = APIRouter()


@router.get("/kpis")
async def obtener_kpis_endpoint(
    cui: Optional[str] = Query(default=None),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    cui_filtro = _resolver_cui_filtro(usuario_actual, cui)
    return obtener_kpis(cui_filtro)


@router.get("/creditos")
async def obtener_creditos_endpoint(
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    cui: Optional[str] = Query(default=None),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    cui_filtro = _resolver_cui_filtro(usuario_actual, cui)
    return obtener_creditos_detallados(cui_filtro, pagina, por_pagina)


@router.get("/pagados")
async def obtener_pagados_endpoint(
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    cui: Optional[str] = Query(default=None),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    cui_filtro = _resolver_cui_filtro(usuario_actual, cui)
    return obtener_pagados_detallados(cui_filtro, pagina, por_pagina)


@router.get("/actividad")
async def obtener_actividad_endpoint(
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=10, ge=1, le=100),
    cui: Optional[str] = Query(default=None),
    usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)
):
    cui_filtro = _resolver_cui_filtro(usuario_actual, cui)
    return obtener_actividad(pagina, por_pagina, cui_filtro)
