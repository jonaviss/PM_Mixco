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
    """
    Schema para distribuir un abono entre múltiples ventas pendientes de un cliente.
    """
    comprador_cui: str = Field(..., description="CUI del cliente con deuda")
    monto_abonado: float = Field(..., gt=0, description="Monto total a distribuir")
    metodo_pago_id: int = Field(default=1, description="ID del método de pago")