from datetime import datetime, timedelta
from typing import Dict, Any
from jose import jwt
from database import verificar_contrasena
from config import JWT_SECRET, JWT_ALGORITHM, TOKEN_EXPIRE_MINUTES
from repositories.auth_repository import find_active_user_by_cui, find_accesos_by_cui


def authenticate_user(cui: str, contrasena: str) -> Dict[str, Any]:
    usuario = find_active_user_by_cui(cui)
    if not usuario:
        raise ValueError("CUI o contraseña incorrectos.")

    if not verificar_contrasena(contrasena, usuario["contrasena_hash"]):
        raise ValueError("CUI o contraseña incorrectos.")

    accesos = find_accesos_by_cui(cui)

    if accesos:
        rango = accesos[0]["rangos"]["nombre"]
        modulos = [
            a["modulos"]["nombre"]
            for a in accesos
            if a.get("modulos")
        ]
    else:
        rango = "cliente"
        modulos = []

    return {
        "cui": usuario["cui"],
        "nombre_completo": usuario["nombre_completo"],
        "rango": rango,
        "modulos": modulos,
    }


def create_token(user_data: Dict[str, Any]) -> str:
    payload = {
        "sub": user_data["cui"],
        "nombre": user_data["nombre_completo"],
        "rango": user_data["rango"],
        "modulos": user_data["modulos"],
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
