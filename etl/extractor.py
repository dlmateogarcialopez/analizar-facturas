"""
extractor.py
------------
Módulo para leer facturas PDF de CHEC (Grupo EPM) y extraer campos estructurados
usando IA (RunPod Serverless) para una precisión superior.
"""

import os
import json
import base64
import time
import pandas as pd
import fitz  # PyMuPDF
from clients.runpod_client import get_runpod_client
from dotenv import load_dotenv

from core.utils import get_nested_val, with_retry
from core.constants import PROMPT_SISTEMA_EXTRACCION, PROMPT_SISTEMA_EXPLORATORIO

load_dotenv()

# ---------------------------------------------------------------------------
# Configuración del LLM
# ---------------------------------------------------------------------------

def _get_client():
    return get_runpod_client()

# ---------------------------------------------------------------------------
# Extracción de Imágenes (Base64)
# ---------------------------------------------------------------------------

import io
from PIL import Image

def _extraer_imagenes_pdf(ruta: str, max_paginas: int = 2) -> list[str]:
    """Convierte las primeras N páginas del PDF y las une verticalmente en una sola imagen JPEG Base64."""
    imagenes_b64 = []
    try:
        doc = fitz.open(ruta)
        imgs = []
        for i in range(min(max_paginas, len(doc))):
            page = doc.load_page(i)
            # dpi=100 reduce considerablemente el tamaño en base64 para evitar límites de payload de RunPod
            pix = page.get_pixmap(dpi=100)
            img_bytes = pix.tobytes("jpeg")
            imgs.append(Image.open(io.BytesIO(img_bytes)))
            
        if not imgs:
            return []
            
        # Unir imágenes verticalmente (stitching) en una sola
        total_width = max(img.width for img in imgs)
        total_height = sum(img.height for img in imgs)
        
        merged_img = Image.new('RGB', (total_width, total_height), color='white')
        y_offset = 0
        for img in imgs:
            merged_img.paste(img, (0, y_offset))
            y_offset += img.height
            
        # Convertir de vuelta a base64
        buffer = io.BytesIO()
        merged_img.save(buffer, format="JPEG", quality=85)
        merged_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        imagenes_b64.append(merged_b64)
            
    except Exception as e:
        print(f"⚠️ Error convirtiendo PDF a imagen {ruta}: {e}")
    return imagenes_b64

# ---------------------------------------------------------------------------
# Procesamiento con LLM (OpenRouter)
# ---------------------------------------------------------------------------

import io
from PIL import Image

def _guardar_excel_bruto(datos: dict):
    """Guarda o anexa el JSON crudo (sin modificaciones posteriores) en un Excel."""
    os.makedirs("reportes", exist_ok=True)
    ruta_excel = os.path.join("reportes", "extraccion_cruda_debug.xlsx")
    try:
        df_nuevo = pd.json_normalize(datos)
        if os.path.exists(ruta_excel):
            df_existente = pd.read_excel(ruta_excel)
            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
            df_final.to_excel(ruta_excel, index=False)
        else:
            df_nuevo.to_excel(ruta_excel, index=False)
    except Exception as e:
        print(f"⚠️ No se pudo guardar excel crudo: {e}")

@with_retry(retries=2, backoff=15)
def _generar_r_runpod(client, prompt_completo, imagenes_b64):
    return client.generate(
        prompt=prompt_completo,
        system_prompt=None, 
        json_mode=True,
        images_b64=imagenes_b64
    )

def parsear_factura(ruta: str) -> dict:
    """Extrae datos de la factura usando RunPod (Qwen-VL) con reintentos."""
    imagenes_b64 = _extraer_imagenes_pdf(ruta, max_paginas=2)
    if not imagenes_b64:
        return {"archivo_origen": os.path.basename(ruta), "error": "No se pudo convertir el PDF a imágenes"}

    client = _get_client()
    prompt_completo = f"Extrae los datos de esta factura de la CHEC en formato JSON siguiendo estrictamente este esquema:\n{PROMPT_SISTEMA_EXTRACCION}\n\nNo incluyas explicaciones, solo el JSON puro."
    #prompt_completo = f"Extrae los datos de esta factura de la CHEC en formato JSON siguiendo estrictamente este esquema:\n{PROMPT_SISTEMA_EXPLORATORIO}\n\nNo incluyas explicaciones, solo el JSON puro."

    try:
        raw_response = _generar_r_runpod(client, prompt_completo, imagenes_b64)
        print(f"\n🔍 [DEBUG] Respuesta cruda de RunPod:\n{raw_response[:1000]}...\n")
        
        content = raw_response.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        datos = json.loads(content.strip())
        datos["archivo_origen"] = os.path.basename(ruta)
        
        # --- ALMACENAR CRUDA EN EXCEL ANTES DE INFERIR TIPO ---
        _guardar_excel_bruto(datos)
        
        # --- Compatibilidad y Aumentado de datos ---
        if "tipo_factura" not in datos:
            estrato = str(get_nested_val(datos, "bloque_datos_cliente.estrato", "")).lower()
            if "comercial" in estrato or "industrial" in estrato:
                datos["tipo_factura"] = 3
            else:
                datos["tipo_factura"] = 1
        return datos

    except Exception as e:
        print(f"❌ Error procesando {ruta} con LLM: {e}")
        return {"archivo_origen": os.path.basename(ruta), "error": str(e)}

def procesar_carpeta(carpeta: str) -> list[dict]:
    """Procesa todos los PDFs en la carpeta usando el extractor IA."""
    resultados = []
    archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(".pdf")]
    
    print(f"🤖 Iniciando extracción inteligente de {len(archivos)} facturas...")
    
    for f in sorted(archivos):
        ruta = os.path.join(carpeta, f)
        print(f"  → Procesando con IA: {f}")
        datos = parsear_factura(ruta)
        
        if "error" not in datos:
            nombre = datos.get("bloque_datos_cliente", {}).get("nombre", "N/A")
            total_raw = datos.get("bloque_control_y_totales", {}).get("valor_total", 0)
            try:
                total = float(str(total_raw).replace('$', '').replace(',', '').strip()) if total_raw is not None else 0.0
            except ValueError:
                total = 0.0
                
            print(f"     ✅ Éxito: {nombre} | Total: ${total:,.0f}")
            resultados.append(datos)
            # Agregar un delay base entre archivos para evitar spam
            time.sleep(5) 
        else:
            print(f"     ❌ Fallo: {datos['error']}")
            
    return resultados
