# Analizador de Facturas CHEC - Universal Agentic Memory

> [!IMPORTANT]
> **CRÍTICO para todas las IAs:** Este archivo es la ÚNICA fuente de verdad para el contexto, estado y reglas del proyecto. Todo cambio estructural, regla de negocio o estado de bug solucionado debe registrarse aquí.

## 🏢 Identidad del Proyecto
**Nombre:** Analizador de Facturas CHEC
**Descripción:** Pipeline ETL en Python que extrae datos estructurados de facturas PDF de CHEC (Grupo EPM) usando modelos VLM (Qwen2.5-VL-72B / InternVL2-26B) vía Modal o RunPod, y genera reportes Excel con análisis inteligente.

## 📚 Glosario Estricto
- **Extracción Cruda:** Datos obtenidos directamente del LLM sin post-procesamiento.
- **Análisis LLM:** Fase de interpretación de consumos y tendencias.
- **Tipo de Factura:** Clasificación (1-4) basada en el estrato y uso.

## 🛠️ Stack Tecnológico
- **Core:** Python 3.9+
- **Visión (Extracción):** Qwen2.5-VL-72B-Instruct (recomendado) o InternVL2-26B
- **Proveedores LLM:** Modal (primario) o RunPod Serverless (alternativo), seleccionable vía `LLM_PROVIDER`
- **OCR/PDF:** PyMuPDF (fitz)
- **Reportes:** openpyxl (Excel), pandas (json_normalize para datos crudos)
- **Entorno:** python-dotenv, requests, openai (client)

## 🏗️ Arquitectura
```
main.py
  └─ etl/pipeline.py  (InvoiceEtlPipeline — Facade)
        ├─ etl/extractor.py     (PDF→images→base64→LLM→JSON anidado)
        ├─ etl/llm_analyzer.py  (per-invoice + portfolio analysis via LLM)
        └─ etl/report_builder.py (5-sheet xlsx: Resumen, Facturas, Por Tipo, Análisis LLM, Datos Crudos)
```

## 📂 Archivos Clave
| Archivo | Propósito |
|------|---------|
| `clients/modal_client.py` | Cliente API para Modal (OpenAI-compatible, max_tokens=4000, sin stop tokens). |
| `clients/runpod_client.py` | Cliente API para RunPod (polling loop, manejo de InternVL). |
| `core/constants.py` | `PROMPT_SISTEMA_EXTRACCION` (esquema JSON anidado por bloques), paleta de colores y estilos Excel. |
| `core/utils.py` | Utilidades: `get_nested_val(d, "a.b.c")`, `clean_float()`, decorador `with_retry`. |
| `etl/extractor.py` | Procesamiento PDF (dpi=100, stitching de páginas). Usa `get_nested_val` para imprimir resultados. |
| `etl/llm_analyzer.py` | Análisis individual y resumen ejecutivo. Usa `get_nested_val` para extraer datos de bloques. |
| `etl/report_builder.py` | Generador de Workbook 5 hojas. Columnas mapeadas con notación de punto (`bloque_X.campo`). |

## ⚙️ Configuración (Variables de Entorno)
Requiere archivo `.env` (basado en `.env.example`):
- `LLM_PROVIDER` — `"modal"` (default) o `"runpod"`. Selecciona el backend de inferencia.
- `MODAL_ENDPOINT_URL` — URL del Web Endpoint de Modal.
- `MODAL_API_KEY` — API Key para autenticación con Modal.
- `RUNPOD_API_KEY` — (alternativo) API Key para RunPod.
- `RUNPOD_ENDPOINT_ID` — (alternativo) Endpoint ID en RunPod.

## 📏 Reglas y Convenciones
1. **Reintentos:** 
   - `extractor.py`: 2 reintentos, backoff 15s.
   - `llm_analyzer.py`: 3 reintentos, backoff variable.
