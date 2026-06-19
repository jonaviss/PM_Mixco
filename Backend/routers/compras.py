"""
Módulo de gestión de compras, proveedores y pagos con control de inventario FIFO.
Permite costo unitario 0 (para donaciones) y registra operador en pagos.
Soporte para compras al contado: se registran como pagadas automáticamente.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from database import supabase
from routers.dependencies import obtener_usuario_actual
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

router = APIRouter()

# ======================== SCHEMAS ========================
class ProveedorCreate(BaseModel):
    nombre: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    activo: Optional[bool] = None

class CompraDetalleCreate(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)
    costo_unitario: float = Field(..., ge=0)

class CompraCreate(BaseModel):
    proveedor_id: str
    fecha_compra: date
    fecha_factura: Optional[date] = None
    factura: Optional[str] = None
    observaciones: Optional[str] = None
    condicion_pago: str = "CREDITO"  # Nuevo campo: CONTADO o CREDITO
    detalles: List[CompraDetalleCreate]

class PagoProveedorCreate(BaseModel):
    compra_id: str
    monto: float = Field(..., gt=0)
    fecha_pago: date
    metodo_pago_id: int = 1
    referencia: Optional[str] = None

# ======================== FUNCIÓN AUXILIAR ========================
async def existe_proveedor_con_nombre(nombre: str, excluir_id: Optional[str] = None) -> bool:
    nombre_normalizado = nombre.strip().lower()
    query = supabase.table("proveedores").select("id, nombre").ilike("nombre", nombre_normalizado)
    if excluir_id:
        query = query.neq("id", excluir_id)
    res = query.execute()
    return len(res.data) > 0

# ======================== ENDPOINTS PROVEEDORES ========================
@router.get("/proveedores")
async def listar_proveedores(
    estado: str = "activos",
    usuario_actual: Dict = Depends(obtener_usuario_actual)
):
    try:
        query = supabase.table("proveedores").select("*")
        if estado == "activos":
            query = query.eq("activo", True)
        elif estado == "inactivos":
            query = query.eq("activo", False)
        res = query.order("nombre").execute()
        return res.data
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/proveedores", status_code=201)
async def crear_proveedor(payload: ProveedorCreate, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    if usuario_actual.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para crear proveedores.")
    if await existe_proveedor_con_nombre(payload.nombre):
        raise HTTPException(400, f"Ya existe un proveedor con el nombre '{payload.nombre}'. Use un nombre diferente.")
    try:
        data = payload.model_dump()
        data["activo"] = True
        res = supabase.table("proveedores").insert(data).execute()
        return {"mensaje": "Proveedor creado", "data": res.data[0]}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.put("/proveedores/{proveedor_id}")
async def actualizar_proveedor(proveedor_id: str, payload: ProveedorUpdate, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    if usuario_actual.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para modificar proveedores.")
    if payload.nombre:
        if await existe_proveedor_con_nombre(payload.nombre, excluir_id=proveedor_id):
            raise HTTPException(400, f"Ya existe otro proveedor con el nombre '{payload.nombre}'. Use un nombre diferente.")
    try:
        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(400, "No hay datos para actualizar")
        res = supabase.table("proveedores").update(update_data).eq("id", proveedor_id).execute()
        if not res.data:
            raise HTTPException(404, "Proveedor no encontrado")
        return {"mensaje": "Proveedor actualizado", "data": res.data[0]}
    except Exception as e:
        raise HTTPException(500, str(e))

# ======================== ENDPOINTS COMPRAS ========================
@router.post("", status_code=201)
async def registrar_compra(payload: CompraCreate, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    if usuario_actual.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para registrar compras.")
    try:
        total_compra = sum(d.cantidad * d.costo_unitario for d in payload.detalles)
        
        # Determinar si es contado o crédito
        es_contado = payload.condicion_pago == "CONTADO"
        
        # Datos de la compra
        compra_data = {
            "proveedor_id": payload.proveedor_id,
            "fecha_compra": payload.fecha_compra.isoformat(),
            "fecha_factura": payload.fecha_factura.isoformat() if payload.fecha_factura else None,
            "factura": payload.factura,
            "observaciones": payload.observaciones,
            "total_compra": total_compra,
            "total_pagado": total_compra if es_contado else 0,
            "estado": "pagado" if es_contado else "pendiente"
        }
        
        res_compra = supabase.table("compras").insert(compra_data).execute()
        compra_id = res_compra.data[0]["id"]

        # Insertar detalles y lotes
        for detalle in payload.detalles:
            detalle_data = {
                "compra_id": compra_id,
                "producto_id": detalle.producto_id,
                "cantidad": detalle.cantidad,
                "costo_unitario": detalle.costo_unitario,
                "subtotal": detalle.cantidad * detalle.costo_unitario
            }
            supabase.table("compras_detalle").insert(detalle_data).execute()

            lote_data = {
                "producto_id": detalle.producto_id,
                "compra_id": compra_id,
                "cantidad_inicial": detalle.cantidad,
                "cantidad_restante": detalle.cantidad,
                "costo_unitario": detalle.costo_unitario,
                "fecha_compra": payload.fecha_compra.isoformat()
            }
            supabase.table("lotes").insert(lote_data).execute()

            # Actualizar stock y costo promedio del producto
            res_prod = supabase.table("inventario_libreria").select("stock, costo_promedio").eq("id", detalle.producto_id).execute()
            if not res_prod.data:
                raise HTTPException(404, f"Producto {detalle.producto_id} no encontrado")
            prod = res_prod.data[0]
            stock_actual = prod["stock"] or 0
            costo_promedio_actual = prod["costo_promedio"] or 0
            nuevo_stock = stock_actual + detalle.cantidad
            nuevo_costo_promedio = (
                (stock_actual * costo_promedio_actual) + (detalle.cantidad * detalle.costo_unitario)
            ) / nuevo_stock if nuevo_stock > 0 else 0
            supabase.table("inventario_libreria").update({
                "stock": nuevo_stock,
                "costo_promedio": nuevo_costo_promedio
            }).eq("id", detalle.producto_id).execute()

        # Si es contado, registrar un pago automático
        if es_contado:
            pago_data = {
                "compra_id": compra_id,
                "monto": total_compra,
                "fecha_pago": payload.fecha_compra.isoformat(),
                "metodo_pago_id": 1,  # Efectivo (ajustar según tus métodos de pago)
                "referencia": "Pago al contado",
                "digitado_por": usuario_actual["sub"]
            }
            supabase.table("pagos_proveedores").insert(pago_data).execute()

        return {"mensaje": "Compra registrada", "compra_id": compra_id, "total": total_compra}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("")
async def listar_compras(proveedor_id: Optional[str] = None, estado: Optional[str] = None, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    try:
        query = supabase.table("compras").select("*, proveedores(nombre)")
        if proveedor_id:
            query = query.eq("proveedor_id", proveedor_id)
        if estado:
            query = query.eq("estado", estado)
        res = query.order("fecha_compra", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{compra_id}")
async def obtener_compra(compra_id: str, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    try:
        res_compra = supabase.table("compras").select("*, proveedores(nombre)").eq("id", compra_id).execute()
        if not res_compra.data:
            raise HTTPException(404, "Compra no encontrada")
        compra = res_compra.data[0]
        res_detalles = supabase.table("compras_detalle").select("*, inventario_libreria(nombre)").eq("compra_id", compra_id).execute()
        # Obtener pagos con operador
        res_pagos = supabase.table("pagos_proveedores").select("*, digitado_por").eq("compra_id", compra_id).execute()
        pagos = res_pagos.data or []
        # Obtener nombres de operadores
        cuis = list(set(p.get("digitado_por") for p in pagos if p.get("digitado_por")))
        nombres = {}
        if cuis:
            res_usuarios = supabase.table("usuarios").select("cui, nombre_completo").in_("cui", cuis).execute()
            nombres = {u["cui"]: u["nombre_completo"] for u in (res_usuarios.data or [])}
        pagos_con_nombre = []
        for p in pagos:
            pagos_con_nombre.append({
                "id": p["id"],
                "monto": p["monto"],
                "fecha_pago": p["fecha_pago"],
                "referencia": p.get("referencia"),
                "operador_cui": p.get("digitado_por"),
                "operador_nombre": nombres.get(p.get("digitado_por"), p.get("digitado_por") or "—")
            })
        return {"compra": compra, "detalles": res_detalles.data, "pagos": pagos_con_nombre}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/lotes/pendientes")
async def lotes_pendientes(producto_id: Optional[str] = None, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    try:
        query = supabase.table("lotes").select("*, compras(proveedor_id, proveedores(nombre)), inventario_libreria(nombre, tipo_producto)").gt("cantidad_restante", 0)
        if producto_id:
            query = query.eq("producto_id", producto_id)
        res = query.order("fecha_compra", desc=False).execute()
        return res.data
    except Exception as e:
        raise HTTPException(500, str(e))

# ======================== ENDPOINTS PAGOS ========================
@router.post("/pagos_proveedores", status_code=201)
async def registrar_pago_proveedor(payload: PagoProveedorCreate, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    if usuario_actual.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para registrar pagos.")
    try:
        res_compra = supabase.table("compras").select("total_compra, total_pagado, estado").eq("id", payload.compra_id).execute()
        if not res_compra.data:
            raise HTTPException(404, "Compra no encontrada")
        compra = res_compra.data[0]
        saldo = compra["total_compra"] - compra["total_pagado"]
        if payload.monto > saldo:
            raise HTTPException(400, f"El monto no puede exceder el saldo pendiente (Q{saldo:.2f})")
        pago_data = {
            "compra_id": payload.compra_id,
            "monto": payload.monto,
            "fecha_pago": payload.fecha_pago.isoformat(),
            "metodo_pago_id": payload.metodo_pago_id,
            "referencia": payload.referencia,
            "digitado_por": usuario_actual["sub"]   # Guardar CUI del operador
        }
        res_pago = supabase.table("pagos_proveedores").insert(pago_data).execute()
        pago_id = res_pago.data[0]["id"]
        nuevo_pagado = compra["total_pagado"] + payload.monto
        nuevo_estado = "pagado" if nuevo_pagado >= compra["total_compra"] else "parcial"
        supabase.table("compras").update({"total_pagado": nuevo_pagado, "estado": nuevo_estado}).eq("id", payload.compra_id).execute()
        return {"mensaje": "Pago registrado", "pago_id": pago_id, "saldo_restante": compra["total_compra"] - nuevo_pagado}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/pagos_proveedores")
async def listar_pagos_proveedores(compra_id: Optional[str] = None, usuario_actual: Dict = Depends(obtener_usuario_actual)):
    try:
        query = supabase.table("pagos_proveedores").select("*, compras(proveedor_id, proveedores(nombre))")
        if compra_id:
            query = query.eq("compra_id", compra_id)
        res = query.order("fecha_pago", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(500, str(e))