import os
import base64
import asyncio
import httpx
import logging
from routers.pdf_libreria import generar_pdf_comprobante, generar_pdf_pago_proveedor
from repositories.common_repository import get_configuracion_correo

logger = logging.getLogger(__name__)


def _enviar_sendgrid(destinatario: str, asunto: str, html: str, pdf_bytes: bytes, pdf_filename: str, api_key: str):
    if not api_key:
        logger.warning("SENDGRID_API_KEY no configurada. Correo abortado.")
        return
    content = [{"type": "text/html", "value": html}]
    attachments = []
    if pdf_bytes:
        encoded = base64.b64encode(pdf_bytes).decode()
        attachments.append({
            "content": encoded,
            "type": "application/pdf",
            "filename": pdf_filename,
            "disposition": "attachment"
        })
    payload = {
        "personalizations": [{"to": [{"email": destinatario}]}],
        "from": {"email": "libreriapmmixco@gmail.com", "name": "Libreria PM Mixco"},
        "subject": asunto,
        "content": content,
    }
    if attachments:
        payload["attachments"] = attachments
    try:
        resp = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        if resp.status_code in (200, 201, 202):
            logger.info(f"Correo enviado a {destinatario}")
        else:
            logger.error(f"SendGrid falló ({resp.status_code}): {resp.text}")
    except Exception as e:
        logger.error(f"Falla al enviar correo via SendGrid: {e}")


