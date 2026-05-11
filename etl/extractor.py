"""
extractor.py
------------
Módulo para leer facturas PDF de CHEC (Grupo EPM) y extraer campos estructurados
usando IA (Qwen2.5-VL-72B en Modal) para una precisión superior.
"""

import os
import sys
import json
import json_repair
import base64
import time
import pandas as pd
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Fix de rutas para asegurar que se encuentren los paquetes core/clients
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.utils import get_nested_val
from core.constants import PROMPT_SISTEMA_EXTRACCION, PROMPT_SISTEMA_EXPLORATORIO, PROMPT_SISTEMA_TEMP

load_dotenv()

# ---------------------------------------------------------------------------
# Configuración del LLM
# ---------------------------------------------------------------------------

def _get_client():
    provider = os.getenv("LLM_PROVIDER", "runpod").lower()
    if provider == "modal":
        from clients.modal_client import ModalClient
        return ModalClient()
    else:
        from clients.runpod_client import RunPodClient
        return RunPodClient()

# ---------------------------------------------------------------------------
# Extracción de Imágenes (Base64)
# ---------------------------------------------------------------------------

import io
from PIL import Image

def _extraer_imagenes_pdf(ruta_pdf: str, max_paginas: int = 2, start_page: int = 0) -> list[str]:
    """Convierte páginas de un PDF a una SOLA imagen (stitched verticalmente) en base64."""
    try:
        doc = fitz.open(ruta_pdf)
        paginas_img = []
        
        for i in range(start_page, min(len(doc), start_page + max_paginas)):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # 1.5x para que la imagen combinada quepa en contexto
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            paginas_img.append(img)
            
        doc.close()
        
        if not paginas_img:
            return []
        
        # Unir todas las páginas en una sola imagen vertical
        if len(paginas_img) == 1:
            imagen_final = paginas_img[0]
        else:
            ancho_max = max(img.width for img in paginas_img)
            alto_total = sum(img.height for img in paginas_img)
            imagen_final = Image.new("RGB", (ancho_max, alto_total), (255, 255, 255))
            y_offset = 0
            for img in paginas_img:
                imagen_final.paste(img, (0, y_offset))
                y_offset += img.height
        
        # Codificar a base64
        buffered = io.BytesIO()
        imagen_final.save(buffered, format="JPEG", quality=88)
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return [img_str]  # Siempre una sola imagen
    except Exception as e:
        print(f"   ❌ Error convirtiendo PDF {ruta_pdf}: {e}")
        return []

# ---------------------------------------------------------------------------
# Inferencia y Procesamiento
# ---------------------------------------------------------------------------

def _generar_llm_inference(client, prompt_completo, imagenes_b64, system_prompt=None):
    return client.generate(
        prompt=prompt_completo,
        system_prompt=system_prompt, 
        json_mode=True,
        images_b64=imagenes_b64
    )

def parsear_factura(ruta: str) -> dict:
    """Extrae datos completos de la factura (2 páginas) usando Qwen2.5-VL-72B."""
    # Extraemos Página 1 (Datos) y Página 2 (Gráficas)
    imagenes_b64 = _extraer_imagenes_pdf(ruta, max_paginas=2, start_page=0)
    
    if not imagenes_b64:
        return {"archivo_origen": os.path.basename(ruta), "error": "No se pudo convertir el PDF a imágenes"}

    client = _get_client()
    prompt_usuario = "Analiza esta imagen de factura CHEC. Es una imagen combinada: la parte superior es la Página 1 (datos del cliente, consumo, totales) y la parte inferior es la Página 2 (gráficas). Extrae TODOS los datos siguiendo el esquema JSON del sistema."

    try:
        # Usamos el PROMPT_SISTEMA_TEMP que contiene los ~70 campos
        raw_response = _generar_llm_inference(client, prompt_usuario, imagenes_b64, system_prompt=PROMPT_SISTEMA_TEMP)
        
        print(f"\n🔍 [DEBUG] Respuesta cruda (primeros 500 chars):\n{raw_response[:500]}...\n")
        
        content = raw_response.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        datos = json_repair.loads(content.strip())
        
        if not isinstance(datos, dict):
            raise ValueError(f"El JSON extraído no es un diccionario válido")
            
        datos["archivo_origen"] = os.path.basename(ruta)
        return datos

    except Exception as e:
        print(f"   ❌ Error procesando {os.path.basename(ruta)}: {e}")
        return {"archivo_origen": os.path.basename(ruta), "error": str(e)}

def procesar_carpeta(input_dir: str) -> list[dict]:
    """Itera sobre PDFs y extrae datos de todos."""
    resultados = []
    archivos = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    
    if not archivos:
        print(f"⚠️ No se encontraron archivos PDF en {input_dir}")
        return []

    print(f"🤖 Procesando con IA (Qwen 72B en Modal): {len(archivos)} facturas...")

    for archivo in archivos:
        ruta = os.path.join(input_dir, archivo)
        print(f"  → Analizando: {archivo} (Extrayendo Datos + Gráficas)")
        
        datos = parsear_factura(ruta)
        resultados.append(datos)
        
    return resultados
