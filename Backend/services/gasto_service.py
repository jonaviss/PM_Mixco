from typing import Dict, Any, Optional
from fastapi import HTTPException
from repositories.gasto_repository import (
    create_gasto, update_gasto, delete_gasto, find_gasto_by_id, list_gastos, sum_gastos_periodo
)
from datetime import date, datetime
import pytz

ZONA_GT = pytz.timezone("America/Guatemala")


def _hoy_gt() -> str:
    return str(datetime.now(ZONA_GT).date())

def _fin_mes() -> str:
    import calendar
    ahora_gt = datetime.now(ZONA_GT).date()
    ultimo_dia = calendar.monthrange(ahora_gt.year, ahora_gt.month)[1]
    return str(ahora_gt.replace(day=ultimo_dia))

def obtener_resumen() -> dict:
    hoy = _hoy_gt()
    inicio_mes = str(datetime.now(ZONA_GT).date().replace(day=1))
    fin_mes = _fin_mes()
    return {
        "total_hoy": sum_gastos_periodo(hoy, hoy),
        "total_mes": sum_gastos_periodo(inicio_mes, fin_mes),
    }


def registrar_gasto(descripcion: str, monto: float, categoria: str, fecha_gasto: str, usuario_cui: str) -> dict:
    if not descripcion.strip():
        raise HTTPException(400, "La descripción es obligatoria")
    if monto <= 0:
        raise HTTPException(400, "El monto debe ser mayor a cero")
    gasto = create_gasto({
        "descripcion": descripcion.strip(),
        "monto": monto,
        "categoria": categoria.strip() or "Otro",
        "fecha_gasto": fecha_gasto or _hoy_gt(),
        "registrado_por": usuario_cui
    })
    return {"mensaje": "Gasto registrado", "data": gasto}


def editar_gasto(gasto_id: str, descripcion: str, monto: float, categoria: str, fecha_gasto: str) -> dict:
    existente = find_gasto_by_id(gasto_id)
    if not existente:
        raise HTTPException(404, "Gasto no encontrado")
    if not descripcion.strip():
        raise HTTPException(400, "La descripción es obligatoria")
    if monto <= 0:
        raise HTTPException(400, "El monto debe ser mayor a cero")
    update_gasto(gasto_id, {
        "descripcion": descripcion.strip(),
        "monto": monto,
        "categoria": categoria.strip() or "Otro",
        "fecha_gasto": fecha_gasto or _hoy_gt()
    })
    return {"mensaje": "Gasto actualizado"}


def eliminar_gasto(gasto_id: str) -> dict:
    existente = find_gasto_by_id(gasto_id)
    if not existente:
        raise HTTPException(404, "Gasto no encontrado")
    delete_gasto(gasto_id)
    return {"mensaje": "Gasto eliminado"}


def listar_gastos(inicio: str, fin: str, pagina: int = 1, por_pagina: int = 30) -> dict:
    return list_gastos(inicio, fin, pagina, por_pagina)