async def despachar_correo_libreria(datos: dict):
    tipo = datos.get("tipo_notificacion", "venta_contado")
    if tipo == "cancelacion":
        titulo_recibo = "Notificacion de Cancelacion y Liberacion de Deuda"
        motivo = datos.get("motivo_cancelacion", "")
    elif tipo == "venta_credito":
        titulo_recibo = "Notificacion de Cargo a Credito"
    elif tipo == "venta_contado":
        titulo_recibo = "Comprobante de Compra en Efectivo"
    elif tipo == "pago_proveedor":
        titulo_recibo = "Recibo de Pago a Proveedor"
    else:
        titulo_recibo = "Comprobante de Abono Recibido"

    monto = datos.get("monto", 0)
    hermano = datos.get("hermano", {})
    nombre_hermano = hermano.get("nombre_completo", "Hermano")
    pdf_bytes = None
    pdf_filename = f"comprobante_{datos.get('id_transaccion', 'tx')[:8]}.pdf"

    try:
        if tipo == "pago_proveedor":
            pdf_bytes = generar_pdf_pago_proveedor(datos)
        else:
            pdf_bytes = generar_pdf_comprobante(datos)
        pdf_filename = f"recibo_pago_{datos.get('pago', {}).get('id', 'tx')[:8]}.pdf"
    except Exception as e:
        logger.error(f"Falla al generar PDF: {e}")

    if tipo == "pago_proveedor":
        compra_data = datos.get("compra", {})
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 24px;
                    border: 1px solid #e8e4d9; border-radius: 12px; background-color: #fafaf8;">
            <h2 style="color: #755b00; text-align: center; margin-bottom: 4px;">PALABRA MIEL MIXCO</h2>
            <p style="text-align: center; color: #7a7565; font-size: 13px; margin-top: 0;">{titulo_recibo}</p>
            <hr style="border: none; border-top: 2px solid #C9A227; margin: 16px 0;">
            <p style="font-size: 14px; color: #1c1c1a;">Estimado(a) <strong>{nombre_hermano}</strong>,</p>
            <p style="font-size: 14px; color: #4d4635; margin-top: 8px;">
                Se realizó un pago a <strong>{compra_data.get("proveedor", "Proveedor")}</strong>
                por un monto de <strong style="color: #15803d;">Q{monto:.2f}</strong>.
            </p>
            <p style="font-size: 14px; color: #4d4635; margin-top: 8px;">
                Factura: {compra_data.get("factura", "—")}<br>
                Referencia: {datos.get("pago", {}).get("referencia", "—")}
            </p>
            <p style="font-size: 14px; color: #4d4635; margin-top: 8px;">
                Adjunto encontrará el recibo de pago en formato PDF.
            </p>
            <div style="background: #f0edea; border-radius: 8px; padding: 12px; margin-top: 16px;
                        text-align: center; border: 1px solid #d1c5af;">
                <p style="font-size: 11px; color: #7a7565; margin: 0;">
                    PM Mixco ERP v2.0.0 — Módulo Librería — Documento generado automáticamente
                </p>
            </div>
        </div>
        """
    elif tipo == "cancelacion":
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 24px;
                    border: 1px solid #e8e4d9; border-radius: 12px; background-color: #fafaf8;">
            <h2 style="color: #755b00; text-align: center; margin-bottom: 4px;">PALABRA MIEL MIXCO</h2>
            <p style="text-align: center; color: #7a7565; font-size: 13px; margin-top: 0;">{titulo_recibo}</p>
            <hr style="border: none; border-top: 2px solid #C9A227; margin: 16px 0;">
            <p style="font-size: 14px; color: #1c1c1a;">Estimado(a) <strong>{nombre_hermano}</strong>,</p>
            <p style="font-size: 14px; color: #4d4635; margin-top: 8px;">
                Le informamos que la venta por un monto de
                <strong style="color: #15803d;">Q{monto:.2f}</strong> ha sido <strong>cancelada</strong>
                y su deuda ha sido <strong>liberada</strong>.
            </p>
            {f'<p style="font-size: 14px; color: #ba1a1a; margin-top: 8px;">Motivo: {motivo}</p>' if motivo else ''}
            <p style="font-size: 14px; color: #4d4635; margin-top: 8px;">
                Adjunto encontrará el comprobante de cancelación en formato PDF.
            </p>
            <div style="background: #f0edea; border-radius: 8px; padding: 12px; margin-top: 16px;
                        text-align: center; border: 1px solid #d1c5af;">
                <p style="font-size: 11px; color: #7a7565; margin: 0;">
                    PM Mixco ERP v2.0.0 — Módulo Librería — Documento generado automáticamente
                </p>
            </div>
        </div>
        """
    else:
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

    correo_destino = datos.get("hermano", {}).get("correo") or "libreriapmmixco@gmail.com"
    asunto = f"{titulo_recibo} — Q{monto:.2f} — PM Mixco"

    api_key = os.getenv("SENDGRID_API_KEY")
    cfg = get_configuracion_correo()
    if cfg:
        api_key = cfg.get("sendgrid_api_key") or api_key

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _enviar_sendgrid, correo_destino, asunto, html_content, pdf_bytes, pdf_filename, api_key)

    # También enviar Telegram si el usuario tiene chat_id
    try:
        from services.telegram_service import enviar_telegram, enviar_pdf_telegram
        chat_id = datos.get("hermano", {}).get("telegram_chat_id")
        if chat_id:
            import locale
            try:
                locale.setlocale(locale.LC_ALL, "es_GT.UTF-8")
            except:
                pass
            monto_str = f"Q{monto:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
            if tipo == "pago_proveedor":
                compra_data = datos.get("compra", {})
                texto = f"<b>{titulo_recibo}</b>\n\nHola {nombre_hermano},\nSe realizó un pago a <b>{compra_data.get('proveedor', 'Proveedor')}</b> por <b>{monto_str}</b>.\nFactura: {compra_data.get('factura', '—')}"
            else:
                texto = f"<b>{titulo_recibo}</b>\n\nHola {nombre_hermano},\nSe registró una transacción por <b>{monto_str}</b> en PM Mixco.\n\n— Módulo Librería"
            if pdf_bytes:
                await enviar_pdf_telegram(chat_id, texto, pdf_bytes, pdf_filename)
            else:
                await enviar_telegram(chat_id, texto)
    except Exception as e:
        logger.warning(f"Telegram opcional falló: {e}")
