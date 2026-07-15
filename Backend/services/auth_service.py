import secrets
import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
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

    if not usuario.get("verificado", False):
        raise ValueError("Debes verificar tu correo electrónico antes de iniciar sesión.")

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
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def registrar_usuario(cui: str, nombre_completo: str, contrasena: str, correo: Optional[str] = None) -> Dict[str, Any]:
    existing = find_user_by_cui(cui)
    if existing:
        raise ValueError("El CUI ya está registrado.")
    if not correo or not correo.strip():
        raise ValueError("El correo electrónico es obligatorio para registrarse.")

    usuario_data = {
        "cui": cui,
        "nombre_completo": nombre_completo,
        "contrasena_hash": _hash_password(contrasena),
        "activo": True,
        "verificado": False,
        "correo": correo.strip(),
    }
    nuevo = create_usuario(usuario_data)

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    supabase.table("verificacion_tokens").insert({
        "cui": cui,
        "token_hash": token_hash,
        "expires_at": expires_at,
        "used": False
    }).execute()

    from services.notificacion_service import enviar_correo_verificacion
    enviar_correo_verificacion(cui, nombre_completo, correo.strip(), token)

    return nuevo


def verificar_correo(token: str) -> str:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    res = supabase.table("verificacion_tokens") \
        .select("*, usuarios!inner(cui, nombre_completo, correo, verificado)") \
        .eq("token_hash", token_hash) \
        .eq("used", False) \
        .execute()
    if not res.data:
        raise ValueError("El enlace de verificación es inválido o ya fue usado.")
    record = res.data[0]
    expires = datetime.fromisoformat(record["expires_at"])
    if datetime.now(timezone.utc) > expires:
        raise ValueError("El enlace de verificación ha expirado. Solicita uno nuevo.")
    update_usuario(record["cui"], {"verificado": True})
    supabase.table("verificacion_tokens").update({"used": True}).eq("id", record["id"]).execute()
    return record["usuarios"]["nombre_completo"]


def generar_token_recuperacion(cui: str) -> Optional[str]:
    user = find_user_by_cui(cui)
    if not user or not user.get("correo"):
        return None

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

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
    if datetime.now(timezone.utc) > expires:
        raise ValueError("Token expirado.")

    update_usuario(record["cui"], {"contrasena_hash": _hash_password(contrasena_nueva)})
    supabase.table("reset_tokens").update({"used": True}).eq("id", record["id"]).execute()
