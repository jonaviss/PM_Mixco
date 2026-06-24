from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Dict, Any
from config import JWT_SECRET, JWT_ALGORITHM

seguridad = HTTPBearer()


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(seguridad)
) -> Dict[str, Any]:
    token = credenciales.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        cui: str = payload.get("sub")

        if cui is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no contiene identificador de usuario.",
            )

        return payload

    except JWTError as e:
        mensaje = (
            "La sesión ha expirado. Inicie sesión nuevamente."
            if "expired" in str(e)
            else "Token de autenticación inválido."
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=mensaje,
        )


def requiere_admin(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)) -> Dict[str, Any]:
    if usuario_actual.get("rango") not in ["administrador", "super_admin"]:
        raise HTTPException(403, "Solo administradores pueden acceder a este módulo.")
    return usuario_actual


def requiere_encargado(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)) -> Dict[str, Any]:
    if usuario_actual.get("rango") not in ["encargado", "administrador", "super_admin"]:
        raise HTTPException(403, "No tiene permisos para esta acción.")
    return usuario_actual
