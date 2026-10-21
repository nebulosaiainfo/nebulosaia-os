# -*- coding: utf-8 -*-
"""
Generador de Facturas en PDF estilizadas - NEXO RETAIL.
Diseño estrictamente profesional en Blanco, Negro y Acentos en Rojo:
- El color ROJO (#DC2626) se utiliza EXCLUSIVAMENTE para:
  1. El número de factura o comprobante (N° F-XXXXX).
  2. Ofertas especiales o badges promocionales.
  3. El descuento aplicado (- CRC X,XXX.XX).
- El resto del documento se estructura en tipografía limpia, blancos y escala de grises/negros.
- Moneda en formato 'CRC' (sin caracteres unicode incompatibles).
"""

import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

PDF_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "01_Core_Facturacion" / "facturas_pdf"
PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Paleta Estricta: Blanco, Negro y Rojo de Acento Exclusivo
COLOR_NEGRO = colors.HexColor("#111827")      # Grafito oscuro / Negro
COLOR_GRIS_OSCURO = colors.HexColor("#374151") # Gris texto secundario
COLOR_GRIS_MEDIO = colors.HexColor("#6B7280")  # Gris detalles / labels
COLOR_BORDE = colors.HexColor("#D1D5DB")       # Borde elegante
COLOR_FONDO_TABLA = colors.HexColor("#F9FAFB") # Fondo encabezados
COLOR_ROJO = colors.HexColor("#DC2626")        # Rojo exclusivo para N° y Descuentos

