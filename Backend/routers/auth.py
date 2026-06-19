"""
Módulo de autenticación.
Maneja el login, generación y validación de tokens JWT.
"""

from fastapi import APIRouter, HTTPException, status
from database import supabase, verificar_contrasena
from schemas import LoginRequest, TokenResponse
from datetime import datetime, timedelta
import os
from jose import jwt
from typing import Dict, Any

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET no configurado en variables de entorno.")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 480


def generar_token_jwt(data: Dict[str, Any]) -> str:
    """
    Genera un token JWT firmado con los datos del usuario.

    Args:
        data: Payload a incluir en el token (sub, rango, modulos)

    Returns:
        str: Token JWT firmado
    """
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest):
    """
    Autentica al usuario con CUI y contraseña.

    Args:
        payload: CUI y contraseña del usuario

    Returns:
        TokenResponse: Token JWT y datos básicos del usuario

    Raises:
        HTTPException 401: Si las credenciales son incorrectas o el usuario está inactivo
        HTTPException 500: Si ocurre un error al consultar la base de datos
    """
    try:
        # 1. Buscar usuario activo por CUI
        res_usuario = supabase.table("usuarios") \
            .select("cui, nombre_completo, contrasena_hash, activo") \
            .eq("cui", payload.cui) \
            .eq("activo", True) \
            .execute()

        if not res_usuario.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="CUI o contraseña incorrectos."
            )

        usuario = res_usuario.data[0]

        # 2. Verificar contraseña
        if not verificar_contrasena(payload.contrasena, usuario["contrasena_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="CUI o contraseña incorrectos."
            )

        # 3. Obtener accesos reales del usuario (módulos y rango)
        res_accesos = supabase.table("accesos_usuarios") \
            .select("rango_id, rangos(nombre), modulo_id, modulos(nombre)") \
            .eq("usuario_cui", usuario["cui"]) \
            .execute()

        # Extraer rango y módulos desde los accesos registrados en BD
        rango = "analista"
        modulos = []

        if res_accesos.data:
            # Tomar el rango del primer acceso (un usuario tiene un rango global)
            rango = res_accesos.data[0]["rangos"]["nombre"]
            modulos = [
                acceso["modulos"]["nombre"]
                for acceso in res_accesos.data
                if acceso.get("modulos")
            ]

        # 4. Generar token con datos reales
        token_payload = {
            "sub": usuario["cui"],
            "nombre": usuario["nombre_completo"],
            "rango": rango,
            "modulos": modulos
        }
        jwt_token = generar_token_jwt(token_payload)

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "nombre_completo": usuario["nombre_completo"],
            "rango": rango,
            "modulos": modulos
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar el inicio de sesión."
        )