"""
Stratified Group K-Fold cross-validation module for Wikipedia Image Accessibility Evaluation.

Guarantees:
1. Grouping: All images and occurrences originating from the same Wikipedia article
   are strictly confined to a single fold to avoid article-context data leakage.
2. Stratification: Every fold maintains a balanced distribution across all domain categories
   (photos, biographies, diagrams, processes, charts, maps, flags, artworks, astronomy).
"""

import collections
import json
import random
from typing import Dict, List, Tuple, Any

def get_articles_and_categories(manifest_path: str = "benchmark/manifests/live-v2.jsonl") -> List[Tuple[str, str]]:
    """Extract unique article slugs and their domain categories from manifest."""
    seen = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            slug = d.get("slug")
            cat = d.get("category")
            if slug and cat and slug not in seen:
                seen[slug] = cat
    return sorted(list(seen.items()), key=lambda x: x[0])

def generate_stratified_group_k_folds(
    articles: List[Tuple[str, str]], 
    n_splits: int = 5, 
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Partition articles into n_splits folds ensuring stratification by category
    and zero leakage across shared article groups.
    """
    random.seed(seed)
    cat_to_groups = collections.defaultdict(list)
    for slug, cat in articles:
        cat_to_groups[cat].append(slug)
    
    folds = [[] for _ in range(n_splits)]
    cat_counts = [collections.defaultdict(int) for _ in range(n_splits)]
    
    # Sort categories by frequency descending for greedy balanced bin packing
    sorted_cats = sorted(cat_to_groups.keys(), key=lambda c: len(cat_to_groups[c]), reverse=True)
    
    for cat in sorted_cats:
        groups = cat_to_groups[cat][:]
        random.shuffle(groups)
        for g in groups:
            # Assign to the fold with minimum occurrences of this category, breaking ties by fold size
            best_fold = min(range(n_splits), key=lambda i: (cat_counts[i][cat], len(folds[i])))
            folds[best_fold].append(g)
            cat_counts[best_fold][cat] += 1
            
    fold_splits = []
    all_slugs = set(slug for slug, _ in articles)
    for i, test_slugs in enumerate(folds):
        train_slugs = sorted(list(all_slugs - set(test_slugs)))
        fold_splits.append({
            "fold": i + 1,
            "test_articles": sorted(test_slugs),
            "train_articles": train_slugs,
            "category_distribution": dict(cat_counts[i])
        })
    return fold_splits

if __name__ == "__main__":
    articles = get_articles_and_categories()
    folds = generate_stratified_group_k_folds(articles, n_splits=5)
    print(f"Generated {len(folds)}-fold StratifiedGroupKFold across {len(articles)} articles:")
    for f in folds:
        print(f"  Fold {f['fold']}: {len(f['test_articles'])} test articles, {len(f['train_articles'])} train/tuning articles")
        print(f"    Test set: {', '.join(f['test_articles'])}")
