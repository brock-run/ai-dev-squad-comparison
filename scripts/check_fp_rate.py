#!/usr/bin/env python3
"""Check False Positive Rate for Judge Results

Validates that FP rate is within acceptable bounds.
"""

import json
import sys
import argparse
from typing import List, Dict, Any


def compute_false_positive_rate(results: List[Dict[str, Any]], method: str = None) -> Dict[str, float]:
    """Compute false positive rate by method."""
    
    method_stats = {}
    
    for result in results:
        if result.get("ground_truth") is None:
            continue  # Skip items without ground truth
        
        evaluation = result.get("evaluation", {})
        for method_result in evaluation.get("results", []):
            method_name = method_result.get("method")
            
            # Filter by specific method if requested
            if method and method_name != method:
                continue
            
            if method_name not in method_stats:
                method_stats[method_name] = {
                    "tp": 0, "tn": 0, "fp": 0, "fn": 0
                }
            
            predicted = method_result.get("equivalent", False)
            actual = result["ground_truth"]
            
            if predicted and actual:
                method_stats[method_name]["tp"] += 1
            elif not predicted and not actual:
                method_stats[method_name]["tn"] += 1
            elif predicted and not actual:
                method_stats[method_name]["fp"] += 1
            elif not predicted and actual:
                method_stats[method_name]["fn"] += 1
    
    # Compute FP rates
    fp_rates = {}
    for method_name, stats in method_stats.items():
        fp = stats["fp"]
        tn = stats["tn"]
        
        if fp + tn == 0:
            fp_rates[method_name] = 0.0
        else:
            fp_rates[method_name] = fp / (fp + tn)
    
    return fp_rates


def main():
    parser = argparse.ArgumentParser(description="Check false positive rate")
    parser.add_argument("results_file", help="Judge results JSON file")
    parser.add_argument("--max-fp", type=float, default=0.02, 
                       help="Maximum allowed FP rate (default: 0.02)")
    parser.add_argument("--method", help="Check specific method only")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Load results
    try:
        with open(args.results_file, 'r') as f:
            data = json.load(f)
        
        results = data.get("results", [])
        if not results:
            print(f"❌ No results found in {args.results_file}")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        sys.exit(1)
    
    # Compute FP rates
    fp_rates = compute_false_positive_rate(results, args.method)
    
    if not fp_rates:
        print("❌ No method results found with ground truth")
        sys.exit(1)
    
    # Check against threshold
    failed_methods = []
    
    print(f"📊 False Positive Rate Check (max allowed: {args.max_fp:.1%})")
    print("=" * 50)
    
    for method, fp_rate in fp_rates.items():
        status = "✅" if fp_rate <= args.max_fp else "❌"
        print(f"{status} {method}: {fp_rate:.3%}")
        
        if fp_rate > args.max_fp:
            failed_methods.append(method)
    
    # Overall result
    if failed_methods:
        print(f"\\n❌ FAILED: {len(failed_methods)} methods exceed FP threshold:")
        for method in failed_methods:
            print(f"   - {method}: {fp_rates[method]:.3%} > {args.max_fp:.1%}")
        sys.exit(1)
    else:
        print(f"\\n✅ PASSED: All methods within FP threshold ({args.max_fp:.1%})")
        
        if args.verbose:
            # Print additional stats
            total_items = len([r for r in results if r.get("ground_truth") is not None])
            print(f"\\n📈 Summary:")
            print(f"   Total items with ground truth: {total_items}")
            print(f"   Methods evaluated: {len(fp_rates)}")
            print(f"   Average FP rate: {sum(fp_rates.values()) / len(fp_rates):.3%}")


if __name__ == "__main__":
    main()