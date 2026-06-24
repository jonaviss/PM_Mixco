from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from schemas import GastoCreate, GastoUpdate
from services.gasto_service import registrar_gasto, editar_gasto, eliminar_gasto, listar_gastos, obtener_resumen
from routers.dependencies import obtener_usuario_actual, requiere_encargado, requiere_empleado

router = APIRouter(prefix="/libreria/gastos", tags=["Gastos"], dependencies=[Depends(requiere_empleado)])


@router.get("")
async def obtener_gastos(
    inicio: str = Query("1900-01-01"),
    fin: str = Query("2100-12-31"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(30, ge=1, le=100),
    usuario_actual=Depends(obtener_usuario_actual)
):
    return listar_gastos(inicio, fin, pagina, por_pagina)


@router.get("/resumen")
async def resumen_gastos(
    usuario_actual=Depends(obtener_usuario_actual)
):
    return obtener_resumen()


@router.post("", status_code=201)
async def crear_gasto(
    payload: GastoCreate,
    usuario_actual=Depends(obtener_usuario_actual)
):
    requiere_encargado(usuario_actual)
    return registrar_gasto(
        payload.descripcion, payload.monto,
        payload.categoria, payload.fecha_gasto,
        usuario_actual["sub"]
    )


@router.put("/{gasto_id}")
async def actualizar_gasto(
    gasto_id: str,
    payload: GastoUpdate,
    usuario_actual=Depends(obtener_usuario_actual)
):
    requiere_encargado(usuario_actual)
    return editar_gasto(gasto_id, payload.descripcion, payload.monto,
                        payload.categoria, payload.fecha_gasto)


@router.delete("/{gasto_id}")
async def borrar_gasto(
    gasto_id: str,
    usuario_actual=Depends(obtener_usuario_actual)
):
    requiere_encargado(usuario_actual)
    return eliminar_gasto(gasto_id)
