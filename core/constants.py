# core/constants.py

# --- PROMPTS ---
PROMPT_SISTEMA_EXTRACCION = """
Tu tarea es leer una gráfica de líneas en una factura eléctrica CHEC (Colombia).

INSTRUCCIONES:
La gráfica se titula "Acumulado horario del mes kWh".
- Eje X: horas 1 a 24, separadas por líneas verticales VERDES.
- Línea AZUL con puntos: "activa_importada_kwh". Hay un número escrito junto a CADA punto azul.
- Línea NARANJA con puntos: "activa_exportada_kwh". Hay un número escrito junto a CADA punto naranja.

PROCESO OBLIGATORIO:
Para CADA hora (1, 2, 3, ... 24), localiza la línea vertical verde correspondiente.
Busca el punto AZUL sobre esa línea y lee el número escrito al lado. Ese es activa_importada_kwh.
Busca el punto NARANJA sobre esa línea y lee el número escrito al lado. Ese es activa_exportada_kwh.
Cada hora tiene un par de valores DIFERENTES. NO repitas el mismo valor para todas las horas.

IMPORTANTE: Los valores CAMBIAN de hora en hora. Por ejemplo, la importada puede ser ~3 en hora 1, ~0 en hora 7, ~2 en hora 13, ~8 en hora 21. La exportada puede ser 0 en hora 1, ~9 en hora 12, 0 en hora 24.

Devuelve EXACTAMENTE 24 objetos. Solo JSON válido, sin explicaciones.

{
  "bloque_acumulado_horario": [
    {"hora": 1, "activa_importada_kwh": ..., "activa_exportada_kwh": ...},
    {"hora": 2, "activa_importada_kwh": ..., "activa_exportada_kwh": ...},
    ...
    {"hora": 24, "activa_importada_kwh": ..., "activa_exportada_kwh": ...}
  ]
}
"""

