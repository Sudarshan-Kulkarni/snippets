# Text-Based Model Evals (Promptfoo + Gemma-1.1-2B-IT)

Evaluates `google/gemma-1.1-2b-it` using **Promptfoo** on an ephemeral NVIDIA T4 GPU:
1. Spins up a temporary `vllm serve` endpoint.
2. Runs Promptfoo test cases comparing two prompt templates using both **deterministic checks** (`icontains`, `not-icontains`, `javascript`) and **LLM-as-a-Judge** (`llm-rubric` pointing at the same Gemma endpoint).
3. Saves the evaluation results to `results.json` and the local Promptfoo database.
4. Automatically spins down the GPU container as soon as the eval finishes.

---

## Run Evals

```bash
python run_evals.py
```

---

## View Results Offline (No GPU Running)

```bash
npx -y -p node@22 -p promptfoo@latest promptfoo view
```
