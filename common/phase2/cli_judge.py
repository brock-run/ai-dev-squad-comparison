"""CLI for AI Judge Shadow Testing

Provides shadow-mode evaluation of semantic equivalence.
"""

import json
import sys
import time
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .ai.clients import OpenAIAdapter, OllamaAdapter, OpenAIEmbeddingAdapter
from .ai.judge import EquivalenceRunner
from .ai.cache import EmbeddingCache
from .enums import EquivalenceMethod, ArtifactType
from .models import Mismatch
# from .persistence import get_db_connection  # Skip DB for now


def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Load labeled dataset for evaluation."""
    dataset = []
    
    with open(dataset_path, 'r') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                dataset.append(entry)
    
    return dataset


def create_ai_clients(config: Dict[str, Any]) -> tuple:
    """Create LLM and embedding clients from config."""
    
    # LLM client
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "ollama")
    
    if provider == "openai":
        api_key = llm_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        llm_client = OpenAIAdapter(
            api_key=api_key,
            model=llm_config.get("model", "gpt-4o-mini"),
            max_tps=llm_config.get("max_tps", 10.0),
            timeout_s=llm_config.get("timeout_s", 30),
            redact=llm_config.get("redact", True)
        )
    else:
        # Default to Ollama for development
        llm_client = OllamaAdapter(
            model=llm_config.get("model", "llama3.2:3b"),
            base_url=llm_config.get("base_url", "http://localhost:11434"),
            max_tps=llm_config.get("max_tps", 5.0),
            timeout_s=llm_config.get("timeout_s", 60)
        )
    
    # Embedding client
    embed_config = config.get("embedding", {})
    embed_provider = embed_config.get("provider", "openai")
    
    if embed_provider == "openai":
        api_key = embed_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  No OpenAI API key for embeddings, falling back to mock embedding client")
            from .ai.mock_clients import MockEmbeddingClient
            embed_client = MockEmbeddingClient(
                model=embed_config.get("model", "mock-embed"),
                dimension=embed_config.get("dimension", 384)
            )
        else:
            embed_client = OpenAIEmbeddingAdapter(
                api_key=api_key,
                model=embed_config.get("model", "text-embedding-3-small")
            )
    else:
        print("ℹ️  Using mock embedding client for testing")
        from .ai.mock_clients import MockEmbeddingClient
        embed_client = MockEmbeddingClient(
            model=embed_config.get("model", "mock-embed"),
            dimension=embed_config.get("dimension", 384)
        )
    
    return llm_client, embed_client


def run_shadow_evaluation(run_id: Optional[str] = None, dataset_path: Optional[str] = None,
                         methods: List[str] = None, config: Dict[str, Any] = None,
                         output_path: str = "judge_results.json") -> Dict[str, Any]:
    """Run shadow evaluation on dataset or specific run."""
    
    if not methods:
        methods = ["exact", "cosine_similarity", "llm_rubric_judge"]
    
    # Handle comma-separated methods in single argument
    if len(methods) == 1 and ',' in methods[0]:
        methods = [m.strip() for m in methods[0].split(',') if m.strip()]
    
    # Convert method strings to enums
    method_enums = []
    method_map = {
        "exact": EquivalenceMethod.EXACT,
        "cosine_similarity": EquivalenceMethod.COSINE_SIMILARITY,
        "llm_rubric_judge": EquivalenceMethod.LLM_RUBRIC_JUDGE,
        "canonical_json": EquivalenceMethod.CANONICAL_JSON,
        "ast_normalized": EquivalenceMethod.AST_NORMALIZED
    }
    
    for method_str in methods:
        if method_str in method_map:
            method_enums.append(method_map[method_str])
        else:
            print(f"Warning: Unknown method '{method_str}', skipping")
    
    # Create AI clients
    llm_client, embed_client = create_ai_clients(config or {})
    
    # Create embedding cache
    cache_dir = config.get("cache_dir", ".cache/embeddings") if config else ".cache/embeddings"
    embedding_cache = EmbeddingCache(cache_dir=cache_dir)
    
    # Create equivalence runner
    budgets = config.get("budgets", {}) if config else {}
    runner = EquivalenceRunner(
        llm_client=llm_client,
        embedding_client=embed_client,
        embedding_cache=embedding_cache,
        budgets=budgets,
        sandbox_enabled=True
    )
    
    # Load evaluation data
    if dataset_path:
        # Load from dataset file
        dataset = load_dataset(dataset_path)
        evaluation_items = []
        
        for entry in dataset:
            # Extract source and target text from golden/candidate
            golden = entry.get("golden", {})
            candidate = entry.get("candidate", {})
            source_text = golden.get("excerpt", "")
            target_text = candidate.get("excerpt", "")
            
            # Extract ground truth from consensus
            consensus = entry.get("consensus", {})
            ground_truth_label = consensus.get("label")
            ground_truth = ground_truth_label == "equivalent" if ground_truth_label else None
            
            evaluation_items.append({
                "id": entry.get("id", f"dataset_{len(evaluation_items)}"),
                "source_text": source_text,
                "target_text": target_text,
                "artifact_type": ArtifactType(entry.get("artifact_type", "text")),
                "ground_truth": ground_truth
            })
    
    elif run_id:
        # Database functionality not available in this version
        raise ValueError("Database run evaluation not implemented yet")
    
    else:
        raise ValueError("Must specify either run_id or dataset_path")
    
    # Run evaluations
    results = []
    total_cost = 0.0
    total_latency = 0.0
    
    print(f"🔍 Running shadow evaluation on {len(evaluation_items)} items...")
    print(f"   Methods: {[m.value for m in method_enums]}")
    
    for i, item in enumerate(evaluation_items):
        print(f"   Progress: {i+1}/{len(evaluation_items)}", end="\\r")
        
        try:
            # Mock diff object for runner
            class MockDiff:
                def __init__(self, item_id):
                    self.id = f"shadow_{item_id}"
                    self.source_artifact_id = f"src_{item_id}"
                    self.target_artifact_id = f"tgt_{item_id}"
            
            diff = MockDiff(item["id"])
            
            # Run evaluation
            evaluation = runner.run(
                diff=diff,
                source_text=item["source_text"],
                target_text=item["target_text"],
                artifact_type=item["artifact_type"],
                methods=method_enums
            )
            
            # Collect results
            item_result = {
                "id": item["id"],
                "artifact_type": item["artifact_type"].value,
                "ground_truth": item.get("ground_truth"),
                "evaluation": {
                    "status": evaluation.status.value,
                    "error_message": evaluation.error_message,
                    "metadata": evaluation.metadata,
                    "results": []
                }
            }
            
            for result in evaluation.results:
                item_result["evaluation"]["results"].append({
                    "method": result.method.value,
                    "equivalent": result.equivalent,
                    "confidence": result.confidence,
                    "similarity_score": result.similarity_score,
                    "reasoning": result.reasoning,
                    "cost": result.cost,
                    "latency_ms": result.latency_ms,
                    "metadata": result.metadata
                })
                
                total_cost += result.cost
                total_latency += result.latency_ms
            
            results.append(item_result)
            
        except Exception as e:
            print(f"\\n❌ Error evaluating item {item['id']}: {e}")
            results.append({
                "id": item["id"],
                "artifact_type": item["artifact_type"].value,
                "ground_truth": item.get("ground_truth"),
                "evaluation": {
                    "status": "error",
                    "error_message": str(e),
                    "results": []
                }
            })
    
    print(f"\\n✅ Completed {len(results)} evaluations")
    
    # Compute summary statistics
    summary = compute_evaluation_summary(results)
    summary.update({
        "total_cost_usd": total_cost,
        "total_latency_ms": total_latency,
        "avg_latency_ms": total_latency / max(1, len(results)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": config
    })
    
    # Save results
    output = {
        "summary": summary,
        "results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"📊 Results saved to {output_path}")
    print_summary(summary)
    
    return output


def compute_evaluation_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary statistics from evaluation results."""
    
    summary = {
        "total_items": len(results),
        "successful_evaluations": 0,
        "failed_evaluations": 0,
        "method_stats": {},
        "agreement_stats": {}
    }
    
    # Count successes/failures
    for result in results:
        if result["evaluation"]["status"] == "completed":
            summary["successful_evaluations"] += 1
        else:
            summary["failed_evaluations"] += 1
    
    # Compute method-specific stats
    method_results = {}
    
    for result in results:
        if result["evaluation"]["status"] != "completed":
            continue
        
        for method_result in result["evaluation"]["results"]:
            method = method_result["method"]
            
            if method not in method_results:
                method_results[method] = {
                    "total": 0,
                    "equivalent_count": 0,
                    "confidence_sum": 0.0,
                    "cost_sum": 0.0,
                    "latency_sum": 0.0
                }
            
            stats = method_results[method]
            stats["total"] += 1
            if method_result["equivalent"]:
                stats["equivalent_count"] += 1
            stats["confidence_sum"] += method_result["confidence"]
            stats["cost_sum"] += method_result["cost"]
            stats["latency_sum"] += method_result["latency_ms"]
    
    # Finalize method stats
    for method, stats in method_results.items():
        if stats["total"] > 0:
            summary["method_stats"][method] = {
                "total_evaluations": stats["total"],
                "equivalent_rate": stats["equivalent_count"] / stats["total"],
                "avg_confidence": stats["confidence_sum"] / stats["total"],
                "avg_cost_usd": stats["cost_sum"] / stats["total"],
                "avg_latency_ms": stats["latency_sum"] / stats["total"]
            }
    
    # Compute agreement between methods (if multiple methods used)
    if len(method_results) > 1:
        agreement_count = 0
        total_pairs = 0
        
        for result in results:
            if result["evaluation"]["status"] != "completed":
                continue
            
            method_decisions = {}
            for method_result in result["evaluation"]["results"]:
                method_decisions[method_result["method"]] = method_result["equivalent"]
            
            # Check pairwise agreement
            methods = list(method_decisions.keys())
            for i in range(len(methods)):
                for j in range(i + 1, len(methods)):
                    total_pairs += 1
                    if method_decisions[methods[i]] == method_decisions[methods[j]]:
                        agreement_count += 1
        
        if total_pairs > 0:
            summary["agreement_stats"]["pairwise_agreement_rate"] = agreement_count / total_pairs
    
    return summary


