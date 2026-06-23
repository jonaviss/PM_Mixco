import os
import asyncio
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from routers.pdf_libreria import generar_pdf_comprobante
from repositories.common_repository import get_configuracion_correo

logger = logging.getLogger(__name__)


def _enviar_smtp(destinatario: str, asunto: str, html: str, pdf_bytes: bytes, pdf_filename: str, gmail_user: str, gmail_pass: str):
    if not gmail_user or not gmail_pass:
        logger.warning("Credenciales de correo no configuradas. Correo abortado.")
        return
    msg = MIMEMultipart("mixed")
    msg["From"] = f"Libreria PM Mixco <{gmail_user}>"
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.attach(MIMEText(html, "html"))
    if pdf_bytes:
        part = MIMEBase("application", "pdf")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=pdf_filename)
        msg.attach(part)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, destinatario, msg.as_string())
        logger.info(f"Correo enviado a {destinatario}")
    except Exception as e:
        logger.error(f"Falla al enviar correo via Gmail SMTP: {e}")


async def despachar_correo_libreria(datos: dict):
    tipo = datos.get("tipo_notificacion", "venta_contado")
    if tipo == "venta_credito":
        titulo_recibo = "Notificacion de Cargo a Credito"
    elif tipo == "venta_contado":
        titulo_recibo = "Comprobante de Compra en Efectivo"
    else:
        titulo_recibo = "Comprobante de Abono Recibido"

    monto = datos.get("monto", 0)
    hermano = datos.get("hermano", {})
    nombre_hermano = hermano.get("nombre_completo", "Hermano")
    pdf_bytes = None
    pdf_filename = f"comprobante_{datos.get('id_transaccion', 'tx')[:8]}.pdf"

    try:
        pdf_bytes = generar_pdf_comprobante(datos)
    except Exception as e:
        logger.error(f"Falla al generar PDF: {e}")

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 24px;
                border: 1px solid #e8e4d9; border-radius: 12px; background-color: #fafaf8;">
        <h2 style="color: #755b00; text-align: center; margin-bottom: 4px;">PALABRA MIEL MIXCO</h2>
        <p style="text-align: center; color: #7a7565; font-size: 13px; margin-top: 0;">{titulo_recibo}</p>
        <hr style="border: none; border-top: 2px solid #C9A227; margin: 16px 0;">
        <p style="font-size: 14px; color: #1c1c1a;">Estimado(a) <strong>{nombre_hermano}</strong>,</p>
        <p style="font-size: 14px; color: #4d4635; margin-top: 8px;">
            Se ha registrado una transacción en el módulo de Librería por un monto de
            <strong style="color: #755b00;">Q{monto:.2f}</strong>.
        </p>
        <p style="font-size: 14px; color: #4d4635; margin-top: 8px;">
            Adjunto encontrará el comprobante en formato PDF con el detalle completo
            de la transacción y el estado de su cuenta.
        </p>
        <div style="background: #f0edea; border-radius: 8px; padding: 12px; margin-top: 16px;
                    text-align: center; border: 1px solid #d1c5af;">
            <p style="font-size: 11px; color: #7a7565; margin: 0;">
                PM Mixco ERP v2.0.0 — Módulo Librería — Documento generado automáticamente
            </p>
        </div>
    </div>
    """

    correo_destino = datos.get("hermano", {}).get("correo") or os.getenv("GMAIL_SMTP_USER")
    asunto = f"{titulo_recibo} — Q{monto:.2f} — PM Mixco"

    gmail_user = os.getenv("GMAIL_SMTP_USER")
    gmail_pass = os.getenv("GMAIL_SMTP_PASSWORD")
    cfg = get_configuracion_correo()
    if cfg:
        gmail_user = cfg.get("smtp_user") or gmail_user
        gmail_pass = cfg.get("smtp_password") or gmail_pass

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _enviar_smtp, correo_destino, asunto, html_content, pdf_bytes, pdf_filename, gmail_user, gmail_pass)
