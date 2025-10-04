#!/usr/bin/env python3
"""Shadow Soak Monitoring Script

Monitors judge performance during shadow soak period.
"""

import json
import time
import argparse
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path


class ShadowSoakMonitor:
    """Monitors shadow soak performance and detects regressions."""
    
    def __init__(self, baseline_file: str, alert_threshold: float = 1.0):
        self.baseline_file = baseline_file
        self.alert_threshold = alert_threshold  # Standard deviations
        self.baseline_metrics = self._load_baseline()
    
    def _load_baseline(self) -> Dict[str, Any]:
        """Load baseline metrics from calibration run."""
        try:
            with open(self.baseline_file, 'r') as f:
                data = json.load(f)
            
            # Handle both calibration manifest format and results format
            summary = data.get("summary", {})
            metrics = data.get("metrics", {})
            
            # Try to get kappa from metrics first (calibration manifest), then summary (results)
            kappa_overall = metrics.get("kappa_overall") or summary.get("kappa_overall", 0.8)
            
            # Try to get method stats from summary first, then fallback
            method_stats = summary.get("method_stats", {})
            
            # Calculate cost per eval
            total_cost = summary.get("total_cost_usd", 0)
            total_items = summary.get("total_items", 1)
            cost_per_eval = total_cost / max(1, total_items)
            
            return {
                "kappa_overall": kappa_overall,
                "method_stats": method_stats,
                "cost_per_eval": cost_per_eval,
                "avg_latency": summary.get("avg_latency_ms", 1000)
            }
        except Exception as e:
            print(f"⚠️  Warning: Could not load baseline from {self.baseline_file}: {e}")
            return {
                "kappa_overall": 0.8,
                "method_stats": {},
                "cost_per_eval": 0.01,
                "avg_latency": 1000
            }
    
    def check_results(self, results_file: str) -> Dict[str, Any]:
        """Check current results against baseline."""
        
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            return {"status": "error", "message": f"Could not load results: {e}"}
        
        summary = data.get("summary", {})
        alerts = []
        
        # Check overall kappa
        current_kappa = summary.get("kappa_overall", 0.0)
        baseline_kappa = self.baseline_metrics["kappa_overall"]
        
        if current_kappa < baseline_kappa - (self.alert_threshold * 0.05):  # 5% std dev
            alerts.append({
                "type": "kappa_regression",
                "severity": "high",
                "message": f"Kappa dropped from {baseline_kappa:.3f} to {current_kappa:.3f}",
                "current": current_kappa,
                "baseline": baseline_kappa
            })
        
        # Check method performance
        current_method_stats = summary.get("method_stats", {})
        baseline_method_stats = self.baseline_metrics["method_stats"]
        
        for method, baseline_stats in baseline_method_stats.items():
            if method not in current_method_stats:
                alerts.append({
                    "type": "method_missing",
                    "severity": "high",
                    "message": f"Method {method} missing from current results",
                    "method": method
                })
                continue
            
            current_stats = current_method_stats[method]
            
            # Check equivalent rate drift
            baseline_equiv_rate = baseline_stats.get("equivalent_rate", 0.5)
            current_equiv_rate = current_stats.get("equivalent_rate", 0.0)
            
            if abs(current_equiv_rate - baseline_equiv_rate) > self.alert_threshold * 0.1:
                alerts.append({
                    "type": "equiv_rate_drift",
                    "severity": "medium",
                    "message": f"{method} equiv rate: {current_equiv_rate:.1%} vs baseline {baseline_equiv_rate:.1%}",
                    "method": method,
                    "current": current_equiv_rate,
                    "baseline": baseline_equiv_rate
                })
            
            # Check confidence drift
            baseline_conf = baseline_stats.get("avg_confidence", 0.5)
            current_conf = current_stats.get("avg_confidence", 0.0)
            
            if abs(current_conf - baseline_conf) > self.alert_threshold * 0.1:
                alerts.append({
                    "type": "confidence_drift",
                    "severity": "low",
                    "message": f"{method} confidence: {current_conf:.2f} vs baseline {baseline_conf:.2f}",
                    "method": method,
                    "current": current_conf,
                    "baseline": baseline_conf
                })
        
        # Check cost drift
        current_cost = summary.get("total_cost_usd", 0) / max(1, summary.get("total_items", 1))
        baseline_cost = self.baseline_metrics["cost_per_eval"]
        
        if current_cost > baseline_cost * (1 + self.alert_threshold * 0.2):  # 20% increase
            alerts.append({
                "type": "cost_increase",
                "severity": "medium",
                "message": f"Cost per eval: ${current_cost:.4f} vs baseline ${baseline_cost:.4f}",
                "current": current_cost,
                "baseline": baseline_cost
            })
        
        # Check latency drift
        current_latency = summary.get("avg_latency_ms", 0)
        baseline_latency = self.baseline_metrics["avg_latency"]
        
        if current_latency > baseline_latency * (1 + self.alert_threshold * 0.3):  # 30% increase
            alerts.append({
                "type": "latency_increase",
                "severity": "medium",
                "message": f"Avg latency: {current_latency:.0f}ms vs baseline {baseline_latency:.0f}ms",
                "current": current_latency,
                "baseline": baseline_latency
            })
        
        # Determine overall status
        high_severity_alerts = [a for a in alerts if a["severity"] == "high"]
        medium_severity_alerts = [a for a in alerts if a["severity"] == "medium"]
        
        if high_severity_alerts:
            status = "critical"
        elif len(medium_severity_alerts) >= 2:
            status = "warning"
        elif alerts:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "alerts": alerts,
            "summary": {
                "total_alerts": len(alerts),
                "high_severity": len(high_severity_alerts),
                "medium_severity": len(medium_severity_alerts),
                "current_kappa": current_kappa,
                "baseline_kappa": baseline_kappa,
                "current_cost": current_cost,
                "baseline_cost": baseline_cost
            }
        }
    
    def generate_report(self, results_files: List[str], output_file: str = None):
        """Generate comprehensive soak report."""
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "baseline_file": self.baseline_file,
            "alert_threshold": self.alert_threshold,
            "results": []
        }
        
        all_alerts = []
        status_counts = {"healthy": 0, "degraded": 0, "warning": 0, "critical": 0}
        
        for results_file in results_files:
            check_result = self.check_results(results_file)
            check_result["file"] = results_file
            report["results"].append(check_result)
            
            status_counts[check_result["status"]] += 1
            all_alerts.extend(check_result.get("alerts", []))
        
        # Aggregate statistics
        report["aggregate"] = {
            "total_files": len(results_files),
            "status_distribution": status_counts,
            "total_alerts": len(all_alerts),
            "alert_types": {}
        }
        
        # Count alert types
        for alert in all_alerts:
            alert_type = alert["type"]
            if alert_type not in report["aggregate"]["alert_types"]:
                report["aggregate"]["alert_types"][alert_type] = 0
            report["aggregate"]["alert_types"][alert_type] += 1
        
        # Overall health assessment
        if status_counts["critical"] > 0:
            report["overall_status"] = "critical"
            report["recommendation"] = "STOP: Critical regressions detected. Investigate immediately."
        elif status_counts["warning"] > len(results_files) * 0.3:  # >30% warning
            report["overall_status"] = "warning"
            report["recommendation"] = "CAUTION: Multiple warnings detected. Monitor closely."
        elif status_counts["degraded"] > len(results_files) * 0.5:  # >50% degraded
            report["overall_status"] = "degraded"
            report["recommendation"] = "MONITOR: Performance degradation detected."
        else:
            report["overall_status"] = "healthy"
            report["recommendation"] = "PROCEED: Shadow soak performing within expected parameters."
        
        # Save report
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📊 Report saved to {output_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(description="Monitor shadow soak performance")
    parser.add_argument("--baseline", required=True, help="Baseline results file")
    parser.add_argument("--results", nargs="+", required=True, help="Current results files")
    parser.add_argument("--output", help="Output report file")
    parser.add_argument("--threshold", type=float, default=1.0, 
                       help="Alert threshold in standard deviations")
    parser.add_argument("--watch", action="store_true", 
                       help="Watch mode: continuously monitor")
    parser.add_argument("--interval", type=int, default=300,
                       help="Watch interval in seconds (default: 5min)")
    
    args = parser.parse_args()
    
    monitor = ShadowSoakMonitor(args.baseline, args.threshold)
    
    if args.watch:
        print(f"👁️  Watching shadow soak (checking every {args.interval}s)...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                print(f"\n🔍 Checking at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Check each results file
                for results_file in args.results:
                    if not Path(results_file).exists():
                        print(f"⚠️  {results_file} not found, skipping")
                        continue
                    
                    result = monitor.check_results(results_file)
                    status_emoji = {
                        "healthy": "✅",
                        "degraded": "🟡", 
                        "warning": "⚠️",
                        "critical": "🚨"
                    }.get(result["status"], "❓")
                    
                    print(f"{status_emoji} {Path(results_file).name}: {result['status']}")
                    
                    if result.get("alerts"):
                        for alert in result["alerts"][:3]:  # Show first 3 alerts
                            severity_emoji = {"high": "🚨", "medium": "⚠️", "low": "ℹ️"}[alert["severity"]]
                            print(f"  {severity_emoji} {alert['message']}")
                        
                        if len(result["alerts"]) > 3:
                            print(f"  ... and {len(result['alerts']) - 3} more alerts")
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
    
    else:
        # Single check mode
        report = monitor.generate_report(args.results, args.output)
        
        # Print summary
        print(f"\n📊 Shadow Soak Report")
        print("=" * 50)
        print(f"Overall Status: {report['overall_status'].upper()}")
        print(f"Recommendation: {report['recommendation']}")
        print(f"Files Checked: {report['aggregate']['total_files']}")
        print(f"Total Alerts: {report['aggregate']['total_alerts']}")
        
        if report['aggregate']['alert_types']:
            print("\nAlert Types:")
            for alert_type, count in report['aggregate']['alert_types'].items():
                print(f"  {alert_type}: {count}")
        
        # Exit with appropriate code
        if report['overall_status'] == 'critical':
            exit(2)
        elif report['overall_status'] in ['warning', 'degraded']:
            exit(1)
        else:
            exit(0)


if __name__ == "__main__":
    main()