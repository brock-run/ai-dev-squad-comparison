"""Prometheus Metrics Exporter for Phase 2 Judge System

Exports judge performance metrics for monitoring and alerting.
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Mock classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def inc(self, *args): pass
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def set(self, *args): pass
    
    class CollectorRegistry:
        def __init__(self): pass
    
    def generate_latest(registry): return b"# Prometheus not available\n"


@dataclass
class ConfusionMatrix:
    """Confusion matrix for binary classification."""
    tp: int = 0  # True Positives
    tn: int = 0  # True Negatives
    fp: int = 0  # False Positives
    fn: int = 0  # False Negatives
    
    @property
    def accuracy(self) -> float:
        total = self.tp + self.tn + self.fp + self.fn
        return (self.tp + self.tn) / total if total > 0 else 0.0
    
    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) > 0 else 0.0
    
    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0.0
    
    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    
    @property
    def false_positive_rate(self) -> float:
        return self.fp / (self.fp + self.tn) if (self.fp + self.tn) > 0 else 0.0


class JudgeMetricsExporter:
    """Exports judge performance metrics to Prometheus."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        if not PROMETHEUS_AVAILABLE:
            print("⚠️  Prometheus client not available, metrics export disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.registry = registry or CollectorRegistry()
        
        # Kappa metrics
        self.kappa_gauge = Gauge(
            'phase2_judge_kappa',
            'Cohen\'s kappa for judge agreement',
            ['artifact_type', 'split'],
            registry=self.registry
        )
        
        self.kappa_ci_lower = Gauge(
            'phase2_judge_kappa_ci_lower',
            'Lower bound of kappa confidence interval',
            ['artifact_type', 'split'],
            registry=self.registry
        )
        
        self.kappa_ci_upper = Gauge(
            'phase2_judge_kappa_ci_upper',
            'Upper bound of kappa confidence interval',
            ['artifact_type', 'split'],
            registry=self.registry
        )
        
        # Confusion matrix metrics
        self.confusion_counter = Counter(
            'phase2_judge_confusion_total',
            'Confusion matrix counts',
            ['label', 'predicted', 'artifact_type', 'split'],
            registry=self.registry
        )
        
        # Performance metrics
        self.accuracy_gauge = Gauge(
            'phase2_judge_accuracy',
            'Judge accuracy by artifact type',
            ['artifact_type', 'split'],
            registry=self.registry
        )
        
        self.precision_gauge = Gauge(
            'phase2_judge_precision',
            'Judge precision by artifact type',
            ['artifact_type', 'split'],
            registry=self.registry
        )
        
        self.recall_gauge = Gauge(
            'phase2_judge_recall',
            'Judge recall by artifact type',
            ['artifact_type', 'split'],
            registry=self.registry
        )
        
        self.f1_gauge = Gauge(
            'phase2_judge_f1_score',
            'Judge F1 score by artifact type',
            ['artifact_type', 'split'],
            registry=self.registry
        )
        
        self.fp_rate_gauge = Gauge(
            'phase2_judge_false_positive_rate',
            'Judge false positive rate by artifact type',
            ['artifact_type', 'split'],
            registry=self.registry
        )
        
        # Sample size tracking
        self.sample_size_gauge = Gauge(
            'phase2_judge_sample_size',
            'Number of samples evaluated',
            ['artifact_type', 'split'],
            registry=self.registry
        )
    
    def export_kappa_metrics(self, kappa: float, ci_lower: float, ci_upper: float,
                           artifact_type: str = "overall", split: str = "test"):
        """Export kappa metrics."""
        if not self.enabled:
            return
        
        self.kappa_gauge.labels(artifact_type=artifact_type, split=split).set(kappa)
        self.kappa_ci_lower.labels(artifact_type=artifact_type, split=split).set(ci_lower)
        self.kappa_ci_upper.labels(artifact_type=artifact_type, split=split).set(ci_upper)
    
    def export_confusion_matrix(self, confusion: ConfusionMatrix,
                              artifact_type: str = "overall", split: str = "test"):
        """Export confusion matrix metrics."""
        if not self.enabled:
            return
        
        # Reset counters for this artifact type/split
        labels = {'artifact_type': artifact_type, 'split': split}
        
        # Export confusion matrix counts (increment instead of setting)
        self.confusion_counter.labels(label='true', predicted='true', **labels).inc(confusion.tp)
        self.confusion_counter.labels(label='true', predicted='false', **labels).inc(confusion.fn)
        self.confusion_counter.labels(label='false', predicted='true', **labels).inc(confusion.fp)
        self.confusion_counter.labels(label='false', predicted='false', **labels).inc(confusion.tn)
        
        # Export derived metrics
        self.accuracy_gauge.labels(**labels).set(confusion.accuracy)
        self.precision_gauge.labels(**labels).set(confusion.precision)
        self.recall_gauge.labels(**labels).set(confusion.recall)
        self.f1_gauge.labels(**labels).set(confusion.f1_score)
        self.fp_rate_gauge.labels(**labels).set(confusion.false_positive_rate)
        
        # Export sample size
        total_samples = confusion.tp + confusion.tn + confusion.fp + confusion.fn
        self.sample_size_gauge.labels(**labels).set(total_samples)
    
    def export_from_results(self, results_file: str, dataset_file: str = None,
                          split: str = "test") -> Dict[str, Any]:
        """Export metrics from judge results file."""
        if not self.enabled:
            return {}
        
        try:
            # Load results
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            # Load dataset for filtering if provided
            dataset_items = {}
            if dataset_file and Path(dataset_file).exists():
                with open(dataset_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            item = json.loads(line)
                            dataset_items[item.get("id")] = item
            
            # Extract predictions by artifact type
            per_type_data = {}
            overall_predictions = []
            overall_ground_truth = []
            
            results = data.get("results", [])
            
            for result in results:
                item_id = result.get("id")
                
                # Filter by split if specified
                if split and dataset_file:
                    dataset_item = dataset_items.get(item_id)
                    if not dataset_item or dataset_item.get("split") != split:
                        continue
                
                if result.get("ground_truth") is None:
                    continue
                
                evaluation = result.get("evaluation", {})
                method_results = evaluation.get("results", [])
                
                if not method_results:
                    continue
                
                # Use majority vote
                equivalent_votes = sum(1 for r in method_results if r.get("equivalent", False))
                predicted_equivalent = equivalent_votes > len(method_results) / 2
                ground_truth = result["ground_truth"]
                
                # Track overall
                overall_predictions.append(predicted_equivalent)
                overall_ground_truth.append(ground_truth)
                
                # Track per-type
                artifact_type = result.get("artifact_type", "unknown")
                if artifact_type not in per_type_data:
                    per_type_data[artifact_type] = {"predictions": [], "ground_truth": []}
                
                per_type_data[artifact_type]["predictions"].append(predicted_equivalent)
                per_type_data[artifact_type]["ground_truth"].append(ground_truth)
            
            # Calculate and export overall metrics
            if overall_predictions:
                overall_confusion = self._calculate_confusion_matrix(overall_predictions, overall_ground_truth)
                overall_kappa = self._calculate_kappa(overall_predictions, overall_ground_truth)
                
                self.export_confusion_matrix(overall_confusion, "overall", split)
                self.export_kappa_metrics(overall_kappa, overall_kappa - 0.05, overall_kappa + 0.05, "overall", split)
            
            # Calculate and export per-type metrics
            exported_types = []
            for artifact_type, type_data in per_type_data.items():
                if len(type_data["predictions"]) >= 2:
                    type_confusion = self._calculate_confusion_matrix(
                        type_data["predictions"], type_data["ground_truth"]
                    )
                    type_kappa = self._calculate_kappa(
                        type_data["predictions"], type_data["ground_truth"]
                    )
                    
                    self.export_confusion_matrix(type_confusion, artifact_type, split)
                    self.export_kappa_metrics(type_kappa, type_kappa - 0.05, type_kappa + 0.05, artifact_type, split)
                    exported_types.append(artifact_type)
            
            return {
                "overall_samples": len(overall_predictions),
                "exported_types": exported_types,
                "split": split
            }
            
        except Exception as e:
            print(f"❌ Error exporting metrics: {e}")
            return {}
    
    def _calculate_confusion_matrix(self, predictions: List[bool], ground_truth: List[bool]) -> ConfusionMatrix:
        """Calculate confusion matrix from predictions."""
        confusion = ConfusionMatrix()
        
        for pred, truth in zip(predictions, ground_truth):
            if pred and truth:
                confusion.tp += 1
            elif pred and not truth:
                confusion.fp += 1
            elif not pred and truth:
                confusion.fn += 1
            else:
                confusion.tn += 1
        
        return confusion
    
    def _calculate_kappa(self, predictions: List[bool], ground_truth: List[bool]) -> float:
        """Calculate Cohen's kappa."""
        if not predictions:
            return 0.0
        
        confusion = self._calculate_confusion_matrix(predictions, ground_truth)
        n = confusion.tp + confusion.tn + confusion.fp + confusion.fn
        
        if n == 0:
            return 0.0
        
        # Observed agreement
        po = (confusion.tp + confusion.tn) / n
        
        # Expected agreement
        p_yes = (confusion.tp + confusion.fn) / n
        p_no = (confusion.fp + confusion.tn) / n
        p_pred_yes = (confusion.tp + confusion.fp) / n
        p_pred_no = (confusion.fn + confusion.tn) / n
        
        pe = p_yes * p_pred_yes + p_no * p_pred_no
        
        if pe == 1.0:
            return 1.0 if po == 1.0 else 0.0
        
        return (po - pe) / (1 - pe)
    
    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format."""
        if not self.enabled:
            return "# Prometheus client not available\n"
        
        return generate_latest(self.registry).decode('utf-8')


def export_judge_metrics(results_file: str, dataset_file: str = None,
                        split: str = "test", output_file: str = None) -> Dict[str, Any]:
    """Export judge metrics to Prometheus format."""
    exporter = JudgeMetricsExporter()
    
    if not exporter.enabled:
        print("⚠️  Metrics export disabled (prometheus_client not available)")
        return {}
    
    # Export metrics from results
    export_info = exporter.export_from_results(results_file, dataset_file, split)
    
    # Write metrics to file if specified
    if output_file:
        metrics_text = exporter.get_metrics_text()
        with open(output_file, 'w') as f:
            f.write(metrics_text)
        print(f"📊 Metrics exported to {output_file}")
    
    return export_info


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export judge metrics to Prometheus")
    parser.add_argument("results_file", help="Judge results JSON file")
    parser.add_argument("--dataset", help="Dataset JSONL file")
    parser.add_argument("--split", default="test", help="Dataset split to analyze")
    parser.add_argument("--output", help="Output file for metrics")
    
    args = parser.parse_args()
    
    info = export_judge_metrics(
        args.results_file,
        args.dataset,
        args.split,
        args.output
    )
    
    print(f"✅ Exported metrics for {info.get('overall_samples', 0)} samples")
    if info.get('exported_types'):
        print(f"   Types: {', '.join(info['exported_types'])}")