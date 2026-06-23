from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from services.gasto_service import registrar_gasto, editar_gasto, eliminar_gasto, listar_gastos
from routers.dependencies import obtener_usuario_actual

router = APIRouter(prefix="/libreria/gastos", tags=["Gastos"])


def _requiere_encargado(usuario: Dict[str, Any]):
    if usuario.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para esta acción.")


@router.get("")
async def obtener_gastos(
    inicio: str = Query("1900-01-01"),
    fin: str = Query("2100-12-31"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(30, ge=1, le=100),
    usuario_actual=Depends(obtener_usuario_actual)
):
    try:
        return listar_gastos(inicio, fin, pagina, por_pagina)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("", status_code=201)
async def crear_gasto(
    payload: dict,
    usuario_actual=Depends(obtener_usuario_actual)
):
    _requiere_encargado(usuario_actual)
    try:
        return registrar_gasto(
            payload["descripcion"], payload["monto"],
            payload.get("categoria", "Otro"), payload.get("fecha_gasto", ""),
            usuario_actual["sub"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.put("/{gasto_id}")
async def actualizar_gasto(
    gasto_id: str,
    payload: dict,
    usuario_actual=Depends(obtener_usuario_actual)
):
    _requiere_encargado(usuario_actual)
    try:
        return editar_gasto(gasto_id, payload["descripcion"], payload["monto"],
                            payload.get("categoria", "Otro"), payload.get("fecha_gasto", ""))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.delete("/{gasto_id}")
async def borrar_gasto(
    gasto_id: str,
    usuario_actual=Depends(obtener_usuario_actual)
):
    _requiere_encargado(usuario_actual)
    try:
        return eliminar_gasto(gasto_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
