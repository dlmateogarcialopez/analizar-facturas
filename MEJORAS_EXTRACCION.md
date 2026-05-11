# Mejoras para Reducir Errores de Extracción LLM

## 1. Mejoras en el Prompt (core/constants.py)

- Incluir ejemplos concretos de valores esperados (estratos válidos, formatos de fecha, rangos de consumo).
- Agregar restricciones explícitas: "devuelve SOLO valores numéricos para consumo_kwh", "fecha en formato YYYY-MM-DD".
- Usar few-shot examples: 1-2 ejemplos de facturas correctamente parseadas dentro del system prompt.

## 2. Post-validación con Reglas de Negocio (sin LLM)

Después de la extracción, aplicar reglas de validación en `extractor.py` o un paso nuevo en `pipeline.py`:

- **Rangos válidos**:
  - consumo_kwh: entre 0 y 5000
  - estrato: valores {1, 2, 3, 4}
  - valor_factura: valores positivos razonables
- **Fechas coherentes**: período de facturación válido (ej: mes anterior no futuro)
- **Cálculos cruzados**: consumo_kwh = lectura_actual - lectura_anterior
- **Campos requeridos**: verificar que campos críticos no estén vacíos

## 3. Output Schema Estructurado

- Usar `response_format` del OpenAI SDK para pedir JSON con schema predefinido en lugar de texto libre.
- Definir tipos explícitos: enteros para consumo, strings para fechas, floats para valores monetarios.

## 4. Reintento Selectivo

- Si ciertos campos fallan consistentemente, hacer una llamada específica solo para esos campos con un prompt enfocado.
- Mantener un log de campos que requieren reintentos para identificar patrones.

## 5. Modelo de Visión Más Potente

- Cambiar a un modelo de visión más avanzado (ej: Qwen2-VL-72B, GPT-4o, Claude 3.5 Sonnet, Gemini 2.0 Flash).
- Modelos más grandes generalmentetienen mejor precisión en OCR y comprensión de layouts complejos.
- Considerar costo vs. precisión: modelos más capaces suelen ser más caros por llamada.
- Verificar que el nuevo modelo soporte el mismo formato de input (base64 JPEG) y sea compatible con la API de RunPod o del proveedor.

## 6. Mejora del System Prompt

- Ser más explícito sobre qué NO hacer: "no inventar datos", "devolver null si no estás seguro".
- Agregar advertencias sobre errores comunes que el modelo tiende a cometer.
- Incluir el rango esperado de cada campo numérico.

## Prioridad Recomendada

1. **Primero**: Post-validación con reglas de negocio (más rápido, sin costo adicional)
2. **Segundo**: Output schema estructurado (mejora significativa, requiere cambio mínimo)
3. **Tercero**: Few-shot examples en prompt (mejora moderada)
4. **Cuarto**: Modelo de visión más potente (mayor costo por llamada, mayor precisión)
5. **Quinto**: Reintento selectivo para campos problemáticos (si aún hay errores)