def print_summary(summary: Dict[str, Any]):
    """Print evaluation summary to console."""
    
    print("\\n📊 Evaluation Summary:")
    print(f"   Total items: {summary['total_items']}")
    print(f"   Successful: {summary['successful_evaluations']}")
    print(f"   Failed: {summary['failed_evaluations']}")
    print(f"   Total cost: ${summary.get('total_cost_usd', 0):.4f}")
    print(f"   Avg latency: {summary.get('avg_latency_ms', 0):.0f}ms")
    
    print("\\n📈 Method Performance:")
    for method, stats in summary["method_stats"].items():
        print(f"   {method}:")
        print(f"     Equivalent rate: {stats['equivalent_rate']:.1%}")
        print(f"     Avg confidence: {stats['avg_confidence']:.2f}")
        print(f"     Avg cost: ${stats['avg_cost_usd']:.4f}")
        print(f"     Avg latency: {stats['avg_latency_ms']:.0f}ms")
    
    if "pairwise_agreement_rate" in summary.get("agreement_stats", {}):
        agreement_rate = summary["agreement_stats"]["pairwise_agreement_rate"]
        print(f"\\n🤝 Method Agreement: {agreement_rate:.1%}")


def main():
    """CLI entry point."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="AI Judge Shadow Evaluation")
    parser.add_argument("--run", help="Run ID to evaluate")
    parser.add_argument("--dataset", help="Dataset file path")
    parser.add_argument("--methods", nargs="+", 
                       default=["exact", "cosine_similarity", "llm_rubric_judge"],
                       help="Evaluation methods to use")
    parser.add_argument("--output", default="judge_results.json",
                       help="Output file path")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--shadow", action="store_true", default=True,
                       help="Run in shadow mode (no mutations)")
    
    args = parser.parse_args()
    
    if not args.run and not args.dataset:
        print("❌ Must specify either --run or --dataset")
        sys.exit(1)
    
    # Load config
    config = {}
    if args.config and Path(args.config).exists():
        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    else:
        # Auto-detect CI environment and use test config
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") or not os.getenv("OPENAI_API_KEY"):
            test_config_path = "config/phase2_test.yaml"
            if Path(test_config_path).exists():
                print(f"ℹ️  Auto-detected CI/test environment, using {test_config_path}")
                import yaml
                with open(test_config_path, 'r') as f:
                    config = yaml.safe_load(f)
            else:
                config = {"use_mock_clients": True}
    
    # Set default config values
    config.setdefault("llm", {})
    config.setdefault("embedding", {})
    config.setdefault("budgets", {
        "max_cost_usd": 0.10,
        "max_latency_ms": 5000,
        "max_tokens_per_request": 8000
    })
    
    try:
        run_shadow_evaluation(
            run_id=args.run,
            dataset_path=args.dataset,
            methods=args.methods,
            config=config,
            output_path=args.output
        )
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()