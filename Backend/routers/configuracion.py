from fastapi import APIRouter, HTTPException, Depends
from routers.dependencies import obtener_usuario_actual, requiere_empleado
from typing import Dict, Any
from schemas import TipoProductoCreate, TipoProductoUpdate, MetodoPagoCreate, MetodoPagoUpdate, ConfiguracionCorreoUpdate
from services.configuracion_service import (
    listar_tipos_producto, crear_tipo_producto, actualizar_tipo_producto, eliminar_tipo_producto,
    listar_metodos_pago, crear_metodo_pago, actualizar_metodo_pago, eliminar_metodo_pago,
    obtener_configuracion_correo, actualizar_configuracion_correo
)

router = APIRouter(prefix="/configuracion", tags=["Configuración"], dependencies=[Depends(requiere_empleado)])


@router.get("/tipos-producto")
async def listar_tipos_producto_endpoint(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return listar_tipos_producto()


@router.post("/tipos-producto", status_code=201)
async def crear_tipo_producto_endpoint(data: TipoProductoCreate, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return crear_tipo_producto(data.nombre)


@router.put("/tipos-producto/{tipo_id}")
async def actualizar_tipo_producto_endpoint(tipo_id: int, data: TipoProductoUpdate, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return actualizar_tipo_producto(tipo_id, {"nombre": data.nombre})


@router.delete("/tipos-producto/{tipo_id}")
async def eliminar_tipo_producto_endpoint(tipo_id: int, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return eliminar_tipo_producto(tipo_id)


@router.get("/metodos-pago")
async def listar_metodos_pago_endpoint(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return listar_metodos_pago()


@router.post("/metodos-pago", status_code=201)
async def crear_metodo_pago_endpoint(data: MetodoPagoCreate, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return crear_metodo_pago(data.nombre)


@router.put("/metodos-pago/{metodo_id}")
async def actualizar_metodo_pago_endpoint(metodo_id: int, data: MetodoPagoUpdate, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return actualizar_metodo_pago(metodo_id, {"nombre": data.nombre})


@router.delete("/metodos-pago/{metodo_id}")
async def eliminar_metodo_pago_endpoint(metodo_id: int, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return eliminar_metodo_pago(metodo_id)


@router.get("/correo")
async def obtener_correo_endpoint(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return obtener_configuracion_correo()


@router.put("/correo")
async def actualizar_correo_endpoint(data: ConfiguracionCorreoUpdate, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    return actualizar_configuracion_correo(data.model_dump(exclude_none=True))
