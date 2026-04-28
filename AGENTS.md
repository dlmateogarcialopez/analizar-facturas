# AGENTS.md

## Project Overview

Python ETL pipeline that extracts structured data from CHEC (Grupo EPM, Colombia) PDF invoices using a vision LLM (Qwen2-VL-7B via RunPod Serverless), then generates a multi-sheet Excel report with AI-powered analysis.

## Entry Point

```
python main.py [--carpeta <dir>] [--output <xlsx>] [--sin-llm]
```

- `--carpeta`: Folder with invoice PDFs (default: `./facturas_tipos`)
- `--output`: Output xlsx path (default: `./reportes/reporte_facturas_<timestamp>.xlsx`)
- `--sin-llm`: Skip LLM analysis, produce only basic extraction

## Architecture

```
main.py
  └─ etl/pipeline.py  (InvoiceEtlPipeline — Facade)
       ├─ etl/extractor.py     (PDF→images→base64→RunPod→JSON)
       ├─ etl/llm_analyzer.py  (per-invoice + portfolio analysis via RunPod)
       └─ etl/report_builder.py (5-sheet xlsx: Resumen, Facturas, Por Tipo, Análisis LLM, Datos Crudos)
```

## Key Files

| File | Purpose |
|------|---------|
| `clients/runpod_client.py` | RunPod API client (polling loop, handles Qwen2-VL-7B vision) |
| `core/constants.py` | System prompts for extraction, color palette, Excel styles |
| `core/utils.py` | `get_nested_val()` (dot-path dict access), `with_retry()` decorator |
| `etl/extractor.py` | PDF→JPEG (dpi=100, first 2 pages stitched), saves `reportes/extraccion_cruda_debug.xlsx` |
| `etl/llm_analyzer.py` | Individual invoice analysis + executive summary |
| `etl/report_builder.py` | 5-sheet Workbook; color-codes rows by invoice type (1-4) |

## Required Env Vars

```
RUNPOD_API_KEY=<key>
RUNPOD_ENDPOINT_ID=<endpoint>
```

The code loads `.env` via `python-dotenv`. Copy `.env.example` to `.env`.

## Rate Limiting & Retries

- `extractor.py`: 5s sleep between PDFs; `@with_retry(retries=2, backoff=15)`
- `llm_analyzer.py`: 5s sleep between invoices; `@with_retry(retries=3, backoff=20/30)`
- RunPod uses async polling until `status == "COMPLETED"`; debug output written to `debug_runpod.json`

## Invoice Types (auto-assigned if missing)

| Type | Description |
|------|-------------|
| 1 | Residencial Clásico |
| 2 | Residencial Moderno |
| 3 | Comercial Alto Consumo |
| 4 | Comercial Técnico |

Assigned from `estrato` field: `"comercial"`/`"industrial"` → type 3, otherwise type 1.

## Generated Files (gitignored)

- `*.xlsx` (reports)
- `facturas_tipos/*.pdf` (invoice PDFs)
- `debug_runpod.json`
- `.env`

## LLM Model Used

**Qwen/Qwen2-VL-7B-Instruct** via RunPod Serverless — vision-capable, receives PDF pages as base64 JPEG.

## Testing a Single File

```bash
python -c "
from etl.extractor import parsear_factura
import json, sys
result = parsear_factura('facturas_tipos/tipo_factura_1.pdf')
print(json.dumps(result, indent=2))
"
```

## Dependencies

```
PyMuPDF>=1.23.0  openpyxl>=3.1.0  openai>=1.0.0  python-dotenv>=1.0.0  requests>=2.31.0
```
