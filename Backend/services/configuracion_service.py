from typing import Dict, Any
from fastapi import HTTPException
from repositories import configuracion_repository as repo


def listar_tipos_producto() -> list:
    return repo.list_all("tipos_producto")


def crear_tipo_producto(nombre: str) -> Dict[str, Any]:
    if not nombre:
        raise HTTPException(400, "El nombre es obligatorio")
    return repo.insert("tipos_producto", {"nombre": nombre})


def actualizar_tipo_producto(tipo_id: int, data: dict) -> Dict[str, Any]:
    result = repo.update("tipos_producto", "id", tipo_id, data)
    if not result:
        raise HTTPException(404, "Tipo de producto no encontrado")
    return result


def eliminar_tipo_producto(tipo_id: int) -> dict:
    if not repo.delete("tipos_producto", "id", tipo_id):
        raise HTTPException(404, "Tipo de producto no encontrado")
    return {"mensaje": "Tipo de producto eliminado"}


def listar_metodos_pago() -> list:
    return repo.list_all("cat_metodos_pago")


def crear_metodo_pago(nombre: str) -> Dict[str, Any]:
    if not nombre:
        raise HTTPException(400, "El nombre es obligatorio")
    return repo.insert("cat_metodos_pago", {"nombre": nombre})


def actualizar_metodo_pago(metodo_id: int, data: dict) -> Dict[str, Any]:
    result = repo.update("cat_metodos_pago", "id", metodo_id, data)
    if not result:
        raise HTTPException(404, "Método de pago no encontrado")
    return result


def eliminar_metodo_pago(metodo_id: int) -> dict:
    if not repo.delete("cat_metodos_pago", "id", metodo_id):
        raise HTTPException(404, "Método de pago no encontrado")
    return {"mensaje": "Método de pago eliminado"}


def obtener_configuracion_correo() -> dict:
    config = repo.get_configuracion_correo_first() or {}
    if config.get("sendgrid_api_key"):
        config["sendgrid_api_key"] = "********"
    return config


def actualizar_configuracion_correo(data: dict) -> dict:
    api_key = data.get("sendgrid_api_key", "").strip()
    if not api_key:
        raise HTTPException(400, "La API Key de SendGrid es obligatoria")
    repo.upsert_configuracion_correo(api_key)
    return {"mensaje": "Configuración de correo actualizada"}
