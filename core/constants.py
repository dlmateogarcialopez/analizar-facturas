# core/constants.py

# ---------------------------------------------------------------------------
# PROMPT PÁGINA 1 — Extracción principal (todos los tipos de factura)
# ---------------------------------------------------------------------------
PROMPT_PAGINA_1 = """
Eres un sistema experto de OCR semántico para facturas de CHEC (Colombia).
Tu tarea: extraer datos de la PÁGINA 1 de una factura y devolver JSON puro.

### REGLAS ESTRICTAS:
1. SOLO JSON válido. Sin markdown, sin ```json, sin explicaciones.
2. Monetarios/Consumos: Solo números. Punto (.) para decimales. Sin $ ni comas.
   - Enteros → Integer. Decimales → Float.
3. Fechas: formato DD/MMM/YYYY (ej. 16/FEB/2026).
4. Campo ausente o ilegible → null. NUNCA inventes datos.

### GUÍA DE UBICACIÓN EN LA PÁGINA 1:

**DATOS DEL CLIENTE** (esquina superior izquierda):
- nombre, direccion, municipio, estrato, clase_servicio, numero_medidor

**CONTROL Y TOTALES** (centro-derecha, recuadros principales):
- numero_de_cuenta (número grande arriba)
- factura_del_mes_de, fecha_maxima_de_pago, fecha_suspension_por_no_pago
- valor_total (número grande verde)
- valor_servicio_de_energia, impuesto_alumbrado_publico
- saldos_meses_anteriores, meses_deuda
- aseo_valor, somos_valor, otros_conceptos_energia_chec
- afiliaciones_seguros, saldo_anterior

**CONSUMO DE ENERGÍA** (sección "Tu consumo de energía este mes fué"):
- fecha_de_lectura, consumo_desde, consumo_hasta, dias_de_consumo
- consumo_activa_en_kwh, lectura_actual_activa, lectura_anterior_activa
- factor_multiplicacion_activa
- consumo_reactiva_en_kvar, lectura_actual_reactiva, lectura_anterior_reactiva
- factor_multiplicacion_reactiva
- kwh_consumidos, valor_kwh, porcentaje_contribucion, valor_total_consumo
- saldo_en_reclamacion, fecha_ultimo_pago, valor_ultimo_pago
- tasa_interes_moratorio, liquidacion_consumo_por, nota_de_lectura
- comportamiento_del_consumo: tendencia, mes_anterior_consumo, mes_anterior_dias, mes_actual_consumo, mes_actual_dias

**INFORMACIÓN DE CALIDAD** (tabla pequeña con Cod. Circuito, Cod. Transformador):
- cod_circuito, cod_transformador

**CONCEPTOS ENERGÍA CHEC** (tabla de valores facturados, lado derecho):
- Mapea cada fila de la tabla con sus columnas Kwh y Valor.
- Los campos posibles son: consumo_activa, contribucion_activa, consumo_activa_pico, 
- consumo_activa_hora_no_pico, consumo_reactiva_hora_pico, consumo_reactiva_hora_no_pico,
- contribucion_activa_hora_pico, contribucion_activa_hora_no_pico,
- contribucion_reactiva_hora_pico, contribucion_reactiva_hora_no_pico,
- cuota_energia, cuota_contribucion, interes_financiacion, intereses_de_mora,
- interes_mora_contribucion, saldo_anterior.
- Cada uno tiene sufijo _kwh y _valor. Si no aplica → null.
- valor_por_servicio_de_energia es el total de esta tabla.

**ÚLTIMOS CONSUMOS FACTURADOS** (gráfica de barras + tabla inferior):
IMPORTANTE: Lee la TABLA de texto que está DEBAJO de las barras, NO los valores de las barras.
- La primera fila de la tabla tiene los MESES (ej. AGO, SEP, OCT..., PROM, ACT).
- Los valores de consumo_kwh son los números ENCIMA de cada barra.
- dias_consumo, sabados, dom_fest, dias_habiles vienen de las filas de la tabla inferior.
- Devuelve un array con un objeto por cada mes visible (incluyendo PROM y ACT).

**FÓRMULA TARIFARIA** (recuadro "Fórmula Tarifaria Regulada = CU"):
- generacion, transmision, distribucion, comercializacion, perdidas, restricciones
- valor_kwh_cu (el valor resaltado en el recuadro verde)

### ESQUEMA JSON:
{
  "bloque_datos_cliente": {
    "nombre": null, "direccion": null, "municipio": null,
    "estrato": null, "clase_servicio": null, "numero_medidor": null
  },
  "bloque_control_y_totales": {
    "numero_de_cuenta": null, "factura_del_mes_de": null,
    "fecha_maxima_de_pago": null, "fecha_suspension_por_no_pago": null,
    "valor_total": null, "valor_servicio_de_energia": null,
    "impuesto_alumbrado_publico": null, "saldos_meses_anteriores": null,
    "meses_deuda": null, "aseo_valor": null, "somos_valor": null,
    "otros_conceptos_energia_chec": null, "afiliaciones_seguros": null,
    "saldo_anterior": null
  },
  "bloque_consumo_energia": {
    "fecha_de_lectura": null, "consumo_desde": null, "consumo_hasta": null,
    "dias_de_consumo": null, "consumo_activa_en_kwh": null,
    "lectura_actual_activa": null, "lectura_anterior_activa": null,
    "factor_multiplicacion_activa": null, "consumo_reactiva_en_kvar": null,
    "lectura_actual_reactiva": null, "lectura_anterior_reactiva": null,
    "factor_multiplicacion_reactiva": null, "kwh_consumidos": null,
    "valor_kwh": null, "porcentaje_contribucion": null,
    "valor_total_consumo": null, "saldo_en_reclamacion": null,
    "fecha_ultimo_pago": null, "valor_ultimo_pago": null,
    "tasa_interes_moratorio": null, "liquidacion_consumo_por": null,
    "nota_de_lectura": null,
    "comportamiento_del_consumo": {
      "tendencia": null, "mes_anterior_consumo": null,
      "mes_anterior_dias": null, "mes_actual_consumo": null,
      "mes_actual_dias": null
    }
  },
  "bloque_informacion_calidad": {
    "cod_circuito": null, "cod_transformador": null
  },
  "bloque_conceptos_energia_chec": {
    "consumo_activa_kwh": null, "consumo_activa_valor": null,
    "contribucion_activa_kwh": null, "contribucion_activa_valor": null,
    "consumo_activa_pico_kwh": null, "consumo_activa_pico_valor": null,
    "consumo_activa_hora_no_pico_kwh": null, "consumo_activa_hora_no_pico_valor": null,
    "consumo_reactiva_hora_pico_kwh": null, "consumo_reactiva_hora_pico_valor": null,
    "consumo_reactiva_hora_no_pico_kwh": null, "consumo_reactiva_hora_no_pico_valor": null,
    "contribucion_activa_hora_pico_kwh": null, "contribucion_activa_hora_pico_valor": null,
    "contribucion_activa_hora_no_pico_kwh": null, "contribucion_activa_hora_no_pico_valor": null,
    "contribucion_reactiva_hora_pico_kwh": null, "contribucion_reactiva_hora_pico_valor": null,
    "contribucion_reactiva_hora_no_pico_kwh": null, "contribucion_reactiva_hora_no_pico_valor": null,
    "cuota_energia_kwh": null, "cuota_energia_valor": null,
    "cuota_contribucion_kwh": null, "cuota_contribucion_valor": null,
    "interes_financiacion_kwh": null, "interes_financiacion_valor": null,
    "intereses_de_mora_kwh": null, "intereses_de_mora_valor": null,
    "interes_mora_contribucion_kwh": null, "interes_mora_contribucion_valor": null,
    "saldo_anterior_kwh": null, "saldo_anterior_valor": null,
    "valor_por_servicio_de_energia": null
  },
  "bloque_ultimos_consumos": [
    {"mes": null, "consumo_kwh": null, "dias_consumo": null,
     "sabados": null, "dom_fest": null, "dias_habiles": null}
  ],
  "bloque_formula_tarifaria": {
    "generacion": null, "transmision": null, "distribucion": null,
    "comercializacion": null, "perdidas": null, "restricciones": null,
    "valor_kwh_cu": null
  }
}
"""


