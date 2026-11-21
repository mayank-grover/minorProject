"""Unit tests for StratifiedGroupKFold partitioning."""

import unittest
from benchmark.stratified_group_kfold import generate_stratified_group_k_folds

class TestStratifiedGroupKFold(unittest.TestCase):
    def setUp(self):
        self.articles = [
            ("A1", "photo"), ("A2", "photo"),
            ("A3", "diagram"), ("A4", "diagram"),
            ("A5", "chart"), ("A6", "chart"),
            ("A7", "map"), ("A8", "map"),
            ("A9", "bio"), ("A10", "bio")
        ]

    def test_zero_leakage_across_folds(self):
        """Test that an article slug never appears in both train and test sets of any fold."""
        folds = generate_stratified_group_k_folds(self.articles, n_splits=5)
        self.assertEqual(len(folds), 5)
        for fold in folds:
            test_set = set(fold["test_articles"])
            train_set = set(fold["train_articles"])
            self.assertTrue(test_set.isdisjoint(train_set), "Data leakage detected: article in both train and test!")
            self.assertEqual(len(test_set) + len(train_set), len(self.articles))

    def test_complete_coverage(self):
        """Test that every article is evaluated as a test instance exactly once."""
        folds = generate_stratified_group_k_folds(self.articles, n_splits=5)
        all_tested = []
        for fold in folds:
            all_tested.extend(fold["test_articles"])
        self.assertEqual(sorted(all_tested), sorted([slug for slug, _ in self.articles]))

if __name__ == "__main__":
    unittest.main()
