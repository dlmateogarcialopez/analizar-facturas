"""
runpod_client.py
----------------
Utilidad para interactuar con el API Serverless de RunPod.
"""

import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

class RunPodClient:
    def __init__(self):
        self.api_key = os.getenv("RUNPOD_API_KEY")
        self.endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
        
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY no encontrada en .env")
        if not self.endpoint_id:
            raise ValueError("RUNPOD_ENDPOINT_ID no encontrada en .env")
            
        self.run_url = f"https://api.runpod.ai/v2/{self.endpoint_id}/run"
        self.status_url = f"https://api.runpod.ai/v2/{self.endpoint_id}/status"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt: str, system_prompt: str = None, json_mode: bool = False, timeout: int = 600, images_b64: list[str] = None, images_urls: list[str] = None) -> str:
        """
        Envía una solicitud al endpoint de RunPod, soportando modelos de Visión (Multimodales).
        """
        # Adaptado al formato openai_route y openai_input probado por el usuario
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if images_b64 or images_urls:
            user_content = [{"type": "text", "text": prompt}]
            
            if images_b64:
                for b64 in images_b64:
                    # El extractor de PDF pasa codificación JPEG
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

        # Payload para RunPod Serverless simulando openai_route de vllm
        payload = {
            "input": {
                "openai_route": "/v1/chat/completions",
                "openai_input": {
                    "model": "Qwen/Qwen2-VL-7B-Instruct",
                    "messages": messages,
                    "max_tokens": 14000,
                    "temperature": 0.0,
                }
            }
        }
        
        if json_mode:
            # Algunas plantillas vLLM usan guided_json
            payload["input"]["openai_input"]["response_format"] = {"type": "json_object"}

        try:
            # 1. Iniciar el trabajo (Asíncrono)
            response = requests.post(
                self.run_url,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            job = response.json()
            job_id = job.get("id")
            
            if not job_id:
                raise Exception(f"No se pudo obtener el JOB_ID de RunPod: {job}")

            # 2. Poll del estado hasta que termine
            print(f"     ⏱️ Esperando respuesta de RunPod (Job: {job_id})...")
            while True:
                status_resp = requests.get(
                    f"{self.status_url}/{job_id}",
                    headers=self.headers,
                    timeout=30
                )
                status_resp.raise_for_status()
                result = status_resp.json()
                
                status = result.get("status")
                if status == "COMPLETED":
                    output = result.get("output", "")
                    
                    # Log total a archivo para debug
                    with open("debug_runpod.json", "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2)
                    
                    # Caso 1: El output es una lista (común en algunas plantillas vLLM/RunPod)
                    if isinstance(output, list) and len(output) > 0:
                        output = output[0]
                    
                    # Caso 2: El output es un diccionario con formato OpenAI o vLLM custom
                    if isinstance(output, dict):
                        # Formato Chat (OpenAI)
                        if "choices" in output and len(output["choices"]) > 0:
                            choice = output["choices"][0]
                            if "message" in choice:
                                return choice["message"]["content"]
                            if "tokens" in choice:
                                if isinstance(choice["tokens"], list):
                                    return "".join(map(str, choice["tokens"]))
                                return str(choice["tokens"])
                            if "text" in choice:
                                return choice["text"]
                        
                        # Formato Directo (Legacy Completion)
                        if "text" in output:
                            return output["text"]
                        
                        return str(output)
                    
                    # Caso 3: Es una cadena directa
                    return str(output)
                elif status == "FAILED":
                    raise Exception(f"RunPod execution FAILED: {result.get('error')}")
                
                # Esperar un segundo antes de volver a preguntar
                time.sleep(1)

        except Exception as e:
            print(f"❌ Error en RunPodClient: {e}")
            raise

runpod_instance = None

def get_runpod_client():
    global runpod_instance
    if runpod_instance is None:
        runpod_instance = RunPodClient()
    return runpod_instance