# ---------------------------------------------------------------------------
# PROMPT PÁGINA 2 — Solo para Prosumidores (gráficas de puntos)
# ---------------------------------------------------------------------------
PROMPT_PAGINA_2_PROSUMIDOR = """
Eres un sistema experto en lectura de gráficas de facturas CHEC (Colombia).
Esta imagen es la PÁGINA 2 de una factura de PROSUMIDOR (usuario con paneles solares).
Contiene dos gráficas que debes leer con máxima precisión. Devuelve SOLO JSON válido.

### REGLAS:
1. SOLO JSON puro. Sin markdown, sin explicaciones.
2. Valores numéricos con punto decimal (ej. 2.9, 0.0, 8.8).
3. Si un valor es ilegible → null. NUNCA inventes.

### GRÁFICA 1: "Acumulado horario del mes kWh"
Esta gráfica tiene:
- Eje X: horas 1 a 24 (marcadas con líneas verticales verdes).
- Línea AZUL con puntos y números: "activa_importada_kwh".
- Línea NARANJA con puntos y números: "activa_exportada_kwh".

PROCESO DE LECTURA OBLIGATORIO:
1. Ubica la hora 1 (primera línea vertical verde a la izquierda).
2. Busca el punto AZUL sobre esa línea → lee el número impreso al lado → ese es activa_importada_kwh.
3. Busca el punto NARANJA sobre esa línea → lee el número impreso al lado → ese es activa_exportada_kwh.
4. Avanza a la hora 2 y repite. Continúa hasta la hora 24.

IMPORTANTE:
- Los valores CAMBIAN de hora en hora. NO repitas el mismo valor.
- Patrón típico solar: importada alta de noche (~3-8 kWh), baja de día (~1-2 kWh).
  Exportada cero de noche, alta al mediodía (~8-10 kWh), baja en la tarde.
- Si la exportada es 0.0 para una hora, el punto naranja estará en el eje X (abajo).
- Hay EXACTAMENTE 24 puntos azules y 24 puntos naranjas.

### GRÁFICA 2: "Importación y exportación en kWh"
Esta gráfica tiene:
- Eje X: meses (ej. AGO, SEP, OCT, NOV, DIC, ENE).
- Puntos AZULES con diamantes: "consumo_importado_kwh" (consumo de la red).
- Puntos NARANJAS/VERDES con diamantes: "exportacion_kwh" (energía enviada a la red).
- Los valores numéricos están impresos junto a cada punto.

PROCESO: Lee cada mes de izquierda a derecha. Para cada mes, lee el valor azul (importado) y el naranja (exportado).

### ESQUEMA JSON:
{
  "bloque_acumulado_horario": [
    {"hora": 1, "activa_importada_kwh": ..., "activa_exportada_kwh": ...},
    {"hora": 2, "activa_importada_kwh": ..., "activa_exportada_kwh": ...},
    ...
    {"hora": 24, "activa_importada_kwh": ..., "activa_exportada_kwh": ...}
  ],
  "bloque_importacion_exportacion": [
    {"mes": "AGO", "consumo_importado_kwh": ..., "exportacion_kwh": ...},
    ...
  ]
}
"""


# ---------------------------------------------------------------------------
# PROMPT CLASIFICACIÓN — Detecta si es prosumidor
# ---------------------------------------------------------------------------
PROMPT_CLASIFICAR_FACTURA = """
Observa esta imagen de la PÁGINA 2 de una factura eléctrica CHEC (Colombia).
Responde SOLO con un JSON:

¿Contiene una gráfica titulada "Acumulado horario del mes kWh" con una línea AZUL y una línea NARANJA con puntos?
¿Contiene una gráfica titulada "Importación y exportación en kWh"?

Si AMBAS gráficas existen → es prosumidor.

{"es_prosumidor": true}  o  {"es_prosumidor": false}
"""


# ---------------------------------------------------------------------------
# Prompts legacy (mantener compatibilidad)
# ---------------------------------------------------------------------------
PROMPT_SISTEMA_EXTRACCION = PROMPT_PAGINA_2_PROSUMIDOR  # Alias
PROMPT_SISTEMA_TEMP = PROMPT_PAGINA_1  # Alias
PROMPT_SISTEMA_EXPLORATORIO = "Extract basic info from invoice in flat JSON."


# ---------------------------------------------------------------------------
# COLORES Y ESTILOS (Excel)
# ---------------------------------------------------------------------------
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
