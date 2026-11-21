"""Unit tests for Multi-Model Benchmark Comparison module."""

import unittest
from benchmark.compare_models import run_multi_model_benchmark

class TestMultiModelBenchmark(unittest.TestCase):
    def test_benchmark_runs_and_identifies_models(self):
        models = run_multi_model_benchmark()
        self.assertIn("Qwen3-VL-2B-Instruct", models)
        self.assertIn("SmolVLM2-2.2B-Instruct", models)
        self.assertGreater(models["Qwen3-VL-2B-Instruct"]["success_rate"], models["SmolVLM2-2.2B-Instruct"]["success_rate"])
        self.assertLess(models["Qwen3-VL-2B-Instruct"]["context_aware_latency_median_s"], models["SmolVLM2-2.2B-Instruct"]["context_aware_latency_median_s"])

if __name__ == "__main__":
    unittest.main()
