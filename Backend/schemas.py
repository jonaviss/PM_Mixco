"""
Módulo de Esquemas de Datos (DTC)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

class LoginRequest(BaseModel):
    cui: str = Field(..., description="CUI de 13 dígitos")
    contrasena: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nombre_completo: str
    rango: str
    modulos: List[str]

class ProductoLibreriaCreate(BaseModel):
    tipo_producto: str
    nombre: str
    descripcion: Optional[str] = None
    precio: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    estado: bool = True
    atributos_especificos: Dict[str, Any] = Field(default_factory=dict)
    proveedor_id: Optional[str] = None
    costo_promedio: Optional[float] = Field(None, ge=0, description="Costo promedio de referencia")

class ProductoLibreriaUpdate(BaseModel):
    tipo_producto: Optional[str] = Field(None, description="Categoría del producto")
    nombre: Optional[str] = Field(None, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, description="Descripción opcional")
    precio: Optional[float] = Field(None, gt=0, description="Precio de venta")
    stock: Optional[int] = Field(None, ge=0, description="Cantidad en inventario")
    estado: Optional[bool] = Field(None, description="Activo o inactivo")
    atributos_especificos: Optional[Dict[str, Any]] = Field(None, description="Atributos adicionales")
    proveedor_id: Optional[str] = None

class VentaLibreriaCreate(BaseModel):
    producto_id: str
    comprador_cui: str
    cantidad: int = Field(..., gt=0)
    tipo_pago: str = Field(..., description="'contado' o 'credito'")

class PagoLibreriaCreate(BaseModel):
    venta_id: str
    monto_abonado: float = Field(..., gt=0)
    metodo_pago_id: int = 1
    digitado_por: str

class AbonoDistribuidoCreate(BaseModel):
    comprador_cui: str = Field(..., description="CUI del cliente con deuda")
    monto_abonado: float = Field(..., gt=0, description="Monto total a distribuir")
    metodo_pago_id: int = Field(default=1, description="ID del método de pago")
    # ======================== ESQUEMAS PARA VENTAS MÚLTIPLES ========================
class VentaProductoItem(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0, description="Cantidad del producto")

class VentaMultipleCreate(BaseModel):
    comprador_cui: str
    tipo_pago: str = Field(..., description="'contado' o 'credito'")
    productos: List[VentaProductoItem] = Field(..., min_items=1, description="Lista de productos a vender")

# ======================== USUARIOS ========================
class UsuarioCreate(BaseModel):
    cui: str = Field(..., min_length=13, max_length=13)
    nombre_completo: str
    contrasena: str = Field(..., min_length=6)
    correo: Optional[str] = None
    rango_id: int
    modulos_ids: List[int] = Field(default_factory=list)

class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None
    activo: Optional[bool] = None
    contrasena: Optional[str] = None

class UsuarioAccesosUpdate(BaseModel):
    rango_id: int
    modulos_ids: List[int] = Field(default_factory=list)

class PerfilUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None

class PasswordChange(BaseModel):
    contrasena_actual: str
    contrasena_nueva: str = Field(..., min_length=6)


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
    condicion_pago: str = "CREDITO"
    detalles: List[CompraDetalleCreate]


class PagoProveedorCreate(BaseModel):
    compra_id: str
    monto: float = Field(..., gt=0)
    fecha_pago: date
    metodo_pago_id: int = 1
    referencia: Optional[str] = None


# ======================== CONFIGURACIÓN ========================
class TipoProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)


class TipoProductoUpdate(BaseModel):
    nombre: str = Field(..., min_length=1)


class MetodoPagoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)


class MetodoPagoUpdate(BaseModel):
    nombre: str = Field(..., min_length=1)


class ConfiguracionCorreoUpdate(BaseModel):
    servidor_smtp: Optional[str] = None
    puerto: Optional[int] = None
    usuario: Optional[str] = None
    contrasena: Optional[str] = None
    correo_origen: Optional[str] = None


# ======================== GASTOS ========================
class GastoCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    monto: float = Field(..., gt=0)
    categoria: str = "Otro"
    fecha_gasto: str = ""


class GastoUpdate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    monto: float = Field(..., gt=0)
    categoria: str = "Otro"
    fecha_gasto: str = ""