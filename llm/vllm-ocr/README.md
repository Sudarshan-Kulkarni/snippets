# vLLM Vision OCR on Modal

A minimal setup to containerize a vision-language model with **vLLM** and deploy it serverless on **Modal** using an NVIDIA L4 GPU.

* **Model:** [`google/paligemma2-3b-mix-448`](https://huggingface.co/google/paligemma2-3b-mix-448)
* **Storage:** Persistent Modal Volume (`vllm-model-cache`) to cache weights across cold starts.

---

## Deploy

```bash
modal deploy deploy.py
```

---

## Test

```bash
python test_client.py --image path/to/image.png --prompt "ocr"
```

---

## TODO

* **Fine-Tuning (LoRA):** Out-of-the-box base model functionality is very minimal and requires strict task keywords (`"ocr"`). Fine-tune the model on a domain-specific dataset (e.g., license plates or receipts) for robust, end-to-end extraction.
