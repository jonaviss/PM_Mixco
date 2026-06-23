import bcrypt
from typing import List, Dict, Any, Optional
from schemas import UsuarioCreate, UsuarioUpdate
from repositories.usuario_repository import (
    find_user_by_cui,
    find_accesos_by_cui,
    find_user_hash,
    list_all_usuarios,
    create_usuario,
    update_usuario,
    delete_accesos_by_cui,
    create_acceso,
    list_roles,
    list_modulos,
)
from config import DEFAULT_PASSWORD


def hash_password(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def get_all_usuarios() -> List[Dict[str, Any]]:
    usuarios = list_all_usuarios()
    for u in usuarios:
        accesos = find_accesos_by_cui(u["cui"])
        if accesos:
            u["rango_id"] = accesos[0]["rango_id"]
            u["rango_nombre"] = accesos[0]["rangos"]["nombre"]
            u["modulos"] = [
                {"id": a["modulo_id"], "nombre": a["modulos"]["nombre"]}
                for a in accesos if a.get("modulos")
            ]
        else:
            u["rango_id"] = None
            u["rango_nombre"] = "cliente"
            u["modulos"] = []
    return usuarios


def create_new_usuario(payload: UsuarioCreate) -> Dict[str, Any]:
    existing = find_user_by_cui(payload.cui)
    if existing:
        raise ValueError(f"El CUI {payload.cui} ya está registrado.")

    usuario_data = {
        "cui": payload.cui,
        "nombre_completo": payload.nombre_completo,
        "contrasena_hash": hash_password(payload.contrasena),
        "activo": True,
        "correo": payload.correo or None,
    }
    nuevo = create_usuario(usuario_data)

    for modulo_id in payload.modulos_ids:
        create_acceso(payload.cui, payload.rango_id, modulo_id)

    return nuevo


def update_existing_usuario(cui: str, payload: UsuarioUpdate) -> None:
    existing = find_user_by_cui(cui)
    if not existing:
        raise ValueError("Usuario no encontrado.")

    update_data = payload.model_dump(exclude_none=True)
    if "contrasena" in update_data:
        update_data["contrasena_hash"] = hash_password(update_data.pop("contrasena"))

    if not update_data:
        raise ValueError("No se enviaron campos para actualizar.")

    update_usuario(cui, update_data)


def toggle_usuario_activo(cui: str) -> bool:
    user = find_user_by_cui(cui)
    if not user:
        raise ValueError("Usuario no encontrado.")

    nuevo_estado = not user["activo"]
    update_usuario(cui, {"activo": nuevo_estado})
    return nuevo_estado


def reset_usuario_password(cui: str) -> None:
    user = find_user_by_cui(cui)
    if not user:
        raise ValueError("Usuario no encontrado.")
    update_usuario(cui, {"contrasena_hash": hash_password(DEFAULT_PASSWORD)})


def update_usuario_accesos(cui: str, rango_id: int, modulos_ids: List[int]) -> None:
    user = find_user_by_cui(cui)
    if not user:
        raise ValueError("Usuario no encontrado.")

    delete_accesos_by_cui(cui)
    for modulo_id in modulos_ids:
        create_acceso(cui, rango_id, modulo_id)


def update_profile(cui: str, nombre_completo: Optional[str], correo: Optional[str]) -> None:
    update_data = {}
    if nombre_completo:
        update_data["nombre_completo"] = nombre_completo
    if correo:
        update_data["correo"] = correo
    if not update_data:
        raise ValueError("No se enviaron campos para actualizar.")
    update_usuario(cui, update_data)


def change_password(cui: str, contrasena_actual: str, contrasena_nueva: str) -> None:
    stored_hash = find_user_hash(cui)
    if not stored_hash:
        raise ValueError("Usuario no encontrado.")

    if not bcrypt.checkpw(contrasena_actual.encode("utf-8"), stored_hash.encode("utf-8")):
        raise ValueError("La contraseña actual no es correcta.")

    update_usuario(cui, {"contrasena_hash": hash_password(contrasena_nueva)})
