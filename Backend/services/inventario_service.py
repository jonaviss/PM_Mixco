from typing import List, Dict, Any
from fastapi import HTTPException
from schemas import ProductoLibreriaCreate, ProductoLibreriaUpdate
from repositories.inventario_repository import (
    list_productos, find_producto_by_id, create_producto, update_producto,
    get_producto_stock, update_producto_stock, get_producto_costo_promedio
)
from repositories.lote_repository import create_lote_auto
from repositories.common_repository import find_usuarios_by_cuis


def get_all_productos(incluir_inactivos: bool = False) -> List[Dict[str, Any]]:
    productos = list_productos(incluir_inactivos)
    cuis = list(set(p.get("creado_por") for p in productos if p.get("creado_por")))
    nombres = find_usuarios_by_cuis(cuis) if cuis else {}
    for p in productos:
        p["creado_por_nombre"] = nombres.get(p.get("creado_por"), p.get("creado_por") or "—")
    return productos


def register_producto(payload: ProductoLibreriaCreate, creado_por: str) -> Dict[str, Any]:
    data = payload.model_dump(exclude_none=True)
    data["creado_por"] = creado_por
    nuevo = create_producto(data)
    producto_id = nuevo["id"]
    stock = data.get("stock", 0)
    costo_promedio = data.get("costo_promedio")
    if stock > 0 and costo_promedio is not None:
        create_lote_auto(producto_id, stock, costo_promedio)
    return nuevo


def update_producto_info(producto_id: str, payload: ProductoLibreriaUpdate) -> Dict[str, Any]:
    existente = find_producto_by_id(producto_id)
    if not existente:
        raise HTTPException(404, "Producto no encontrado")
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(400, "No se enviaron campos para actualizar.")
    result = update_producto(producto_id, update_data)
    return result


def toggle_producto_estado(producto_id: str) -> tuple:
    existente = find_producto_by_id(producto_id)
    if not existente:
        raise HTTPException(404, "Producto no encontrado")
    nuevo_estado = not existente["estado"]
    update_producto(producto_id, {"estado": nuevo_estado})
    mensaje = "Producto reactivado" if nuevo_estado else "Producto desactivado"
    return mensaje, nuevo_estado


def verificar_stock(producto_id: str, cantidad: int) -> Dict[str, Any]:
    from repositories.inventario_repository import find_producto_basico
    prod = find_producto_basico(producto_id)
    if not prod:
        raise HTTPException(404, f"Producto {producto_id} no encontrado")
    if prod["stock"] < cantidad:
        raise HTTPException(400, f"Stock insuficiente para '{prod['nombre']}'. Disponible: {prod['stock']}")
    return prod
