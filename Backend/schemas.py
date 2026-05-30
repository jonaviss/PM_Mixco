"""
Módulo de Esquemas de Datos (DTC) - PM Mixco ERP.
Define los contratos de datos (data contracts) para toda la API, 
asegurando la validación estricta de las entradas y salidas del sistema.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Modelos de Autenticación ---

class LoginRequest(BaseModel):
    """Solicitud de inicio de sesión soportando múltiples idiomas de entrada."""
    cui: str = Field(..., description="CUI de 13 dígitos del usuario")
    contrasena: Optional[str] = Field(None, description="Contraseña en español")
    password: Optional[str] = Field(None, description="Contraseña en inglés")

class TokenResponse(BaseModel):
    """Estructura de respuesta tras una autenticación exitosa."""
    access_token: str
    token_type: str = "bearer"
    nombre_completo: str
    rango: str
    modulos: List[str]

class TokenData(BaseModel):
    """Información contenida dentro del token JWT."""
    cui: str
    rango: str
    modulos: List[str]

# --- Modelos de Librería ---

class ProductoLibreriaCreate(BaseModel):
    sku: str = Field(..., description="Código único, ej. PLAY-M-001")
    tipo_producto: str = Field(..., description="Playera, CD, Libro, Biblia, Poster")
    nombre: str = Field(..., description="Nombre comercial del producto")
    descripcion: Optional[str] = None
    precio: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    estado: bool = True
    atributos_especificos: Dict[str, Any] = Field(
        default_factory=dict, 
        description="JSON con atributos: talla, color, editorial, etc."
    )

class VentaLibreriaCreate(BaseModel):
    producto_id: str = Field(..., description="UUID del producto")
    comprador_cui: Optional[str] = None
    cantidad: int = Field(..., gt=0)

# --- Modelos de Cafetería ---

class ConsumoCafeteriaCreate(BaseModel):
    """Esquema para registrar el consumo de alimentos en cafetería."""
    usuario_cui: str
    total_cobrado: float = Field(..., gt=0)
    productos: List[Dict[str, Any]] = Field(
        ..., 
        description="Lista de productos: [{'producto_id': str, 'cantidad': int}]"
    )

# --- Modelos de Finanzas ---

class OfrendaCreate(BaseModel):
    """Esquema para el registro contable de diezmos y ofrendas."""
    miembro_cui: Optional[str] = None
    tipo: str = Field(..., pattern="^(diezmo|ofrendas_generales|ofrendas_pro_templo)$")
    monto: float = Field(..., gt=0)