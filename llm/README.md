# LLM

Snippets for serving, benchmarking, and evaluating Large Language Models (LLMs) and Vision-Language Models (VLMs).
Each subfolder is a self-contained implementation with its own configuration and README.

## Core ideas
- **Inference & Serving**: Containerizing open-weight models with **vLLM** behind an OpenAI-compatible API on serverless GPUs (Modal).
- **Performance Benchmarking**: Measuring throughput (`req/s`, `tok/s`) and latency (`TTFT`, `TPOT`, `ITL`) under concurrent load using `vllm bench serve`.
- **Quality & Behavior Evals**: Testing model outputs using deterministic checks and **LLM-as-a-Judge** rubrics (`promptfoo`).

## Implementations
| Folder | Model | Stack | Where it runs | Status |
|---|---|---|---|---|
| [vllm-ocr](vllm-ocr/) | `google/paligemma2-3b-mix-448` | vLLM + Modal (T4) | Cloud (Modal Serverless GPU) | Working |
| [evals](evals/) | `google/gemma-1.1-2b-it` | Promptfoo + vLLM + Modal (T4) | Local CLI + Ephemeral Cloud GPU | Working |
