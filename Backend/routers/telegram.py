import os
import asyncio
import logging
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from repositories.usuario_repository import find_user_by_cui, update_usuario

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

router = APIRouter(prefix="/telegram", tags=["Telegram"])

_ultimo_update_id = 0


async def enviar_telegram(chat_id: str, mensaje: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        return False
    if not chat_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(f"{TELEGRAM_API}/sendMessage", json={
                "chat_id": chat_id,
                "text": mensaje,
                "parse_mode": "HTML"
            })
            return res.status_code == 200
    except Exception as e:
        logger.error(f"Falla al enviar Telegram: {e}")
        return False


async def enviar_pdf_telegram(chat_id: str, mensaje: str, pdf_bytes: bytes, pdf_filename: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                f"{TELEGRAM_API}/sendDocument",
                data={"chat_id": chat_id, "caption": mensaje, "parse_mode": "HTML"},
                files={"document": (pdf_filename, pdf_bytes, "application/pdf")}
            )
            return res.status_code == 200
    except Exception as e:
        logger.error(f"Falla al enviar PDF por Telegram: {e}")
        return False


async def _procesar_mensaje(chat_id: str, text: str):
    if text == "/start":
        await enviar_telegram(chat_id,
            "Hola. Enviá tu CUI (13 dígitos) para vincular tu cuenta de PM Mixco.")
        return

    if text.isdigit() and len(text) == 13:
        user = find_user_by_cui(text)
        if not user:
            await enviar_telegram(chat_id,
                "No encontré ningún usuario con ese CUI. Verificá e intentá de nuevo.")
            return

        update_usuario(text, {"telegram_chat_id": chat_id})
        nombre = user.get("nombre_completo", "usuario")
        await enviar_telegram(chat_id,
            f"Vinculado correctamente con {nombre}.\n"
            "A partir de ahora recibirás notificaciones de tus compras aquí.")
        logger.info(f"Telegram chat_id {chat_id} vinculado a CUI {text} ({nombre})")
        return

    await enviar_telegram(chat_id,
        "Enviá /start para comenzar.")


async def polling_loop():
    global _ultimo_update_id
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN no configurado. Polling desactivado.")
        return

    logger.info("Iniciando polling de Telegram...")
    while True:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                params = {"limit": 10, "timeout": 5}
                if _ultimo_update_id:
                    params["offset"] = _ultimo_update_id + 1
                res = await client.get(f"{TELEGRAM_API}/getUpdates", params=params)
                if res.status_code != 200:
                    await asyncio.sleep(3)
                    continue
                data = res.json()
                for update in data.get("result", []):
                    _ultimo_update_id = update["update_id"]
                    msg = update.get("message", {})
                    chat = msg.get("chat", {})
                    chat_id = str(chat.get("id", ""))
                    text = (msg.get("text") or "").strip()
                    if chat_id and text:
                        await _procesar_mensaje(chat_id, text)
        except asyncio.CancelledError:
            logger.info("Polling de Telegram detenido.")
            break
        except Exception as e:
            logger.error(f"Error en polling Telegram: {e}")
        await asyncio.sleep(3)


class TelegramUpdate(BaseModel):
    update_id: int
    message: dict = None


@router.get("/ultimo-chat-id")
async def ultimo_chat_id():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(f"{TELEGRAM_API}/getUpdates", params={"limit": 1})
            if res.status_code != 200:
                return {"error": "No se pudo conectar con Telegram"}
            data = res.json()
            if not data.get("ok") or not data.get("result"):
                return {"chat_id": None, "mensaje": "No hay mensajes recientes."}
            update = data["result"][-1]
            msg = update.get("message", {})
            chat = msg.get("chat", {})
            return {
                "chat_id": str(chat.get("id", "")),
                "nombre": chat.get("first_name", ""),
                "username": chat.get("username", ""),
                "ultimo_mensaje": msg.get("text", "")
            }
    except Exception as e:
        return {"error": str(e)}


@router.post("/webhook")
async def webhook_telegram(update: TelegramUpdate):
    msg = update.message or {}
    chat = msg.get("chat", {})
    chat_id = str(chat.get("id", ""))
    text = (msg.get("text") or "").strip()
    if chat_id and text:
        await _procesar_mensaje(chat_id, text)
    return {"ok": True}
