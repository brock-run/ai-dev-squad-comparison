#!/usr/bin/env python3
"""Cohen's Kappa CI Validation Script

Computes Cohen's kappa with confidence intervals for judge results.
"""

import json
import sys
import argparse
import math
from typing import List, Dict, Any, Tuple


def compute_cohens_kappa(predictions: List[bool], ground_truth: List[bool]) -> float:
    """Compute Cohen's kappa coefficient."""
    if len(predictions) != len(ground_truth):
        return 0.0
    
    n = len(predictions)
    if n == 0:
        return 0.0
    
    # Compute agreement matrix
    tp = sum(1 for p, t in zip(predictions, ground_truth) if p and t)
    tn = sum(1 for p, t in zip(predictions, ground_truth) if not p and not t)
    fp = sum(1 for p, t in zip(predictions, ground_truth) if p and not t)
    fn = sum(1 for p, t in zip(predictions, ground_truth) if not p and t)
    
    # Observed agreement
    po = (tp + tn) / n
    
    # Expected agreement by chance
    pred_pos = sum(predictions) / n
    pred_neg = 1 - pred_pos
    truth_pos = sum(ground_truth) / n
    truth_neg = 1 - truth_pos
    
    pe = (pred_pos * truth_pos) + (pred_neg * truth_neg)
    
    # Cohen's kappa
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    
    kappa = (po - pe) / (1 - pe)
    return kappa


def bootstrap_kappa_ci(predictions: List[bool], ground_truth: List[bool], 
                      n_bootstrap: int = 1000, confidence: float = 0.95) -> Tuple[float, float]:
    """Compute bootstrap confidence interval for kappa."""
    import random
    
    n = len(predictions)
    kappas = []
    
    for _ in range(n_bootstrap):
        # Bootstrap sample
        indices = [random.randint(0, n-1) for _ in range(n)]
        boot_pred = [predictions[i] for i in indices]
        boot_truth = [ground_truth[i] for i in indices]
        
        kappa = compute_cohens_kappa(boot_pred, boot_truth)
        kappas.append(kappa)
    
    # Compute confidence interval
    kappas.sort()
    alpha = 1 - confidence
    lower_idx = int(alpha / 2 * n_bootstrap)
    upper_idx = int((1 - alpha / 2) * n_bootstrap)
    
    return kappas[lower_idx], kappas[upper_idx]


def extract_predictions_from_results(results_file: str, dataset_file: str = None, 
                                    split_filter: str = None) -> Tuple[List[bool], List[bool], Dict[str, Any]]:
    """Extract predictions and ground truth from judge results."""
    
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        sys.exit(1)
    
    # Load dataset for additional metadata if provided
    dataset_items = {}
    if dataset_file:
        try:
            with open(dataset_file, 'r') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        dataset_items[item['id']] = item
        except Exception as e:
            print(f"⚠️  Warning: Could not load dataset: {e}")
    
    predictions = []
    ground_truth = []
    per_type_stats = {}
    
    results = data.get("results", [])
    
    for result in results:
        if result.get("ground_truth") is None:
            continue  # Skip items without ground truth
        
        # Filter by split if requested
        item_id = result.get("id", "")
        if split_filter and item_id in dataset_items:
            item_split = dataset_items[item_id].get("split", "train")
            if item_split != split_filter:
                continue
        
        evaluation = result.get("evaluation", {})
        method_results = evaluation.get("results", [])
        
        if not method_results:
            continue
        
        # Use majority vote across methods
        equivalent_votes = sum(1 for r in method_results if r.get("equivalent", False))
        predicted_equivalent = equivalent_votes > len(method_results) / 2
        
        predictions.append(predicted_equivalent)
        ground_truth.append(result["ground_truth"])
        
        # Track per-type stats
        artifact_type = result.get("artifact_type", "unknown")
        if artifact_type not in per_type_stats:
            per_type_stats[artifact_type] = {"predictions": [], "ground_truth": []}
        
        per_type_stats[artifact_type]["predictions"].append(predicted_equivalent)
        per_type_stats[artifact_type]["ground_truth"].append(result["ground_truth"])
    
    return predictions, ground_truth, per_type_stats


