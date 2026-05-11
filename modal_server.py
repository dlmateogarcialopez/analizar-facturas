"""
modal_server.py
----------------
Script para desplegar un Web Endpoint de vLLM (Compatible con OpenAI) en Modal.
Optimizado para Qwen2.5-VL-72B-Instruct-AWQ con versiones estables.
"""

import os
import modal

# Configuración de Imagen: Forzamos versiones estables para evitar errores de Tokenizer y RoPE
vllm_image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "vllm==0.8.2",
        "transformers==4.49.0",
        "fastapi",
        "uvicorn",
        "accelerate",
        "qwen-vl-utils",
        "autoawq"
    )
    .env({
        "HF_HUB_DISABLE_XET": "1",
        "VLLM_USE_V1": "0"      # Aseguramos motor V0 estable
    })
    .run_commands(
        "mkdir -p /usr/local/lib/python3.10/site-packages/pyairports",
        "touch /usr/local/lib/python3.10/site-packages/pyairports/__init__.py",
        "echo 'AIRPORT_LIST = []' > /usr/local/lib/python3.10/site-packages/pyairports/airports.py"
    )
)

app = modal.App("vllm-openai-server")

MODEL_NAME = "Qwen/Qwen2.5-VL-72B-Instruct-AWQ"

def download_model():
    import huggingface_hub
    huggingface_hub.snapshot_download(
        repo_id=MODEL_NAME,
        ignore_patterns=["*.pt", "*.bin"],
    )

image_con_modelo = vllm_image.run_function(
    download_model,
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=3600,
)

@app.function(
    image=image_con_modelo,
    gpu="A100-80GB",
    secrets=[modal.Secret.from_name("huggingface-secret")],
    scaledown_window=300,
    timeout=1800,
)
@modal.web_server(port=8000, startup_timeout=600)
def serve():
    import subprocess
    import sys
    
    EXPECTED_TOKEN = "as-IOXTeApdSmKLQ2gPUiSanh"
    
    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL_NAME,
        "--served-model-name", MODEL_NAME,
        "--host", "0.0.0.0",
        "--port", "8000",
        "--max-model-len", "16384",
        "--trust-remote-code",
        "--enforce-eager",
        "--gpu-memory-utilization", "0.92",
        "--dtype", "float16",
        "--quantization", "awq_marlin",
        "--limit-mm-per-prompt", "image=4",
        "--api-key", EXPECTED_TOKEN
    ]
    
    subprocess.Popen(cmd)
