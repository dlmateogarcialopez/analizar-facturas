"""
llm_analyzer.py
---------------
Módulo de análisis inteligente usando RunPod Serverless.
"""

import os
import json
import time
from clients.runpod_client import get_runpod_client
from dotenv import load_dotenv

from core.utils import get_nested_val, with_retry

load_dotenv()

def _get_client():
    return get_runpod_client()

@with_retry(retries=3, backoff=20)
def _generar_r_analisis(client, prompt):
    return client.generate(prompt=prompt)

def analizar_factura(factura: dict) -> dict:
    client = _get_client()
    
    prompt = f"""
    Como experto energético, analiza los datos de esta factura de CHEC Colombia:
    {json.dumps(factura, indent=2)}
    
    Genera un análisis breve (4 párrafos cortos):
    1. Diagnóstico de Consumo (kWh)
    2. Análisis del Valor ($)
    3. Alertas o Anomalías
    4. 2 Recomendaciones de ahorro
    """
    
    try:
        response_text = _generar_r_analisis(client, prompt)
        return {
            "archivo": factura.get("archivo_origen"),
            "cliente": get_nested_val(factura, "bloque_datos_cliente.nombre", "N/A"),
            "tipo": factura.get("tipo_factura", 1),
            "analisis": response_text.strip()
        }
    except Exception as e:
        return {
            "archivo": factura.get("archivo_origen"),
            "analisis": f"Error en análisis: {e}"
        }
@with_retry(retries=3, backoff=30)
def _generar_r_resumen(client, prompt):
    return client.generate(prompt=prompt)

def generar_resumen_ejecutivo(facturas: list[dict]) -> str:
    client = _get_client()
    
    resumen_datos = []
    for f in facturas:
        resumen_datos.append({
            "archivo": f.get("archivo_origen"),
            "valor": get_nested_val(f, "bloque_control_y_totales.valor_total"),
            "consumo": get_nested_val(f, "bloque_consumo_energia.kwh_consumidos"),
            "municipio": get_nested_val(f, "bloque_datos_cliente.municipio")
        })
        
    prompt = f"""
    Genera un Informe Ejecutivo para este portafolio de facturas CHEC:
    {json.dumps(resumen_datos, indent=2)}
    
    Resumen en 300 palabras:
    - Diagnóstico Global
    - Riesgos y Alertas
    - Plan de Acción y Ahorro
    """
    
    try:
        response_text = _generar_r_resumen(client, prompt)
        return response_text.strip()
    except Exception as e:
        return f"Error en resumen ejecutivo: {e}"

def analizar_todas(facturas: list[dict]) -> tuple[list[dict], str]:
    print("🤖 Generando análisis inteligente con RunPod...")
    individuales = []
    for f in facturas:
        print(f"  → Analizando: {f.get('archivo_origen')}")
        individuales.append(analizar_factura(f))
        time.sleep(5) # Rate limit protection for free models
        
    resumen = generar_resumen_ejecutivo(facturas)
    return individuales, resumen
