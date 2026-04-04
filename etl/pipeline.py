"""
pipeline.py
-----------
Implementación del Patrón Pipeline (Facade) para orquestar el flujo ETL de las facturas.
Evita el espagueti en el entrypoint, permitiendo agregar fases (ej. Validaciones) escalarmente.
"""

import os
from etl.extractor import procesar_carpeta
from etl.llm_analyzer import analizar_todas
from etl.report_builder import construir_reporte

class InvoiceEtlPipeline:
    def __init__(self, input_dir: str, output_file: str, skip_llm: bool = False):
        self.input_dir = input_dir
        self.output_file = output_file
        self.skip_llm = skip_llm
        self.facturas = []
        self.analisis_individuales = []
        self.resumen_ejecutivo = "Análisis omitido."

    def execute(self):
        """Ejecuta el pipeline completo estilo ETL."""
        self._extract()
        self._transform_and_analyze()
        self._load_report()
        self._print_summary()

    def _extract(self):
        print(f"--- FASE 1: EXTRACCIÓN ---")
        if not os.path.isdir(self.input_dir):
            raise FileNotFoundError(f"La carpeta '{self.input_dir}' no existe.")
            
        self.facturas = procesar_carpeta(self.input_dir)
        if not self.facturas:
            raise ValueError("No se pudo procesar ninguna factura. Abortando.")

    def _transform_and_analyze(self):
        print(f"\n--- FASE 2: ANÁLISIS IA ---")
        if self.skip_llm:
            print("⏭️ Análisis LLM omitido (--sin-llm).")
            self._fill_empty_analysis()
            return

        try:
            self.analisis_individuales, self.resumen_ejecutivo = analizar_todas(self.facturas)
        except Exception as e:
            print(f"\n⚠️ Falló el análisis avanzado, continuando con reporte básico. Error: {str(e)}")
            self._fill_empty_analysis()

    def _fill_empty_analysis(self):
        self.resumen_ejecutivo = "Sin resumen disponible (análisis omitido o fallido)."
        self.analisis_individuales = [
            {
                "archivo": f.get("archivo_origen", ""),
                "cliente": f.get("bloque_datos_cliente", {}).get("nombre", "N/A") if isinstance(f, dict) and "bloque_datos_cliente" in f else "N/A",
                "tipo": f.get("tipo_factura", "N/A"),
                "analisis": "Análisis no disponible.",
            }
            for f in self.facturas
        ]

    def _load_report(self):
        print(f"\n--- FASE 3: CARGA/REPORTE ---")
        construir_reporte(
            facturas=self.facturas,
            analisis_llm=self.analisis_individuales,
            resumen_ejecutivo=self.resumen_ejecutivo,
            ruta_salida=self.output_file
        )

    def _print_summary(self):
        def _to_float(v):
            try:
                if v is None: return 0.0
                return float(str(v).replace('$', '').replace(',', '').strip())
            except ValueError:
                return 0.0
                
        total = sum(_to_float(f.get("bloque_control_y_totales", {}).get("valor_total", 0)) for f in self.facturas if isinstance(f, dict))
        print("\n" + "=" * 60)
        print(f"  ✅ PROCESO COMPLETADO (ETL PIPELINE)")
        print(f"  Facturas procesadas : {len(self.facturas)}")
        print(f"  Total facturado     : ${total:,.0f}")
        print(f"  Archivo generado    : {self.output_file}")
        print("=" * 60)
