"""
Módulo de dependencias centralizadas.
Provee la función de validación JWT que se inyecta en cada endpoint protegido.
"""

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Dict, Any

# Esquema de seguridad Bearer para Swagger y validación automática
seguridad = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "PALABRA_MIEL_MIXCO_SECRET_KEY_2026")
ALGORITHM = "HS256"


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(seguridad)
) -> Dict[str, Any]:
    """
    Valida el token JWT del header Authorization y retorna el payload decodificado.

    Args:
        credenciales: Token Bearer extraído automáticamente del header

    Returns:
        dict: Payload del token con sub, rango y modulos

    Raises:
        HTTPException 401: Si el token es inválido, expirado o mal formado
    """
    token = credenciales.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        cui: str = payload.get("sub")

        if cui is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no contiene identificador de usuario."
            )

        return payload

    except JWTError as e:
        mensaje = "La sesión ha expirado. Inicie sesión nuevamente." \
            if "expired" in str(e) else "Token de autenticación inválido."

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=mensaje
        )