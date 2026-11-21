# Stratified Group K-Fold Cross-Validation Methodology

## 1. Overview
Standard random K-Fold cross-validation is not suitable for Wikipedia image accessibility evaluation because Wikipedia articles contain multiple related images and shared textual context (lead summaries, infoboxes, and section text). Splitting images randomly across folds causes **context data leakage**, where a model is evaluated on images whose accompanying article text it has already seen during prompt tuning.

To prevent this while providing rigorous cross-validation across all domains, this project implements **Stratified Group K-Fold Cross-Validation** (`benchmark/stratified_group_kfold.py`).

## 2. Methodology & Guarantees
- **Grouping (Article-Cluster Level):** An entire Wikipedia article and all its image occurrences are strictly allocated to either the training/tuning partition or the held-out test partition for any given fold.
- **Stratification (Domain Balance):** Categories (animals, nature, monuments, objects, biographies, diagrams, processes, maps, charts, flags, artworks, and astronomy) are partitioned evenly across all $K$ folds.
- **Full Coverage ($K = 5$):** Every single article and image occurrence serves as a completely unseen test case in exactly one fold, ensuring comprehensive evaluation without cherry-picking.

## 3. Five-Fold Partition Summary
- **Dataset:** 28 Wikipedia articles, 56 frozen image occurrences (`benchmark/manifests/live-v2.jsonl`).
- **Splits:**
  - **Fold 1:** 6 test articles (12 image occurrences)
  - **Fold 2:** 6 test articles (12 image occurrences)
  - **Fold 3:** 6 test articles (12 image occurrences)
  - **Fold 4:** 5 test articles (10 image occurrences)
  - **Fold 5:** 5 test articles (10 image occurrences)
- Full partition manifests are generated in `benchmark/results/kfold/fold_assignments.json`.

## 4. Execution & Reproducibility
```sh
# Run cross-validation split generation and summary
PYTHONPATH=. python3 benchmark/evaluate_kfold.py

# Verify zero-leakage constraints via unit test
python3 -m unittest tests/test_kfold.py
```
