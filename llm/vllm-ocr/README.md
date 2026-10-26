# vLLM Vision OCR on Modal

A minimal setup to containerize a vision-language model with **vLLM** and deploy it serverless on **Modal** using an NVIDIA T4 GPU.

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

## Benchmark

Run `vllm bench serve` (250 images at concurrency 4) against the deployed NVIDIA T4 endpoint:

```bash
modal run benchmark.py --num-prompts 250
```

### Cold Start vs. Warm Start (250 Images, Concurrency 4, NVIDIA T4)

| Metric | Cold Start | Warm Start | Improvement |
| :--- | :--- | :--- | :--- |
| **P99 TTFT (Tail Latency)** | `9,953.20 ms` | `2,906.69 ms` | **70.8% faster** |
| **Median TTFT** | `2,307.12 ms` | `1,937.73 ms` | **16.0% faster** |
| **Mean TTFT** | `2,196.58 ms` | `2,024.08 ms` | **7.9% faster** |
| **P99 TPOT** | `157.76 ms` | `102.05 ms` | **35.3% faster** |
| **Median TPOT** | `74.80 ms` | `69.52 ms` | **7.1% faster** |
| **Output Token Throughput** | `28.54 tok/s` | `30.12 tok/s` | **+5.5%** |
| **Total Token Throughput** | `972.02 tok/s` | `1,026.05 tok/s` | **+5.6%** |
| **Request Throughput** | `0.89 req/s` | `0.94 req/s` | **+5.6%** |
| **Total Duration** | `280.34 s` | `265.58 s` | **14.8s faster** |

#### Warm Start Output
```text
============ Serving Benchmark Result ============
Successful requests:                     250       
Failed requests:                         0         
Maximum request concurrency:             4         
Benchmark duration (s):                  265.58    
Total input tokens:                      264500    
Total generated tokens:                  8000      
Request throughput (req/s):              0.94      
Output token throughput (tok/s):         30.12     
Peak output token throughput (tok/s):    92.00     
Peak concurrent requests:                8.00      
Total token throughput (tok/s):          1026.05   
---------------Time to First Token----------------
Mean TTFT (ms):                          2024.08   
Median TTFT (ms):                        1937.73   
P99 TTFT (ms):                           2906.69   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          70.96     
Median TPOT (ms):                        69.52     
P99 TPOT (ms):                           102.05    
---------------Inter-token Latency----------------
Mean ITL (ms):                           68.74     
Median ITL (ms):                         79.04     
P99 ITL (ms):                            675.33    
==================================================
```

#### Cold Start Output
```text
============ Serving Benchmark Result ============
Successful requests:                     250       
Failed requests:                         0         
Maximum request concurrency:             4         
Benchmark duration (s):                  280.34    
Total input tokens:                      264500    
Total generated tokens:                  8000      
Request throughput (req/s):              0.89      
Output token throughput (tok/s):         28.54     
Peak output token throughput (tok/s):    92.00     
Peak concurrent requests:                8.00      
Total token throughput (tok/s):          972.02    
---------------Time to First Token----------------
Mean TTFT (ms):                          2196.58   
Median TTFT (ms):                        2307.12   
P99 TTFT (ms):                           9953.20   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          72.97     
Median TPOT (ms):                        74.80     
P99 TPOT (ms):                           157.76    
---------------Inter-token Latency----------------
Mean ITL (ms):                           70.69     
Median ITL (ms):                         78.48     
P99 ITL (ms):                            676.73    
==================================================
```

---

## TODO

* **Fine-Tuning (LoRA):** Out-of-the-box base model functionality is very minimal and requires strict task keywords (`"ocr"`). Fine-tune the model on a domain-specific dataset (e.g., license plates or receipts) for robust, end-to-end extraction.
