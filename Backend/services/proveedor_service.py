from typing import Dict, Any
from fastapi import HTTPException
from schemas import ProveedorCreate, ProveedorUpdate
from repositories.proveedor_repository import (
    list_proveedores, find_proveedor_by_id, find_proveedor_por_nombre,
    create_proveedor, update_proveedor
)


def get_all_proveedores(estado: str = "activos") -> list:
    return list_proveedores(estado)


def register_proveedor(payload: ProveedorCreate) -> Dict[str, Any]:
    if find_proveedor_por_nombre(payload.nombre):
        raise HTTPException(400, f"Ya existe un proveedor con el nombre '{payload.nombre}'. Use un nombre diferente.")
    data = payload.model_dump()
    nuevo = create_proveedor(data)
    return {"mensaje": "Proveedor creado", "data": nuevo}


def update_proveedor_info(proveedor_id: str, payload: ProveedorUpdate) -> Dict[str, Any]:
    existente = find_proveedor_by_id(proveedor_id)
    if not existente:
        raise HTTPException(404, "Proveedor no encontrado")
    if payload.nombre:
        if find_proveedor_por_nombre(payload.nombre, excluir_id=proveedor_id):
            raise HTTPException(400, f"Ya existe otro proveedor con el nombre '{payload.nombre}'. Use un nombre diferente.")
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(400, "No hay datos para actualizar")
    result = update_proveedor(proveedor_id, update_data)
    return {"mensaje": "Proveedor actualizado", "data": result}