PROMPT_SISTEMA_TEMP= """
Eres un sistema experto de OCR semántico y análisis de documentos alimentado por inteligencia artificial. Tu tarea es extraer datos de una factura de servicios públicos de CHEC (Colombia) a partir de una imagen y estructurarlos estrictamente en formato JSON.

### REGLAS GLOBALES ESTRICTAS:
1. FORMATO DE SALIDA: Tu respuesta DEBE ser única y exclusivamente un objeto JSON válido. No incluyas markdown (como ```json), no incluyas preámbulos, saludos, ni explicaciones.
2. TIPOS DE DATOS: 
   - Monetarios y Consumos: Extrae solo los números. Usa punto (.) para decimales. Elimina símbolos de moneda ($), comas de miles y texto. Si es entero, devuelve un Integer; si tiene decimales, un Float.
   - Fechas: Convierte toda fecha al formato DD/MMM/YYYY (ej. 16/FEB/2026).
   - Ausencia de datos: Si un campo no está presente en la imagen o es ilegible, asigna explícitamente el valor `null`. NUNCA inventes datos.

### DICCIONARIO DE EXTRACCIÓN (GUÍA ESPACIAL Y CONTEXTUAL):

- BLOQUE CLIENTE: Busca en la cabecera. 'tipo_factura' es un entero (1-4) inferido del diseño. 'estrato', 'clase_servicio' y 'numero_medidor' suelen estar agrupados cerca a los datos del titular.
- BLOQUE TOTALES: 'valor_servicio_de_energia' y 'valor_total' son los montos principales a pagar. Revisa la sección de liquidación para desgloses como 'aseo_valor', 'impuesto_alumbrado_publico' y 'saldos_meses_anteriores'.
- BLOQUE CONSUMO: Busca la tabla detallada de lecturas. Presta especial atención a diferenciar 'Consumo activa' (kWh) de 'Consumo reactiva' (kVar). Los campos 'mes_anterior...' y 'mes_actual...' se encuentran en la pequeña tabla de 'Comportamiento del Consumo'.
- BLOQUE CONCEPTOS ENERGÍA: Mapea la tabla de cobros detallados. Asocia correctamente los valores de las columnas "Kwh" y "Valor" con su fila descriptiva correspondiente (ej. 'Consumo activa pico', 'Cuota contribución').
- GRÁFICO ACUMULADO HORARIO (24 horas): Esta gráfica se titula "Acumulado horario del mes kWh".
  * Eje X: horas 1 a 24, separadas por líneas verticales VERDES.
  * Línea AZUL con puntos: "activa_importada_kwh". Hay un número escrito junto a CADA punto azul.
  * Línea NARANJA con puntos: "activa_exportada_kwh". Hay un número escrito junto a CADA punto naranja.
  * PROCESO: Para CADA hora (1-24), localiza la línea vertical verde correspondiente. Lee el número del punto AZUL (importada) y el del punto NARANJA (exportada). Los valores CAMBIAN de hora en hora. NO repitas valores. Devuelve EXACTAMENTE 24 objetos.
- GRÁFICO ÚLTIMOS CONSUMOS: Analiza el gráfico de barras y la tabla inferior. Mapea el valor superior de cada barra con los datos de la tabla ('Días Consumo', 'Sábados', etc.) alineados verticalmente por mes.
- GRÁFICO IMPORTACIÓN/EXPORTACIÓN: Eje X en meses. Línea AZUL es importado, línea NARANJA es exportado.
- FÓRMULA TARIFARIA: Busca el recuadro "Fórmula Tarifaria Regulada = CU". Extrae los valores numéricos bajo Generación, Transmisión, Distribución, Comercialización, Pérdidas y Restricciones.

### ESQUEMA JSON ESPERADO:
{
  "bloque_datos_cliente": {
    "nombre": null,
    "direccion": null,
    "municipio": null,
    "estrato": null,
    "clase_servicio": null,
    "numero_medidor": null,
    "tipo_factura": null
  },
  "bloque_control_y_totales": {
    "numero_de_cuenta": null,
    "factura_del_mes_de": null,
    "fecha_maxima_de_pago": null,
    "fecha_suspension_por_no_pago": null,
    "valor_total": null,
    "valor_servicio_de_energia": null,
    "impuesto_alumbrado_publico": null,
    "saldos_meses_anteriores": null,
    "meses_deuda": null,
    "aseo_valor": null,
    "somos_valor": null,
    "otros_conceptos_energia_chec": null,
    "afiliaciones_seguros": null,
    "saldo_anterior": null
  },
  "bloque_consumo_energia": {
    "fecha_de_lectura": null,
    "consumo_desde": null,
    "consumo_hasta": null,
    "dias_de_consumo": null,
    "consumo_activa_en_kwh": null,
    "lectura_actual_activa": null,
    "lectura_anterior_activa": null,
    "factor_multiplicacion_activa": null,
    "consumo_reactiva_en_kvar": null,
    "lectura_actual_reactiva": null,
    "lectura_anterior_reactiva": null,
    "factor_multiplicacion_reactiva": null,
    "kwh_consumidos": null,
    "valor_kwh": null,
    "porcentaje_contribucion": null,
    "valor_total_consumo": null,
    "saldo_en_reclamacion": null,
    "fecha_ultimo_pago": null,
    "valor_ultimo_pago": null,
    "tasa_interes_moratorio": null,
    "liquidacion_consumo_por": null,
    "nota_de_lectura": null,
    "comportamiento_del_consumo": {
      "tendencia": null,
      "mes_anterior_consumo": null,
      "mes_anterior_dias": null,
      "mes_actual_consumo": null,
      "mes_actual_dias": null
    }
  },
  "bloque_informacion_calidad": {
    "cod_circuito": null,
    "cod_transformador": null
  },
  "bloque_conceptos_energia_chec": {
    "consumo_activa_pico_kwh": null,
    "consumo_activa_pico_valor": null,
    "consumo_activa_hora_no_pico_kwh": null,
    "consumo_activa_hora_no_pico_valor": null,
    "consumo_reactiva_hora_pico_kwh": null,
    "consumo_reactiva_hora_pico_valor": null,
    "consumo_reactiva_hora_no_pico_kwh": null,
    "consumo_reactiva_hora_no_pico_valor": null,
    "contribucion_activa_hora_no_pico_kwh": null,
    "contribucion_activa_hora_no_pico_valor": null,
    "contribucion_activa_hora_pico_kwh": null,
    "contribucion_activa_hora_pico_valor": null,
    "contribucion_reactiva_hora_pico_kwh": null,
    "contribucion_reactiva_hora_pico_valor": null,
    "contribucion_reactiva_hora_no_pico_kwh": null,
    "contribucion_reactiva_hora_no_pico_valor": null,
    "consumo_activa_kwh": null,
    "consumo_activa_valor": null,
    "contribucion_activa_kwh": null,
    "contribucion_activa_valor": null,
    "cuota_energia_kwh": null,
    "cuota_energia_valor": null,
    "cuota_contribucion_kwh": null,
    "cuota_contribucion_valor": null,
    "interes_financiacion_kwh": null,
    "interes_financiacion_valor": null,
    "intereses_de_mora_kwh": null,
    "intereses_de_mora_valor": null,
    "interes_mora_contribucion_kwh": null,
    "interes_mora_contribucion_valor": null,
    "saldo_anterior_kwh": null,
    "saldo_anterior_valor": null,
    "valor_por_servicio_de_energia": null
  },
  "bloque_acumulado_horario": [
    {
      "hora": null,
      "activa_importada_kwh": null,
      "activa_exportada_kwh": null
    }
  ],
  "bloque_ultimos_consumos": [
    {
      "mes": null,
      "consumo_kwh": null,
      "dias_consumo": null,
      "sabados": null,
      "dom_fest": null,
      "dias_habiles": null
    }
  ],
  "bloque_formula_tarifaria": {
    "generacion": null,
    "transmision": null,
    "distribucion": null,
    "comercializacion": null,
    "perdidas": null,
    "restricciones": null,
    "valor_kwh_cu": null
  },
  "bloque_importacion_exportacion": [
    {
      "mes": null,
      "consumo_importado_kwh": null,
      "exportacion_kwh": null
    }
  ]
}
"""


PROMPT_SISTEMA_EXPLORATORIO = "Extract basic info from invoice in flat JSON."

# --- COLORES Y ESTILOS ---
COLOR_VERDE_OSCURO = "004B3E"
COLOR_VERDE_MEDIO = "008F76"
COLOR_VERDE_CLARO = "78C2AD"
COLOR_VERDE_PALIDO = "E8F5F1"
COLOR_GRIS_CABECERA = "E0E0E0"
COLOR_BLANCO = "FFFFFF"
COLOR_GRIS_FILA = "F2F2F2"
COLOR_AMARILLO_ALT = "FFF9C4"
FORMATO_MONEDA = '"$"#,##0.00'
FORMATO_KW = '#,##0.00 "kWh"'
from openpyxl.styles import Border, Side
BORDER_THIN = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
