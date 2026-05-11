"""
main.py
-------
Entry point limpio y mantenible de la aplicación CHEC.
"""

import argparse
import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Asegurar que el directorio raíz del proyecto esté en el path para los imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Forzar codificación UTF-8 para evitar errores en terminales Windows con emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from etl.pipeline import InvoiceEtlPipeline

def _banner():
    print("=" * 60)
    print("  PROCESADOR DE FACTURAS CHEC (Grupo EPM)")
    print("  Arquitectura ETL Pipeline")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

def _parsear_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Procesa facturas PDF de CHEC y genera reporte Excel con análisis LLM."
    )
    parser.add_argument(
        "--carpeta",
        default=os.path.join(os.path.dirname(__file__), "facturas_tipos"),
        help="Carpeta con los archivos PDF (default: ./facturas_tipos)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(
            os.path.dirname(__file__),
            "reportes",
            f"reporte_facturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        ),
        help="Ruta del archivo Excel de salida",
    )
    parser.add_argument(
        "--sin-llm",
        action="store_true",
        help="Omitir el análisis LLM avanzado",
    )
    return parser.parse_args()

def main():
    _banner()
    args = _parsear_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    pipeline = InvoiceEtlPipeline(
        input_dir=args.carpeta,
        output_file=args.output,
        skip_llm=True
          # Temporalmente forzado a True para probar solo Fase 1 y 3
    )

    try:
        pipeline.execute()
    except Exception as e:
        print(f"\n❌ Pipeline finalizó con un error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
