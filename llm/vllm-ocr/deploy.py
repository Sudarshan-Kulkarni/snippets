import os
import subprocess
from pathlib import Path
import modal

# Helper to load .env without external dependencies
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

dockerfile_path = Path(__file__).parent / "Dockerfile"
MODEL_NAME = "google/paligemma2-3b-mix-448"

app = modal.App("vllm-ocr-paligemma")


image = modal.Image.from_dockerfile(dockerfile_path)

hf_cache_volume = modal.Volume.from_name("vllm-model-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu="T4",                       
    volumes={"/root/.cache/huggingface": hf_cache_volume},
    secrets=[modal.Secret.from_name("hf-secret")], 
    timeout=600,
    scaledown_window=300,
    max_containers=1,
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=8000, startup_timeout=600)
def serve():
    """Starts the vLLM OpenAI-compatible server as a background subprocess."""
    model_name = "google/paligemma2-3b-mix-448"
    cmd = [
        "vllm", "serve", model_name,
        "--host", "0.0.0.0",
        "--port", "8000",
        "--dtype", "float16",
        "--max-model-len", "4096",
        "--gpu-memory-utilization", "0.90",
        "--enforce-eager",
        "--trust-remote-code",
    ]
    subprocess.Popen(cmd)
