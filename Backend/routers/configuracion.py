from fastapi import APIRouter, HTTPException, Depends
from routers.dependencies import obtener_usuario_actual
from typing import Dict, Any
from services.configuracion_service import (
    listar_tipos_producto, crear_tipo_producto, actualizar_tipo_producto, eliminar_tipo_producto,
    listar_metodos_pago, crear_metodo_pago, actualizar_metodo_pago, eliminar_metodo_pago,
    obtener_configuracion_correo, actualizar_configuracion_correo
)

router = APIRouter(prefix="/configuracion", tags=["Configuración"])


@router.get("/tipos-producto")
async def listar_tipos_producto_endpoint(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return listar_tipos_producto()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/tipos-producto", status_code=201)
async def crear_tipo_producto_endpoint(data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return crear_tipo_producto(data.get("nombre", ""))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.put("/tipos-producto/{tipo_id}")
async def actualizar_tipo_producto_endpoint(tipo_id: int, data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return actualizar_tipo_producto(tipo_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.delete("/tipos-producto/{tipo_id}")
async def eliminar_tipo_producto_endpoint(tipo_id: int, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return eliminar_tipo_producto(tipo_id)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/metodos-pago")
async def listar_metodos_pago_endpoint(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return listar_metodos_pago()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/metodos-pago", status_code=201)
async def crear_metodo_pago_endpoint(data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return crear_metodo_pago(data.get("nombre", ""))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.put("/metodos-pago/{metodo_id}")
async def actualizar_metodo_pago_endpoint(metodo_id: int, data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return actualizar_metodo_pago(metodo_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.delete("/metodos-pago/{metodo_id}")
async def eliminar_metodo_pago_endpoint(metodo_id: int, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return eliminar_metodo_pago(metodo_id)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/correo")
async def obtener_correo_endpoint(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return obtener_configuracion_correo()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.put("/correo")
async def actualizar_correo_endpoint(data: dict, usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    try:
        return actualizar_configuracion_correo(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
