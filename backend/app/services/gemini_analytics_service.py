# -*- coding: utf-8 -*-
"""
Motor de IA Gemini para Análisis de Negocios y WMS (NEXO INTELLIGENCE).
Diseñado para cualquier giro empresarial (Retail, Tecnología, Repuestos, Alimentos, Belleza, etc.).
Cumple con la regla de privacidad estricta:
NUNCA se envían nombres de personas, clientes ni datos fiscales sensibles.
Únicamente se procesan matrices agregadas de productos, categorías, stock y márgenes.
"""

import os
import json
import urllib.request
import urllib.error

# Cargar API Key desde entorno o fallback
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

PROMPT_ANALISIS_EMPRESARIAL = """
Eres el Director de Estrategia Financiera y Operaciones Comerciales de más alto nivel para empresarios y directores generales.
Tu filosofía es: "Menos información es más. Máxima precisión analítica, datos duros, cero texto de relleno."

Analiza la matriz numérica del inventario WMS y catálogo comercial en formato JSON anonimizado.
Debes responder ESTRICTAMENTE con esta estructura (sin introducciones ni despedidas innecesarias):

### 📌 DICTAMEN EJECUTIVO (PARRAFO ÚNICO)
[Escribe EXACTAMENTE un solo párrafo de 3 a 4 líneas de longitud, ultra analítico y directo al grano, que sintetice la salud del capital de trabajo, los márgenes operativos globales y la prioridad comercial inmediata del negocio según sus datos].

### 📊 TABLA 1: DIAGNÓSTICO DE RENTABILIDAD & ROTACIÓN DE STOCK
| Artículo / Categoría | Stock Físico | Precio Unitario | Margen Estimado | Clasificación Rotación | Veredicto Operativo |
(Genera las filas evaluando los productos reales de la matriz, identificando productos estrella vs productos estancados).

### ⚡ TABLA 2: MATRIZ DE ACCIÓN COMERCIAL & RIESGO DE LIQUIDEZ
| Foco Estratégico | Nivel de Riesgo | Causa Raíz Detectada | Acción Inmediata Recomendada | Impacto Financiero Esperado |
(Genera 3 o 4 filas con recomendaciones ejecutivas concretas: liquidar sobrestock, reponer quiebre de stock, bundling o promociones).

Normas estrictas:
- Mantén el tono profesional, ejecutivo, sintético y en español.
- Responde únicamente con el párrafo y las 2 tablas en formato Markdown limpio.
"""

def analizar_tendencias_wms_con_gemini(matriz_wms_anonimizada: list, giro_comercial: str = "Comercio General") -> str:
    """
    Realiza una auditoría estratégica comercial llamando a Gemini REST API directamente.
    """
    key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    if not key:
        return "⚠️ Configura GEMINI_API_KEY para habilitar la auditoría estratégica de inventario con IA."

    data_str = json.dumps(matriz_wms_anonimizada, ensure_ascii=False, indent=2)
    prompt_completo = f"{PROMPT_ANALISIS_EMPRESARIAL}\n\nGIRO O RUBRO COMERCIAL: {giro_comercial}\n\nMATRIZ DE PRODUCTOS DEL ALMACÉN WMS:\n{data_str}"

    models_order = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]

    for model_name in models_order:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt_completo}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 1500
            }
        }
        
        try:
            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=25) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                candidates = res_body.get("candidates", [])
                if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                    return candidates[0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as err:
            err_msg = err.read().decode('utf-8', errors='ignore')
            # Si el modelo no está disponible, intentar el siguiente
            if err.code in [400, 404]:
                continue
            return f"Aviso de API Gemini ({err.code}): {err_msg[:200]}"
        except Exception as e:
            continue

    return "No fue posible conectar con los modelos de Gemini API en este momento. Revisa tu conexión o cuota de la API."
