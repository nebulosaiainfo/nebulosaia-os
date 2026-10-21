# -*- coding: utf-8 -*-
"""
Servicio de Exportación Ejecutiva a Excel (.xlsx) para NEXO RETAIL & BUSINESS OS.
Genera libros de trabajo con múltiples hojas, tablas dinámicas analíticas,
fórmulas financieras, formateo numérico profesional y porcentajes de participación.
"""

import os
import json
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Paleta Ejecutiva
COLOR_NAVY = "0F172A"       # Fondo Encabezados Principales
COLOR_SLATE_HEADER = "1E293B"# Fondo Encabezados Columnas
COLOR_WHITE = "FFFFFF"
COLOR_LIGHT_BG = "F8FAFC"   # Fondo alterno
COLOR_BORDER = "CBD5E1"     # Gris borde
COLOR_TOTAL = "E2E8F0"      # Fila de totales
COLOR_ACCENT_RED = "DC2626" # Descuentos

font_title = Font(name="Calibri", size=14, bold=True, color=COLOR_WHITE)
font_subtitle = Font(name="Calibri", size=9, italic=True, color="94A3B8")
font_header = Font(name="Calibri", size=10, bold=True, color=COLOR_WHITE)
font_bold = Font(name="Calibri", size=10, bold=True, color="0F172A")
font_regular = Font(name="Calibri", size=10, color="1E293B")
font_total = Font(name="Calibri", size=10, bold=True, color="0F172A")
font_discount = Font(name="Calibri", size=10, bold=True, color=COLOR_ACCENT_RED)

fill_title = PatternFill(start_color=COLOR_NAVY, end_color=COLOR_NAVY, fill_type="solid")
fill_header = PatternFill(start_color=COLOR_SLATE_HEADER, end_color=COLOR_SLATE_HEADER, fill_type="solid")
fill_alt = PatternFill(start_color=COLOR_LIGHT_BG, end_color=COLOR_LIGHT_BG, fill_type="solid")
fill_total = PatternFill(start_color=COLOR_TOTAL, end_color=COLOR_TOTAL, fill_type="solid")

thin_border_side = Side(style='thin', color=COLOR_BORDER)
double_bottom_side = Side(style='double', color="0F172A")
top_thin_side = Side(style='thin', color="0F172A")

cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
total_border = Border(left=thin_border_side, right=thin_border_side, top=top_thin_side, bottom=double_bottom_side)

align_left = Alignment(horizontal="left", vertical="center")
align_center = Alignment(horizontal="center", vertical="center")
align_right = Alignment(horizontal="right", vertical="center")

FORMAT_CURRENCY = '"CRC "#,##0.00'
FORMAT_PERCENT = '0.0%'
FORMAT_INT = '#,##0'

def autofit_columns(ws, max_len_cap=50):
    ws.views.sheetView[0].showGridLines = True
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val = cell.value
            if val is not None:
                # Evitar contar fórmulas largas como ancho real
                val_str = str(val)
                if val_str.startswith("="):
                    val_str = "123,456.78"
                max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 11), max_len_cap)

