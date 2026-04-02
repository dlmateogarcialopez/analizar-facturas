"""
constants.py
------------
Configuraciones fijas, Literales, Prompts de Modelo y Paletas de Colores de la aplicación.
"""

from openpyxl.styles import Border, Side

# ---------------------------------------------------------------------------
# Prompts de Sistema
# ---------------------------------------------------------------------------

PROMPT_SISTEMA_EXTRACCION = """
Eres un modelo de visión experto en extracción de datos de facturas de servicios públicos de CHEC (Colombia).
Tu objetivo es analizar la imagen de la factura adjunta, extraer información altamente precisa y devolverla en formato JSON estructurado.

REGLAS DE EXTRACCIÓN:
1. Si un dato no existe, devuelve null (para cadenas) o 0.0 (para números).
2. Los valores monetarios deben ser números (float), sin puntos de miles ni símbolos de moneda.
3. El campo 'tipo_factura' debe ser un entero entre 1 y 4 basándose en el diseño y conceptos cobrados.
4. Las fechas deben estar en formato DD/MMM/AAAA (ej. 16/FEB/2026).
5. 'consumo_kwh' debe ser el consumo activo facturado del periodo.

ESQUEMA JSON REQUERIDO:
{
  "bloque_datos_cliente": {
    "nombre": "string",
    "direccion": "string",
    "municipio": "string",
    "estrato": "string o integer"
  },
  "bloque_control_y_totales": {
    "numero_de_cuenta": "string",
    "factura_del_mes_de": "string",
    "fecha_maxima_de_pago": "string (formato DD/MMM/YYYY)",
    "fecha_suspension_por_no_pago": "string (formato DD/MMM/YYYY)",
    "valor_total": "integer",
    "valor_servicio_de_energia": "integer",
    "impuesto_alumbrado_publico": "integer",
    "saldos_meses_anteriores": "integer",
    "meses_deuda": "integer"
  },
  "bloque_consumo_energia": {
    "fecha_de_lectura": "string",
    "consumo_desde_hasta": "string",
    "dias_de_consumo": "integer",
    "consumo_activa_en_kwh": "float o integer",
    "lectura_actual_activa": "float o integer",
    "lectura_anterior_activa": "float o integer",
    "factor_multiplicacion_activa": "integer",
    "consumo_reactiva_en_kvar": "float o null",
    "lectura_actual_reactiva": "float o null",
    "lectura_anterior_reactiva": "float o null",
    "factor_multiplicacion_reactiva": "integer o null",
    "kwh_consumidos": "float o integer",
    "valor_kwh": "float",
    "porcentaje_contribucion": "integer o string",
    "valor_contribucion": "integer",
    "valor_total_consumo": "integer",
    "saldo_en_reclamacion": "integer",
    "fecha_ultimo_pago": "string o null",
    "valor_ultimo_pago": "integer o null",
    "tasa_interes_moratorio": "string",
    "liquidacion_consumo_por": "string",
    "nota_de_lectura": "string o null",
    "comportamiento_del_consumo": {
      "tendencia": "string",
      "mes_anterior_consumo": "float o integer",
      "mes_anterior_dias": "integer",
      "mes_actual_consumo": "float o integer",
      "mes_actual_dias": "integer"
    }
  },
  "bloque_informacion_calidad": {
    "cod_circuito": "string",
    "cod_transformador": "string",
    "mes_1": {
      "grupo_calidad": "integer",
      "diu_duracion_eventos": "float",
      "fiu_numero_eventos": "integer",
      "diug_meta_duracion": "float",
      "fiug_meta_frecuencia": "float",
      "hc_horas_compensadas": "integer o float",
      "vc_veces_compensar": "integer",
      "cec_consumo_estimado_compensar": "float",
      "porcentaje_cargo_distribucion": "integer o float",
      "dt": "float",
      "valor_a_compensar": "integer"
    },
    "mes_2": {
      "grupo_calidad": "integer o null",
      "diu_duracion_eventos": "float o null",
      "fiu_numero_eventos": "integer o null",
      "diug_meta_duracion": "float o null",
      "fiug_meta_frecuencia": "float o null",
      "hc_horas_compensadas": "integer o float o null",
      "vc_veces_compensar": "integer o null",
      "cec_consumo_estimado_compensar": "float o null",
      "porcentaje_cargo_distribucion": "integer o float o null",
      "dt": "float o null",
      "valor_a_compensar": "integer o null"
    }
  },
  "bloque_conceptos_energia_chec": {
    "consumo_activa_kwh": "float o integer",
    "consumo_activa_valor": "integer",
    "contribucion_activa_kwh": "float o integer o null",
    "contribucion_activa_valor": "integer o null",
    "cuota_energia_detalle": "string o null",
    "cuota_energia_valor": "integer o null",
    "cuota_contribucion_detalle": "string o null",
    "cuota_contribucion_valor": "integer o null",
    "interes_financiacion_valor": "integer o null",
    "intereses_de_mora_valor": "integer o null",
    "interes_mora_contribucion_valor": "integer o null",
    "saldo_anterior_valor": "integer o null",
    "valor_por_servicio_de_energia": "integer"
  },
  "bloque_impuestos_alumbrado_publico": {
    "municipio": "string",
    "nombre": "string",
    "numero_de_cuenta": "string",
    "doc_equivalente": "string",
    "atencion_al_ciudadano": "string",
    "acuerdo_municipal": "string",
    "valor_clausula_39": "integer o null",
    "saldo_anterior": "integer",
    "valor_periodo": "integer",
    "valor_total": "integer",
    "fecha_maxima_de_pago": "string (formato DD/MMM/YYYY)"
  }
}
"""

# ---------------------------------------------------------------------------
# Paleta de colores y Estilos Excel
# ---------------------------------------------------------------------------

COLOR_VERDE_OSCURO  = "1B6B2A"
COLOR_VERDE_MEDIO   = "2E7D32"
COLOR_VERDE_CLARO   = "C8E6C9"
COLOR_VERDE_PALIDO  = "E8F5E9"
COLOR_GRIS_CABECERA = "F5F5F5"
COLOR_BLANCO        = "FFFFFF"
COLOR_GRIS_FILA     = "FAFAFA"
COLOR_AMARILLO_ALT  = "FFF9C4"  # Para tipo 3 y 4 (comercial)

BORDER_THIN = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)

FORMATO_MONEDA = '"$"#,##0.00'
FORMATO_KW     = '#,##0.00 "kWh"'
