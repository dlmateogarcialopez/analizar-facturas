"""
utils.py
--------
Utilidades compartidas para procesamiento de datos y flujos resilientes.
"""
import time
from functools import wraps

def get_nested_val(data: dict, path: str, default=""):
    """Accede a valores en un diccionario anidado usando puntos (ej. 'bloque.campo')."""
    if not path or not data:
        return default
    
    parts = path.split(".")
    current = data
    for p in parts:
        if isinstance(current, dict):
            current = current.get(p, default)
        else:
            return default
    return current

def with_retry(retries: int = 3, backoff: int = 15):
    """
    Decorador genérico para aplicar lógicas de reintento sobre llamadas APIs propensas a error temporal.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retries - 1:
                        wait_time = backoff * (attempt + 1)
                        print(f"     ⚠️ Fallo temporal en {func.__name__}. Reintentando en {wait_time}s... (Intento {attempt+1}/{retries})")
                        time.sleep(wait_time)
            
            # Si se acaban los intentos, elevamos la última excepción
            # para que el cliente (extractor o analyzer) maneje el "fallback" a nivel de negocio.
            raise Exception(f"Excedidos los {retries} intentos. Último error: {last_exception}") from last_exception
        return wrapper
    return decorator

def clean_float(value) -> float:
    """Extrae un número float limpio a partir de una cadena con comas y puntos."""
    if value is None: return 0.0
    if isinstance(value, (int, float)): return float(value)
    
    s = str(value).replace('$', '').replace(' ', '').strip()
    if not s: return 0.0
    
    # Manejar formatos de separadores combinados (ej. 1.234,50 o 1,234.50)
    if ',' in s and '.' in s:
        last_comma = s.rfind(',')
        last_dot = s.rfind('.')
        if last_dot > last_comma:
            s = s.replace(',', '')
        else:
            s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        # Si la última coma tiene 2 dígitos, asumimos que es decimal (ej. 1500,50)
        if len(s) - s.rfind(',') - 1 == 2:
            s = s.replace(',', '', s.count(',') - 1).replace(',', '.')
        else:
            s = s.replace(',', '') # Miles (ej. 1,500,000)
    elif '.' in s:
        # Si el último punto tiene 2 dígitos, asumimos que es decimal
        if len(s) - s.rfind('.') - 1 == 2:
            s = s.replace('.', '', s.count('.') - 1)
        else:
            s = s.replace('.', '') # Miles (ej. 1.500.000)
            
    try:
        return float(s)
    except ValueError:
        import re
        d = re.sub(r'[^\d.]', '', s)
        try:
            return float(d) if d else 0.0
        except:
            return 0.0

def get_nested_val(d: dict, path: str, default=None):
    """Obtiene un valor anidado en un diccionario usando sintaxis de punto (ej. 'a.b.c')."""
    if not isinstance(d, dict) or not path:
        return default
    keys = path.split('.')
    current = d
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k, default)
            if current is None:
                return default
        else:
            return default
    return current
