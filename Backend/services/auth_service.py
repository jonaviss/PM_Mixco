import secrets
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt
from database import verificar_contrasena, supabase
from config import JWT_SECRET, JWT_ALGORITHM, TOKEN_EXPIRE_MINUTES
from repositories.auth_repository import find_active_user_by_cui, find_accesos_by_cui
from repositories.usuario_repository import create_usuario, find_user_by_cui, update_usuario


def _hash_password(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


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


def registrar_usuario(cui: str, nombre_completo: str, contrasena: str, correo: Optional[str] = None) -> Dict[str, Any]:
    existing = find_user_by_cui(cui)
    if existing:
        raise ValueError("El CUI ya está registrado.")

    usuario_data = {
        "cui": cui,
        "nombre_completo": nombre_completo,
        "contrasena_hash": _hash_password(contrasena),
        "activo": True,
        "correo": correo or "",
    }
    nuevo = create_usuario(usuario_data)

    return nuevo


def generar_token_recuperacion(cui: str) -> Optional[str]:
    user = find_user_by_cui(cui)
    if not user or not user.get("correo"):
        return None

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

    supabase.table("reset_tokens").insert({
        "cui": cui,
        "token_hash": token_hash,
        "expires_at": expires_at,
        "used": False
    }).execute()

    return token


def restablecer_contrasena(token: str, contrasena_nueva: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    res = supabase.table("reset_tokens") \
        .select("*") \
        .eq("token_hash", token_hash) \
        .eq("used", False) \
        .execute()
    if not res.data:
        raise ValueError("Token inválido o expirado.")

    record = res.data[0]
    expires = datetime.fromisoformat(record["expires_at"])
    if datetime.utcnow() > expires:
        raise ValueError("Token expirado.")

    update_usuario(record["cui"], {"contrasena_hash": _hash_password(contrasena_nueva)})
    supabase.table("reset_tokens").update({"used": True}).eq("id", record["id"]).execute()
