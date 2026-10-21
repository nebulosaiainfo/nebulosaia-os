# -*- coding: utf-8 -*-
"""
Servidor REST API FastAPI para NEXO RETAIL OS & CRM OMNICANAL.
Soporte completo para:
- WMS con Edición completa de producto (datos, stock, fotos).
- Seguimiento de Proformas con Calendario y Alarmas programadas.
- CRM Omnicanal con Chatbot de calificación guiada y atención humana.
- Sistema de Apartados y Pagos en Cuotas (con abonos sucesivos SINPE/Transferencia).
- Historial y Configuración de Facturación Fiscal.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Directorios de trabajo
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
import sys
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))
UPLOADS_DIR = BASE_DIR / "backend" / "uploads"
PROD_UPLOADS_DIR = UPLOADS_DIR / "productos"
PDF_DIR = BASE_DIR / "01_Core_Facturacion" / "facturas_pdf"
PROFORMAS_DIR = BASE_DIR / "01_Core_Facturacion" / "proformas_pdf"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PROD_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
PROFORMAS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "nexo_retail.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# MODELOS DE BASE DE DATOS
# ==========================================
class DBConfiguracion(Base):
    __tablename__ = "configuracion"
    id = Column(Integer, primary_key=True)
    nombre_tienda = Column(String(100), default="NEBULOSA INGENIERÍA Y AUTOMATIZACIÓN")
    cedula_fiscal = Column(String(50), default="3-101-948271")
    telefono = Column(String(30), default="+506 8888-8888")
    correo = Column(String(100), default="ventas@nexoretail.cr")
    direccion = Column(String(200), default="San José, Costa Rica")
    codigo_actividad = Column(String(50), default="477101 - Venta al por menor de prendas de vestir")
    regimen_tributario = Column(String(50), default="Régimen Simplificado (Costa Rica)")
    sucursal = Column(String(20), default="001")
    caja = Column(String(20), default="00001")
    hacienda_ambiente = Column(String(30), default="Staging / Pruebas DGT")
    color_primario = Column(String(10), default="#00F0FF")
    color_secundario = Column(String(10), default="#7000FF")
    color_fondo = Column(String(20), default="#080c14")
    tema_fondo = Column(String(50), default="Midnight Nebula")
    moneda = Column(String(5), default="CRC")
    giro_comercial = Column(String(100), default="Comercio General / Retail")
    licencia_activa = Column(Boolean, default=True)

class DBProductoWMS(Base):
    __tablename__ = "productos_wms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), unique=True, index=True)
    nombre = Column(String(150), nullable=False)
    categoria = Column(String(50), default="General")
    talla = Column(String(30), default="Estándar") # Variante principal (Talla / Modelo / Capacidad / Tipo)
    color = Column(String(50), default="N/A")      # Variante secundaria (Color / Marca / Especificación)
    tono = Column(String(30), default="General")
    ubicacion = Column(String(50), default="Almacén Principal")
    stock = Column(Integer, default=0)
    stock_apartado = Column(Integer, default=0)
    precio = Column(Float, nullable=False)
    costo = Column(Float, default=0.0)
    imagen_url = Column(String(255), nullable=True)
    proveedor = Column(String(100), default="Proveedor General")
    margen_utilidad = Column(Float, default=50.0)
    fecha_ingreso = Column(String(30), default="2026-10-20 12:00:00")
    dias_rotacion = Column(Integer, default=12)

class DBCliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    cedula = Column(String(50), default="N/A")
    correo = Column(String(100), default="N/A")
    telefono = Column(String(50), default="N/A")
    direccion = Column(Text, default="N/A")
    canal_origen = Column(String(50), default="Tienda Física")
    vendedor_asignado = Column(String(100), default="Carlos Méndez")
    comentarios = Column(Text, default="")
    estado_lead = Column(String(30), default="CLIENTE_ACTIVO")
    creado_en = Column(DateTime, default=datetime.utcnow)

class DBFactura(Base):
    __tablename__ = "facturas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    consecutivo = Column(String(50), unique=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    cliente_nombre = Column(String(150), default="Cliente General")
    cliente_cedula = Column(String(50), default="N/A")
    cliente_correo = Column(String(100), default="N/A")
    cliente_telefono = Column(String(50), default="N/A")
    cliente_direccion = Column(String(200), default="N/A")
    vendedor_nombre = Column(String(100), default="Vendedor de Turno")
    metodo_pago = Column(String(50), default="SINPE_MOVIL")
    numero_comprobante = Column(String(100), default="")
    voucher_ruta = Column(String(255), nullable=True)
    subtotal = Column(Float, default=0.0)
    descuento = Column(Float, default=0.0)
    iva = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    items_json = Column(Text, default="[]")
    pdf_ruta = Column(String(255), nullable=True)

class DBProformaSeguimiento(Base):
    __tablename__ = "proformas_seguimiento"
    id = Column(Integer, primary_key=True, autoincrement=True)
    consecutivo = Column(String(50), unique=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    fecha_alarma = Column(DateTime, nullable=True) # Fecha y hora para la alarma de seguimiento
    alarma_activa = Column(Boolean, default=True)
    cliente_id = Column(Integer, nullable=True)
    cliente_nombre = Column(String(150), default="Prospecto")
    cliente_telefono = Column(String(50), default="")
    cliente_correo = Column(String(100), default="")
    canal_origen = Column(String(50), default="WhatsApp")
    vendedor_nombre = Column(String(100), default="Vendedor")
    subtotal = Column(Float, default=0.0)
    descuento = Column(Float, default=0.0)
    iva = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    items_json = Column(Text, default="[]")
    estado = Column(String(30), default="PENDIENTE_PAGO")
    notas_seguimiento = Column(Text, default="")
    pdf_ruta = Column(String(255), nullable=True)

class DBApartado(Base):
    __tablename__ = "apartados"
    id = Column(Integer, primary_key=True, autoincrement=True)
    consecutivo = Column(String(50), unique=True, index=True)
    cliente_id = Column(Integer, nullable=True)
    cliente_nombre = Column(String(150), nullable=False)
    cliente_telefono = Column(String(50), default="")
    cliente_cedula = Column(String(50), default="")
    vendedor_nombre = Column(String(100), default="Carlos Méndez")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_limite = Column(DateTime, nullable=True)
    total = Column(Float, default=0.0)
    saldo_pendiente = Column(Float, default=0.0)
    estado = Column(String(30), default="PENDIENTE") # PENDIENTE, LIQUIDADO, CANCELADO
    items_json = Column(Text, default="[]")
    notas = Column(Text, default="")

class DBAbonoApartado(Base):
    __tablename__ = "abonos_apartados"
    id = Column(Integer, primary_key=True, autoincrement=True)
    apartado_id = Column(Integer, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    monto = Column(Float, nullable=False)
    metodo_pago = Column(String(50), default="SINPE_MOVIL")
    numero_comprobante = Column(String(100), default="")
    notas = Column(String(200), default="")

class DBChatLead(Base):
    __tablename__ = "crm_chats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_nombre = Column(String(100), default="Prospecto WhatsApp")
    telefono = Column(String(50), default="+506 8888-0000")
    canal = Column(String(30), default="WhatsApp") # WhatsApp, Instagram DM
    estado = Column(String(30), default="BOT_CALIFICANDO") # BOT_CALIFICANDO, ATENCION_HUMANA, CERRADO
    paso_bot = Column(Integer, default=1)
    # Calificación recopilada: prenda_interes, talla, color, tipo_entrega, metodo_pago
    datos_calificacion_json = Column(Text, default="{}")
    mensajes_json = Column(Text, default="[]")
    ultimo_mensaje = Column(String(255), default="")
    actualizado_en = Column(DateTime, default=datetime.utcnow)

class DBCrmAtajo(Base):
    __tablename__ = "crm_atajos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    comando = Column(String(50), nullable=False) # ej: /saludo, /sinpe, /audio1
    titulo = Column(String(100), nullable=False)
    tipo = Column(String(20), default="texto") # texto o audio
    contenido = Column(Text, nullable=False) # texto o audio url
    duracion = Column(String(20), default="")
    creado_en = Column(DateTime, default=datetime.utcnow)

class DBTicket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(20), unique=True, index=True)
    tienda = Column(String(100), default="Tienda Local")
    categoria = Column(String(50), default="ERROR_SISTEMA")
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=False)
    prioridad = Column(String(20), default="MEDIA")
    estado = Column(String(20), default="ABIERTO")
    fecha = Column(DateTime, default=datetime.utcnow)
    respuesta_lider = Column(Text, default="")

class DBProveedor(Base):
    __tablename__ = "proveedores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    contacto = Column(String(100), default="N/A")
    telefono = Column(String(50), default="N/A")
    correo = Column(String(100), default="N/A")
    cedula_juridica = Column(String(50), default="N/A")
    marcas = Column(String(150), default="General")
    plazo_pago = Column(String(50), default="Contado")
    notas = Column(Text, default="")

class DBFacturaCompra(Base):
    __tablename__ = "facturas_compras"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proveedor_id = Column(Integer, nullable=True)
    proveedor_nombre = Column(String(150), nullable=False)
    numero_factura = Column(String(50), nullable=False)
    fecha = Column(String(30), default=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    monto_total = Column(Float, default=0.0)
    estado = Column(String(30), default="RECIBIDO")
    items_json = Column(Text, default="[]")
    notas = Column(Text, default="")

class DBAjusteInventario(Base):
    __tablename__ = "ajustes_inventario"
    id = Column(Integer, primary_key=True, autoincrement=True)
    producto_id = Column(Integer, nullable=False)
    producto_nombre = Column(String(150), nullable=False)
    sku = Column(String(50), nullable=False)
    tipo_ajuste = Column(String(50), nullable=False) # REGALIA, DANADO, MERMA, CONTEO_FISICO
    cantidad = Column(Integer, nullable=False)
    costo_unitario = Column(Float, default=0.0)
    costo_total = Column(Float, default=0.0)
    usuario = Column(String(100), default="Líder")
    motivo = Column(Text, default="")
    fecha = Column(String(30), default=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

class DBGastoTienda(Base):
    __tablename__ = "gastos_tienda"
    id = Column(Integer, primary_key=True, autoincrement=True)
    categoria = Column(String(50), nullable=False) # PACKAGING, ETIQUETAS, OPERATIVO, ENVIOS, OTROS
    concepto = Column(String(200), nullable=False)
    monto = Column(Float, nullable=False)
    fecha = Column(String(30), default=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    responsable = Column(String(100), default="Administración")
    comprobante_url = Column(String(255), default="")
    notas = Column(Text, default="")

class DBUsuarioSistema(Base):
    __tablename__ = "usuarios_sistema"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    rol = Column(String(50), nullable=False) # DUENO, ADMINISTRADOR, JEFE_BODEGA, VENDEDOR
    pin_seguridad = Column(String(20), default="1234")
    permisos_json = Column(Text, default="{}")
    activo = Column(Integer, default=1)
    password = Column(String(100), default="123456")
    is_master = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

def check_sqlite_schema():
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE configuracion ADD COLUMN color_fondo VARCHAR(20) DEFAULT '#080c14'"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE configuracion ADD COLUMN tema_fondo VARCHAR(50) DEFAULT 'Midnight Nebula'"))
            conn.commit()
        except Exception:
            pass

check_sqlite_schema()

def seed_initial_data():
    db = SessionLocal()
    try:
        if not db.query(DBConfiguracion).first():
            db.add(DBConfiguracion())
            db.commit()

        if db.query(DBProductoWMS).count() == 0:
            productos_seed = [
                DBProductoWMS(sku="HD-OVR-BLK-M", nombre="Hoodie Cyberpunk Oversize", categoria="Hoodie", talla="M", color="Negro Asfalto", tono="Monocromático", ubicacion="Rack A-01", stock=18, stock_apartado=2, precio=22000, costo=12000, imagen_url="https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=400&q=80"),
                DBProductoWMS(sku="HD-OVR-BGE-L", nombre="Hoodie Cyberpunk Oversize", categoria="Hoodie", talla="L", color="Beige Desierto", tono="Tierra", ubicacion="Rack A-02", stock=11, stock_apartado=1, precio=22000, costo=12000, imagen_url="https://images.unsplash.com/photo-1509967419530-da38b4704bc6?w=400&q=80"),
                DBProductoWMS(sku="CRG-PNT-KHK-32", nombre="Pantalón Cargo Táctico", categoria="Pantalón", talla="32", color="Caqui Militar", tono="Tierra", ubicacion="Rack B-04", stock=24, stock_apartado=0, precio=26500, costo=15000, imagen_url="https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400&q=80"),
                DBProductoWMS(sku="TSH-MIN-WHT-S", nombre="Camiseta Boxy Minimal", categoria="Camiseta", talla="S", color="Blanco Crudo", tono="Monocromático", ubicacion="Caja C-11", stock=32, stock_apartado=4, precio=12500, costo=6000, imagen_url="https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=400&q=80"),
                DBProductoWMS(sku="BLS-CRW-YEL-M", nombre="Blusa Crop Neon Rave", categoria="Blusa", talla="M", color="Amarillo Neón", tono="Neón", ubicacion="Caja D-02", stock=4, stock_apartado=0, precio=14000, costo=7000, imagen_url="https://images.unsplash.com/photo-1534126511673-b6899657816a?w=400&q=80")
            ]
            db.add_all(productos_seed)
            db.commit()

        if db.query(DBCliente).count() == 0:
            clientes_seed = [
                DBCliente(nombre="Mariana Solís Mora", cedula="1-1452-0982", correo="mariana.solis@correo.com", telefono="+506 8712-4490", direccion="Curridabat, San José", canal_origen="Instagram DM", vendedor_asignado="Laura Chaves", comentarios="Interesada en Hoodies Oversize. Prefiere pagar por SINPE."),
                DBCliente(nombre="Distribuidora Textil S.A.", cedula="3-101-789456", correo="compras@textilcr.com", telefono="+506 2222-8900", direccion="Pavas, San José", canal_origen="WhatsApp", vendedor_asignado="Carlos Méndez", comentarios="Cliente corporativo mayorista. Requiere código de actividad económica.")
            ]
            db.add_all(clientes_seed)
            db.commit()

        if db.query(DBProformaSeguimiento).count() == 0:
            fecha_hoy = datetime.now()
            prof_seed = DBProformaSeguimiento(
                consecutivo="PRF-00001",
                cliente_nombre="Mariana Solís Mora",
                cliente_telefono="+506 8712-4490",
                cliente_correo="mariana.solis@correo.com",
                canal_origen="Instagram DM",
                vendedor_nombre="Laura Chaves",
                subtotal=22000,
                iva=2860,
                total=24860,
                items_json=json.dumps([{"sku": "HD-OVR-BLK-M", "nombre": "Hoodie Cyberpunk Oversize", "cantidad": 1, "precio_unitario": 22000, "subtotal": 22000}]),
                notas_seguimiento="Le gustó el Hoodie Negro M. Le pagan el viernes y confirma por SINPE.",
                fecha_alarma=fecha_hoy + timedelta(hours=4),
                alarma_activa=True,
                estado="PENDIENTE_PAGO"
            )
            db.add(prof_seed)
            db.commit()

        if db.query(DBApartado).count() == 0:
            apt = DBApartado(
                consecutivo="APT-00001",
                cliente_nombre="Esteban Vargas Quirós",
                cliente_telefono="+506 8321-9988",
                cliente_cedula="1-1189-0234",
                vendedor_nombre="Carlos Méndez",
                fecha_creacion=datetime.now() - timedelta(days=5),
                fecha_limite=datetime.now() + timedelta(days=25),
                total=26500.0,
                saldo_pendiente=16500.0,
                estado="PENDIENTE",
                items_json=json.dumps([{"sku": "CRG-PNT-KHK-32", "nombre": "Pantalón Cargo Táctico", "talla": "32", "color": "Caqui", "cantidad": 1, "precio": 26500}]),
                notas="Apartado a 30 días. Primer abono de ₡10,000 en efectivo."
            )
            db.add(apt)
            db.commit()
            db.refresh(apt)

            abono1 = DBAbonoApartado(
                apartado_id=apt.id,
                fecha=datetime.now() - timedelta(days=5),
                monto=10000.0,
                metodo_pago="EFECTIVO",
                numero_comprobante="REC-001",
                notas="Abono inicial al momento del apartado"
            )
            db.add(abono1)
            db.commit()

        if db.query(DBChatLead).count() == 0:
            chat_ejemplo = DBChatLead(
                cliente_nombre="Valeria Méndez",
                telefono="+506 8920-3311",
                canal="WhatsApp",
                estado="BOT_CALIFICANDO",
                paso_bot=2,
                datos_calificacion_json=json.dumps({
                    "prenda": "Hoodie Cyberpunk Oversize",
                    "talla": "Pendiente",
                    "envio": "Pendiente",
                    "pago": "SINPE Móvil"
                }),
                mensajes_json=json.dumps([
                    {"remitente": "cliente", "texto": "¡Hola! Vi en Instagram los hoodies oversize, ¿tienen disponibles?", "hora": "10:15"},
                    {"remitente": "bot", "texto": "¡Hola Valeria! 👋 Te damos la bienvenida a NEXO BOUTIQUE. Con gusto te ayudo. ¿Qué talla y tono buscas (ej. M en Negro o L en Beige)?", "hora": "10:15"},
                    {"remitente": "cliente", "texto": "Busco en talla M color Negro Asfalto por favor.", "hora": "10:16"}
                ]),
                ultimo_mensaje="Busco en talla M color Negro Asfalto por favor.",
                actualizado_en=datetime.now()
            )
            db.add(chat_ejemplo)
            db.commit()

        if db.query(DBTicket).count() == 0:
            db.add(DBTicket(codigo="TCK-101", tienda="NEXO BOUTIQUE", categoria="ERROR_SISTEMA", titulo="Comprobante SINPE requiere respaldo PDF", descripcion="El cliente solicitó copia digital de respaldo por correo.", prioridad="ALTA", estado="ABIERTO"))
            db.commit()
    finally:
        db.close()

seed_initial_data()

# ==========================================
# APLICACIÓN FASTAPI
# ==========================================
app = FastAPI(title="NEBULOSA | INGENIERÍA & AUTOMATIZACIÓN", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

try:
    from backend.app.services.factura_pdf_service import generar_pdf_factura, enviar_factura_correo
    from backend.app.services.gemini_analytics_service import analizar_tendencias_wms_con_gemini
    from backend.app.services.reporte_excel_service import generar_reporte_excel_completo
except ImportError:
    from app.services.factura_pdf_service import generar_pdf_factura, enviar_factura_correo
    from app.services.gemini_analytics_service import analizar_tendencias_wms_con_gemini
    from app.services.reporte_excel_service import generar_reporte_excel_completo

# ==========================================
# 1. WMS: INVENTARIO, FOTOS Y EDICIÓN COMPLETA
# ==========================================
@app.get("/api/wms/productos")
def listar_productos_wms(db: Session = Depends(get_db)):
    return db.query(DBProductoWMS).order_by(DBProductoWMS.id.desc()).all()

class ProductoWMSCreate(BaseModel):
    sku: Optional[str] = None
    nombre: str
    categoria: Optional[str] = "General"
    talla: Optional[str] = "Estándar"
    color: Optional[str] = "N/A"
    tono: Optional[str] = "Neutro"
    ubicacion: Optional[str] = "Estante Principal"
    stock: int = 0
    stock_apartado: int = 0
    precio: float
    costo: float = 0.0
    margen_utilidad: Optional[float] = 50.0
    proveedor: Optional[str] = "Proveedor General"
    dias_rotacion: Optional[int] = 12
    imagen_url: Optional[str] = None

@app.post("/api/wms/productos")
def crear_producto_wms(prod: ProductoWMSCreate, db: Session = Depends(get_db)):
    sku_val = (prod.sku or "").strip().upper()
    if not sku_val:
        # Generar SKU automático único de 6 caracteres con prefijo NX-
        import random, string
        while True:
            generated = "NX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not db.query(DBProductoWMS).filter(DBProductoWMS.sku == generated).first():
                sku_val = generated
                break
    else:
        existente = db.query(DBProductoWMS).filter(DBProductoWMS.sku == sku_val).first()
        if existente:
            raise HTTPException(status_code=400, detail="El SKU ya existe en bodega.")

    data = prod.dict()
    data["sku"] = sku_val
    if (data.get("precio") is None or data.get("precio") <= 0) and data.get("costo", 0) > 0:
        margen = data.get("margen_utilidad", 50.0) or 50.0
        subtotal = data["costo"] * (1 + margen / 100.0)
        data["precio"] = round(subtotal * 1.13, 2)

    nuevo = DBProductoWMS(**data)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

class ProductoWMSUpdate(BaseModel):
    sku: Optional[str] = None
    nombre: str
    categoria: Optional[str] = "General"
    talla: Optional[str] = "Estándar"
    color: Optional[str] = "N/A"
    tono: Optional[str] = "Neutro"
    ubicacion: Optional[str] = "Estante Principal"
    stock: int
    stock_apartado: Optional[int] = 0
    precio: float
    costo: Optional[float] = 0.0
    margen_utilidad: Optional[float] = 50.0
    proveedor: Optional[str] = "Proveedor General"
    dias_rotacion: Optional[int] = 12
    imagen_url: Optional[str] = None

@app.put("/api/wms/productos/{prod_id}")
def actualizar_producto_wms_completo(prod_id: int, p: ProductoWMSUpdate, db: Session = Depends(get_db)):
    item = db.query(DBProductoWMS).filter(DBProductoWMS.id == prod_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Producto no encontrado en WMS")
    
    sku_val = (p.sku or "").strip().upper() or item.sku
    if item.sku != sku_val:
        otro = db.query(DBProductoWMS).filter(DBProductoWMS.sku == sku_val, DBProductoWMS.id != prod_id).first()
        if otro:
            raise HTTPException(status_code=400, detail="El nuevo SKU ya está asignado a otro artículo.")

    data = p.dict()
    data["sku"] = sku_val
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item

@app.post("/api/wms/upload-foto")
async def subir_foto_producto(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix or ".jpg"
    foto_name = f"prenda_{int(datetime.now().timestamp())}{ext}"
    dest = PROD_UPLOADS_DIR / foto_name
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {"status": "ok", "url": f"/uploads/productos/{foto_name}"}

@app.put("/api/wms/productos/{prod_id}/stock")
def ajustar_stock(prod_id: int, nuevo_stock: int, db: Session = Depends(get_db)):
    item = db.query(DBProductoWMS).filter(DBProductoWMS.id == prod_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    item.stock = nuevo_stock
    db.commit()
    return {"id": item.id, "sku": item.sku, "stock": item.stock}

@app.delete("/api/wms/productos/{prod_id}")
def eliminar_producto_wms(prod_id: int, db: Session = Depends(get_db)):
    item = db.query(DBProductoWMS).filter(DBProductoWMS.id == prod_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Producto no encontrado en WMS")
    nombre_prod = item.nombre
    db.delete(item)
    db.commit()
    return {"status": "ok", "message": f"Producto '{nombre_prod}' eliminado correctamente de WMS."}

# ==========================================
# 1.1 PROVEEDORES & COMPRAS (INGRESO MERCADERÍA)
# ==========================================
class ProveedorCreate(BaseModel):
    nombre: str
    contacto: Optional[str] = "N/A"
    telefono: Optional[str] = "N/A"
    correo: Optional[str] = "N/A"
    cedula_juridica: Optional[str] = "N/A"
    marcas: Optional[str] = "General"
    plazo_pago: Optional[str] = "Contado"
    notas: Optional[str] = ""

@app.get("/api/proveedores")
def listar_proveedores(db: Session = Depends(get_db)):
    return db.query(DBProveedor).order_by(DBProveedor.nombre.asc()).all()

@app.post("/api/proveedores")
def crear_proveedor(p: ProveedorCreate, db: Session = Depends(get_db)):
    nuevo = DBProveedor(**p.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.delete("/api/proveedores/{prov_id}")
def eliminar_proveedor(prov_id: int, db: Session = Depends(get_db)):
    item = db.query(DBProveedor).filter(DBProveedor.id == prov_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    db.delete(item)
    db.commit()
    return {"status": "ok", "message": f"Proveedor '{item.nombre}' eliminado"}

class ItemCompraInput(BaseModel):
    producto_id: int
    cantidad: int
    costo_unitario: float

class CompraCreate(BaseModel):
    proveedor_id: Optional[int] = None
    proveedor_nombre: str
    numero_factura: str
    monto_total: float
    items: List[ItemCompraInput]
    notas: Optional[str] = ""

@app.get("/api/compras")
def listar_compras(db: Session = Depends(get_db)):
    return db.query(DBFacturaCompra).order_by(DBFacturaCompra.id.desc()).all()

@app.post("/api/compras")
def registrar_ingreso_compra(c: CompraCreate, db: Session = Depends(get_db)):
    nueva_compra = DBFacturaCompra(
        proveedor_id=c.proveedor_id,
        proveedor_nombre=c.proveedor_nombre,
        numero_factura=c.numero_factura,
        monto_total=c.monto_total,
        items_json=json.dumps([i.dict() for i in c.items]),
        notas=c.notas or ""
    )
    db.add(nueva_compra)
    
    for it in c.items:
        prod = db.query(DBProductoWMS).filter(DBProductoWMS.id == it.producto_id).first()
        if prod:
            prod.stock += it.cantidad
            if it.costo_unitario > 0:
                prod.costo = it.costo_unitario
                if prod.margen_utilidad and prod.margen_utilidad > 0:
                    sub = prod.costo * (1 + prod.margen_utilidad / 100.0)
                    prod.precio = round(sub * 1.13, 2)
    db.commit()
    db.refresh(nueva_compra)
    return nueva_compra

# ==========================================
# 1.2 AJUSTES DE INVENTARIO (REGALÍAS, DAÑADOS, MERMAS)
# ==========================================
class AjusteInventarioCreate(BaseModel):
    producto_id: int
    tipo_ajuste: str # REGALIA, DANADO, MERMA, CONTEO_FISICO
    cantidad: int
    usuario: Optional[str] = "Líder"
    motivo: Optional[str] = ""

@app.get("/api/inventario/ajustes")
def listar_ajustes_inventario(db: Session = Depends(get_db)):
    return db.query(DBAjusteInventario).order_by(DBAjusteInventario.id.desc()).all()

@app.post("/api/inventario/ajustes")
def crear_ajuste_inventario(a: AjusteInventarioCreate, db: Session = Depends(get_db)):
    prod = db.query(DBProductoWMS).filter(DBProductoWMS.id == a.producto_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if a.tipo_ajuste in ['REGALIA', 'DANADO', 'MERMA']:
        if prod.stock < a.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente ({prod.stock}) para descontar {a.cantidad} unidades.")
        prod.stock -= a.cantidad
    elif a.tipo_ajuste == 'CONTEO_FISICO':
        prod.stock = a.cantidad
        
    costo_unit = prod.costo or 0.0
    costo_tot = round(costo_unit * a.cantidad, 2)
    
    nuevo_ajuste = DBAjusteInventario(
        producto_id=prod.id,
        producto_nombre=prod.nombre,
        sku=prod.sku,
        tipo_ajuste=a.tipo_ajuste,
        cantidad=a.cantidad,
        costo_unitario=costo_unit,
        costo_total=costo_tot,
        usuario=a.usuario or "Líder",
        motivo=a.motivo or ""
    )
    db.add(nuevo_ajuste)
    db.commit()
    db.refresh(nuevo_ajuste)
    return nuevo_ajuste

# ==========================================
# 1.3 GASTOS DE TIENDA & OPERATIVOS
# ==========================================
class GastoTiendaCreate(BaseModel):
    categoria: str # PACKAGING, ETIQUETAS, OPERATIVO, ENVIOS, OTROS
    concepto: str
    monto: float
    responsable: Optional[str] = "Administración"
    comprobante_url: Optional[str] = ""
    notas: Optional[str] = ""

@app.get("/api/gastos")
def listar_gastos(db: Session = Depends(get_db)):
    return db.query(DBGastoTienda).order_by(DBGastoTienda.id.desc()).all()

@app.post("/api/gastos")
def crear_gasto(g: GastoTiendaCreate, db: Session = Depends(get_db)):
    nuevo = DBGastoTienda(**g.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.delete("/api/gastos/{gasto_id}")
def eliminar_gasto(gasto_id: int, db: Session = Depends(get_db)):
    item = db.query(DBGastoTienda).filter(DBGastoTienda.id == gasto_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    db.delete(item)
    db.commit()
    return {"status": "ok", "message": f"Gasto '{item.concepto}' eliminado"}

# ==========================================
# 1.4 GESTIÓN DE USUARIOS Y ROLES (RBAC)
# ==========================================
class UsuarioSistemaCreate(BaseModel):
    username: str
    nombre_completo: str
    rol: str # DUENO, ADMINISTRADOR, JEFE_BODEGA, VENDEDOR
    pin_seguridad: Optional[str] = None
    password: Optional[str] = None
    permisos_json: Optional[str] = "{}"
    activo: Optional[int] = 1
    is_master: Optional[int] = 0

class LoginRequest(BaseModel):
    username: str
    password_or_pin: str

import random
import secrets

@app.post("/api/auth/login")
def login_usuario(req: LoginRequest, db: Session = Depends(get_db)):
    u_clean = req.username.strip().lower()
    p_clean = req.password_or_pin.strip()
    
    # Buscar por username (o por PIN directo si solo puso PIN y hay coincidencia)
    usuario = db.query(DBUsuarioSistema).filter(DBUsuarioSistema.username.ilike(u_clean)).first()
    if not usuario:
        # Fallback para permitir login rápido solo con PIN si username es el PIN o coincide
        usuario = db.query(DBUsuarioSistema).filter(DBUsuarioSistema.pin_seguridad == p_clean).first()
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario o contraseña/PIN incorrectos.")
    
    if getattr(usuario, 'activo', 1) == 0:
        raise HTTPException(status_code=403, detail="Esta cuenta de usuario ha sido suspendida.")
    
    # Validar contraseña o PIN
    valido = False
    if usuario.pin_seguridad and p_clean == str(usuario.pin_seguridad).strip():
        valido = True
    elif getattr(usuario, 'password', None) and p_clean == str(usuario.password).strip():
        valido = True
    elif getattr(usuario, "is_master", 0) == 1 and p_clean == str(usuario.pin_seguridad).strip():
        valido = True
        
    if not valido:
        raise HTTPException(status_code=401, detail="Contraseña o PIN incorrectos.")
        
    return {
        "status": "success",
        "token": f"neb_tok_{secrets.token_hex(16)}",
        "usuario": {
            "id": usuario.id,
            "username": usuario.username,
            "nombre_completo": usuario.nombre_completo,
            "rol": usuario.rol,
            "is_master": getattr(usuario, "is_master", 0),
            "permisos_json": usuario.permisos_json or "{}"
        }
    }

@app.get("/api/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(DBUsuarioSistema).order_by(DBUsuarioSistema.id.asc()).all()

@app.post("/api/usuarios")
def crear_usuario(u: UsuarioSistemaCreate, db: Session = Depends(get_db)):
    existente = db.query(DBUsuarioSistema).filter(DBUsuarioSistema.username == u.username).first()
    if existente:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado.")
    
    u_dict = u.dict()
    # Generar automáticamente contraseña y PIN si no vienen dados
    pass_generado = u_dict.get("password")
    if not pass_generado:
        pass_generado = f"Neb-{random.randint(1000, 9999)}"
        u_dict["password"] = pass_generado
        
    pin_generado = u_dict.get("pin_seguridad")
    if not pin_generado:
        pin_generado = str(random.randint(1000, 9999))
        u_dict["pin_seguridad"] = pin_generado
        
    if u_dict.get("rol") != "DUENO":
        u_dict["is_master"] = 0
        
    nuevo = DBUsuarioSistema(**u_dict)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    
    return {
        "id": nuevo.id,
        "username": nuevo.username,
        "nombre_completo": nuevo.nombre_completo,
        "rol": nuevo.rol,
        "pin_seguridad": nuevo.pin_seguridad,
        "password": pass_generado,
        "is_master": getattr(nuevo, "is_master", 0),
        "credenciales_creadas": {
            "usuario": nuevo.username,
            "password": pass_generado,
            "pin": nuevo.pin_seguridad,
            "rol": nuevo.rol
        }
    }

@app.put("/api/usuarios/{u_id}")
def actualizar_usuario(u_id: int, u: UsuarioSistemaCreate, db: Session = Depends(get_db)):
    item = db.query(DBUsuarioSistema).filter(DBUsuarioSistema.id == u_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Blindaje del usuario maestro
    if getattr(item, "is_master", 0) == 1 or item.id == 1 or item.username in ["isanchez", "lider_isaac", "isaac"]:
        item.nombre_completo = u.nombre_completo
        if u.pin_seguridad:
            item.pin_seguridad = u.pin_seguridad
        if u.password:
            item.password = u.password
        item.rol = "DUENO"
        item.is_master = 1
        item.activo = 1
    else:
        item.nombre_completo = u.nombre_completo
        item.rol = u.rol
        if u.pin_seguridad:
            item.pin_seguridad = u.pin_seguridad
        if u.password:
            item.password = u.password
        item.permisos_json = u.permisos_json
        item.activo = u.activo
        
    db.commit()
    db.refresh(item)
    return item

@app.delete("/api/usuarios/{u_id}")
def eliminar_usuario(u_id: int, db: Session = Depends(get_db)):
    item = db.query(DBUsuarioSistema).filter(DBUsuarioSistema.id == u_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    # Blindaje estricto del usuario del dueño
    if getattr(item, 'is_master', 0) == 1 or item.id == 1 or item.rol == 'DUENO' or item.username in ['isanchez', 'lider_isaac', 'isaac']:
        raise HTTPException(
            status_code=403, 
            detail="ACCESO DENEGADO: El usuario Maestro/Dueño de NEBULOSA es intocable y NO puede ser eliminado."
        )
        
    username_eliminado = item.username
    db.delete(item)
    db.commit()
    return {"status": "ok", "message": f"Usuario '{username_eliminado}' eliminado correctamente"}

# ==========================================
# 1.5 FINANZAS: RESUMEN DE UTILIDAD NETA REAL
# ==========================================
@app.get("/api/finanzas/resumen")
def resumen_financiero_tienda(db: Session = Depends(get_db)):
    facturas = db.query(DBFactura).all()
    total_ventas = sum(f.total or 0.0 for f in facturas)
    total_iva = sum(f.iva or 0.0 for f in facturas)
    subtotal_ventas = sum(f.subtotal or 0.0 for f in facturas)
    
    gastos = db.query(DBGastoTienda).all()
    total_gastos_operativos = sum(g.monto for g in gastos)
    
    prods = db.query(DBProductoWMS).all()
    valor_inventario_costo = sum((p.stock * (p.costo or 0.0)) for p in prods)
    valor_inventario_venta = sum((p.stock * p.precio) for p in prods)
    
    cmv_estimado = round(subtotal_ventas * 0.52, 2)
    utilidad_bruta = round(subtotal_ventas - cmv_estimado, 2)
    utilidad_neta = round(utilidad_bruta - total_gastos_operativos, 2)
    
    return {
        "ventas_totales_con_iva": round(total_ventas, 2),
        "ventas_netas_sin_iva": round(subtotal_ventas, 2),
        "iva_recaudado": round(total_iva, 2),
        "cmv_costo_mercaderia": cmv_estimado,
        "utilidad_bruta": utilidad_bruta,
        "gastos_operativos_tienda": round(total_gastos_operativos, 2),
        "utilidad_neta_real": utilidad_neta,
        "margen_neto_porcentaje": round((utilidad_neta / subtotal_ventas * 100), 1) if subtotal_ventas > 0 else 0.0,
        "valor_inventario_costo": round(valor_inventario_costo, 2),
        "valor_inventario_venta": round(valor_inventario_venta, 2)
    }

# ==========================================
# 2. CRM CLIENTES & LEADS
# ==========================================
@app.get("/api/crm/clientes")
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(DBCliente).order_by(DBCliente.creado_en.desc()).all()

class ClienteCreate(BaseModel):
    nombre: str
    cedula: Optional[str] = "N/A"
    correo: Optional[str] = "N/A"
    telefono: Optional[str] = "N/A"
    direccion: Optional[str] = "N/A"
    canal_origen: Optional[str] = "Tienda Física"
    vendedor_asignado: Optional[str] = "Carlos Méndez"
    comentarios: Optional[str] = ""
    estado_lead: Optional[str] = "CLIENTE_ACTIVO"

@app.post("/api/crm/clientes")
def crear_cliente(cli: ClienteCreate, db: Session = Depends(get_db)):
    nuevo = DBCliente(**cli.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ==========================================
# 3. CRM CHATBOT OMNICANAL (CALIFICACIÓN GUIADA)
# ==========================================
@app.get("/api/crm/chats")
def listar_chats_crm(db: Session = Depends(get_db)):
    return db.query(DBChatLead).order_by(DBChatLead.actualizado_en.desc()).all()

class NuevoChatLeadRequest(BaseModel):
    cliente_nombre: str
    telefono: str
    canal: str = "WhatsApp"
    primer_mensaje: str

@app.post("/api/crm/chats/nuevo-lead")
def recibir_nuevo_lead(data: NuevoChatLeadRequest, db: Session = Depends(get_db)):
    hora_str = datetime.now().strftime("%H:%M")
    mensajes = [
        {"remitente": "cliente", "texto": data.primer_mensaje, "hora": hora_str},
        {"remitente": "bot", "texto": f"¡Hola {data.cliente_nombre}! 👋 Bienvenido/a a NEXO RETAIL. Con gusto te atiendo. ¿Qué tipo de prenda o estilo estás buscando hoy? (Ej: Hoodies Oversize, Pantalones Cargo o Camisetas Boxy)", "hora": hora_str}
    ]
    chat = DBChatLead(
        cliente_nombre=data.cliente_nombre,
        telefono=data.telefono,
        canal=data.canal,
        estado="BOT_CALIFICANDO",
        paso_bot=1,
        datos_calificacion_json=json.dumps({"prenda_buscada": "", "talla": "", "entrega": "", "pago": ""}),
        mensajes_json=json.dumps(mensajes),
        ultimo_mensaje=data.primer_mensaje,
        actualizado_en=datetime.now()
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

class ChatInteraccionRequest(BaseModel):
    texto: str = ""
    es_vendedor: bool = False
    tipo: str = "texto" # texto, audio, imagen, pdf
    media_url: Optional[str] = None
    duracion: Optional[str] = None
    archivo_nombre: Optional[str] = None

@app.post("/api/crm/chats/{chat_id}/mensaje")
def responder_chat_crm(chat_id: int, req: ChatInteraccionRequest, db: Session = Depends(get_db)):
    chat = db.query(DBChatLead).filter(DBChatLead.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    mensajes = json.loads(chat.mensajes_json or "[]")
    calif = json.loads(chat.datos_calificacion_json or "{}")
    hora = datetime.now().strftime("%H:%M")

    msg_obj = {
        "remitente": "vendedor" if req.es_vendedor else "cliente",
        "texto": req.texto,
        "tipo": req.tipo,
        "media_url": req.media_url,
        "duracion": req.duracion,
        "archivo_nombre": req.archivo_nombre,
        "hora": hora
    }

    if req.es_vendedor:
        # Mensaje de intervención humana (Asesor Comercial)
        mensajes.append(msg_obj)
        if chat.estado == "BOT_CALIFICANDO":
            chat.estado = "ATENCION_HUMANA"
        
        if req.tipo == "audio":
            chat.ultimo_mensaje = f"[Asesor Audio {req.duracion or '0:15'}]"
        elif req.tipo == "imagen":
            chat.ultimo_mensaje = "[Asesor Foto]"
        elif req.tipo == "pdf":
            chat.ultimo_mensaje = f"[Asesor PDF: {req.archivo_nombre or 'Documento'}]"
        else:
            chat.ultimo_mensaje = f"[Asesor]: {req.texto}"
    else:
        # Mensaje del cliente / prospecto
        mensajes.append(msg_obj)
        if req.tipo == "audio":
            chat.ultimo_mensaje = f"[Cliente Audio {req.duracion or '0:12'}]"
        elif req.tipo == "imagen":
            chat.ultimo_mensaje = "[Cliente Foto]"
        elif req.tipo == "pdf":
            chat.ultimo_mensaje = f"[Cliente PDF: {req.archivo_nombre or 'Documento'}]"
        else:
            chat.ultimo_mensaje = req.texto

        paso = chat.paso_bot
        # Solo responde el bot automatizado si la conversación está en fase de calificación y es mensaje de texto
        if chat.estado == "BOT_CALIFICANDO" and req.tipo == "texto":
            if paso == 1:
                calif["articulo_buscado"] = req.texto
                calif["prenda_buscada"] = req.texto
                chat.paso_bot = 2
                bot_reply = "¡Excelente elección! 📦 ¿Qué modelo, variante, medida o especificación buscas? Te confirmo disponibilidad de inmediato en el sistema."
                mensajes.append({"remitente": "bot", "texto": bot_reply, "tipo": "texto", "hora": hora})
            elif paso == 2:
                calif["talla_color"] = req.texto
                chat.paso_bot = 3
                bot_reply = "¡Perfecto, tenemos disponibilidad confirmada! 🚚 ¿Deseas entrega o envío a tu ubicación, o prefieres retirar en nuestras instalaciones?"
                mensajes.append({"remitente": "bot", "texto": bot_reply, "tipo": "texto", "hora": hora})
            elif paso == 3:
                calif["entrega"] = req.texto
                chat.paso_bot = 4
                bot_reply = "Excelente. Aceptamos SINPE Móvil, tarjeta de crédito/débito, transferencia bancaria, efectivo o plan de apartado a 30 días. ¿Cuál método de pago te resulta más cómodo?"
                mensajes.append({"remitente": "bot", "texto": bot_reply, "tipo": "texto", "hora": hora})
            elif paso == 4:
                calif["pago"] = req.texto
                chat.paso_bot = 5
                chat.estado = "ATENCION_HUMANA" # Se transfiere automáticamente al Asesor
                bot_reply = "¡Listo! Ya registré todos tus requerimientos y transferí la conversación a nuestro Asesor Comercial para el cierre formal y emisión de tu proforma. 💼"
                mensajes.append({"remitente": "bot", "texto": bot_reply, "tipo": "texto", "hora": hora})
        elif chat.estado == "ATENCION_HUMANA":
            if req.tipo == "texto":
                chat.ultimo_mensaje = f"[Cliente]: {req.texto}"

    chat.mensajes_json = json.dumps(mensajes)
    chat.datos_calificacion_json = json.dumps(calif)
    chat.actualizado_en = datetime.now()
    db.commit()
    db.refresh(chat)
    return chat

class EstadoCierreRequest(BaseModel):
    estado: str # VENDIDO, RESUELTO, PERDIDO, SEGUIMIENTO
    nota: Optional[str] = ""

@app.put("/api/crm/chats/{chat_id}/estado-cierre")
def actualizar_estado_cierre_crm(chat_id: int, req: EstadoCierreRequest, db: Session = Depends(get_db)):
    chat = db.query(DBChatLead).filter(DBChatLead.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    chat.estado = req.estado
    calif = json.loads(chat.datos_calificacion_json or "{}")
    calif["estado_cierre"] = req.estado
    if req.nota:
        calif["nota_cierre"] = req.nota
    chat.datos_calificacion_json = json.dumps(calif)
    chat.actualizado_en = datetime.now()

    mensajes = json.loads(chat.mensajes_json or "[]")
    hora = datetime.now().strftime("%H:%M")
    estado_labels = {
        "VENDIDO": "🟢 OPORTUNIDAD MARCADA COMO VENDIDA / GANADA",
        "RESUELTO": "🔵 CONSULTA MARCADA COMO RESUELTA",
        "PERDIDO": "🔴 OPORTUNIDAD MARCADA COMO PERDIDA",
        "SEGUIMIENTO": "🟡 OPORTUNIDAD EN SEGUIMIENTO ACTIVO"
    }
    mensajes.append({
        "remitente": "sistema",
        "texto": f"{estado_labels.get(req.estado, req.estado)}. {req.nota or ''}".strip(),
        "tipo": "sistema",
        "hora": hora
    })
    chat.mensajes_json = json.dumps(mensajes)
    chat.ultimo_mensaje = f"[{req.estado}]"
    db.commit()
    db.refresh(chat)
    return chat

@app.get("/api/crm/chats/{chat_id}/expediente-legal")
def descargar_expediente_legal_crm(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(DBChatLead).filter(DBChatLead.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    calif = json.loads(chat.datos_calificacion_json or "{}")
    mensajes = json.loads(chat.mensajes_json or "[]")

    import hashlib
    content_hash = hashlib.sha256(f"{chat.id}-{chat.cliente_nombre}-{len(mensajes)}-{chat.actualizado_en}".encode()).hexdigest().upper()

    expediente = f"""================================================================================
