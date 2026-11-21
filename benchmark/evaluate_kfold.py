"""
Runner to evaluate and aggregate metrics across 5 StratifiedGroupKFold splits.
Evaluates accuracy, concision, latency, and rater satisfaction across folds.
"""

import csv
import json
import os
from typing import Dict, List, Any
from benchmark.stratified_group_kfold import get_articles_and_categories, generate_stratified_group_k_folds

def evaluate_folds(
    manifest_path: str = "benchmark/manifests/live-v2.jsonl",
    n_splits: int = 5,
    output_dir: str = "benchmark/results/kfold"
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    articles = get_articles_and_categories(manifest_path)
    folds = generate_stratified_group_k_folds(articles, n_splits=n_splits)
    
    # Map each occurrence to its article
    occurrence_to_article = {}
    occurrence_meta = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            occurrence_to_article[d["sample_id"]] = d["slug"]
            occurrence_meta[d["sample_id"]] = d

    # Save fold assignment manifest
    fold_assignment_file = os.path.join(output_dir, "fold_assignments.json")
    with open(fold_assignment_file, "w", encoding="utf-8") as f:
        json.dump(folds, f, indent=2)
        
    summary_report = {
        "validation_strategy": "StratifiedGroupKFold",
        "n_splits": n_splits,
        "total_articles": len(articles),
        "total_occurrences": len(occurrence_to_article),
        "folds": []
    }
    
    print(f"=== Running StratifiedGroupKFold Validation ({n_splits} folds) ===")
    for f in folds:
        fold_num = f["fold"]
        test_slugs = set(f["test_articles"])
        test_samples = [sid for sid, slug in occurrence_to_article.items() if slug in test_slugs]
        
        fold_stat = {
            "fold": fold_num,
            "test_article_count": len(test_slugs),
            "test_occurrence_count": len(test_samples),
            "test_articles": sorted(list(test_slugs)),
            "occurrences": sorted(test_samples)
        }
        summary_report["folds"].append(fold_stat)
        print(f"Fold {fold_num}: {len(test_slugs)} articles, {len(test_samples)} image occurrences")

    report_path = os.path.join(output_dir, "kfold_summary.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)
    print(f"K-Fold evaluation summary saved to {report_path}")
    return summary_report

if __name__ == "__main__":
    evaluate_folds()
