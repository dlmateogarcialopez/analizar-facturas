"""
extractor.py
------------
Módulo para leer facturas PDF de CHEC (Grupo EPM) y extraer campos estructurados
usando IA (Qwen2.5-VL-72B en Modal).

Flujo de extracción:
  Pass 1: Página 1 → Datos de cliente, consumo, totales, fórmula tarifaria
  Clasificación: Página 2 → ¿Es prosumidor? (gráficas azul/naranja)
  Pass 2 (condicional): Página 2 → Gráficas horarias e importación/exportación
"""

import os
import sys
import json
import json_repair
import re
import base64
import time
import io
import pandas as pd
import fitz  # PyMuPDF
from PIL import Image
from dotenv import load_dotenv

# Fix de rutas para asegurar que se encuentren los paquetes core/clients
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.utils import get_nested_val
from core.constants import (
    PROMPT_PAGINA_1,
    PROMPT_PAGINA_2_PROSUMIDOR,
    PROMPT_CLASIFICAR_FACTURA,
)

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

def _extraer_pagina_pdf(ruta_pdf: str, pagina: int = 0, zoom: float = 3.0) -> str:
    """Convierte UNA página de un PDF a base64 JPEG con alta resolución."""
    try:
        doc = fitz.open(ruta_pdf)
        if pagina >= len(doc):
            doc.close()
            return None

        page = doc.load_page(pagina)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=90)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"   ❌ Error convirtiendo página {pagina} de {ruta_pdf}: {e}")
        return None


def _num_paginas_pdf(ruta_pdf: str) -> int:
    """Retorna el número de páginas del PDF."""
    try:
        doc = fitz.open(ruta_pdf)
        n = len(doc)
        doc.close()
        return n
    except:
        return 0


# ---------------------------------------------------------------------------
# Inferencia LLM
# ---------------------------------------------------------------------------

def _llamar_llm(client, prompt_usuario: str, imagen_b64: str, system_prompt: str) -> str:
    """Envía una imagen + prompt al LLM y retorna la respuesta raw."""
    return client.generate(
        prompt=prompt_usuario,
        system_prompt=system_prompt,
        json_mode=True,
        images_b64=[imagen_b64]
    )


def _parsear_json_response(raw: str) -> dict:
    """Limpia y parsea una respuesta JSON del LLM."""
    content = raw.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    datos = json_repair.loads(content.strip())
    if not isinstance(datos, dict):
        raise ValueError(f"El JSON extraído no es un diccionario válido: {type(datos)}")
    return datos


# ---------------------------------------------------------------------------
# Clasificación Local (GRATIS): ¿Es prosumidor?
# ---------------------------------------------------------------------------

def _clasificar_factura(ruta_pdf: str) -> bool:
    """
    Detecta si la factura es de prosumidor buscando palabras clave en el texto.
    Es un método local, rápido y gratuito.
    """
    try:
        doc = fitz.open(ruta_pdf)
        texto_completo = ""
        # Revisamos principalmente la página 2, que es donde están las gráficas
        for i in range(min(len(doc), 2)):
            texto_completo += doc[i].get_text()
        doc.close()

        keywords = [
            "Acumulado horario del mes",
            "Importación y exportación",
            "Energía exportada",
            "activa_exportada_kwh"
        ]
        
        for kw in keywords:
            if kw.lower() in texto_completo.lower():
                print(f"   🏷️  Clasificación Local: PROSUMIDOR ☀️ (Detectado por: '{kw}')")
                return True
                
        print(f"   🏷️  Clasificación Local: ESTÁNDAR")
        return False
    except Exception as e:
        print(f"   ⚠️ Error en clasificación local: {e}")
        return False


# ---------------------------------------------------------------------------
# Extracción Local (GRATIS): Datos técnicos de Página 2
# ---------------------------------------------------------------------------

def _extraer_datos_tecnicos_local(ruta_pdf: str) -> dict:
    """
    Extrae clase_servicio y numero_medidor de la Página 2 usando PyMuPDF.
    Estos campos están en la tabla 'Datos técnicos' que solo aparece en P2.
    Es 100% local y gratuito.
    """
    result = {"clase_servicio": None, "numero_medidor": None}
    try:
        doc = fitz.open(ruta_pdf)
        if len(doc) < 2:
            doc.close()
            return result

        page = doc[1]
        full_text = page.get_text()

        # --- Clase de servicio ---
        # Patrón: "N Residencial", "N Comercial", "N Industrial", "N Oficial"
        clase_match = re.search(
            r'(?<!\d)([1-6]\s+(?:Residencial|Comercial|Industrial|Oficial|No Residencial))',
            full_text, re.IGNORECASE
        )
        if clase_match:
            result["clase_servicio"] = clase_match.group(1).strip()

        # --- Número de medidor ---
        # Buscar número largo (5-12 dígitos) posicionalmente cerca del header 'medidor'
        blocks = page.get_text('dict')['blocks']
        spans = []
        for block in blocks:
            if 'lines' not in block:
                continue
            for line in block['lines']:
                for span in line['spans']:
                    spans.append({
                        'text': span['text'].strip(),
                        'x': span['bbox'][0],
                        'y': span['bbox'][1],
                    })

        medidor_hdr = None
        for s in spans:
            if 'de medidor' in s['text'] or s['text'].lower() == 'medidor':
                medidor_hdr = s
                break

        if medidor_hdr:
            candidates = []
            for s in spans:
                if re.match(r'^\d{5,12}$', s['text']) and s['y'] > medidor_hdr['y']:
                    dist = abs(s['x'] - medidor_hdr['x'])
                    candidates.append((dist, s['text']))
            candidates.sort()
            if candidates:
                result["numero_medidor"] = candidates[0][1]

        doc.close()

        if result["clase_servicio"] or result["numero_medidor"]:
            print(f"   📋 Datos técnicos (local): clase={result['clase_servicio']}, medidor={result['numero_medidor']}")

    except Exception as e:
        print(f"   ⚠️ Error extrayendo datos técnicos locales: {e}")

    return result


