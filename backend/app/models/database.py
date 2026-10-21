# -*- coding: utf-8 -*-
"""
NEXO CRM & WMS RETAIL - Esquema de Base de Datos Integral
Roles: LÍDER (Isaac / Soporte Maestro), ADMIN (Dueño Tienda), VENDEDOR.
Módulos: WMS Talla/Color, Facturación con Vouchers/SINPE, Clientes con Vendedor Asignado, Tickets de Soporte.
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

Base = declarative_base()

class RolUsuario(str, enum.Enum):
    LIDER = "LIDER"          # Isaac: control total, licencias, personalización profunda
    ADMIN = "ADMIN"          # Dueño de la tienda
    VENDEDOR = "VENDEDOR"    # Personal de tienda / mostrador

class EstadoTicket(str, enum.Enum):
    ABIERTO = "ABIERTO"
    EN_PROCESO = "EN_PROCESO"
    RESUELTO = "RESUELTO"
    CERRADO = "CERRADO"

class MetodoPago(str, enum.Enum):
    EFECTIVO = "EFECTIVO"
    SINPE_MOVIL = "SINPE_MOVIL"
    TRANSFERENCIA = "TRANSFERENCIA"
    TARJETA = "TARJETA"
    MIXTO = "MIXTO"

# ==========================================
# 1. CONFIGURACIÓN DE TENANT & ESTÉTICA WHITE-LABEL
# ==========================================
class ConfiguracionTenant(Base):
    __tablename__ = "configuracion_tenant"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_tienda = Column(String(100), default="Tienda Moda & Retail")
    cedula_juridica_o_fisica = Column(String(30), nullable=True)
    correo_contacto = Column(String(100), nullable=True)
    telefono = Column(String(30), nullable=True)
    direccion = Column(String(255), nullable=True)
    codigo_actividad_hacienda = Column(String(20), nullable=True) # Ej: 477101 Venta ropa
    
    # Personalización estética en tiempo real (Color picker / Theme)
    tema_activo = Column(String(30), default="cyberpunk_dark") # dark, light, neon, pastel
    color_primario = Column(String(10), default="#00F0FF")
    color_secundario = Column(String(10), default="#7000FF")
    color_fondo = Column(String(10), default="#0A0E17")
    color_tarjetas = Column(String(10), default="#141C2E")
    url_logotipo = Column(String(255), nullable=True)
    moneda_simbolo = Column(String(5), default="₡") # ₡ o $
    
    # Bloqueo de soporte / Mantenimiento
    codigo_verificacion_soporte = Column(String(10), nullable=True) # Código solicitado a Isaac
    licencia_activa = Column(Boolean, default=True)

# ==========================================
# 2. USUARIOS & ROLES (LÍDER, ADMIN, VENDEDOR)
# ==========================================
class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_completo = Column(String(120), nullable=False)
    correo = Column(String(120), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(Enum(RolUsuario), default=RolUsuario.VENDEDOR)
    google_id = Column(String(100), nullable=True)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    ventas = relationship("Factura", back_populates="vendedor")
    clientes_asignados = relationship("Cliente", back_populates="vendedor_asignado")
    tickets_reportados = relationship("TicketSoporte", back_populates="usuario_solicitante")

# ==========================================
# 3. CLIENTES & ASIGNACIÓN DE VENDEDOR
# ==========================================
class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_completo = Column(String(150), nullable=False)
    cedula = Column(String(30), nullable=True) # Cédula física, jurídica o pasaporte
    correo = Column(String(120), nullable=True)
    telefono = Column(String(30), nullable=True)
    direccion = Column(Text, nullable=True)
    codigo_actividad = Column(String(20), nullable=True) # Opcional Hacienda
    comentarios_notas = Column(Text, nullable=True)      # Comentario histórico por cliente
    
    # Vendedor asignado exclusivo
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    vendedor_asignado = relationship("Usuario", back_populates="clientes_asignados")
    
    creado_en = Column(DateTime, default=datetime.utcnow)
    facturas = relationship("Factura", back_populates="cliente")

# ==========================================
# 4. WMS RETAIL (PRODUCTO, TALLA, COLOR, STOCK)
# ==========================================
class Producto(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False) # Ej: Hoodie Cyberpunk Oversize
    categoria = Column(String(50), default="Prendas")
    descripcion = Column(Text, nullable=True)
    precio_base = Column(Float, nullable=False)
    costo_base = Column(Float, default=0.0)
    
    variantes = relationship("VarianteProducto", back_populates="producto", cascade="all, delete-orphan")

class VarianteProducto(Base):
    __tablename__ = "variantes_producto"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    sku = Column(String(50), unique=True, nullable=False) # Ej: HD-OVR-BLK-M
    codigo_barras = Column(String(50), unique=True, nullable=True)
    
    # Atributos de moda para WMS
    talla = Column(String(10), nullable=False) # S, M, L, XL, etc.
    color_nombre = Column(String(50), nullable=False) # Negro Asfalto, Beige Tierra
    color_hex = Column(String(10), nullable=True)     # #1A1A1A
    tono_categoria = Column(String(30), nullable=True) # Neutro, Tierra, Pastel, Neón (Para IA)
    
    # Control de Stock WMS
    stock_actual = Column(Integer, default=0)
    stock_apartado = Column(Integer, default=0) # Reservas por confirmar pago
    stock_minimo_alerta = Column(Integer, default=3)
    ubicacion_bodega = Column(String(50), nullable=True) # Pasillo A / Rack 3 / Caja 12
    
    producto = relationship("Producto", back_populates="variantes")

# ==========================================
# 5. FACTURACIÓN & REGISTRO DE VOUCHERS / SINPE
# ==========================================
class Factura(Base):
    __tablename__ = "facturas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    consecutivo = Column(String(50), unique=True, nullable=False) # F-00001
    fecha_emision = Column(DateTime, default=datetime.utcnow)
    
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Métodos de pago y comprobantes bancarios
    metodo_pago = Column(Enum(MetodoPago), default=MetodoPago.SINPE_MOVIL)
    numero_comprobante_banco = Column(String(100), nullable=True) # Código SINPE o Transferencia
    archivo_voucher_adjunto = Column(String(255), nullable=True)  # Ruta imagen voucher
    
    # Totales monetarios
    subtotal = Column(Float, default=0.0)
    impuesto_iva = Column(Float, default=0.0) # 13% o exento
    total = Column(Float, nullable=False)
    
    # Estado y PDF generado
    ruta_pdf_generado = Column(String(255), nullable=True)
    correo_enviado = Column(Boolean, default=False)
    
    cliente = relationship("Cliente", back_populates="facturas")
    vendedor = relationship("Usuario", back_populates="ventas")
    lineas = relationship("LineaFactura", back_populates="factura", cascade="all, delete-orphan")

class LineaFactura(Base):
    __tablename__ = "lineas_factura"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    factura_id = Column(Integer, ForeignKey("facturas.id"), nullable=False)
    variante_id = Column(Integer, ForeignKey("variantes_producto.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False)
    subtotal_linea = Column(Float, nullable=False)
    
    factura = relationship("Factura", back_populates="lineas")
    variante = relationship("VarianteProducto")

# ==========================================
# 6. MÓDULO DE TICKETS DE SOPORTE & REPORTES DE ERROR
# ==========================================
class TicketSoporte(Base):
    __tablename__ = "tickets_soporte"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_ticket = Column(String(20), unique=True, nullable=False) # TCK-2026-001
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=False)
    categoria = Column(String(50), default="ERROR_SISTEMA") # ERROR_SISTEMA, PEDIDO_ESTETICA, CONSULTA_WMS
    prioridad = Column(String(20), default="MEDIA")         # BAJA, MEDIA, ALTA, URGENTE
    estado = Column(Enum(EstadoTicket), default=EstadoTicket.ABIERTO)
    captura_pantalla_adjunta = Column(String(255), nullable=True)
    
    # Respuesta directa de Isaac (Líder)
    respuesta_lider = Column(Text, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    usuario_solicitante = relationship("Usuario", back_populates="tickets_reportados")
