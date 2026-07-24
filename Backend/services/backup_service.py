import os
import json
import io
import zipfile
import logging
from datetime import datetime
from database import supabase

logger = logging.getLogger(__name__)

TABLAS = [
    "usuarios", "accesos_usuarios", "rangos", "modulos",
    "inventario_libreria", "libreria_ventas", "libreria_ventas_detalle", "libreria_pagos",
    "compras", "compras_detalle", "pagos_proveedores", "proveedores", "lotes",
    "gastos", "tipos_producto", "cat_metodos_pago", "categorias_gasto",
    "configuracion_correo", "reset_tokens", "verificacion_tokens",
]

def generar_backup() -> bytes:
    zip_buffer = io.BytesIO()
    resumen = {}
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for tabla in TABLAS:
            try:
                res = supabase.table(tabla).select("*").execute()
                data = res.data or []
                content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
                zf.writestr(f"{tabla}.json", content)
                resumen[tabla] = f"{len(data)} registros"
            except Exception as e:
                resumen[tabla] = f"ERROR: {e}"
        zf.writestr("resumen.json", json.dumps(resumen, indent=2, ensure_ascii=False))
    return zip_buffer.getvalue(), resumen


def enviar_backup_correo():
    try:
        from services.notificacion_service import _enviar_gmail_smtp
        zip_bytes, resumen = generar_backup()
        fecha = datetime.now().strftime("%Y-%m-%d")
        total = sum(v for v in resumen.values() if isinstance(v, int)) or 0
        lines = "\n".join(f"  {k}: {v}" for k, v in resumen.items())
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:24px;border:1px solid #e8e4d9;border-radius:12px;">
            <h2 style="color:#755b00;text-align:center;">Backup PM Mixco</h2>
            <p style="color:#4d4635;font-size:14px;">Backup diario — {fecha}</p>
            <pre style="font-size:12px;background:#f5f5f5;padding:12px;border-radius:8px;">{lines}</pre>
            <p style="font-size:11px;color:#7a7565;margin-top:12px;">Backup automático del sistema.</p>
        </div>
        """
        destinatario = os.getenv("GMAIL_SMTP_USER", "libreriapmmixco@gmail.com")
        import base64
        encoded = base64.b64encode(zip_bytes).decode()
        payload = {
            "personalizations": [{"to": [{"email": destinatario}]}],
            "from": {"email": destinatario, "name": "PM Mixco Backup"},
            "subject": f"Backup PM Mixco — {fecha}",
            "content": [{"type": "text/html", "value": html}],
            "attachments": [{
                "content": encoded,
                "type": "application/zip",
                "filename": f"backup_{fecha}.zip",
                "disposition": "attachment"
            }]
        }
        api_key = os.getenv("SENDGRID_API_KEY")
        if api_key:
            import httpx
            resp = httpx.post("https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload, timeout=60)
            if resp.status_code in (200, 201, 202):
                logger.info(f"Backup enviado por SendGrid a {destinatario}")
            else:
                logger.error(f"SendGrid falló: {resp.status_code}")
        else:
            _enviar_gmail_smtp(destinatario,
                f"Backup PM Mixco — {fecha}",
                html + f'<p style="font-size:12px;">Adjunto: backup_{fecha}.zip</p>')
            logger.info(f"Backup enviado por Gmail SMTP a {destinatario}")
    except Exception as e:
        logger.error(f"Error enviando backup: {e}")
