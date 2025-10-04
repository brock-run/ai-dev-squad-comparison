"""Decision Rules for AI Judge

Implements conjunctive decision rules for semantic equivalence.
"""

from typing import Dict, List, Any, Optional
from enum import Enum

from ..enums import EquivalenceMethod, ArtifactType
from ..diff_entities import EvaluationResult


class DecisionRuleType(Enum):
    """Types of decision rules."""
    CONJUNCTIVE = "conjunctive"
    DISJUNCTIVE = "disjunctive"
    WEIGHTED = "weighted"
    THRESHOLD = "threshold"


class DecisionRule:
    """Base class for decision rules."""
    
    def __init__(self, rule_id: str, rule_type: DecisionRuleType, 
                 artifact_type: ArtifactType, version: str = "v1"):
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.artifact_type = artifact_type
        self.version = version
    
    def evaluate(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Evaluate results using this rule.
        
        Returns:
            {
                "equivalent": bool,
                "confidence": float,
                "reasoning": str,
                "rule_id": str,
                "method_contributions": Dict[str, Any]
            }
        """
        raise NotImplementedError


class ConjunctiveRule(DecisionRule):
    """Conjunctive decision rule: requires multiple conditions to be met."""
    
    def __init__(self, rule_id: str, artifact_type: ArtifactType, 
                 thresholds: Dict[str, float], violation_blocklist: List[str] = None):
        super().__init__(rule_id, DecisionRuleType.CONJUNCTIVE, artifact_type)
        self.thresholds = thresholds
        self.violation_blocklist = violation_blocklist or [
            "unit_change", "policy_violation", "numerical_meaning", 
            "semantic_change", "behavior_change"
        ]
    
    def evaluate(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Evaluate using conjunctive rule."""
        
        # Organize results by method
        method_results = {result.method: result for result in results}
        
        # Check for exact match first (highest confidence)
        if EquivalenceMethod.EXACT in method_results:
            exact_result = method_results[EquivalenceMethod.EXACT]
            if exact_result.equivalent:
                return {
                    "equivalent": True,
                    "confidence": 1.0,
                    "reasoning": "Exact string match",
                    "rule_id": self.rule_id,
                    "method_contributions": {"exact": {"weight": 1.0, "decision": True}}
                }
        
        # Check for deterministic structural equivalence
        structural_methods = [
            EquivalenceMethod.CANONICAL_JSON,
            EquivalenceMethod.AST_NORMALIZED
        ]
        
        for method in structural_methods:
            if method in method_results:
                result = method_results[method]
                if result.equivalent and result.confidence >= self.thresholds.get(f"{method.value}_conf", 0.9):
                    return {
                        "equivalent": True,
                        "confidence": result.confidence,
                        "reasoning": f"Structural equivalence via {method.value}",
                        "rule_id": self.rule_id,
                        "method_contributions": {method.value: {"weight": 1.0, "decision": True}}
                    }
        
        # Conjunctive semantic evaluation
        semantic_conditions = []
        method_contributions = {}
        
        # Cosine similarity condition
        if EquivalenceMethod.COSINE_SIMILARITY in method_results:
            cosine_result = method_results[EquivalenceMethod.COSINE_SIMILARITY]
            cosine_threshold = self.thresholds.get("cosine_similarity", 0.86)
            cosine_meets = cosine_result.similarity_score >= cosine_threshold
            
            semantic_conditions.append(cosine_meets)
            method_contributions["cosine_similarity"] = {
                "score": cosine_result.similarity_score,
                "threshold": cosine_threshold,
                "meets_threshold": cosine_meets,
                "weight": 0.4
            }
        
        # LLM confidence condition
        if EquivalenceMethod.LLM_RUBRIC_JUDGE in method_results:
            llm_result = method_results[EquivalenceMethod.LLM_RUBRIC_JUDGE]
            llm_threshold = self.thresholds.get("llm_confidence", 0.70)
            llm_meets = (llm_result.equivalent and 
                        llm_result.confidence >= llm_threshold)
            
            # Check for violations
            violations = llm_result.metadata.get("violations", [])
            has_blocklist_violations = any(v in self.violation_blocklist for v in violations)
            
            if has_blocklist_violations:
                llm_meets = False
            
            semantic_conditions.append(llm_meets)
            method_contributions["llm_rubric_judge"] = {
                "equivalent": llm_result.equivalent,
                "confidence": llm_result.confidence,
                "threshold": llm_threshold,
                "violations": violations,
                "has_blocklist_violations": has_blocklist_violations,
                "meets_threshold": llm_meets,
                "weight": 0.6
            }
        
        # Conjunctive decision: ALL conditions must be met
        all_conditions_met = len(semantic_conditions) > 0 and all(semantic_conditions)
        
        if all_conditions_met:
            # Weighted confidence from contributing methods
            total_weight = sum(contrib.get("weight", 0) for contrib in method_contributions.values())
            if total_weight > 0:
                weighted_confidence = sum(
                    contrib.get("confidence", contrib.get("score", 0.5)) * contrib.get("weight", 0)
                    for contrib in method_contributions.values()
                ) / total_weight
            else:
                weighted_confidence = 0.5
            
            return {
                "equivalent": True,
                "confidence": min(0.95, weighted_confidence),  # Cap at 95%
                "reasoning": f"Conjunctive rule: {len(semantic_conditions)} conditions met",
                "rule_id": self.rule_id,
                "method_contributions": method_contributions
            }
        
        else:
            # Determine why conditions failed
            failed_conditions = []
            for method, contrib in method_contributions.items():
                if not contrib.get("meets_threshold", False):
                    if "violations" in contrib and contrib["has_blocklist_violations"]:
                        failed_conditions.append(f"{method} (violations: {contrib['violations']})")
                    else:
                        failed_conditions.append(f"{method} (below threshold)")
            
            return {
                "equivalent": False,
                "confidence": 0.1,  # Low confidence when conditions fail
                "reasoning": f"Conjunctive rule failed: {', '.join(failed_conditions)}",
                "rule_id": self.rule_id,
                "method_contributions": method_contributions
            }


class DecisionRuleEngine:
    """Engine for applying decision rules to evaluation results."""
    
    def __init__(self):
        self.rules = {}
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default decision rules."""
        
        # Text conjunctive rule
        self.rules["text.conjunctive.v1"] = ConjunctiveRule(
            rule_id="text.conjunctive.v1",
            artifact_type=ArtifactType.TEXT,
            thresholds={
                "cosine_similarity": 0.86,
                "llm_confidence": 0.70
            }
        )
        
        # JSON conjunctive rule
        self.rules["json.conjunctive.v1"] = ConjunctiveRule(
            rule_id="json.conjunctive.v1",
            artifact_type=ArtifactType.JSON,
            thresholds={
                "cosine_similarity": 0.90,
                "llm_confidence": 0.75,
                "canonical_json_conf": 0.95
            }
        )
        
        # Code conjunctive rule
        self.rules["code.conjunctive.v1"] = ConjunctiveRule(
            rule_id="code.conjunctive.v1",
            artifact_type=ArtifactType.CODE,
            thresholds={
                "cosine_similarity": 0.88,
                "llm_confidence": 0.75,
                "ast_normalized_conf": 0.90
            }
        )
    
    def register_rule(self, rule: DecisionRule):
        """Register a custom decision rule."""
        self.rules[rule.rule_id] = rule
    
    def apply_rule(self, rule_id: str, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Apply a specific decision rule to evaluation results."""
        
        if rule_id not in self.rules:
            raise ValueError(f"Unknown decision rule: {rule_id}")
        
        rule = self.rules[rule_id]
        return rule.evaluate(results)
    
    def get_default_rule_id(self, artifact_type: ArtifactType) -> str:
        """Get default rule ID for artifact type."""
        
        rule_map = {
            ArtifactType.TEXT: "text.conjunctive.v1",
            ArtifactType.JSON: "json.conjunctive.v1",
            ArtifactType.CODE: "code.conjunctive.v1"
        }
        
        return rule_map.get(artifact_type, "text.conjunctive.v1")
    
    def list_rules(self) -> List[Dict[str, Any]]:
        """List all registered rules."""
        
        return [
            {
                "rule_id": rule.rule_id,
                "rule_type": rule.rule_type.value,
                "artifact_type": rule.artifact_type.value,
                "version": rule.version
            }
            for rule in self.rules.values()
        ]


# Global decision rule engine
decision_engine = DecisionRuleEngine()


if __name__ == "__main__":
    # Test decision rules
    print("🧪 Testing decision rules...")
    
    from ..diff_entities import EvaluationResult
    from ..enums import EquivalenceMethod, ArtifactType
    
    # Mock evaluation results
    results = [
        EvaluationResult(
            method=EquivalenceMethod.EXACT,
            equivalent=False,
            confidence=0.0,
            similarity_score=0.0,
            reasoning="Strings differ",
            cost=0.0,
            latency_ms=10
        ),
        EvaluationResult(
            method=EquivalenceMethod.COSINE_SIMILARITY,
            equivalent=True,
            confidence=0.85,
            similarity_score=0.88,
            reasoning="High semantic similarity",
            cost=0.001,
            latency_ms=200
        ),
        EvaluationResult(
            method=EquivalenceMethod.LLM_RUBRIC_JUDGE,
            equivalent=True,
            confidence=0.80,
            similarity_score=1.0,
            reasoning="Semantically equivalent with minor formatting differences",
            cost=0.002,
            latency_ms=1500,
            metadata={"violations": []}
        )
    ]
    
    engine = DecisionRuleEngine()
    
    # Test text conjunctive rule
    decision = engine.apply_rule("text.conjunctive.v1", results)
    
    print(f"✅ Decision: {decision['equivalent']}")
    print(f"   Confidence: {decision['confidence']:.2f}")
    print(f"   Reasoning: {decision['reasoning']}")
    print(f"   Rule: {decision['rule_id']}")
    
    # Test with violations
    results[2].metadata["violations"] = ["unit_change"]
    decision_with_violations = engine.apply_rule("text.conjunctive.v1", results)
    
    print(f"\\n❌ With violations: {decision_with_violations['equivalent']}")
    print(f"   Reasoning: {decision_with_violations['reasoning']}")
    
    print("\\n🎉 Decision rules working correctly!")