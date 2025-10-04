#!/usr/bin/env python3
"""Judge Confusion Matrix Exporter for Grafana

Exports confusion matrix metrics and per-type kappa for Grafana monitoring.
"""

import json
import argparse
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict

try:
    from prometheus_client import Counter, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


def calculate_kappa(tp: int, tn: int, fp: int, fn: int) -> float:
    """Calculate Cohen's kappa from confusion matrix."""
    n = tp + tn + fp + fn
    if n == 0:
        return 0.0
    
    # Observed agreement
    po = (tp + tn) / n
    
    # Expected agreement
    p_yes = (tp + fn) / n
    p_no = (fp + tn) / n
    p_pred_yes = (tp + fp) / n
    p_pred_no = (fn + tn) / n
    
    pe = p_yes * p_pred_yes + p_no * p_pred_no
    
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    
    return (po - pe) / (1 - pe)


def export_confusion_metrics(results_file: str, dataset_file: str = None, 
                           split: str = "test", output_file: str = None) -> Dict[str, Any]:
    """Export confusion matrix and kappa metrics."""
    
    if not PROMETHEUS_AVAILABLE:
        print("❌ Prometheus client not available")
        return {}
    
    # Load results
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        return {}
    
    # Load dataset for filtering if provided
    dataset_items = {}
    if dataset_file and Path(dataset_file).exists():
        try:
            with open(dataset_file, 'r') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        dataset_items[item.get("id")] = item
        except Exception as e:
            print(f"⚠️  Warning: Could not load dataset: {e}")
    
    # Create registry and metrics
    registry = CollectorRegistry()
    
    # Confusion matrix counter
    confusion_counter = Counter(
        'judge_confusion_total',
        'Confusion matrix counts for judge decisions',
        ['artifact_type', 'label', 'predicted', 'method'],
        registry=registry
    )
    
    # Per-type kappa gauge
    kappa_gauge = Gauge(
        'phase2_kappa_by_type',
        'Cohen\'s kappa by mismatch type',
        ['mismatch_type'],
        registry=registry
    )
    
    # Process results by method and type
    method_type_stats = defaultdict(lambda: defaultdict(lambda: {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0}))
    type_stats = defaultdict(lambda: {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0})
    
    results = data.get("results", [])
    processed_count = 0
    
    for result in results:
        item_id = result.get("id")
        
        # Filter by split if specified
        if split and dataset_file:
            dataset_item = dataset_items.get(item_id)
            if not dataset_item or dataset_item.get("split") != split:
                continue
        
        ground_truth = result.get("ground_truth")
        if ground_truth is None:
            continue
        
        artifact_type = result.get("artifact_type", "unknown")
        evaluation = result.get("evaluation", {})
        method_results = evaluation.get("results", [])
        
        processed_count += 1
        
        # Process each method result
        for method_result in method_results:
            method = method_result.get("method", "unknown")
            predicted = method_result.get("equivalent", False)
            
            # Update confusion matrix
            if predicted and ground_truth:
                confusion_counter.labels(
                    artifact_type=artifact_type,
                    label='true',
                    predicted='true',
                    method=method
                ).inc()
                method_type_stats[method][artifact_type]['tp'] += 1
                type_stats[artifact_type]['tp'] += 1
            elif predicted and not ground_truth:
                confusion_counter.labels(
                    artifact_type=artifact_type,
                    label='false',
                    predicted='true',
                    method=method
                ).inc()
                method_type_stats[method][artifact_type]['fp'] += 1
                type_stats[artifact_type]['fp'] += 1
            elif not predicted and ground_truth:
                confusion_counter.labels(
                    artifact_type=artifact_type,
                    label='true',
                    predicted='false',
                    method=method
                ).inc()
                method_type_stats[method][artifact_type]['fn'] += 1
                type_stats[artifact_type]['fn'] += 1
            else:  # not predicted and not ground_truth
                confusion_counter.labels(
                    artifact_type=artifact_type,
                    label='false',
                    predicted='false',
                    method=method
                ).inc()
                method_type_stats[method][artifact_type]['tn'] += 1
                type_stats[artifact_type]['tn'] += 1
    
    # Calculate and export per-type kappa
    kappa_results = {}
    for artifact_type, stats in type_stats.items():
        if stats['tp'] + stats['tn'] + stats['fp'] + stats['fn'] > 0:
            kappa = calculate_kappa(stats['tp'], stats['tn'], stats['fp'], stats['fn'])
            kappa_gauge.labels(mismatch_type=artifact_type).set(kappa)
            kappa_results[artifact_type] = kappa
    
    # Generate metrics output
    metrics_text = generate_latest(registry).decode('utf-8')
    
    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(metrics_text)
        print(f"📊 Metrics exported to {output_file}")
    else:
        print(metrics_text)
    
    # Summary
    summary = {
        "processed_items": processed_count,
        "artifact_types": list(type_stats.keys()),
        "methods": list(method_type_stats.keys()),
        "kappa_by_type": kappa_results,
        "split": split
    }
    
    print(f"\n📈 Summary:")
    print(f"   Processed items: {processed_count}")
    print(f"   Artifact types: {len(type_stats)}")
    print(f"   Methods: {len(method_type_stats)}")
    
    if kappa_results:
        print(f"   Kappa by type:")
        for artifact_type, kappa in kappa_results.items():
            print(f"     {artifact_type}: {kappa:.3f}")
    
    return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Export judge confusion metrics for Grafana")
    parser.add_argument("results_file", help="Judge results JSON file")
    parser.add_argument("--dataset", help="Dataset JSONL file for filtering")
    parser.add_argument("--split", default="test", help="Dataset split to analyze")
    parser.add_argument("--output", help="Output metrics file")
    
    args = parser.parse_args()
    
    if not PROMETHEUS_AVAILABLE:
        print("❌ prometheus_client not available. Install with: pip install prometheus_client")
        sys.exit(1)
    
    summary = export_confusion_metrics(
        args.results_file,
        args.dataset,
        args.split,
        args.output
    )
    
    if summary["processed_items"] == 0:
        print("⚠️  No items processed. Check dataset and results files.")
        sys.exit(1)
    
    print(f"\n✅ Successfully exported metrics for {summary['processed_items']} items")


if __name__ == "__main__":
    main()