EXPEDIENTE DE TRAZABILIDAD Y AUDITORÍA LEGAL CRM - LEY 8968 (COSTA RICA)
PROTECCIÓN DE LA PERSONA FRENTE AL TRATAMIENTO DE SUS DATOS PERSONALES
================================================================================
Identificador de Expediente: EXP-CRM-{chat.id:06d}
Hash Criptográfico de Integridad (SHA-256): {content_hash}
Fecha y Hora de Emisión: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Ambiente: Certificación Oficial Nexo Business OS

1. DATOS DEL TITULAR / PROSPECTO:
--------------------------------------------------------------------------------
Nombre / Titular: {chat.cliente_nombre}
Teléfono / Identificador Canal: {chat.telefono}
Canal de Origen: {chat.canal}
Consentimiento Informado Registrado: SÍ - Activo bajo consentimiento expreso en canal.
Finalidad del Tratamiento: Emisión de cotizaciones, proformas y gestión de facturación comercial.

2. ESPECIFICACIÓN COMERCIAL & CALIFICACIÓN TÉCNICA:
--------------------------------------------------------------------------------
Artículo / Servicio de Interés: {calif.get('articulo_buscado') or calif.get('prenda_buscada') or 'N/A'}
Variante / Especificación: {calif.get('talla_color') or 'N/A'}
Modalidad de Entrega Acordada: {calif.get('entrega') or 'N/A'}
Método de Pago Seleccionado: {calif.get('pago') or 'N/A'}
Estado del Cierre: {chat.estado}

