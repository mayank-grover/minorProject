"""Unit tests for Stratified Group K-Fold scoring module."""

import unittest
from benchmark.kfold_scoring import compute_fold_metrics

class TestKFoldScoring(unittest.TestCase):
    def test_scoring_aggregation(self):
        metrics = compute_fold_metrics()
        self.assertIn("aggregate", metrics)
        self.assertIn("folds", metrics)
        self.assertEqual(len(metrics["folds"]), 5)
        self.assertGreaterEqual(metrics["aggregate"]["cross_fold_mean_factuality"], 1.0)
        self.assertLessEqual(metrics["aggregate"]["cross_fold_mean_factuality"], 5.0)

if __name__ == "__main__":
    unittest.main()
