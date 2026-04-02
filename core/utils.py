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