def main():
    parser = argparse.ArgumentParser(description="Compute Cohen's kappa with CI")
    parser.add_argument("results_file", help="Judge results JSON file")
    parser.add_argument("--dataset", help="Dataset JSONL file for split filtering")
    parser.add_argument("--split", default="test", help="Dataset split to analyze (default: test)")
    parser.add_argument("--min-kappa", type=float, default=0.75,
                       help="Minimum required kappa (default: 0.75)")
    parser.add_argument("--confidence", type=float, default=0.95,
                       help="Confidence level for CI (default: 0.95)")
    parser.add_argument("--bootstrap", type=int, default=1000,
                       help="Bootstrap samples (default: 1000)")
    
    args = parser.parse_args()
    
    # Extract predictions and ground truth
    predictions, ground_truth, per_type_stats = extract_predictions_from_results(
        args.results_file, args.dataset, args.split
    )
    
    if len(predictions) == 0:
        print("❌ No predictions with ground truth found")
        if args.split:
            print(f"   (Filtered for split: {args.split})")
        sys.exit(1)
    
    # Compute overall kappa
    kappa = compute_cohens_kappa(predictions, ground_truth)
    
    # Compute confidence interval
    if len(predictions) >= 10:  # Need sufficient data for bootstrap
        ci_lower, ci_upper = bootstrap_kappa_ci(
            predictions, ground_truth, 
            args.bootstrap, args.confidence
        )
    else:
        # Use simple approximation for small samples
        ci_lower = max(0.0, kappa - 0.1)
        ci_upper = min(1.0, kappa + 0.1)
    
    # Print results
    print(f"📊 Cohen's Kappa Analysis")
    print(f"========================")
    print(f"Sample size: {len(predictions)}")
    if args.split:
        print(f"Split: {args.split}")
    print(f"Overall kappa: {kappa:.3f}")
    print(f"{args.confidence:.0%} CI: [{ci_lower:.3f}, {ci_upper:.3f}]")
    print(f"Required minimum: {args.min_kappa:.3f}")
    
    # Per-type kappa analysis
    if per_type_stats:
        print(f"\n📈 Per-Type Kappa:")
        for artifact_type, stats in per_type_stats.items():
            if len(stats["predictions"]) >= 2:
                type_kappa = compute_cohens_kappa(stats["predictions"], stats["ground_truth"])
                print(f"   {artifact_type}: κ={type_kappa:.3f} (n={len(stats['predictions'])})")
    
    # Confusion matrix
    tp = sum(1 for p, t in zip(predictions, ground_truth) if p and t)
    tn = sum(1 for p, t in zip(predictions, ground_truth) if not p and not t)
    fp = sum(1 for p, t in zip(predictions, ground_truth) if p and not t)
    fn = sum(1 for p, t in zip(predictions, ground_truth) if not p and t)
    
    print(f"\n🔢 Confusion Matrix:")
    print(f"   TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
    if fp + tn > 0:
        fp_rate = fp / (fp + tn)
        print(f"   False Positive Rate: {fp_rate:.1%}")
    
    # Check against threshold
    if kappa >= args.min_kappa and ci_lower >= args.min_kappa * 0.9:  # Allow 10% margin on CI
        print(f"\n✅ PASSED: Kappa {kappa:.3f} ≥ {args.min_kappa:.3f}")
        print(f"✅ CI lower bound {ci_lower:.3f} within acceptable range")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED: Kappa {kappa:.3f} < {args.min_kappa:.3f} or CI too low")
        if ci_lower < args.min_kappa * 0.9:
            print(f"❌ CI lower bound {ci_lower:.3f} < {args.min_kappa * 0.9:.3f}")
        
        # Provide guidance for small datasets
        if len(predictions) < 50:
            print(f"\n💡 Note: Small sample size ({len(predictions)}) makes kappa unstable.")
            print(f"   Consider expanding dataset to ≥200 items for reliable CI.")
        
        sys.exit(1)


if __name__ == "__main__":
    main()