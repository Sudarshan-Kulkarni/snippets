# Base CUDA image with Ubuntu
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# Environment settings
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface

# Install C compiler, Python, and system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-pip \
    python3-dev \
    python-is-python3 \
    git \
    curl \
    ca-certificates \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install vLLM with vision support
RUN pip3 install --upgrade pip && \
    pip3 install \
    "vllm>=0.6.3" \
    torchvision \
    huggingface_hub

# Expose standard OpenAI API port
EXPOSE 8000

# Default entrypoint
CMD ["vllm", "serve", "google/paligemma2-3b-mix-448", "--host", "0.0.0.0", "--port", "8000", "--dtype", "float16", "--enforce-eager", "--trust-remote-code"]
