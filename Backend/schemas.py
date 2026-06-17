"""
Módulo de Esquemas de Datos (DTC)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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