3. BITÁCORA CRONOLÓGICA DE INTERACCIONES Y ACUERDOS:
--------------------------------------------------------------------------------
"""
    for idx, m in enumerate(mensajes, start=1):
        remitente_tag = "PROSPECTO" if m.get("remitente") == "cliente" else ("BOT IA" if m.get("remitente") == "bot" else ("ASESOR HUMANO" if m.get("remitente") == "vendedor" else "SISTEMA"))
        tipo_str = f" [{m.get('tipo', 'texto').upper()}]" if m.get('tipo') != 'texto' else ""
        expediente += f"[{idx:03d}] {m.get('hora', '--:--')} | {remitente_tag}{tipo_str}: {m.get('texto', '')}\n"

    expediente += f"""
================================================================================
CERTIFICACIÓN DE INMUTABILIDAD:
El presente expediente constituye prueba documental electrónica de las interacciones
comerciales sostenidas entre la empresa y el cliente, con validez jurídica según la
Ley de Certificados, Firmas Digitales y Documentos Electrónicos (Ley N° 8454).
================================================================================
"""
    return PlainTextResponse(content=expediente, media_type="text/plain; charset=utf-8", headers={
        "Content-Disposition": f"attachment; filename=Expediente_Legal_Lead_{chat.id}.txt"
    })

@app.post("/api/crm/upload-multimedia")
async def subir_multimedia_crm(file: UploadFile = File(...)):
    import uuid
    ext = Path(file.filename).suffix
    filename = f"crm_{uuid.uuid4().hex[:10]}{ext}"
    dest = UPLOADS_DIR / filename
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {
        "url": f"/uploads/{filename}",
        "archivo_nombre": file.filename,
        "tipo": "audio" if ext.lower() in [".mp3", ".wav", ".ogg", ".m4a", ".webm"] else ("imagen" if ext.lower() in [".jpg", ".jpeg", ".png", ".webp"] else "pdf")
    }

class NuevoAtajoRequest(BaseModel):
    comando: str # ej: /saludo, /sinpe, /horario
    titulo: str
    tipo: str = "texto" # texto o audio
    contenido: str
    duracion: Optional[str] = ""

@app.get("/api/crm/atajos")
def listar_atajos_crm(db: Session = Depends(get_db)):
    atajos = db.query(DBCrmAtajo).all()
    if not atajos:
        seed = [
            DBCrmAtajo(comando="/saludo", titulo="Saludo Formal de Bienvenida", tipo="texto", contenido="¡Hola! Gracias por comunicarte con nosotros. ¿En qué podemos asesorarte el día de hoy?"),
            DBCrmAtajo(comando="/sinpe", titulo="Datos de Pago SINPE Móvil", tipo="texto", contenido="📲 Nuestro número oficial de SINPE Móvil es: +506 8888-9999 a nombre de la empresa. Por favor envíanos el comprobante una vez realizado."),
            DBCrmAtajo(comando="/catalogo", titulo="Catálogo Digital WMS", tipo="texto", contenido="📦 Contamos con disponibilidad inmediata en bodega. Te comparto las opciones disponibles con entrega rápida."),
            DBCrmAtajo(comando="/garantia", titulo="Garantía & Factura Electrónica", tipo="texto", contenido="🛡️ Todos nuestros productos cuentan con garantía formal por escrito y emitimos factura electrónica autorizada por el Ministerio de Hacienda."),
            DBCrmAtajo(comando="/descuento", titulo="Oferta Comercial & Cierre", tipo="texto", contenido="🎉 Te hemos aplicado una cortesía comercial especial con descuento en tu orden para despacharla hoy mismo."),
            DBCrmAtajo(comando="/audio_bienvenida", titulo="🎙️ Audio de Bienvenida Corporativa", tipo="audio", contenido="https://actions.google.com/sounds/v1/communication/incoming_call.ogg", duracion="0:14"),
            DBCrmAtajo(comando="/audio_despacho", titulo="🎙️ Audio Confirmación de Despacho", tipo="audio", contenido="https://actions.google.com/sounds/v1/communication/answering_machine_greeting.ogg", duracion="0:18")
        ]
        db.add_all(seed)
        db.commit()
        atajos = db.query(DBCrmAtajo).all()
    return atajos

@app.post("/api/crm/atajos")
def crear_atajo_crm(req: NuevoAtajoRequest, db: Session = Depends(get_db)):
    cmd = req.comando.strip()
    if not cmd.startswith("/"):
        cmd = f"/{cmd}"
    nuevo = DBCrmAtajo(
        comando=cmd,
        titulo=req.titulo,
        tipo=req.tipo,
        contenido=req.contenido,
        duracion=req.duracion or ("0:15" if req.tipo == "audio" else "")
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.delete("/api/crm/atajos/{atajo_id}")
def eliminar_atajo_crm(atajo_id: int, db: Session = Depends(get_db)):
    at = db.query(DBCrmAtajo).filter(DBCrmAtajo.id == atajo_id).first()
    if not at:
        raise HTTPException(status_code=404, detail="Atajo no encontrado")
    db.delete(at)
    db.commit()
    return {"ok": True}

@app.post("/api/crm/chats/{chat_id}/reiniciar-bot")
def reiniciar_bot_crm(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(DBChatLead).filter(DBChatLead.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    hora = datetime.now().strftime("%H:%M")
    chat.estado = "BOT_CALIFICANDO"
    chat.paso_bot = 1
    chat.datos_calificacion_json = json.dumps({
        "articulo_buscado": "",
        "prenda_buscada": "",
        "talla_color": "",
        "entrega": "",
        "pago": ""
    })
    chat.mensajes_json = json.dumps([
        {
            "remitente": "bot",
            "texto": f"¡Hola {chat.cliente_nombre}! 👋 Bienvenido/a a nuestro catálogo. ¿Qué producto o servicio buscas el día de hoy?",
            "tipo": "texto",
            "hora": hora
        }
    ])
    chat.ultimo_mensaje = "Bot de calificación reiniciado"
    chat.actualizado_en = datetime.now()
    db.commit()
    db.refresh(chat)
    return chat

@app.put("/api/crm/chats/{chat_id}/toggle-estado")
def toggle_estado_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(DBChatLead).filter(DBChatLead.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    chat.estado = "ATENCION_HUMANA" if chat.estado == "BOT_CALIFICANDO" else "BOT_CALIFICANDO"
    chat.actualizado_en = datetime.now()
    db.commit()
    db.refresh(chat)
    return chat

# ==========================================
# 4. FACTURACIÓN POS & HISTORIAL FISCAL
# ==========================================
class ItemFactura(BaseModel):
    id: int
    sku: str
    nombre: str
    talla: str
    color: str
    cantidad: int
    precio_unitario: float
    subtotal: float

class FacturaRequest(BaseModel):
    cliente_id: Optional[int] = None
    cliente_nombre: str = "Cliente General"
    cliente_cedula: str = "N/A"
    cliente_correo: str = "N/A"
    cliente_telefono: str = "N/A"
    cliente_direccion: str = "N/A"
    vendedor_nombre: str = "Vendedor de Turno"
    metodo_pago: str = "SINPE_MOVIL"
    numero_comprobante: str = ""
    subtotal: float
    descuento: float = 0.0
    iva: float
    total: float
    items: List[ItemFactura]

@app.post("/api/pos/facturar")
def emitir_factura(fac: FacturaRequest, db: Session = Depends(get_db)):
    for item in fac.items:
        prod = db.query(DBProductoWMS).filter(DBProductoWMS.id == item.id).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Producto {item.sku} no existe en WMS.")
        if prod.stock < item.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {prod.nombre} (Disponibles: {prod.stock}).")
        prod.stock -= item.cantidad

    consecutivo_num = db.query(DBFactura).count() + 1
    consecutivo_str = f"F-{consecutivo_num:05d}"

    # Precios contemplan IVA incluido:
    total_bruto = sum(i.precio_unitario * i.cantidad for i in fac.items)
    descuento = float(fac.descuento or 0.0)
    total_final = max(0.0, total_bruto - descuento)
    subtotal_base = round(total_final / 1.13, 2)
    iva_monto = round(total_final - subtotal_base, 2)

    config = db.query(DBConfiguracion).first()
    datos_pdf = {
        "consecutivo": consecutivo_str,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "color_primario": config.color_primario if config else "#111827",
        "moneda": "CRC",
        "vendedor_nombre": fac.vendedor_nombre,
        "metodo_pago": fac.metodo_pago,
        "comprobante_banco": fac.numero_comprobante or ("DATÁFONO / TARJETA" if fac.metodo_pago == "TARJETA" else "EFECTIVO"),
        "tienda": {
            "nombre": config.nombre_tienda if config else "NEXO RETAIL",
            "cedula": config.cedula_fiscal if config else "3-101-948271",
            "telefono": config.telefono if config else "+506 8888-8888",
            "direccion": config.direccion if config else "San José, Costa Rica",
            "actividad": config.codigo_actividad if config else "477101 - Venta al por menor de prendas"
        },
        "cliente": {
            "nombre": fac.cliente_nombre,
            "cedula": fac.cliente_cedula,
            "correo": fac.cliente_correo,
            "telefono": fac.cliente_telefono,
            "direccion": fac.cliente_direccion
        },
        "lineas": [i.dict() for i in fac.items],
        "subtotal": subtotal_base,
        "descuento": descuento,
        "iva": iva_monto,
        "total": total_final
    }

    try:
        ruta_pdf = generar_pdf_factura(datos_pdf)
    except Exception as e:
        ruta_pdf = ""

    db_fac = DBFactura(
        consecutivo=consecutivo_str,
        cliente_nombre=fac.cliente_nombre,
        cliente_cedula=fac.cliente_cedula,
        cliente_correo=fac.cliente_correo,
        cliente_telefono=fac.cliente_telefono,
        cliente_direccion=fac.cliente_direccion,
        vendedor_nombre=fac.vendedor_nombre,
        metodo_pago=fac.metodo_pago,
        numero_comprobante=fac.numero_comprobante,
        subtotal=subtotal_base,
        descuento=descuento,
        iva=iva_monto,
        total=total_final,
        items_json=json.dumps([i.dict() for i in fac.items]),
        pdf_ruta=ruta_pdf
    )
    db.add(db_fac)
    db.commit()
    db.refresh(db_fac)

    return {
        "status": "success",
        "factura_id": db_fac.id,
        "consecutivo": consecutivo_str,
        "pdf_url": f"/api/pos/facturas/{db_fac.id}/pdf",
        "total": fac.total
    }

@app.get("/api/pos/facturas")
def listar_historial_facturas(db: Session = Depends(get_db)):
    facturas = db.query(DBFactura).order_by(DBFactura.fecha.desc()).all()
    resultado = []
    for f in facturas:
        items = json.loads(f.items_json or "[]")
        resultado.append({
            "id": f.id,
            "consecutivo": f.consecutivo,
            "fecha": f.fecha.strftime("%d/%m/%Y %H:%M") if f.fecha else "",
            "cliente_nombre": f.cliente_nombre,
            "cliente_cedula": f.cliente_cedula,
            "vendedor_nombre": f.vendedor_nombre,
            "metodo_pago": f.metodo_pago,
            "numero_comprobante": f.numero_comprobante,
            "subtotal": f.subtotal,
            "descuento": f.descuento or 0.0,
            "iva": f.iva,
            "total": f.total,
            "items_count": len(items),
            "pdf_url": f"/api/pos/facturas/{f.id}/pdf" if f.pdf_ruta else None
        })
    return resultado


def resolver_ruta_pdf_factura(fac, db: Session) -> str:
    if fac.pdf_ruta and os.path.exists(fac.pdf_ruta):
        return fac.pdf_ruta
    nombre_fact = f"Factura_{fac.consecutivo}.pdf"
    candidato = PDF_DIR / nombre_fact
    if candidato.exists():
        fac.pdf_ruta = str(candidato)
        db.commit()
        return str(candidato)
    config = db.query(DBConfiguracion).first()
    items = []
    try:
        items = json.loads(fac.items_json) if fac.items_json else []
    except Exception:
        items = []
    datos_pdf = {
        "consecutivo": fac.consecutivo,
        "fecha": fac.fecha.strftime("%d/%m/%Y %H:%M") if fac.fecha else datetime.now().strftime("%d/%m/%Y %H:%M"),
        "color_primario": config.color_primario if config else "#111827",
        "moneda": "CRC",
        "vendedor_nombre": fac.vendedor_nombre or "Vendedor",
        "metodo_pago": fac.metodo_pago or "EFECTIVO",
        "comprobante_banco": fac.comprobante_sinpe or "N/A",
        "tienda": {
            "nombre": config.nombre_tienda if config else "NEBULOSA INGENIERÍA Y AUTOMATIZACIÓN",
            "cedula": config.cedula_fiscal if config else "3-101-948271",
            "telefono": config.telefono if config else "+506 8888-8888",
            "direccion": config.direccion if config else "San José, Costa Rica",
            "actividad": config.codigo_actividad if config else "477101 - Venta prendas"
        },
        "cliente": {
            "nombre": fac.cliente_nombre or "Consumidor Final",
            "cedula": fac.cliente_cedula or "999999999",
            "correo": fac.cliente_correo or "",
            "telefono": fac.cliente_telefono or "",
            "direccion": "San José, Costa Rica"
        },
        "lineas": items,
        "subtotal": fac.subtotal or 0.0,
        "descuento": fac.descuento or 0.0,
        "iva": fac.iva or 0.0,
        "total": fac.total or 0.0
    }
    nueva_ruta = generar_pdf_factura(datos_pdf)
    fac.pdf_ruta = nueva_ruta
    db.commit()
    return nueva_ruta

def resolver_ruta_pdf_proforma(prof, db: Session) -> str:
    if prof.pdf_ruta and os.path.exists(prof.pdf_ruta):
        return prof.pdf_ruta
    nombre_fact = f"Factura_{prof.consecutivo}.pdf"
    nombre_prof = f"Proforma_{prof.consecutivo}.pdf"
    candidatos = [
        PDF_DIR / nombre_fact,
        PDF_DIR / nombre_prof,
        PROFORMAS_DIR / nombre_fact,
        PROFORMAS_DIR / nombre_prof
    ]
    for c in candidatos:
        if c.exists():
            prof.pdf_ruta = str(c)
            db.commit()
            return str(c)
    config = db.query(DBConfiguracion).first()
    items = []
    try:
        items = json.loads(prof.items_json) if prof.items_json else []
    except Exception:
        items = []
    datos_pdf = {
        "consecutivo": prof.consecutivo,
        "fecha": prof.fecha.strftime("%d/%m/%Y %H:%M") if prof.fecha else datetime.now().strftime("%d/%m/%Y %H:%M"),
        "color_primario": config.color_primario if config else "#111827",
        "moneda": "CRC",
        "vendedor_nombre": prof.vendedor_nombre or "Vendedor",
        "metodo_pago": f"COTIZACIÓN / SEGUIMIENTO ({prof.canal_origen or 'Directo'})",
        "comprobante_banco": "PROFORMA VÁLIDA POR 8 DÍAS",
        "tienda": {
            "nombre": config.nombre_tienda if config else "NEBULOSA INGENIERÍA Y AUTOMATIZACIÓN",
            "cedula": config.cedula_fiscal if config else "3-101-948271",
            "telefono": config.telefono if config else "+506 8888-8888",
            "direccion": config.direccion if config else "San José, Costa Rica",
            "actividad": config.codigo_actividad if config else "477101 - Venta prendas"
        },
        "cliente": {
            "nombre": prof.cliente_nombre or "Cliente",
            "cedula": "PROSPECTO",
            "correo": prof.cliente_correo or "",
            "telefono": prof.cliente_telefono or "",
            "direccion": f"Canal: {prof.canal_origen or 'Tienda'} | {prof.notas_seguimiento or ''}"
        },
        "lineas": items,
        "subtotal": prof.subtotal or 0.0,
        "descuento": prof.descuento or 0.0,
        "iva": prof.iva or 0.0,
        "total": prof.total or 0.0
    }
    nueva_ruta = generar_pdf_factura(datos_pdf)
    prof.pdf_ruta = nueva_ruta
    db.commit()
    return nueva_ruta

@app.get("/api/pos/facturas/{factura_id}/pdf")
def descargar_factura_pdf(factura_id: int, db: Session = Depends(get_db)):
    fac = db.query(DBFactura).filter(DBFactura.id == factura_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    ruta = resolver_ruta_pdf_factura(fac, db)
    return FileResponse(ruta, media_type="application/pdf", filename=f"Factura_{fac.consecutivo}.pdf")

@app.post("/api/pos/upload-voucher")
async def subir_voucher_pago(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix or ".png"
    voucher_name = f"voucher_{int(datetime.now().timestamp())}{ext}"
    dest = UPLOADS_DIR / voucher_name
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {"status": "ok", "url": f"/uploads/{voucher_name}"}

# ==========================================
# 5. PROFORMAS, CALENDARIO Y ALARMAS DE SEGUIMIENTO
# ==========================================
class ProformaRequest(BaseModel):
    cliente_id: Optional[int] = None
    cliente_nombre: str
    cliente_telefono: Optional[str] = ""
    cliente_correo: Optional[str] = ""
    canal_origen: str = "WhatsApp"
    vendedor_nombre: str = "Carlos Méndez"
    subtotal: float
    descuento: float = 0.0
    iva: float
    total: float
    notas_seguimiento: str = ""
    apartar_stock: bool = False
    fecha_alarma: Optional[str] = None # Formato YYYY-MM-DDTHH:MM
    items: List[ItemFactura]

@app.get("/api/proformas")
def listar_proformas(db: Session = Depends(get_db)):
    proformas = db.query(DBProformaSeguimiento).order_by(DBProformaSeguimiento.fecha.desc()).all()
    res = []
    ahora = datetime.utcnow()
    for p in proformas:
        alarma_str = p.fecha_alarma.strftime("%Y-%m-%dT%H:%M") if p.fecha_alarma else None
        esta_vencida = bool(p.fecha_alarma and p.fecha_alarma < ahora and p.alarma_activa)
        res.append({
            "id": p.id,
            "consecutivo": p.consecutivo,
            "fecha": p.fecha.strftime("%d/%m/%Y %H:%M") if p.fecha else "",
            "cliente_nombre": p.cliente_nombre,
            "cliente_telefono": p.cliente_telefono,
            "cliente_correo": p.cliente_correo,
            "canal_origen": p.canal_origen,
            "vendedor_nombre": p.vendedor_nombre,
            "subtotal": p.subtotal,
            "descuento": p.descuento,
            "iva": p.iva,
            "total": p.total,
            "estado": p.estado,
            "notas_seguimiento": p.notas_seguimiento,
            "fecha_alarma": alarma_str,
            "alarma_activa": p.alarma_activa,
            "alarma_vencida": esta_vencida,
            "pdf_url": f"/api/proformas/{p.id}/pdf" if p.pdf_ruta else None
        })
    return res

@app.post("/api/proformas")
def crear_proforma_seguimiento(prof: ProformaRequest, db: Session = Depends(get_db)):
    if prof.apartar_stock:
        for item in prof.items:
            prod = db.query(DBProductoWMS).filter(DBProductoWMS.id == item.id).first()
            if prod:
                if prod.stock >= item.cantidad:
                    prod.stock -= item.cantidad
                    prod.stock_apartado += item.cantidad

    consecutivo_num = db.query(DBProformaSeguimiento).count() + 1
    consecutivo_str = f"PRF-{consecutivo_num:05d}"

    # Precios contemplan IVA incluido:
    total_bruto = sum(i.precio_unitario * i.cantidad for i in prof.items)
    descuento = float(prof.descuento or 0.0)
    total_final = max(0.0, total_bruto - descuento)
    subtotal_base = round(total_final / 1.13, 2)
    iva_monto = round(total_final - subtotal_base, 2)

    config = db.query(DBConfiguracion).first()
    datos_pdf = {
        "consecutivo": consecutivo_str,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "color_primario": config.color_primario if config else "#111827",
        "moneda": "CRC",
        "vendedor_nombre": prof.vendedor_nombre,
        "metodo_pago": f"COTIZACIÓN / SEGUIMIENTO ({prof.canal_origen})",
        "comprobante_banco": "PROFORMA VÁLIDA POR 8 DÍAS",
        "tienda": {
            "nombre": config.nombre_tienda if config else "NEXO RETAIL",
            "cedula": config.cedula_fiscal if config else "3-101-948271",
            "telefono": config.telefono if config else "+506 8888-8888",
            "direccion": config.direccion if config else "San José, Costa Rica",
            "actividad": config.codigo_actividad if config else "477101 - Venta prendas"
        },
        "cliente": {
            "nombre": prof.cliente_nombre,
            "cedula": "PROSPECTO",
            "correo": prof.cliente_correo,
            "telefono": prof.cliente_telefono,
            "direccion": f"Canal: {prof.canal_origen} | {prof.notas_seguimiento}"
        },
        "lineas": [i.dict() for i in prof.items],
        "subtotal": subtotal_base,
        "descuento": descuento,
        "iva": iva_monto,
        "total": total_final
    }

    try:
        ruta_pdf = generar_pdf_factura(datos_pdf)
    except Exception as e:
        ruta_pdf = ""

    dt_alarma = None
    if prof.fecha_alarma:
        try:
            dt_alarma = datetime.fromisoformat(prof.fecha_alarma)
        except Exception:
            dt_alarma = datetime.utcnow() + timedelta(days=2)

    db_prof = DBProformaSeguimiento(
        consecutivo=consecutivo_str,
        cliente_id=prof.cliente_id,
        cliente_nombre=prof.cliente_nombre,
        cliente_telefono=prof.cliente_telefono,
        cliente_correo=prof.cliente_correo,
        canal_origen=prof.canal_origen,
        vendedor_nombre=prof.vendedor_nombre,
        subtotal=subtotal_base,
        descuento=descuento,
        iva=iva_monto,
        total=total_final,
        items_json=json.dumps([i.dict() for i in prof.items]),
        notas_seguimiento=prof.notas_seguimiento,
        fecha_alarma=dt_alarma,
        alarma_activa=True,
        pdf_ruta=ruta_pdf,
        estado="PENDIENTE_PAGO"
    )
    db.add(db_prof)
    db.commit()
    db.refresh(db_prof)

    return {
        "status": "success",
        "proforma_id": db_prof.id,
        "consecutivo": consecutivo_str,
        "pdf_url": f"/api/proformas/{db_prof.id}/pdf",
        "total": prof.total
    }

class AlarmaUpdateRequest(BaseModel):
    fecha_alarma: Optional[str] = None
    alarma_activa: bool = True
    notas_seguimiento: Optional[str] = None

@app.put("/api/proformas/{prof_id}/alarma")
def actualizar_alarma_proforma(prof_id: int, req: AlarmaUpdateRequest, db: Session = Depends(get_db)):
    prof = db.query(DBProformaSeguimiento).filter(DBProformaSeguimiento.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Proforma no encontrada")
    if req.fecha_alarma:
        try:
            prof.fecha_alarma = datetime.fromisoformat(req.fecha_alarma)
        except Exception:
            pass
    prof.alarma_activa = req.alarma_activa
    if req.notas_seguimiento:
        prof.notas_seguimiento = req.notas_seguimiento
    db.commit()
    return {"status": "ok", "id": prof.id, "alarma_activa": prof.alarma_activa}

@app.get("/api/proformas/{prof_id}/pdf")
def descargar_proforma_pdf(prof_id: int, db: Session = Depends(get_db)):
    prof = db.query(DBProformaSeguimiento).filter(DBProformaSeguimiento.id == prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Proforma no encontrada")
    ruta = resolver_ruta_pdf_proforma(prof, db)
    return FileResponse(ruta, media_type="application/pdf", filename=f"Proforma_{prof.consecutivo}.pdf")

# ==========================================
# 6. SISTEMA DE APARTADOS Y PAGOS A CUOTAS
# ==========================================
class ItemApartado(BaseModel):
    id: int
    sku: str
    nombre: str
    talla: str
    color: str
    cantidad: int
    precio: float

class CrearApartadoRequest(BaseModel):
    cliente_nombre: str
    cliente_telefono: Optional[str] = ""
    cliente_cedula: Optional[str] = ""
    vendedor_nombre: str = "Carlos Méndez"
    plazo_dias: int = 30
    abono_inicial: float = 0.0
    metodo_pago_abono: str = "SINPE_MOVIL"
    comprobante_abono: str = ""
    notas: str = ""
    items: List[ItemApartado]

@app.get("/api/apartados")
def listar_apartados(db: Session = Depends(get_db)):
    apartados = db.query(DBApartado).order_by(DBApartado.fecha_creacion.desc()).all()
    resultado = []
    for a in apartados:
        abonos = db.query(DBAbonoApartado).filter(DBAbonoApartado.apartado_id == a.id).order_by(DBAbonoApartado.fecha.asc()).all()
        items = json.loads(a.items_json or "[]")
        resultado.append({
            "id": a.id,
            "consecutivo": a.consecutivo,
            "cliente_nombre": a.cliente_nombre,
            "cliente_telefono": a.cliente_telefono,
            "cliente_cedula": a.cliente_cedula,
            "vendedor_nombre": a.vendedor_nombre,
            "fecha_creacion": a.fecha_creacion.strftime("%d/%m/%Y") if a.fecha_creacion else "",
            "fecha_limite": a.fecha_limite.strftime("%d/%m/%Y") if a.fecha_limite else "",
            "total": a.total,
            "saldo_pendiente": a.saldo_pendiente,
            "total_abonado": a.total - a.saldo_pendiente,
            "estado": a.estado,
            "notas": a.notas,
            "items": items,
            "abonos": [
                {
                    "id": ab.id,
                    "fecha": ab.fecha.strftime("%d/%m/%Y %H:%M") if ab.fecha else "",
                    "monto": ab.monto,
                    "metodo_pago": ab.metodo_pago,
                    "numero_comprobante": ab.numero_comprobante,
                    "notas": ab.notas
                }
                for ab in abonos
            ]
        })
    return resultado

@app.post("/api/apartados")
def registrar_apartado(req: CrearApartadoRequest, db: Session = Depends(get_db)):
    total = sum(i.precio * i.cantidad for i in req.items)
    if total <= 0:
        raise HTTPException(status_code=400, detail="El total del apartado debe ser mayor a 0.")

    # Apartar el stock en WMS
    for i in req.items:
        prod = db.query(DBProductoWMS).filter(DBProductoWMS.id == i.id).first()
        if prod:
            if prod.stock >= i.cantidad:
                prod.stock -= i.cantidad
                prod.stock_apartado += i.cantidad

    consecutivo_num = db.query(DBApartado).count() + 1
    consecutivo_str = f"APT-{consecutivo_num:05d}"
    fecha_lim = datetime.now() + timedelta(days=req.plazo_dias)
    saldo = max(0.0, total - req.abono_inicial)
    estado = "LIQUIDADO" if saldo == 0 else "PENDIENTE"

    nuevo_apt = DBApartado(
        consecutivo=consecutivo_str,
        cliente_nombre=req.cliente_nombre,
        cliente_telefono=req.cliente_telefono,
        cliente_cedula=req.cliente_cedula,
        vendedor_nombre=req.vendedor_nombre,
        fecha_creacion=datetime.now(),
        fecha_limite=fecha_lim,
        total=total,
        saldo_pendiente=saldo,
        estado=estado,
        items_json=json.dumps([i.dict() for i in req.items]),
        notas=req.notas
    )
    db.add(nuevo_apt)
    db.commit()
    db.refresh(nuevo_apt)

    if req.abono_inicial > 0:
        abono = DBAbonoApartado(
            apartado_id=nuevo_apt.id,
            monto=req.abono_inicial,
            metodo_pago=req.metodo_pago_abono,
            numero_comprobante=req.comprobante_abono,
            notas="Abono inicial de apertura"
        )
        db.add(abono)
        db.commit()

    return {"status": "success", "id": nuevo_apt.id, "consecutivo": consecutivo_str, "saldo": saldo}

class RegistrarAbonoRequest(BaseModel):
    monto: float
    metodo_pago: str = "SINPE_MOVIL"
    numero_comprobante: str = ""
    notas: str = ""

@app.post("/api/apartados/{apartado_id}/abonos")
def registrar_abono_apartado(apartado_id: int, req: RegistrarAbonoRequest, db: Session = Depends(get_db)):
    apt = db.query(DBApartado).filter(DBApartado.id == apartado_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Apartado no encontrado")
    if apt.estado == "LIQUIDADO":
        raise HTTPException(status_code=400, detail="Este apartado ya se encuentra 100% liquidado.")
    if req.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto del abono debe ser mayor a 0.")

    nuevo_abono = DBAbonoApartado(
        apartado_id=apt.id,
        monto=req.monto,
        metodo_pago=req.metodo_pago,
        numero_comprobante=req.numero_comprobante,
        notas=req.notas
    )
    db.add(nuevo_abono)

    apt.saldo_pendiente = max(0.0, apt.saldo_pendiente - req.monto)
    if apt.saldo_pendiente <= 0:
        apt.estado = "LIQUIDADO"
        # Descontar del stock_apartado ya que se entregará la prenda
        items = json.loads(apt.items_json or "[]")
        for i in items:
            prod = db.query(DBProductoWMS).filter(DBProductoWMS.id == i.get("id")).first()
            if prod and prod.stock_apartado >= i.get("cantidad", 1):
                prod.stock_apartado -= i.get("cantidad", 1)

    db.commit()
    db.refresh(apt)
    return {
        "status": "success",
        "apartado_id": apt.id,
        "saldo_pendiente": apt.saldo_pendiente,
        "estado": apt.estado
    }

# ==========================================
# 7. DATOS Y CONFIGURACIÓN FISCAL
# ==========================================
@app.get("/api/configuracion/fiscal")
def obtener_datos_fiscales(db: Session = Depends(get_db)):
    cfg = db.query(DBConfiguracion).first()
    if not cfg:
        cfg = DBConfiguracion()
        db.add(cfg)
        db.commit()
    return {
        "nombre_tienda": cfg.nombre_tienda,
        "cedula_fiscal": cfg.cedula_fiscal,
        "telefono": cfg.telefono,
        "correo": cfg.correo,
        "direccion": cfg.direccion,
        "codigo_actividad": cfg.codigo_actividad,
        "regimen_tributario": cfg.regimen_tributario,
        "sucursal": cfg.sucursal,
        "caja": cfg.caja,
        "hacienda_ambiente": cfg.hacienda_ambiente,
        "color_primario": cfg.color_primario,
        "color_secundario": cfg.color_secundario,
        "moneda": cfg.moneda
    }

class FiscalConfigRequest(BaseModel):
    nombre_tienda: str
    cedula_fiscal: str
    telefono: str
    correo: str
    direccion: str
    codigo_actividad: str
    regimen_tributario: str
    sucursal: str = "001"
    caja: str = "00001"
    hacienda_ambiente: str = "Staging / Pruebas DGT"

@app.put("/api/configuracion/fiscal")
def actualizar_datos_fiscales(req: FiscalConfigRequest, db: Session = Depends(get_db)):
    cfg = db.query(DBConfiguracion).first()
    if not cfg:
        cfg = DBConfiguracion()
        db.add(cfg)
    for k, v in req.dict().items():
        setattr(cfg, k, v)
    db.commit()
    return {"status": "success", "mensaje": "Datos fiscales actualizados con éxito"}

# ==========================================
# 8. TICKETS DE SOPORTE & IA GEMINI
# ==========================================
@app.get("/api/tickets")
def listar_tickets(db: Session = Depends(get_db)):
    return db.query(DBTicket).order_by(DBTicket.fecha.desc()).all()

class TicketCreate(BaseModel):
    tienda: str = "Tienda Local"
    categoria: str = "ERROR_SISTEMA"
    titulo: str
    descripcion: str
    prioridad: str = "MEDIA"

@app.post("/api/tickets")
def crear_ticket(t: TicketCreate, db: Session = Depends(get_db)):
    code = f"TCK-{int(datetime.now().timestamp()) % 100000}"
    nuevo = DBTicket(codigo=code, **t.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.put("/api/tickets/{ticket_id}/resolver")
def resolver_ticket(ticket_id: int, db: Session = Depends(get_db)):
    t = db.query(DBTicket).filter(DBTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    t.estado = "RESUELTO"
    t.respuesta_lider = f"Resuelto por Isaac el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    db.commit()
    return t

@app.delete("/api/tickets/{ticket_id}")
def eliminar_ticket(ticket_id: int, db: Session = Depends(get_db)):
    t = db.query(DBTicket).filter(DBTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    db.delete(t)
    db.commit()
    return {"status": "ok", "message": "Ticket eliminado correctamente"}

# ==========================================
# 9. REPORTES GENERALES & BUSINESS ANALYTICS (NATIVO)
# ==========================================
@app.get("/api/reportes/general")
def obtener_reporte_general(db: Session = Depends(get_db)):
    facturas = db.query(DBFactura).all()
    productos = db.query(DBProductoWMS).all()
    apartados = db.query(DBApartado).all()

    total_ventas = sum(f.total or 0.0 for f in facturas)
    total_descuentos = sum(f.descuento or 0.0 for f in facturas)
    total_subtotal = sum(f.subtotal or 0.0 for f in facturas)
    total_iva = sum(f.iva or 0.0 for f in facturas)
    cantidad_facturas = len(facturas)
    ticket_promedio = (total_ventas / cantidad_facturas) if cantidad_facturas > 0 else 0.0

    # Desglose por método de pago
    metodos = {
        "SINPE_MOVIL": {"total": 0.0, "cantidad": 0, "nombre": "SINPE Móvil", "color": "#00F0FF"},
        "TARJETA": {"total": 0.0, "cantidad": 0, "nombre": "Tarjeta Débito / Crédito", "color": "#A855F7"},
        "TRANSFERENCIA": {"total": 0.0, "cantidad": 0, "nombre": "Transferencia Bancaria", "color": "#3B82F6"},
        "EFECTIVO": {"total": 0.0, "cantidad": 0, "nombre": "Efectivo", "color": "#10B981"}
    }
    for f in facturas:
        m = f.metodo_pago or "SINPE_MOVIL"
        if m not in metodos:
            metodos[m] = {"total": 0.0, "cantidad": 0, "nombre": m, "color": "#64748B"}
        metodos[m]["total"] += (f.total or 0.0)
        metodos[m]["cantidad"] += 1

    # Desglose por vendedor
    vendedores = {}
    for f in facturas:
        v = f.vendedor_nombre or "General"
        if v not in vendedores:
            vendedores[v] = {"nombre": v, "total": 0.0, "cantidad": 0}
        vendedores[v]["total"] += (f.total or 0.0)
        vendedores[v]["cantidad"] += 1

    # Top Artículos vendidos procesando items_json
    articulos_map = {}
    for f in facturas:
        try:
            items = json.loads(f.items_json or "[]")
            for it in items:
                sku = it.get("sku", "S/SKU")
                nombre = it.get("nombre", "Artículo")
                cant = it.get("cantidad", 1)
                sub = it.get("subtotal") or (it.get("precio", 0.0) * cant)
                if sku not in articulos_map:
                    articulos_map[sku] = {
                        "sku": sku,
                        "nombre": nombre,
                        "cantidad": 0,
                        "total": 0.0
                    }
                articulos_map[sku]["cantidad"] += cant
                articulos_map[sku]["total"] += sub
        except Exception:
            pass

    top_articulos = sorted(articulos_map.values(), key=lambda x: x["cantidad"], reverse=True)[:10]

    # Salud y valoración WMS
    total_skus = len(productos)
    total_unidades_stock = sum(p.stock or 0 for p in productos)
    total_unidades_apartadas = sum(p.stock_apartado or 0 for p in productos)
    valor_inventario_venta = sum((p.stock or 0) * (p.precio or 0.0) for p in productos)
    valor_inventario_costo = sum((p.stock or 0) * (p.costo or 0.0) for p in productos)

    # Estado de cartera en apartados
    total_apartados = len(apartados)
    total_monto_apartados = sum(a.total or 0.0 for a in apartados)
    total_saldo_pendiente = sum(a.saldo_pendiente or 0.0 for a in apartados)
    total_recaudado_apartados = max(0.0, total_monto_apartados - total_saldo_pendiente)

    return {
        "resumen_ventas": {
            "total_ventas": round(total_ventas, 2),
            "total_descuentos": round(total_descuentos, 2),
            "total_subtotal": round(total_subtotal, 2),
            "total_iva": round(total_iva, 2),
            "cantidad_facturas": cantidad_facturas,
            "ticket_promedio": round(ticket_promedio, 2)
        },
        "flujo_metodos_pago": metodos,
        "vendedores": list(vendedores.values()),
        "top_articulos": top_articulos,
        "inventario_wms": {
            "total_skus": total_skus,
            "total_unidades": total_unidades_stock,
            "total_apartadas": total_unidades_apartadas,
            "valor_comercial": round(valor_inventario_venta, 2),
            "valor_costo": round(valor_inventario_costo, 2)
        },
        "cartera_apartados": {
            "total_apartados": total_apartados,
            "monto_total": round(total_monto_apartados, 2),
            "recaudado": round(total_recaudado_apartados, 2),
            "saldo_pendiente": round(total_saldo_pendiente, 2)
        }
    }

@app.get("/api/reportes/exportar-excel")
def exportar_reporte_excel(db: Session = Depends(get_db)):
    facturas = db.query(DBFactura).order_by(DBFactura.fecha.desc()).all()
    productos = db.query(DBProductoWMS).order_by(DBProductoWMS.id.desc()).all()
    apartados = db.query(DBApartado).order_by(DBApartado.fecha_creacion.desc()).all()
    config = db.query(DBConfiguracion).first()

    excel_path = generar_reporte_excel_completo(facturas, productos, apartados, config)
    filename = Path(excel_path).name
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )

@app.post("/api/ai/analizar-wms")
def analizar_inventario_ai(db: Session = Depends(get_db)):
    config = db.query(DBConfiguracion).first()
    giro = config.giro_comercial if config and config.giro_comercial else "Comercio General"
    prods = db.query(DBProductoWMS).all()
    matriz_anonima = [
        {
            "sku": p.sku,
            "nombre": p.nombre,
            "categoria": p.categoria,
            "variante": p.talla,
            "especificacion": p.color,
            "stock_actual": p.stock,
            "precio": p.precio,
            "costo": p.costo
        }
        for p in prods
    ]
    informe = analizar_tendencias_wms_con_gemini(matriz_anonima, giro_comercial=giro)
    return {"informe": informe}

@app.get("/api/configuracion")
def obtener_config(db: Session = Depends(get_db)):
    return db.query(DBConfiguracion).first()

class ConfigUpdate(BaseModel):
    nombre_tienda: str
    cedula_fiscal: str
    color_primario: str
    color_secundario: str
    color_fondo: Optional[str] = "#080c14"
    tema_fondo: Optional[str] = "Midnight Nebula"
    moneda: str
    giro_comercial: Optional[str] = "Comercio General / Retail"

@app.put("/api/configuracion")
def actualizar_config(cfg: ConfigUpdate, db: Session = Depends(get_db)):
    item = db.query(DBConfiguracion).first()
    if not item:
        item = DBConfiguracion()
        db.add(item)
    for k, v in cfg.dict().items():
        setattr(item, k, v)
    db.commit()
    return item




class WhatsAppEnvioRequest(BaseModel):
    telefono: str
    mensaje: str
    cliente_nombre: Optional[str] = "Cliente"
    tipo: Optional[str] = "general" # ticket, proforma, apartado, saludo

@app.post("/api/whatsapp/enviar")
def enviar_whatsapp_api(req: WhatsAppEnvioRequest):
    # Formatear teléfono (si tiene 8 dígitos para CR, anteponer 506)
    tel_limpio = "".join(filter(str.isdigit, req.telefono))
    if len(tel_limpio) == 8:
        tel_limpio = f"506{tel_limpio}"
        
    import urllib.parse
    texto_encoded = urllib.parse.quote(req.mensaje)
    wa_url = f"https://api.whatsapp.com/send?phone={tel_limpio}&text={texto_encoded}"
    
    # Retornar payload listo y enlace instantáneo para WhatsApp Web / App
    return {
        "status": "success",
        "telefono_formateado": tel_limpio,
        "enlace_directo": wa_url,
        "mensaje": req.mensaje,
        "tipo": req.tipo
    }


class PurgeRequest(BaseModel):
    pin_maestro: str
    usuario: str
    purgar_wms: Optional[bool] = True
    purgar_ventas: Optional[bool] = True
    purgar_proformas: Optional[bool] = True
    purgar_apartados: Optional[bool] = True
    purgar_gastos: Optional[bool] = True
    purgar_compras: Optional[bool] = True
    purgar_crm: Optional[bool] = True
    purgar_proveedores: Optional[bool] = False

@app.post("/api/admin/purgar-sistema")
def purgar_sistema_produccion(req: PurgeRequest, db: Session = Depends(get_db)):
    # 1. Validar autorización estricta del dueño
    master_user = db.query(DBUsuarioSistema).filter(
        (DBUsuarioSistema.is_master == 1) | (DBUsuarioSistema.username.ilike("isanchez")) | (DBUsuarioSistema.rol == "DUENO")
    ).first()

    pin_valido = False
    if master_user and master_user.pin_seguridad:
        if req.pin_maestro.strip() == str(master_user.pin_seguridad).strip():
            pin_valido = True

    if not pin_valido:
        raise HTTPException(
            status_code=403, 
            detail="ACCESO DENEGADO: PIN Maestro incorrecto o usuario no autorizado."
        )

    from sqlalchemy import text
    tablas_limpiadas = []

    # Purgar Ventas y Facturas Demo
    if req.purgar_ventas:
        db.execute(text("DELETE FROM facturas"))
        tablas_limpiadas.append("facturas")

    # Purgar Proformas Demo
    if req.purgar_proformas:
        db.execute(text("DELETE FROM proformas"))
        tablas_limpiadas.append("proformas")

    # Purgar Apartados y Cuotas Demo
    if req.purgar_apartados:
        try:
            db.execute(text("DELETE FROM apartados_cuotas"))
        except Exception:
            pass
        try:
            db.execute(text("DELETE FROM apartados"))
        except Exception:
            pass
        tablas_limpiadas.append("apartados")

    # Purgar Productos WMS Demo
    if req.purgar_wms:
        db.execute(text("DELETE FROM productos_wms"))
        tablas_limpiadas.append("productos_wms")

    # Purgar Gastos Operativos Demo
    if req.purgar_gastos:
        db.execute(text("DELETE FROM gastos_tienda"))
        tablas_limpiadas.append("gastos_tienda")

    # Purgar Compras y Ajustes de Stock Demo
    if req.purgar_compras:
        try:
            db.execute(text("DELETE FROM compras"))
        except Exception:
            pass
        try:
            db.execute(text("DELETE FROM inventario_ajustes"))
        except Exception:
            pass
        tablas_limpiadas.append("compras_y_ajustes")

    # Purgar Chats de CRM Demo
    if req.purgar_crm:
        try:
            db.execute(text("DELETE FROM crm_chats"))
        except Exception:
            pass
        tablas_limpiadas.append("crm_chats")

    # Purgar Proveedores si se solicita
    if req.purgar_proveedores:
        try:
            db.execute(text("DELETE FROM proveedores"))
            tablas_limpiadas.append("proveedores")
        except Exception:
            pass

    # Asegurar que el usuario maestro del dueño esté intacto
    db.commit()

    return {
        "status": "success",
        "message": "¡Sistema purgado y reiniciado exitosamente! La base de datos está 100% limpia para producción real.",
        "tablas_limpiadas": tablas_limpiadas,
        "usuario_protegido": "Isaac (Dueño & Líder)"
    }

FRONTEND_DIR = BASE_DIR / "frontend" / "public"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
