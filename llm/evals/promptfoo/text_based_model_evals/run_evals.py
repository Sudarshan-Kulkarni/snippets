import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
import modal

HERE = Path(__file__).parent
DOCKERFILE_PATH = (HERE / "../../../vllm-ocr/Dockerfile").resolve()
APP_NAME = "vllm-gemma-text-eval"
MODEL_NAME = "google/gemma-1.1-2b-it"

app = modal.App(APP_NAME)
image = modal.Image.from_dockerfile(DOCKERFILE_PATH)
hf_cache_volume = modal.Volume.from_name("vllm-model-cache", create_if_missing=True)

# Gemma-2's default Hugging Face template rejects `role: "system"`, which Promptfoo's
# `llm-rubric` judge sends. This template prepends any system message to the first user turn.
GEMMA_CHAT_TEMPLATE = (
    "{{ bos_token }}"
    "{% if messages[0]['role'] == 'system' %}"
    "{% set system_message = messages[0]['content'] + '\\n\\n' %}"
    "{% set messages = messages[1:] %}"
    "{% else %}"
    "{% set system_message = '' %}"
    "{% endif %}"
    "{% for message in messages %}"
    "{% if (message['role'] == 'assistant') %}{% set role = 'model' %}{% else %}{% set role = message['role'] %}{% endif %}"
    "{{ '<start_of_turn>' + role + '\\n' + (system_message if loop.first else '') + message['content'] | trim + '<end_of_turn>\\n' }}"
    "{% endfor %}"
    "{% if add_generation_prompt %}{{'<start_of_turn>model\\n'}}{% endif %}"
)


@app.function(
    image=image,
    gpu="T4",
    volumes={"/root/.cache/huggingface": hf_cache_volume},
    secrets=[modal.Secret.from_name("hf-secret")],
    timeout=900,
    scaledown_window=60,
    max_containers=1,
)
@modal.concurrent(max_inputs=16)
@modal.web_server(port=8000, startup_timeout=600)
def serve():
    """Starts vLLM server for google/gemma-1.1-2b-it on an NVIDIA T4 GPU."""
    os.environ["TRITON_CACHE_DIR"] = "/root/.cache/huggingface/triton"
    os.environ["VLLM_CACHE_ROOT"] = "/root/.cache/huggingface/vllm"

    template_path = "/tmp/gemma_chat_template.jinja"
    with open(template_path, "w") as f:
        f.write(GEMMA_CHAT_TEMPLATE)

    cmd = [
        "vllm", "serve", "google/gemma-1.1-2b-it",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--dtype", "float16",
        "--max-model-len", "4096",
        "--gpu-memory-utilization", "0.90",
        "--chat-template", template_path,
        "--enforce-eager",
    ]
    subprocess.Popen(cmd)


def wait_until_ready(base_url: str, timeout_s: int = 420):
    models_url = f"{base_url.rstrip('/')}/v1/models"
    print(f"Waiting for vLLM server to finish loading {MODEL_NAME} at {models_url} ...", flush=True)
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            with urllib.request.urlopen(models_url, timeout=180) as resp:
                if resp.status == 200:
                    print(f"vLLM server is ready! (took {time.time() - start:.1f}s)\n", flush=True)
                    return
        except Exception as e:
            print(f"  Still warming up ({int(time.time() - start)}s elapsed): {e}", flush=True)
            time.sleep(5)
    raise TimeoutError(f"vLLM server did not become ready within {timeout_s}s.")


if __name__ == "__main__":
    modal_bin = str(Path(sys.executable).parent / "modal")
    print(f"1. Deploying temporary Modal T4 app '{APP_NAME}'...", flush=True)
    subprocess.run([modal_bin, "deploy", str( Path(__file__).resolve() )], check=True)

    try:
        fn = modal.Function.from_name(APP_NAME, "serve")
        web_url = fn.get_web_url()
        vllm_base_url = f"{web_url.rstrip('/')}/v1"
        print(f"Modal Endpoint URL: {vllm_base_url}", flush=True)

        # Trigger container start and wait until model is loaded in VRAM
        wait_until_ready(web_url)

        print("2. Running Promptfoo evaluation suite...", flush=True)
        env = os.environ.copy()
        env["VLLM_BASE_URL"] = vllm_base_url
        env["PROMPTFOO_DISABLE_TELEMETRY"] = "1"

        results_path = HERE / "results.json"
        cmd = [
            "npx", "-y", "-p", "node@22", "-p", "promptfoo@latest",
            "promptfoo", "eval",
            "-c", str(HERE / "promptfooconfig.yaml"),
            "-o", str(results_path),
        ]
        subprocess.run(cmd, cwd=HERE, env=env, check=False)
        print(f"\n3. Results saved to {results_path}", flush=True)
    finally:
        print(f"\n4. Tearing down Modal app '{APP_NAME}' and stopping GPU container immediately...", flush=True)
        subprocess.run([modal_bin, "app", "stop", "-y", APP_NAME], check=False)
        print("Done! Modal GPU container is stopped. Run `npx -y -p node@22 -p promptfoo@latest promptfoo view` to inspect results offline.", flush=True)
