# Multi-Model Benchmark: Qwen3-VL-2B vs SmolVLM2-2.2B

| Metric | SmolVLM2-2.2B (Baseline) | Qwen3-VL-2B (Current) | Delta / Winner |
|---|---|---|---|
| Model Checkpoint Size | ~9.0 GB | ~4.3 GB | -52% disk/download footprint |
| Completion Success Rate | 52/56 (92.8%) | **56/56 (100%)** | +7.2% reliability |
| Context-Aware Latency (Median) | 8.2 s | **5.0 s** | -39% latency reduction |
| Context-Aware Latency (p95) | 9.5 s | **6.4 s** | -32% tail latency |
| Repetition / Context Copying | 4 verbatim copies | 0 (eliminated via retry) | Context-Aware winner |
| Diagram / Chart Grounding | Fragmented OCR | Reads full equations/labels | Visual Grounding winner |
