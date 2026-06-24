from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from routers.dependencies import obtener_usuario_actual, requiere_empleado
from schemas import ProveedorCreate, ProveedorUpdate, CompraCreate, PagoProveedorCreate
from typing import Dict, Optional
from services.proveedor_service import get_all_proveedores, register_proveedor, update_proveedor_info
from services.compra_service import (
    get_all_compras, register_compra, get_compra_detalle,
    register_pago_proveedor, get_lotes_pendientes, _requiere_permiso
)
from repositories.compra_repository import list_pagos_proveedores as repo_list_pagos

router = APIRouter(dependencies=[Depends(requiere_empleado)])


@router.get("/proveedores")
async def listar_proveedores(estado: str = "activos", usuario_actual: Dict = Depends(obtener_usuario_actual)):
    return get_all_proveedores(estado)


@router.post("/proveedores", status_code=201)
async def crear_proveedor(payload: ProveedorCreate, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    _requiere_permiso(usuario_actual)
    return register_proveedor(payload)


@router.put("/proveedores/{proveedor_id}")
async def actualizar_proveedor(proveedor_id: str, payload: ProveedorUpdate, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    _requiere_permiso(usuario_actual)
    return update_proveedor_info(proveedor_id, payload)


@router.post("", status_code=201)
async def registrar_compra(payload: CompraCreate, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    _requiere_permiso(usuario_actual)
    return register_compra(payload, usuario_actual["sub"])


@router.get("")
async def listar_compras(proveedor_id: Optional[str] = None, estado: Optional[str] = None, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    return get_all_compras(proveedor_id, estado)


@router.get("/lotes/pendientes")
async def lotes_pendientes(producto_id: Optional[str] = None, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    return get_lotes_pendientes(producto_id)


@router.get("/{compra_id}")
async def obtener_compra(compra_id: str, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    return get_compra_detalle(compra_id)


@router.post("/pagos_proveedores", status_code=201)
async def registrar_pago_proveedor(payload: PagoProveedorCreate, background_tasks: BackgroundTasks, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    _requiere_permiso(usuario_actual)
    return register_pago_proveedor(payload, usuario_actual["sub"], background_tasks)


@router.get("/pagos_proveedores")
async def listar_pagos_proveedores(compra_id: Optional[str] = None, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    return repo_list_pagos(compra_id)