def generar_reporte_excel_completo(facturas, productos, apartados, config) -> str:
    """
    Genera un archivo Excel multi-hoja completo y profesional.
    Retorna la ruta absoluta del archivo generado en backend/data/uploads/
    """
    wb = openpyxl.Workbook()
    
    nombre_tienda = config.nombre_tienda if config else "NEXO RETAIL & BUSINESS"
    cedula_tienda = config.cedula_fiscal if config else "3-101-000000"
    giro_tienda = config.giro_comercial if config else "Comercio General / Retail"
    fecha_emision = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ========================================================
    # HOJA 1: RESUMEN EJECUTIVO & KPIS
    # ========================================================
    ws1 = wb.active
    ws1.title = "Resumen Ejecutivo"
    ws1.sheet_properties.tabColor = "00F0FF"

    # Banner Header
    ws1.merge_cells("A1:F1")
    ws1['A1'] = f"REPORTE GENERAL DE GESTIÓN Y BUSINESS ANALYTICS — {nombre_tienda.upper()}"
    ws1['A1'].font = font_title
    ws1['A1'].fill = fill_title
    ws1['A1'].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws1.row_dimensions[1].height = 30

    ws1.merge_cells("A2:F2")
    ws1['A2'] = f"Cédula Fiscal: {cedula_tienda}  |  Giro Comercial: {giro_tienda}  |  Generado: {fecha_emision}  |  Moneda Oficial: CRC"
    ws1['A2'].font = font_subtitle
    ws1['A2'].fill = fill_title
    ws1['A2'].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws1.row_dimensions[2].height = 18

    # Espacio
    ws1.append([])

    # Métricas calculadas
    total_ventas = sum(f.total or 0.0 for f in facturas)
    total_descuentos = sum(f.descuento or 0.0 for f in facturas)
    total_subtotal_base = sum(f.subtotal or 0.0 for f in facturas)
    total_iva = sum(f.iva or 0.0 for f in facturas)
    cant_facturas = len(facturas)
    ticket_promedio = (total_ventas / cant_facturas) if cant_facturas > 0 else 0.0

    # TABLA 1: VENTAS Y FACTURACIÓN
    ws1.append(["MÉTRICAS CLAVE DE VENTAS & FISCALES", "VALOR CONSOLIDADO", "NOTAS / DESGLOSE"])
    h_row = ws1.max_row
    for c in range(1, 4):
        cell = ws1.cell(row=h_row, column=c)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_left if c < 2 else align_right

    rows_ventas = [
        ("Ventas Totales Netas Cobradas (IVA Incluido)", total_ventas, FORMAT_CURRENCY, "Monto efectivo total facturado"),
        ("Subtotal Base Imponible (Sin Impuestos)", total_subtotal_base, FORMAT_CURRENCY, "Base gravable legal"),
        ("I.V.A. (13% Incluido Recaudado)", total_iva, FORMAT_CURRENCY, "Débito fiscal para Hacienda"),
        ("Total Descuentos y Promociones Otorgadas", total_descuentos, FORMAT_CURRENCY, "Beneficio directo al cliente"),
        ("Cantidad de Facturas Emitidas", cant_facturas, FORMAT_INT, "Volumen de transacciones"),
        ("Ticket Promedio por Venta", ticket_promedio, FORMAT_CURRENCY, "Monto promedio por factura")
    ]
    for label, val, fmt, note in rows_ventas:
        ws1.append([label, val, note])
        r = ws1.max_row
        ws1.cell(row=r, column=1).font = font_regular
        ws1.cell(row=r, column=1).border = cell_border
        c2 = ws1.cell(row=r, column=2)
        c2.font = font_bold
        c2.number_format = fmt
        c2.alignment = align_right
        c2.border = cell_border
        c3 = ws1.cell(row=r, column=3)
        c3.font = font_regular
        c3.alignment = align_left
        c3.border = cell_border

    ws1.append([])

    # TABLA 2: VALORACIÓN WMS
    total_skus = len(productos)
    total_unidades = sum(p.stock or 0 for p in productos)
    total_apartadas = sum(p.stock_apartado or 0 for p in productos)
    val_comercial = sum((p.stock or 0) * (p.precio or 0.0) for p in productos)
    val_costo = sum((p.stock or 0) * (p.costo or 0.0) for p in productos)
    margen_potencial = max(0.0, val_comercial - val_costo)
    margen_pct = (margen_potencial / val_comercial) if val_comercial > 0 else 0.0

    ws1.append(["VALORACIÓN Y SALUD DE BODEGA WMS", "VALOR CONSOLIDADO", "NOTAS DE INVENTARIO"])
    h_row = ws1.max_row
    for c in range(1, 4):
        cell = ws1.cell(row=h_row, column=c)
        cell.font = font_header
        cell.fill = fill_header

    rows_wms = [
        ("Total de Artículos / SKUs Registrados", total_skus, FORMAT_INT, "Catálogo activo"),
        ("Existencias Físicas en Almacén (Disponibles)", total_unidades, FORMAT_INT, "Unidades para venta inmediata"),
        ("Unidades Comprometidas en Apartados", total_apartadas, FORMAT_INT, "Reservas activas de clientes"),
        ("Valoración Comercial Total (PVP con IVA)", val_comercial, FORMAT_CURRENCY, "Valor bruto en anaquel"),
        ("Valoración en Costo de Adquisición", val_costo, FORMAT_CURRENCY, "Capital inmovilizado en compras"),
        ("Margen Bruto Teórico Estimado", margen_potencial, FORMAT_CURRENCY, "Ganancia potencial proyectada"),
        ("Rentabilidad Estimada de Catálogo (%)", margen_pct, FORMAT_PERCENT, "Margen sobre ventas brutas")
    ]
    for label, val, fmt, note in rows_wms:
        ws1.append([label, val, note])
        r = ws1.max_row
        ws1.cell(row=r, column=1).font = font_regular
        ws1.cell(row=r, column=1).border = cell_border
        c2 = ws1.cell(row=r, column=2)
        c2.font = font_bold
        c2.number_format = fmt
        c2.alignment = align_right
        c2.border = cell_border
        c3 = ws1.cell(row=r, column=3)
        c3.font = font_regular
        c3.alignment = align_left
        c3.border = cell_border

    ws1.append([])

    # TABLA 3: CARTERA DE APARTADOS
    total_apartados = len(apartados)
    total_monto_apart = sum(a.total or 0.0 for a in apartados)
    total_pendiente = sum(a.saldo_pendiente or 0.0 for a in apartados)
    total_recaudado = max(0.0, total_monto_apart - total_pendiente)
    tasa_cobro = (total_recaudado / total_monto_apart) if total_monto_apart > 0 else 0.0

    ws1.append(["ESTADO DE CARTERA (SISTEMA DE APARTADOS)", "VALOR CONSOLIDADO", "ESTADO DE COBRANZA"])
    h_row = ws1.max_row
    for c in range(1, 4):
        cell = ws1.cell(row=h_row, column=c)
        cell.font = font_header
        cell.fill = fill_header

    rows_apart = [
        ("Total de Apartados Generados", total_apartados, FORMAT_INT, "Clientes en plan de pagos"),
        ("Monto Total Comprometido en Apartados", total_monto_apart, FORMAT_CURRENCY, "Venta acordada"),
        ("Monto Ya Recaudado (Abonos Confirmados)", total_recaudado, FORMAT_CURRENCY, "Dinero ingresado a caja"),
        ("Saldo Pendiente por Cobrar", total_pendiente, FORMAT_CURRENCY, "Cuentas activas por cobrar"),
        ("Tasa de Recuperación de Cartera (%)", tasa_cobro, FORMAT_PERCENT, "Porcentaje de amortización")
    ]
    for label, val, fmt, note in rows_apart:
        ws1.append([label, val, note])
        r = ws1.max_row
        ws1.cell(row=r, column=1).font = font_regular
        ws1.cell(row=r, column=1).border = cell_border
        c2 = ws1.cell(row=r, column=2)
        c2.font = font_bold
        c2.number_format = fmt
        c2.alignment = align_right
        c2.border = cell_border
        c3 = ws1.cell(row=r, column=3)
        c3.font = font_regular
        c3.alignment = align_left
        c3.border = cell_border

    autofit_columns(ws1)

    # ========================================================
    # HOJA 2: FLUJO DE CAJA POR MÉTODO DE PAGO
    # ========================================================
    ws2 = wb.create_sheet(title="Flujo por Método de Pago")
    ws2.sheet_properties.tabColor = "38BDF8"

    ws2.append(["MÉTODO DE PAGO", "TRANSACCIONES", "MONTO TOTAL RECAUDADO", "% PARTICIPACIÓN", "TICKET PROMEDIO"])
    h_row = ws2.max_row
    for c in range(1, 6):
        cell = ws2.cell(row=h_row, column=c)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center if c == 2 else (align_right if c >= 3 else align_left)

    metodos_def = [
        ("SINPE_MOVIL", "SINPE Móvil"),
        ("TARJETA", "Tarjeta Débito / Crédito"),
        ("TRANSFERENCIA", "Transferencia Bancaria"),
        ("EFECTIVO", "Efectivo")
    ]
    metodos_map = {k: {"nombre": name, "cant": 0, "total": 0.0} for k, name in metodos_def}
    for f in facturas:
        m = f.metodo_pago or "SINPE_MOVIL"
        if m in metodos_map:
            metodos_map[m]["cant"] += 1
            metodos_map[m]["total"] += (f.total or 0.0)
        else:
            if m not in metodos_map:
                metodos_map[m] = {"nombre": m, "cant": 0, "total": 0.0}
            metodos_map[m]["cant"] += 1
            metodos_map[m]["total"] += (f.total or 0.0)

    start_r = ws2.max_row + 1
    for k, data in metodos_map.items():
        curr_r = ws2.max_row + 1
        formula_pct = f"=C{curr_r}/$C${start_r + len(metodos_map)}" if total_ventas > 0 else 0.0
        formula_avg = f"=IF(B{curr_r}>0, C{curr_r}/B{curr_r}, 0)"
        ws2.append([data["nombre"], data["cant"], data["total"], formula_pct, formula_avg])
        r = ws2.max_row
        ws2.cell(row=r, column=1).font = font_bold
        ws2.cell(row=r, column=1).border = cell_border
        
        c_cant = ws2.cell(row=r, column=2)
        c_cant.font = font_regular
        c_cant.number_format = FORMAT_INT
        c_cant.alignment = align_center
        c_cant.border = cell_border

        c_tot = ws2.cell(row=r, column=3)
        c_tot.font = font_bold
        c_tot.number_format = FORMAT_CURRENCY
        c_tot.alignment = align_right
        c_tot.border = cell_border

        c_pct = ws2.cell(row=r, column=4)
        c_pct.font = font_regular
        c_pct.number_format = FORMAT_PERCENT
        c_pct.alignment = align_right
        c_pct.border = cell_border

        c_avg = ws2.cell(row=r, column=5)
        c_avg.font = font_regular
        c_avg.number_format = FORMAT_CURRENCY
        c_avg.alignment = align_right
        c_avg.border = cell_border

    end_r = ws2.max_row
    # Fila de Totales
    total_r = end_r + 1
    ws2.append([
        "TOTAL GENERAL",
        f"=SUM(B{start_r}:B{end_r})",
        f"=SUM(C{start_r}:C{end_r})",
        f"=SUM(D{start_r}:D{end_r})",
        f"=IF(B{total_r}>0, C{total_r}/B{total_r}, 0)"
    ])
    for c in range(1, 6):
        cell = ws2.cell(row=total_r, column=c)
        cell.font = font_total
        cell.fill = fill_total
        cell.border = total_border
        if c == 2:
            cell.number_format = FORMAT_INT
            cell.alignment = align_center
        elif c in [3, 5]:
            cell.number_format = FORMAT_CURRENCY
            cell.alignment = align_right
        elif c == 4:
            cell.number_format = FORMAT_PERCENT
            cell.alignment = align_right

    autofit_columns(ws2)

    # ========================================================
    # HOJA 3: DETALLE DE FACTURACIÓN & FISCAL
    # ========================================================
    ws3 = wb.create_sheet(title="Historial de Facturación")
    ws3.sheet_properties.tabColor = "10B981"

    headers_fac = [
        "CONSECUTIVO", "FECHA & HORA", "CLIENTE", "CÉDULA", "TELÉFONO",
        "VENDEDOR", "MÉTODO PAGO", "COMPROBANTE / REF",
        "SUBTOTAL BASE (CRC)", "DESCUENTO (CRC)", "IVA 13% INCLUIDO (CRC)", "TOTAL COBRADO (CRC)"
    ]
    ws3.append(headers_fac)
    h_row = ws3.max_row
    for c in range(1, len(headers_fac) + 1):
        cell = ws3.cell(row=h_row, column=c)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center if c in [1, 2, 4, 5, 7, 8] else (align_right if c >= 9 else align_left)

    f_start = ws3.max_row + 1
    for idx, f in enumerate(facturas):
        fecha_f = f.fecha.strftime("%d/%m/%Y %H:%M") if f.fecha else "N/A"
        ws3.append([
            f.consecutivo,
            fecha_f,
            f.cliente_nombre or "Cliente General",
            f.cliente_cedula or "N/A",
            f.cliente_telefono or "N/A",
            f.vendedor_nombre or "General",
            f.metodo_pago,
            f.numero_comprobante or "S/C",
            f.subtotal or 0.0,
            f.descuento or 0.0,
            f.iva or 0.0,
            f.total or 0.0
        ])
        r = ws3.max_row
        row_fill = fill_alt if idx % 2 == 1 else None
        for c in range(1, len(headers_fac) + 1):
            cell = ws3.cell(row=r, column=c)
            cell.font = font_discount if (c == 10 and (f.descuento or 0) > 0) else (font_bold if c == 12 else font_regular)
            if row_fill: cell.fill = row_fill
            cell.border = cell_border
            if c in [1, 2, 4, 5, 7, 8]:
                cell.alignment = align_center
            elif c >= 9:
                cell.number_format = FORMAT_CURRENCY
                cell.alignment = align_right

    f_end = ws3.max_row
    if f_end >= f_start:
        ws3.append([
            "TOTALES", "", "", "", "", "", "", "",
            f"=SUM(I{f_start}:I{f_end})",
            f"=SUM(J{f_start}:J{f_end})",
            f"=SUM(K{f_start}:K{f_end})",
            f"=SUM(L{f_start}:L{f_end})"
        ])
        tot_r = ws3.max_row
        for c in range(1, len(headers_fac) + 1):
            cell = ws3.cell(row=tot_r, column=c)
            cell.font = font_total
            cell.fill = fill_total
            cell.border = total_border
            if c >= 9:
                cell.number_format = FORMAT_CURRENCY
                cell.alignment = align_right

    autofit_columns(ws3)

    # ========================================================
    # HOJA 4: INVENTARIO WMS & VALORACIÓN
    # ========================================================
    ws4 = wb.create_sheet(title="Inventario WMS")
    ws4.sheet_properties.tabColor = "8B5CF6"

    headers_wms = [
        "SKU / CÓDIGO", "NOMBRE DEL PRODUCTO / SERVICIO", "CATEGORÍA",
        "VARIANTE PRINCIPAL", "ESPECIFICACIÓN", "UBICACIÓN",
        "STOCK FÍSICO", "STOCK APARTADO",
        "COSTO UNITARIO", "PRECIO VENTA (IVA INC.)",
        "VALOR COSTO TOTAL", "VALOR VENTA TOTAL",
        "MARGEN BRUTO UNITARIO", "MARGEN %"
    ]
    ws4.append(headers_wms)
    h_row = ws4.max_row
    for c in range(1, len(headers_wms) + 1):
        cell = ws4.cell(row=h_row, column=c)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center if c in [1, 3, 4, 5, 6, 7, 8] else (align_right if c >= 9 else align_left)

    w_start = ws4.max_row + 1
    for idx, p in enumerate(productos):
        r_num = ws4.max_row + 1
        formula_val_costo = f"=G{r_num}*I{r_num}"
        formula_val_venta = f"=G{r_num}*J{r_num}"
        formula_margen_u = f"=J{r_num}-I{r_num}"
        formula_margen_p = f"=IF(J{r_num}>0, M{r_num}/J{r_num}, 0)"

        ws4.append([
            p.sku,
            p.nombre,
            p.categoria or "General",
            p.talla or "Estándar",
            p.color or "General",
            p.ubicacion or "Principal",
            p.stock or 0,
            p.stock_apartado or 0,
            p.costo or 0.0,
            p.precio or 0.0,
            formula_val_costo,
            formula_val_venta,
            formula_margen_u,
            formula_margen_p
        ])
        r = ws4.max_row
        row_fill = fill_alt if idx % 2 == 1 else None
        for c in range(1, len(headers_wms) + 1):
            cell = ws4.cell(row=r, column=c)
            cell.font = font_bold if c in [1, 12, 14] else font_regular
            if row_fill: cell.fill = row_fill
            cell.border = cell_border
            if c in [1, 3, 4, 5, 6]:
                cell.alignment = align_center
            elif c in [7, 8]:
                cell.number_format = FORMAT_INT
                cell.alignment = align_center
            elif c in [9, 10, 11, 12, 13]:
                cell.number_format = FORMAT_CURRENCY
                cell.alignment = align_right
            elif c == 14:
                cell.number_format = FORMAT_PERCENT
                cell.alignment = align_right

    w_end = ws4.max_row
    if w_end >= w_start:
        ws4.append([
            "TOTALES CONSOLIDADOS", "", "", "", "", "",
            f"=SUM(G{w_start}:G{w_end})",
            f"=SUM(H{w_start}:H{w_end})",
            "", "",
            f"=SUM(K{w_start}:K{w_end})",
            f"=SUM(L{w_start}:L{w_end})",
            f"=L{w_end + 1}-K{w_end + 1}",
            f"=IF(L{w_end + 1}>0, M{w_end + 1}/L{w_end + 1}, 0)"
        ])
        tot_r = ws4.max_row
        for c in range(1, len(headers_wms) + 1):
            cell = ws4.cell(row=tot_r, column=c)
            cell.font = font_total
            cell.fill = fill_total
            cell.border = total_border
            if c in [7, 8]:
                cell.number_format = FORMAT_INT
                cell.alignment = align_center
            elif c in [11, 12, 13]:
                cell.number_format = FORMAT_CURRENCY
                cell.alignment = align_right
            elif c == 14:
                cell.number_format = FORMAT_PERCENT
                cell.alignment = align_right

    autofit_columns(ws4)

    # ========================================================
    # HOJA 5: CARTERA DE APARTADOS
    # ========================================================
    ws5 = wb.create_sheet(title="Cartera de Apartados")
    ws5.sheet_properties.tabColor = "F59E0B"

    headers_apart = [
        "CONSECUTIVO", "FECHA CREACIÓN", "CLIENTE", "TELÉFONO", "CÉDULA",
        "VENDEDOR", "MONTO TOTAL (CRC)", "RECAUDADO / ABONOS (CRC)",
        "SALDO PENDIENTE (CRC)", "% AMORTIZADO", "ESTADO"
    ]
    ws5.append(headers_apart)
    h_row = ws5.max_row
    for c in range(1, len(headers_apart) + 1):
        cell = ws5.cell(row=h_row, column=c)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center if c in [1, 2, 4, 5, 11] else (align_right if c in [7, 8, 9, 10] else align_left)

    a_start = ws5.max_row + 1
    for idx, a in enumerate(apartados):
        r_num = ws5.max_row + 1
        formula_pct = f"=IF(G{r_num}>0, H{r_num}/G{r_num}, 0)"
        monto_tot = a.total or 0.0
        saldo_pend = a.saldo_pendiente or 0.0
        recaudado = max(0.0, monto_tot - saldo_pend)
        fecha_a = a.fecha_creacion.strftime("%d/%m/%Y") if a.fecha_creacion else "N/A"

        ws5.append([
            a.consecutivo,
            fecha_a,
            a.cliente_nombre,
            a.cliente_telefono or "N/A",
            a.cliente_cedula or "N/A",
            a.vendedor_nombre or "General",
            monto_tot,
            recaudado,
            saldo_pend,
            formula_pct,
            a.estado or "PENDIENTE"
        ])
        r = ws5.max_row
        row_fill = fill_alt if idx % 2 == 1 else None
        for c in range(1, len(headers_apart) + 1):
            cell = ws5.cell(row=r, column=c)
            cell.font = font_bold if c in [1, 9] else font_regular
            if row_fill: cell.fill = row_fill
            cell.border = cell_border
            if c in [1, 2, 4, 5, 11]:
                cell.alignment = align_center
            elif c in [7, 8, 9]:
                cell.number_format = FORMAT_CURRENCY
                cell.alignment = align_right
            elif c == 10:
                cell.number_format = FORMAT_PERCENT
                cell.alignment = align_right

    a_end = ws5.max_row
    if a_end >= a_start:
        ws5.append([
            "TOTALES", "", "", "", "", "",
            f"=SUM(G{a_start}:G{a_end})",
            f"=SUM(H{a_start}:H{a_end})",
            f"=SUM(I{a_start}:I{a_end})",
            f"=IF(G{a_end + 1}>0, H{a_end + 1}/G{a_end + 1}, 0)",
            ""
        ])
        tot_r = ws5.max_row
        for c in range(1, len(headers_apart) + 1):
            cell = ws5.cell(row=tot_r, column=c)
            cell.font = font_total
            cell.fill = fill_total
            cell.border = total_border
            if c in [7, 8, 9]:
                cell.number_format = FORMAT_CURRENCY
                cell.alignment = align_right
            elif c == 10:
                cell.number_format = FORMAT_PERCENT
                cell.alignment = align_right

    autofit_columns(ws5)

    # ========================================================
    # GUARDAR ARCHIVO
    # ========================================================
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "reportes"))
    os.makedirs(out_dir, exist_ok=True)
    filename = f"Reporte_Consolidado_NEXO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(out_dir, filename)
    wb.save(filepath)
    return filepath