2. **Clasificación de Facturas:**
   - Tipo 1: Residencial Clásico.
   - Tipo 2: Residencial Moderno.
   - Tipo 3: Comercial Alto Consumo (`"comercial"`/`"industrial"`).
   - Tipo 4: Comercial Técnico.
3. **Manejo de Gráficas:** El modelo no debe calcular; debe realizar OCR literal de los puntos de datos marcados en las gráficas (ej. puntos sobre líneas azul/naranja).
4. **Esquema JSON Anidado:** El prompt actual usa bloques anidados (`bloque_datos_cliente`, `bloque_control_y_totales`, `bloque_consumo_energia`, etc.) en vez de un JSON plano. Todo el código Python usa `get_nested_val(d, "bloque.campo")` para acceder a los datos.
5. **Normalización Numérica:** Usar siempre `clean_float()` de `core/utils.py` para parsear valores monetarios que pueden venir con formatos locales (puntos de miles, comas, etc.).
6. **Selección de Modelo VLM:** Para extracción de datos (ETL), la familia Qwen2-VL es superior a InternVL2 gracias a su arquitectura M-RoPE que preserva la resolución nativa de la imagen. InternVL2-26B puede usarse para análisis de texto pero falla con schemas JSON grandes (>50 campos) porque fragmenta la imagen en parches rígidos.

## 🧠 Registro de Memoria y Decisiones (Memory Log)
*Registra aquí las decisiones arquitectónicas clave o los bugs solucionados recientemente.*

- **[2026-05-04] Lección: Secuencias de Parada en JSON:**
  - No usar `stop: ["}"]` en peticiones con JSON anidados, ya que el modelo se detiene al cerrar el primer objeto interno (ej. `bloque_datos_cliente`), dejando el JSON principal incompleto.
- **[2026-05-04] Cambio a InternVL2-26B:**
  - Se cambió el modelo a `InternVL2-26B` para evaluar estabilidad. Se ajustaron penalizaciones de frecuencia (0.3) y presencia (0.2) para evitar bucles.
- **[2026-05-07] Implementación de `clean_float()`:**
  - Creada en `core/utils.py` para normalizar formatos numéricos locales (ej. `6.458.106` → `6458106.0`). Resolvió `ValueError` en `report_builder.py` al generar Excel.
- **[2026-05-07] Soporte Dual Modal/RunPod:**
  - Se agregó `clients/modal_client.py` como proveedor LLM primario. Se eliminaron stop tokens y se aumentó `max_tokens` a 4000.
  - Variable `LLM_PROVIDER` controla la selección dinámica del backend.
- **[2026-05-08] Migración a Esquema JSON Anidado:**
  - Prompt reescrito en `constants.py` con estructura por bloques semánticos (`bloque_datos_cliente`, `bloque_control_y_totales`, `bloque_consumo_energia`, `bloque_conceptos_energia_chec`, `bloque_acumulado_horario`, etc.).
  - Incluye "Diccionario de Extracción" con guía espacial/contextual que indica al modelo DÓNDE buscar cada dato en la factura.
  - Todo el pipeline (`extractor`, `pipeline`, `llm_analyzer`, `report_builder`) adaptado para usar `get_nested_val()` con notación de punto.
- **[2026-05-08] Decisión: Qwen2.5-VL-72B > InternVL2-26B para ETL:**
  - InternVL2-26B devuelve JSONs vacíos con schemas de >50 campos (sobrecarga de atención por parches rígidos de imagen).
  - Qwen2-VL (cualquier tamaño) usa M-RoPE para resolución dinámica, haciéndolo ideal para documentos densos.
  - Recomendación: usar Qwen2.5-VL-72B-Instruct para extracción y reservar modelos grandes generalistas solo para análisis textual.

---
*Nota para IAs: Si el contexto de este documento crece a más de 300 líneas, modulariza creando archivos Markdown en la carpeta `.agent/memory/` y referéncialos aquí.*
