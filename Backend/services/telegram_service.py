import os
import logging
import httpx

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def enviar_telegram(chat_id: str, mensaje: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN no configurado.")
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
            if res.status_code != 200:
                logger.error(f"Telegram error {res.status_code}: {res.text}")
                return False
            return True
    except Exception as e:
        logger.error(f"Falla al enviar Telegram: {e}")
        return False


async def enviar_pdf_telegram(chat_id: str, mensaje: str, pdf_bytes: bytes, pdf_filename: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        return False
    if not chat_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                f"{TELEGRAM_API}/sendDocument",
                data={"chat_id": chat_id, "caption": mensaje, "parse_mode": "HTML"},
                files={"document": (pdf_filename, pdf_bytes, "application/pdf")}
            )
            if res.status_code != 200:
                logger.error(f"Telegram PDF error {res.status_code}: {res.text}")
                return False
            return True
    except Exception as e:
        logger.error(f"Falla al enviar PDF por Telegram: {e}")
        return False