def generar_pdf_factura(datos_factura: dict) -> str:
    """
    Genera un PDF profesional monocromático con acentos en rojo exclusivamente para número y descuentos.
    Retorna la ruta absoluta del archivo generado.
    """
    consecutivo = datos_factura.get("consecutivo", "F-00001")
    fecha_str = datos_factura.get("fecha", datetime.now().strftime("%d/%m/%Y %H:%M"))
    nombre_archivo = f"Factura_{consecutivo}.pdf"
    ruta_pdf = str(PDF_OUTPUT_DIR / nombre_archivo)
    
    doc = SimpleDocTemplate(
        ruta_pdf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Estilo base
    style_normal = styles['Normal']
    style_normal.textColor = COLOR_NEGRO
    
    story = []
    
    # 1. ENCABEZADO: TIENDA & CONSECUTIVO EN ROJO
    tienda = datos_factura.get("tienda", {})
    es_proforma = "PROFORMA" in consecutivo or "PRF" in consecutivo or "COTIZACIÓN" in str(datos_factura.get("metodo_pago", "")).upper()
    titulo_doc = "COTIZACIÓN / PROFORMA" if es_proforma else "COMPROBANTE ELECTRÓNICO"
    
    header_data = [
        [
            Paragraph(
                f"<b><font size='16' color='#111827'>{tienda.get('nombre', 'NEXO RETAIL BOUTIQUE')}</font></b><br/>"
                f"<font size='9' color='#4B5563'>Cédula Jurídica: {tienda.get('cedula', '3-101-948271')}<br/>"
                f"Teléfono: {tienda.get('telefono', '+506 8888-8888')}<br/>"
                f"Dirección: {tienda.get('direccion', 'San José, Costa Rica')}<br/>"
                f"Actividad Económica: {tienda.get('actividad', '477101 - Venta al por menor de prendas')}</font>",
                style_normal
            ),
            Paragraph(
                f"<b><font size='12' color='#111827'>{titulo_doc}</font></b><br/>"
                f"<b><font size='14' color='#DC2626'>N° {consecutivo}</font></b><br/>"
                f"<font size='8' color='#4B5563'>Fecha: {fecha_str}<br/>"
                f"Vendedor: {datos_factura.get('vendedor_nombre', 'Vendedor de Turno')}</font>",
                style_normal
            )
        ]
    ]
    t_header = Table(header_data, colWidths=[330, 210])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 14))
    
    # 2. DATOS DEL CLIENTE Y MÉTODO DE PAGO
    cliente = datos_factura.get("cliente", {})
    cli_info = [
        [
            Paragraph("<b><font size='9' color='#111827'>DATOS DEL RECEPTOR / CLIENTE</font></b>", style_normal),
            Paragraph(f"<b><font size='9' color='#111827'>FORMA DE PAGO: {datos_factura.get('metodo_pago', 'SINPE_MOVIL')}</font></b>", style_normal)
        ],
        [
            Paragraph(
                f"<font size='9' color='#1F2937'><b>Nombre:</b> {cliente.get('nombre', 'Cliente General')}<br/>"
                f"<b>Cédula:</b> {cliente.get('cedula', 'N/A')} &nbsp;|&nbsp; <b>Tel:</b> {cliente.get('telefono', 'N/A')}<br/>"
                f"<b>Correo:</b> {cliente.get('correo', 'N/A')}<br/>"
                f"<b>Dirección:</b> {cliente.get('direccion', 'N/A')}</font>",
                style_normal
            ),
            Paragraph(
                f"<font size='9' color='#1F2937'><b>Comprobante / Ref:</b><br/>"
                f"<b>{datos_factura.get('comprobante_banco', 'N/A')}</b><br/>"
                f"<font size='8' color='#6B7280'>Moneda Oficial: CRC (Colones Costarricenses)</font></font>",
                style_normal
            )
        ]
    ]
    t_cli = Table(cli_info, colWidths=[330, 210])
    t_cli.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FAFB")),
        ('BOX', (0,0), (-1,-1), 1, COLOR_BORDE),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t_cli)
    story.append(Spacer(1, 14))
    
    # 3. TABLA DE ARTÍCULOS / PRODUCTOS / SERVICIOS
    lineas = datos_factura.get("lineas", [])
    table_rows = [
        [
            Paragraph("<b><font size='8' color='#111827'>Código / SKU</font></b>", style_normal),
            Paragraph("<b><font size='8' color='#111827'>Descripción (Producto / Servicio / Detalle)</font></b>", style_normal),
            Paragraph("<b><font size='8' color='#111827'>Cant.</font></b>", style_normal),
            Paragraph("<b><font size='8' color='#111827'>Precio (IVA Inc.)</font></b>", style_normal),
            Paragraph("<b><font size='8' color='#111827'>Subtotal</font></b>", style_normal)
        ]
    ]
    
    for item in lineas:
        talla_val = item.get('talla', '')
        color_val = item.get('color', '')
        detalle_parts = []
        if talla_val and talla_val not in ['-', 'N/A', 'General']:
            detalle_parts.append(f"Variante: {talla_val}")
        if color_val and color_val not in ['-', 'N/A', 'Único']:
            detalle_parts.append(f"Detalle: {color_val}")
        detalle_str = f"<br/><font size='7.5' color='#6B7280'>{' | '.join(detalle_parts)}</font>" if detalle_parts else ""

        table_rows.append([
            Paragraph(f"<font size='8' color='#4B5563'><b>{item.get('sku', 'N/A')}</b></font>", style_normal),
            Paragraph(f"<b><font size='8' color='#111827'>{item.get('nombre', 'Producto / Servicio')}</font></b>{detalle_str}", style_normal),
            Paragraph(f"<font size='8'>{item.get('cantidad', 1)}</font>", style_normal),
            Paragraph(f"<font size='8'>CRC {item.get('precio_unitario', 0):,.2f}</font>", style_normal),
            Paragraph(f"<font size='8'><b>CRC {item.get('subtotal', 0):,.2f}</b></font>", style_normal)
        ])
        
    t_items = Table(table_rows, colWidths=[90, 240, 45, 85, 80])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F3F4F6")),
        ('LINEBELOW', (0,0), (-1,0), 1.5, COLOR_NEGRO),
        ('ALIGN', (2,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, COLOR_BORDE),
        ('BOX', (0,0), (-1,-1), 1, COLOR_NEGRO),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 14))
    
    # 4. TOTALES CON DESCUENTO EN ROJO
    descuento = float(datos_factura.get("descuento", 0.0))
    subtotal = float(datos_factura.get("subtotal", 0.0))
    iva = float(datos_factura.get("iva", 0.0))
    total = float(datos_factura.get("total", 0.0))
    
    tot_data = [
        [
            Paragraph("<font size='8.5' color='#4B5563'>Subtotal (Base Imponible):</font>", style_normal),
            Paragraph(f"<font size='8.5' color='#111827'>CRC {subtotal:,.2f}</font>", style_normal)
        ]
    ]
    
    if descuento > 0:
        tot_data.append([
            Paragraph("<b><font size='8.5' color='#DC2626'>Descuento / Oferta:</font></b>", style_normal),
            Paragraph(f"<b><font size='8.5' color='#DC2626'>- CRC {descuento:,.2f}</font></b>", style_normal)
        ])
        
    tot_data.append([
        Paragraph("<font size='8.5' color='#4B5563'>I.V.A. (13% Incluido):</font>", style_normal),
        Paragraph(f"<font size='8.5' color='#111827'>CRC {iva:,.2f}</font>", style_normal)
    ])
    tot_data.append([
        Paragraph("<b><font size='10' color='#111827'>TOTAL A PAGAR:</font></b>", style_normal),
        Paragraph(f"<b><font size='10' color='#111827'>CRC {total:,.2f}</font></b>", style_normal)
    ])
    
    t_tot = Table(tot_data, colWidths=[140, 100])
    t_tot.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#F3F4F6")),
        ('BOX', (0,-1), (-1,-1), 1.2, COLOR_NEGRO),
        ('LINEABOVE', (0,-1), (-1,-1), 1, COLOR_NEGRO),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    
    wrapper_tot = Table([["", t_tot]], colWidths=[300, 240])
    story.append(wrapper_tot)
    story.append(Spacer(1, 16))
    
    # 5. PIE DE PÁGINA / POLÍTICAS COMERCIALES
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_BORDE))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<font size='7' color='#6B7280'>Comprobante emitido bajo normativa administrativa y contable vigente. "
        "Para reclamos, cambios o garantías es indispensable presentar este comprobante en un plazo no mayor a 8 días hábiles. "
        "Los artículos o productos en oferta y liquidación especial se entregan en su condición final. Gracias por su preferencia.</font>",
        style_normal
    ))
    
    doc.build(story)
    return ruta_pdf