# ---------------------------------------------------------------------------
# Extracción principal
# ---------------------------------------------------------------------------

def parsear_factura(ruta: str) -> dict:
    """
    Extrae datos completos de una factura CHEC.

    Flujo:
      1. Pass 1: Página 1 con zoom 2.0x → datos principales
      2. Clasificación: Página 2 → detecta si es prosumidor
      3. Pass 2 (solo prosumidor): Página 2 con zoom 2.0x → gráficas
      4. Merge de resultados
    """
    archivo = os.path.basename(ruta)
    num_paginas = _num_paginas_pdf(ruta)

    if num_paginas == 0:
        return {"archivo_origen": archivo, "error": "No se pudo abrir el PDF"}

    client = _get_client()

    # ─── PASS 1: Página 1 (todos los tipos) ───
    print(f"   📄 Pass 1: Extrayendo datos de Página 1 (Zoom 3.0)...")
    img_p1 = _extraer_pagina_pdf(ruta, pagina=0, zoom=3.0)
    if not img_p1:
        return {"archivo_origen": archivo, "error": "No se pudo convertir Página 1"}

    try:
        raw_p1 = _llamar_llm(
            client,
            "Analiza esta imagen de la Página 1 de una factura CHEC. Extrae TODOS los datos siguiendo el esquema JSON del sistema.",
            img_p1,
            PROMPT_PAGINA_1
        )
        print(f"   ✅ Pass 1 completado ({len(raw_p1)} chars)")
        datos = _parsear_json_response(raw_p1)
    except Exception as e:
        print(f"   ❌ Error en Pass 1: {e}")
        return {"archivo_origen": archivo, "error": f"Pass 1 falló: {e}"}

    # ─── CLASIFICACIÓN + PASS 2 (si tiene página 2) ───
    if num_paginas >= 2:
        img_p2 = _extraer_pagina_pdf(ruta, pagina=1, zoom=3.0)

        if img_p2:
            # Clasificar localmente (Gratis)
            es_prosumidor = _clasificar_factura(ruta)

            if es_prosumidor:
                # Pass 2: Extraer gráficas de página 2
                print(f"   📊 Pass 2: Extrayendo gráficas de Página 2 (Prosumidor)...")
                try:
                    raw_p2 = _llamar_llm(
                        client,
                        "Analiza esta imagen de la Página 2 de una factura CHEC de prosumidor. "
                        "Lee las dos gráficas: 'Acumulado horario del mes kWh' y 'Importación y exportación en kWh'. "
                        "Sigue el proceso de lectura paso a paso para cada punto.",
                        img_p2,
                        PROMPT_PAGINA_2_PROSUMIDOR
                    )
                    print(f"   ✅ Pass 2 completado ({len(raw_p2)} chars)")
                    datos_p2 = _parsear_json_response(raw_p2)

                    # Merge: añadir gráficas al resultado principal
                    if "bloque_acumulado_horario" in datos_p2:
                        datos["bloque_acumulado_horario"] = datos_p2["bloque_acumulado_horario"]
                    if "bloque_importacion_exportacion" in datos_p2:
                        datos["bloque_importacion_exportacion"] = datos_p2["bloque_importacion_exportacion"]

                except Exception as e:
                    print(f"   ⚠️ Error en Pass 2 (gráficas): {e}")
                    # No es fatal, seguimos con los datos de Pass 1
            else:
                # No es prosumidor: los bloques de gráficas son null
                datos.setdefault("bloque_acumulado_horario", None)
                datos.setdefault("bloque_importacion_exportacion", None)
    else:
        datos.setdefault("bloque_acumulado_horario", None)
        datos.setdefault("bloque_importacion_exportacion", None)

    # ─── EXTRACCIÓN LOCAL: Datos técnicos de Página 2 (Gratis) ───
    if num_paginas >= 2:
        datos_tecnicos = _extraer_datos_tecnicos_local(ruta)
        # Inyectar en bloque_datos_cliente si el LLM no los devolvió
        if "bloque_datos_cliente" not in datos:
            datos["bloque_datos_cliente"] = {}
        if not datos["bloque_datos_cliente"].get("clase_servicio") and datos_tecnicos["clase_servicio"]:
            datos["bloque_datos_cliente"]["clase_servicio"] = datos_tecnicos["clase_servicio"]
        if not datos["bloque_datos_cliente"].get("numero_medidor") and datos_tecnicos["numero_medidor"]:
            datos["bloque_datos_cliente"]["numero_medidor"] = datos_tecnicos["numero_medidor"]

    datos["archivo_origen"] = archivo
    return datos


def procesar_carpeta(input_dir: str) -> list[dict]:
    """Itera sobre PDFs y extrae datos de todos."""
    resultados = []
    archivos = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]

    if not archivos:
        print(f"⚠️ No se encontraron archivos PDF en {input_dir}")
        return []

    print(f"🤖 Procesando con IA (Qwen 72B en Modal): {len(archivos)} facturas...")

    for i, archivo in enumerate(archivos, 1):
        ruta = os.path.join(input_dir, archivo)
        print(f"\n  [{i}/{len(archivos)}] → {archivo}")

        datos = parsear_factura(ruta)
        resultados.append(datos)

    return resultados
