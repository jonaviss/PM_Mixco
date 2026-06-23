from fastapi import APIRouter, HTTPException, Depends
from routers.dependencies import obtener_usuario_actual
from typing import Dict, Any
from services.cliente_service import obtener_mis_compras, obtener_mis_pagos

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
