"""
modal_client.py
----------------
Utilidad para interactuar con el Web Endpoint compatible con OpenAI alojado en Modal.
Incluye manejo de reintentos para soportar los Cold Starts (hasta 4-5 minutos).
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

class ModalClient:
    def __init__(self):
        self.endpoint_url = os.getenv("MODAL_ENDPOINT_URL")
        self.api_key = os.getenv("MODAL_API_KEY", "")
        
        if not self.endpoint_url:
            raise ValueError("MODAL_ENDPOINT_URL no encontrada en .env")
            
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def generate(self, prompt: str, system_prompt: str = None, json_mode: bool = False, timeout: int = 600, images_b64: list[str] = None, images_urls: list[str] = None) -> str:
        """
        Envía una solicitud al Web Endpoint de Modal.
        Incluye manejo de Cold Starts mediante reintentos.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if images_b64 or images_urls:
            user_content = [{"type": "text", "text": prompt}]
            
            if images_b64:
                for b64 in images_b64:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    })
                    
            if images_urls:
                for url in images_urls:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": url}
                    })
                    
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": prompt})

        # Payload para el Endpoint OpenAI Compatible en Modal
        payload = {
            "model": "Qwen/Qwen2.5-VL-72B-Instruct-AWQ", 
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.01,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            payload["max_tokens"] = 4000

        max_retries = 12
        retry_delay = 30 # Segundos entre reintentos para soportar Cold Starts de hasta 6 minutos

        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    print(f"     ⏱️ Esperando a que el contenedor de Modal inicie (Intento {attempt}/{max_retries})...")
                    
                response = requests.post(
                    self.endpoint_url,
                    headers=self.headers,
                    json=payload,
                    timeout=timeout
                )
                
                # Modal puede devolver 502/503/504 mientras el contenedor despierta
                if response.status_code in [502, 503, 504]:
                    print(f"     ⚠️ Contenedor en Modal aún no disponible (Cold Start) HTTP {response.status_code}.")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                        
                response.raise_for_status()
                result = response.json()
                
                # Log total a archivo para debug
                with open("debug_modal.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice:
                        return choice["message"]["content"]
                        
                return str(result)

            except requests.exceptions.RequestException as e:
                # Tratar timeout o errores de conexión como posible cold start
                if attempt < max_retries:
                    print(f"     ⚠️ Error temporal conectando a Modal: {e}. Reintentando en {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Error fatal en ModalClient tras {max_retries} intentos: {e}")
                    raise Exception(f"Modal execution FAILED: {e}")

        raise Exception("Modal execution FAILED: Excedido número máximo de reintentos por Cold Start.")