def enviar_factura_correo(destinatario: str, ruta_pdf: str, datos_tienda: dict, datos_factura: dict) -> bool:
    """Envía la factura generada por correo SMTP."""
    remitente = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    servidor_smtp = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    puerto = int(os.getenv("SMTP_PORT", "587"))
    
    if not remitente or not password or not destinatario or "@" not in destinatario:
        print(f"[CORREO SIMULADO] Se guardó PDF en {ruta_pdf} para {destinatario}.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{datos_tienda.get('nombre', 'NEXO RETAIL')} <{remitente}>"
        msg['To'] = destinatario
        msg['Subject'] = f"Comprobante de Compra #{datos_factura.get('consecutivo', '')} - {datos_tienda.get('nombre', '')}"
        
        cuerpo = f"""
        Hola {datos_factura.get('cliente', {}).get('nombre', 'Estimado cliente')},
        
        Adjunto encontrarás tu comprobante #{datos_factura.get('consecutivo', '')} por un monto de CRC {datos_factura.get('total', 0):,.2f}.
        Método de pago: {datos_factura.get('metodo_pago', 'SINPE')} (Ref: {datos_factura.get('comprobante_banco', '')}).
        
        ¡Muchas gracias por su preferencia!
        {datos_tienda.get('nombre', '')}
        """
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        with open(ruta_pdf, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{Path(ruta_pdf).name}"')
            msg.attach(part)
            
        with smtplib.SMTP(servidor_smtp, puerto) as server:
            server.starttls()
            server.login(remitente, password)
            server.send_message(msg)
            
        return True
    except Exception as e:
        print(f"[ERROR SMTP] No se pudo enviar el correo: {e}")
        return False


def generar_pdf_apartado(datos_apartado: dict) -> str:
    """
    Genera un comprobante oficial de Apartado y Control de Cuotas con el mismo
    diseño y formato profesional en Blanco, Negro y Acentos en Rojo que las facturas y proformas.
    Retorna la ruta absoluta del archivo generado.
    """
    consecutivo = datos_apartado.get("consecutivo", "APT-00001")
    fecha_str = datos_apartado.get("fecha", datetime.now().strftime("%d/%m/%Y %H:%M"))
    fecha_limite_str = datos_apartado.get("fecha_limite", "30 días a partir de la emisión")
    nombre_archivo = f"Apartado_{consecutivo}.pdf"
    
    apartados_dir = PDF_OUTPUT_DIR.parent / "apartados_pdf"
    apartados_dir.mkdir(parents=True, exist_ok=True)
    ruta_pdf = str(apartados_dir / nombre_archivo)
    
    doc = SimpleDocTemplate(
        ruta_pdf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    style_normal = styles['Normal']
    style_normal.textColor = COLOR_NEGRO
    
    story = []
    
    # 1. ENCABEZADO: TIENDA & CONSECUTIVO EN ROJO
    tienda = datos_apartado.get("tienda", {})
    header_data = [
        [
            Paragraph(
                f"<b><font size='16' color='#111827'>{tienda.get('nombre', 'NEBULOSA | RETAIL')}</font></b><br/>"
                f"<font size='9' color='#4B5563'>Cédula Jurídica: {tienda.get('cedula', '3-101-948271')}<br/>"
                f"Teléfono: {tienda.get('telefono', '+506 8888-8888')}<br/>"
                f"Dirección: {tienda.get('direccion', 'San José, Costa Rica')}<br/>"
                f"Actividad Económica: {tienda.get('actividad', '477101 - Venta al por menor de prendas')}</font>",
                style_normal
            ),
            Paragraph(
                f"<b><font size='12' color='#111827'>CONTROL DE APARTADO Y CUOTAS</font></b><br/>"
                f"<b><font size='14' color='#DC2626'>N° {consecutivo}</font></b><br/>"
                f"<font size='8' color='#4B5563'>Fecha Emisión: {fecha_str}<br/>"
                f"<b>Fecha Límite Retiro: {fecha_limite_str}</b><br/>"
                f"Vendedor: {datos_apartado.get('vendedor_nombre', 'Vendedor de Turno')}</font>",
                style_normal
            )
        ]
    ]
    t_header = Table(header_data, colWidths=[320, 220])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 14))
    
    # 2. DATOS DEL CLIENTE Y ESTADO DEL PLAN
    cliente = datos_apartado.get("cliente", {})
    estado_str = str(datos_apartado.get("estado", "PENDIENTE")).upper()
    is_liquidado = estado_str == "LIQUIDADO"
    badge_estado = (
        "<font color='#059669'><b>100% LIQUIDADO (ENTREGAR PRENDAS)</b></font>"
        if is_liquidado
        else "<font color='#D97706'><b>ACTIVO (PENDIENTE DE SALDO)</b></font>"
    )
    
    cli_info = [
        [
            Paragraph("<b><font size='9' color='#111827'>DATOS DEL TITULAR / CLIENTE</font></b>", style_normal),
            Paragraph("<b><font size='9' color='#111827'>ESTADO DEL PLAN DE APARTADO</font></b>", style_normal)
        ],
        [
            Paragraph(
                f"<font size='9' color='#1F2937'><b>Nombre:</b> {cliente.get('nombre', 'Cliente General')}<br/>"
                f"<b>Cédula:</b> {cliente.get('cedula', 'N/A')} &nbsp;|&nbsp; <b>Tel:</b> {cliente.get('telefono', 'N/A')}<br/>"
                f"<b>Notas / Observaciones:</b> {datos_apartado.get('notas', 'Sin observaciones adicionales')}</font>",
                style_normal
            ),
            Paragraph(
                f"<font size='9' color='#1F2937'><b>Condición:</b> {badge_estado}<br/>"
                f"<b>Plazo Otorgado:</b> 30 días hábiles<br/>"
                f"<font size='8' color='#6B7280'>Moneda Oficial: CRC (Colones Costarricenses)</font></font>",
                style_normal
            )
        ]
    ]
    t_cli = Table(cli_info, colWidths=[320, 220])
    t_cli.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9FAFB")),
        ('BOX', (0,0), (-1,-1), 1, COLOR_BORDE),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t_cli)
    story.append(Spacer(1, 14))
    
    # 3. TABLA DE PRENDAS RESERVADAS
    lineas = datos_apartado.get("lineas", [])
    table_rows = [
        [
            Paragraph("<b><font size='8' color='#111827'>Código / SKU</font></b>", style_normal),
            Paragraph("<b><font size='8' color='#111827'>Prenda Reservada en Bodega</font></b>", style_normal),
            Paragraph("<b><font size='8' color='#111827'>Cant.</font></b>", style_normal),
            Paragraph("<b><font size='8' color='#111827'>Precio Unit.</font></b>", style_normal),
            Paragraph("<b><font size='8' color='#111827'>Subtotal</font></b>", style_normal)
        ]
    ]
    
    for item in lineas:
        talla_val = item.get('talla', '')
        color_val = item.get('color', '')
        detalles = []
        if talla_val and talla_val not in ['-', 'N/A', 'General']:
            detalles.append(f"Talla: {talla_val}")
        if color_val and color_val not in ['-', 'N/A', 'Único']:
            detalles.append(f"Color: {color_val}")
        det_str = f"<br/><font size='7.5' color='#6B7280'>{' | '.join(detalles)}</font>" if detalles else ""
        
        cant = item.get('cantidad', 1)
        pu = float(item.get('precio', item.get('precio_unitario', 0)))
        sub = cant * pu
        table_rows.append([
            Paragraph(f"<font size='8' color='#4B5563'><b>{item.get('sku', 'N/A')}</b></font>", style_normal),
            Paragraph(f"<b><font size='8' color='#111827'>{item.get('nombre', 'Artículo')}</font></b>{det_str}", style_normal),
            Paragraph(f"<font size='8'>{cant}</font>", style_normal),
            Paragraph(f"<font size='8'>CRC {pu:,.2f}</font>", style_normal),
            Paragraph(f"<font size='8'><b>CRC {sub:,.2f}</b></font>", style_normal)
        ])
        
    t_items = Table(table_rows, colWidths=[85, 235, 45, 90, 85])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F3F4F6")),
        ('LINEBELOW', (0,0), (-1,0), 1.5, COLOR_NEGRO),
        ('ALIGN', (2,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, COLOR_BORDE),
        ('BOX', (0,0), (-1,-1), 1, COLOR_NEGRO),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 14))
    
    # 4. RESUMEN FINANCIERO: TOTAL, ABONOS Y SALDO PENDIENTE
    total = float(datos_apartado.get("total", 0.0))
    saldo_pendiente = float(datos_apartado.get("saldo_pendiente", 0.0))
    total_abonado = max(0.0, total - saldo_pendiente)
    
    tot_data = [
        [
            Paragraph("<font size='8.5' color='#4B5563'>Total Prendas Apartadas:</font>", style_normal),
            Paragraph(f"<font size='8.5' color='#111827'>CRC {total:,.2f}</font>", style_normal)
        ],
        [
            Paragraph("<b><font size='8.5' color='#059669'>Total Abonado a la Fecha:</font></b>", style_normal),
            Paragraph(f"<b><font size='8.5' color='#059669'>CRC {total_abonado:,.2f}</font></b>", style_normal)
        ]
    ]
    
    if saldo_pendiente > 0:
        tot_data.append([
            Paragraph("<b><font size='10' color='#DC2626'>SALDO PENDIENTE POR PAGAR:</font></b>", style_normal),
            Paragraph(f"<b><font size='10' color='#DC2626'>CRC {saldo_pendiente:,.2f}</font></b>", style_normal)
        ])
    else:
        tot_data.append([
            Paragraph("<b><font size='10' color='#059669'>ESTADO FINAL:</font></b>", style_normal),
            Paragraph("<b><font size='10' color='#059669'>100% CANCELADO</font></b>", style_normal)
        ])
        
    t_tot = Table(tot_data, colWidths=[160, 110])
    t_tot.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#F3F4F6")),
        ('BOX', (0,-1), (-1,-1), 1.2, COLOR_NEGRO),
        ('LINEABOVE', (0,-1), (-1,-1), 1, COLOR_NEGRO),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    wrapper_tot = Table([["", t_tot]], colWidths=[270, 270])
    story.append(wrapper_tot)
    story.append(Spacer(1, 14))
    
    # 5. TABLA DE HISTORIAL DE ABONOS Y CUOTAS SUCESIVAS
    abonos = datos_apartado.get("abonos", [])
    story.append(Paragraph("<b><font size='9' color='#111827'>HISTORIAL DETALLADO DE ABONOS Y CUOTAS</font></b>", style_normal))
    story.append(Spacer(1, 4))
    
    abonos_rows = [
        [
            Paragraph("<b><font size='7.5' color='#111827'>#</font></b>", style_normal),
            Paragraph("<b><font size='7.5' color='#111827'>Fecha y Hora</font></b>", style_normal),
            Paragraph("<b><font size='7.5' color='#111827'>Medio de Pago</font></b>", style_normal),
            Paragraph("<b><font size='7.5' color='#111827'>Comprobante / Ref</font></b>", style_normal),
            Paragraph("<b><font size='7.5' color='#111827'>Monto Cuota</font></b>", style_normal),
            Paragraph("<b><font size='7.5' color='#111827'>Saldo Restante</font></b>", style_normal),
        ]
    ]
    
    if abonos:
        saldo_acum = total
        for idx, ab in enumerate(abonos, 1):
            monto_cuota = float(ab.get('monto', 0.0))
            saldo_acum = max(0.0, saldo_acum - monto_cuota)
            abonos_rows.append([
                Paragraph(f"<font size='7.5'>{idx}</font>", style_normal),
                Paragraph(f"<font size='7.5'>{ab.get('fecha', '-')}</font>", style_normal),
                Paragraph(f"<font size='7.5'><b>{ab.get('metodo_pago', 'SINPE_MOVIL')}</b></font>", style_normal),
                Paragraph(f"<font size='7.5'>{ab.get('numero_comprobante', 'S/C')}</font>", style_normal),
                Paragraph(f"<font size='7.5' color='#059669'><b>+CRC {monto_cuota:,.2f}</b></font>", style_normal),
                Paragraph(f"<font size='7.5'>CRC {saldo_acum:,.2f}</font>", style_normal),
            ])
    else:
        abonos_rows.append([
            Paragraph("<font size='7.5' color='#6B7280'>1</font>", style_normal),
            Paragraph(f"<font size='7.5' color='#6B7280'>{fecha_str}</font>", style_normal),
            Paragraph("<font size='7.5' color='#6B7280'>APERTURA</font>", style_normal),
            Paragraph("<font size='7.5' color='#6B7280'>REGISTRO INICIAL</font>", style_normal),
            Paragraph(f"<font size='7.5' color='#059669'><b>+CRC {total_abonado:,.2f}</b></font>", style_normal),
            Paragraph(f"<font size='7.5'>CRC {saldo_pendiente:,.2f}</font>", style_normal),
        ])
        
    t_abonos = Table(abonos_rows, colWidths=[25, 115, 110, 110, 90, 90])
    t_abonos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F9FAFB")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, COLOR_BORDE),
        ('BOX', (0,0), (-1,-1), 1, COLOR_BORDE),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_abonos)
    story.append(Spacer(1, 14))
    
    # 6. TERMINOS Y CONDICIONES DEL APARTADO
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_BORDE))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<font size='7' color='#6B7280'>"
        "<b>TERMINOS Y POLITICAS DE APARTADO:</b><br/>"
        "1. Las prendas detalladas quedan bajo custodia y reserva exclusiva hasta la fecha limite estipulada.<br/>"
        "2. Para retirar sus articulos o registrar nuevos abonos, favor presentar este comprobante o su documento de identificacion.<br/>"
        "3. Al liquidar el 100% del saldo, se entrega el articulo y se emite la factura electronica correspondiente. Gracias por su preferencia.<br/>"
        "NEBULOSA | INGENIERIA & AUTOMATIZACION - Software Empresarial PRO</font>",
        style_normal
    ))
    
    doc.build(story)
    return ruta_pdf
