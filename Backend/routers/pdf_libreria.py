"""
Módulo de generación de PDF para comprobantes de librería.
Genera comprobantes de venta con detalle de productos y resumen financiero.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import pytz

ZONA_GT = pytz.timezone("America/Guatemala")

# Colores institucionales
COLOR_PRIMARIO    = HexColor('#755b00')
COLOR_DORADO      = HexColor('#C9A227')
COLOR_FONDO       = HexColor('#F7F3EC')
COLOR_ERROR       = HexColor('#ba1a1a')
COLOR_EXITO       = HexColor('#15803d')
COLOR_GRIS        = HexColor('#6b7280')
COLOR_BORDE       = HexColor('#d1c5af')
COLOR_TEXTO       = HexColor('#1c1c1a')


def formatear_moneda(valor: float) -> str:
    """Formatea un valor como moneda en Quetzales."""
    return f"Q{valor:,.2f}"


def formatear_fecha(fecha_iso: str) -> str:
    """Formatea una fecha ISO al formato DD/MM/YYYY HH:MM."""
    if not fecha_iso:
        return "—"
    try:
        if isinstance(fecha_iso, str):
            from dateutil import parser
            fecha = parser.parse(fecha_iso)
        else:
            fecha = fecha_iso
        fecha_gt = fecha.astimezone(ZONA_GT)
        return fecha_gt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(fecha_iso)[:16]


def generar_pdf_comprobante(datos: dict) -> bytes:
    """
    Genera un PDF de comprobante de venta.

    Args:
        datos: Diccionario con los datos de la transacción que incluye:
            - tipo_notificacion: 'venta_contado' o 'venta_credito'
            - venta: dict con datos de la venta
            - productos: list con detalle de productos
            - hermano: dict con datos del comprador

    Returns:
        bytes: Contenido del PDF generado
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    estilos = getSampleStyleSheet()

    # Estilos personalizados
    estilo_titulo = ParagraphStyle(
        'titulo',
        parent=estilos['Normal'],
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=COLOR_PRIMARIO,
        alignment=TA_CENTER,
        spaceAfter=2*mm
    )

    estilo_subtitulo = ParagraphStyle(
        'subtitulo',
        parent=estilos['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=COLOR_GRIS,
        alignment=TA_CENTER,
        spaceAfter=1*mm
    )

    estilo_seccion = ParagraphStyle(
        'seccion',
        parent=estilos['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        textColor=COLOR_GRIS,
        spaceBefore=4*mm,
        spaceAfter=2*mm
    )

    estilo_normal = ParagraphStyle(
        'normal_custom',
        parent=estilos['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=COLOR_TEXTO
    )

    estilo_bold = ParagraphStyle(
        'bold_custom',
        parent=estilos['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=COLOR_TEXTO
    )

    estilo_pie = ParagraphStyle(
        'pie',
        parent=estilos['Normal'],
        fontSize=7,
        fontName='Helvetica',
        textColor=COLOR_GRIS,
        alignment=TA_CENTER
    )

    tipo = datos.get("tipo_notificacion", "venta_contado")
    venta = datos.get("venta", {})
    productos = datos.get("productos", [])
    hermano = datos.get("hermano", {})
    motivo_cancelacion = datos.get("motivo_cancelacion")

    if tipo == "cancelacion":
        titulo_doc = "NOTIFICACION DE CANCELACION"
        color_tipo = COLOR_EXITO
    elif tipo == "venta_credito":
        titulo_doc = "NOTIFICACION DE CARGO A CREDITO"
        color_tipo = COLOR_ERROR
    else:
        titulo_doc = "COMPROBANTE DE COMPRA EN EFECTIVO"
        color_tipo = COLOR_PRIMARIO

    elementos = []

    # --- ENCABEZADO ---
    elementos.append(Paragraph("PALABRA MIEL MIXCO", estilo_titulo))
    elementos.append(Spacer(1, 3*mm))
    elementos.append(HRFlowable(width="100%", thickness=2, color=COLOR_DORADO))
    elementos.append(Spacer(1, 3*mm))

    estilo_tipo = ParagraphStyle(
        'tipo',
        parent=estilos['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=color_tipo,
        alignment=TA_CENTER,
        spaceAfter=3*mm
    )
    elementos.append(Paragraph(titulo_doc, estilo_tipo))

    # --- DATOS DE LA OPERACIÓN ---
    fecha_emision = datetime.now(ZONA_GT).strftime("%d/%m/%Y %H:%M")
    id_corto = str(venta.get("id", ""))[:8].upper()

    datos_op = [
        ["No. Operacion:", id_corto, "Fecha:", fecha_emision],
        ["Operador:", venta.get("operador", "—"), "Estado:", venta.get("estado_pago", "—").upper()],
    ]

    tabla_op = Table(datos_op, colWidths=[35*mm, 55*mm, 25*mm, 55*mm])
    tabla_op.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), COLOR_GRIS),
        ('TEXTCOLOR', (2, 0), (2, -1), COLOR_GRIS),
        ('TEXTCOLOR', (1, 0), (1, -1), COLOR_TEXTO),
        ('TEXTCOLOR', (3, 0), (3, -1), COLOR_TEXTO),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla_op)
    elementos.append(Spacer(1, 3*mm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))

    # --- DATOS DEL HERMANO ---
    elementos.append(Paragraph("DATOS DEL HERMANO", estilo_seccion))

    datos_hermano = [
        ["Nombre:", hermano.get("nombre_completo", "—")],
        ["CUI:", hermano.get("cui", "—")],
    ]
    if tipo == "cancelacion" and motivo_cancelacion:
        datos_hermano.append(["Motivo:", motivo_cancelacion])

    tabla_hermano = Table(datos_hermano, colWidths=[35*mm, 135*mm])
    tabla_hermano.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), COLOR_GRIS),
        ('TEXTCOLOR', (1, 0), (1, -1), COLOR_TEXTO),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla_hermano)
    elementos.append(Spacer(1, 2*mm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))

    # --- DETALLE DE PRODUCTOS ---
    if productos:
        elementos.append(Paragraph("DETALLE DE PRODUCTOS", estilo_seccion))

        encabezado_prod = [["Producto", "Tipo", "Cant.", "Precio Unit.", "Subtotal"]]
        filas_prod = []
        for p in productos:
            filas_prod.append([
                p.get("nombre", "—"),
                p.get("tipo_producto", "—"),
                str(p.get("cantidad", 0)),
                formatear_moneda(float(p.get("precio_unitario", 0))),
                formatear_moneda(float(p.get("subtotal", 0)))
            ])

        tabla_prod = Table(
            encabezado_prod + filas_prod,
            colWidths=[65*mm, 30*mm, 15*mm, 30*mm, 30*mm]
        )
        tabla_prod.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_FONDO),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_PRIMARIO),
            ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_TEXTO),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDE),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, COLOR_FONDO]),
        ]))
        elementos.append(tabla_prod)
        elementos.append(Spacer(1, 2*mm))

    # --- RESUMEN FINANCIERO ---
    elementos.append(Paragraph("RESUMEN FINANCIERO", estilo_seccion))

    total_venta   = float(venta.get("total_venta", 0))
    total_pagado  = float(venta.get("total_pagado", 0))

    if tipo == "cancelacion":
        datos_resumen = [
            ["Total de la Venta:", formatear_moneda(total_venta)],
            ["Total Pagado:",      formatear_moneda(total_pagado)],
            ["Estado:",            "CANCELADA — DEUDA LIBERADA"],
        ]
        color_saldo = COLOR_EXITO
    else:
        saldo = float(venta.get("saldo_pendiente", 0))
        datos_resumen = [
            ["Total de la Venta:", formatear_moneda(total_venta)],
            ["Total Pagado:",      formatear_moneda(total_pagado)],
            ["Saldo Pendiente:",   formatear_moneda(saldo)],
        ]
        color_saldo = COLOR_ERROR if saldo > 0 else COLOR_EXITO

    tabla_resumen = Table(datos_resumen, colWidths=[100*mm, 70*mm])
    tabla_resumen.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, 1), COLOR_TEXTO),
        ('TEXTCOLOR', (0, 2), (-1, 2), color_saldo),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, COLOR_BORDE),
        ('LINEABOVE', (0, 2), (-1, 2), 1, COLOR_DORADO),
    ]))
    elementos.append(tabla_resumen)

    # --- PIE DE PÁGINA ---
    elementos.append(Spacer(1, 6*mm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))
    elementos.append(Spacer(1, 2*mm))
    elementos.append(Paragraph(
        f"PM Mixco ERP v2.0.0  •  Emitido el {fecha_emision}  •  Documento generado automáticamente",
        estilo_pie
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.read()


def generar_pdf_pago_proveedor(datos: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle('titulo', parent=estilos['Normal'], fontSize=18,
        fontName='Helvetica-Bold', textColor=COLOR_PRIMARIO, alignment=TA_CENTER, spaceAfter=2*mm)
    estilo_sub = ParagraphStyle('subtitulo', parent=estilos['Normal'], fontSize=10,
        fontName='Helvetica', textColor=COLOR_GRIS, alignment=TA_CENTER, spaceAfter=1*mm)
    estilo_seccion = ParagraphStyle('seccion', parent=estilos['Normal'], fontSize=8,
        fontName='Helvetica-Bold', textColor=COLOR_GRIS, spaceBefore=4*mm, spaceAfter=2*mm)
    estilo_bold = ParagraphStyle('bold_custom', parent=estilos['Normal'], fontSize=9,
        fontName='Helvetica-Bold', textColor=COLOR_TEXTO)
    estilo_normal = ParagraphStyle('normal_custom', parent=estilos['Normal'], fontSize=9,
        fontName='Helvetica', textColor=COLOR_TEXTO)
    estilo_pie = ParagraphStyle('pie', parent=estilos['Normal'], fontSize=7,
        fontName='Helvetica', textColor=COLOR_GRIS, alignment=TA_CENTER)

    monto = datos.get("monto", 0)
    hermano = datos.get("hermano", {})
    compra_data = datos.get("compra", {})
    pago_data = datos.get("pago", {})
    fecha_emision = datetime.now(ZONA_GT).strftime("%d/%m/%Y %H:%M")

    elementos = []
    elementos.append(Paragraph("PALABRA MIEL MIXCO", estilo_titulo))
    elementos.append(Spacer(1, 3*mm))
    elementos.append(HRFlowable(width="100%", thickness=2, color=COLOR_DORADO))
    elementos.append(Spacer(1, 3*mm))

    estilo_tipo = ParagraphStyle('tipo', parent=estilos['Normal'], fontSize=12,
        fontName='Helvetica-Bold', textColor=COLOR_PRIMARIO, alignment=TA_CENTER, spaceAfter=3*mm)
    elementos.append(Paragraph("RECIBO DE PAGO A PROVEEDOR", estilo_tipo))

    # Datos del pago
    elementos.append(Paragraph("DATOS DEL PAGO", estilo_seccion))
    id_corto = str(pago_data.get("id", ""))[:8].upper()
    datos_pago = [
        ["No. Recibo:", id_corto, "Fecha:", fecha_emision],
        ["Monto Pagado:", formatear_moneda(float(monto)), "Referencia:", pago_data.get("referencia", "—")],
    ]
    tabla_pago = Table(datos_pago, colWidths=[35*mm, 55*mm, 25*mm, 55*mm])
    tabla_pago.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), COLOR_GRIS),
        ('TEXTCOLOR', (2, 0), (2, -1), COLOR_GRIS),
        ('TEXTCOLOR', (1, 0), (1, -1), COLOR_TEXTO),
        ('TEXTCOLOR', (3, 0), (3, -1), COLOR_TEXTO),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla_pago)
    elementos.append(Spacer(1, 3*mm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))

    # Datos del hermano
    elementos.append(Paragraph("DATOS DEL HERMANO", estilo_seccion))
    datos_hermano = [
        ["Nombre:", hermano.get("nombre_completo", "—")],
        ["CUI:", hermano.get("cui", "—")],
    ]
    tabla_h = Table(datos_hermano, colWidths=[35*mm, 135*mm])
    tabla_h.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), COLOR_GRIS),
        ('TEXTCOLOR', (1, 0), (1, -1), COLOR_TEXTO),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla_h)
    elementos.append(Spacer(1, 2*mm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))

    # Datos de la compra
    elementos.append(Paragraph("DATOS DE LA COMPRA", estilo_seccion))
    datos_compra = [
        ["Proveedor:", compra_data.get("proveedor", "—")],
        ["Factura:", compra_data.get("factura", "—")],
        ["Total Compra:", formatear_moneda(float(compra_data.get("total_compra", 0)))],
    ]
    tabla_c = Table(datos_compra, colWidths=[40*mm, 130*mm])
    tabla_c.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), COLOR_GRIS),
        ('TEXTCOLOR', (1, 0), (1, -1), COLOR_TEXTO),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla_c)
    elementos.append(Spacer(1, 2*mm))

    # Resumen
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))
    elementos.append(Paragraph("RESUMEN", estilo_seccion))
    datos_resumen = [
        ["Monto Pagado:", formatear_moneda(float(monto))],
    ]
    tabla_r = Table(datos_resumen, colWidths=[100*mm, 70*mm])
    tabla_r.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), COLOR_TEXTO),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (0, 0), (-1, 0), 1, COLOR_DORADO),
    ]))
    elementos.append(tabla_r)

    elementos.append(Spacer(1, 6*mm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))
    elementos.append(Spacer(1, 2*mm))
    elementos.append(Paragraph(
        f"PM Mixco ERP v2.0.0  •  Emitido el {fecha_emision}  •  Documento generado automáticamente",
        estilo_pie))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.read()