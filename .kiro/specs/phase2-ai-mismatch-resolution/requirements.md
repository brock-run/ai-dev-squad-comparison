# Phase 2: AI-Powered Mismatch Resolution - Requirements

## Introduction

Phase 2 builds upon the enhanced telemetry integration from Phase 1 to introduce intelligent mismatch analysis and resolution capabilities. This phase focuses on using AI to understand, categorize, and automatically resolve replay mismatches, making the record-replay system more robust and user-friendly.

## Success Metrics

- **≥70%** of benign mismatches are auto-resolved without human edits on held-out replay suite (200+ labeled examples)
- **≤2%** false-positive destructive resolutions (measured by rollbacks and test failures) with 95% confidence interval
- **p95 time** from mismatch → resolved state ≤ 5 minutes with human-in-the-loop
- **Cost tracking** for all AI operations with budgets: ≤$0.10 per 100KB analyzed, ≤$100/day total
- **Zero provenance gaps**: every suggestion/resolution has diff, approval, checkpoint, and replayability
- **Circuit breaker SLO**: ≤1 hour detection, ≤5 minutes disable, ≤15 minutes notification
- **User satisfaction**: ≥4.0/5.0 rating for AI resolution features
- **Learning improvement**: 10% monthly improvement in auto-resolution accuracy

## Data Model

### Core Entities

#### Mismatch
```yaml
Mismatch:
  id: string (UUID)
  run_id: string (references existing Run)
  artifact_ids: array[string] (references existing Artifacts)
  mismatch_type: enum[whitespace, json_ordering, markdown_formatting, semantics_text, semantics_code, nondeterminism, policy_violation, env_drift]
  # Tier 1 (Day 1): whitespace, json_ordering - Safe auto-resolution
  # Tier 2 (Week 2): markdown_formatting - Advisory resolution  
  # Tier 3 (Week 4+): semantics_text, semantics_code - Experimental
  # Tier 4 (Analysis only): policy_violation, env_drift - No auto-resolution
  detectors: array[string] (detector names that found this mismatch)
  evidence:
    diff_id: string (references existing Diff)
    eval_ids: array[string] (references existing Evaluations)
    cost_estimate: float (AI operation costs)
    latency_ms: integer (analysis duration)
  status: enum[detected, analyzing, resolved, failed, skipped, error, inconclusive]
  confidence_score: float (0.0-1.0)
  created_at: datetime
  updated_at: datetime
  error_code: string (optional)
  error_message: string (optional)
  provenance:
    seeds: array[integer] (determinism seeds)
    model_versions: object (AI model versions used)
    checkpoint_id: string (rollback checkpoint)
```

#### ResolutionPlan
```yaml
ResolutionPlan:
  id: string (UUID)
  mismatch_id: string (references Mismatch)
  actions: array[ResolutionAction]
  safety_level: enum[experimental, advisory, automatic] (mirrors Rule.enforcement_level)
  approvals: array[Approval]
  outcome:
    status: enum[pending, applied, rolled_back, failed]
    artifacts: array[string] (new artifact IDs created)
    logs: array[string] (operation logs)
  created_at: datetime
  applied_at: datetime (optional)
```

#### EquivalenceCriterion
```yaml
EquivalenceCriterion:
  id: string
  version: string
  selector:
    artifact_type: enum[text, code, json, binary]
  method: array[EquivalenceMethod]
  validators: array[Validator]
  calibration:
    threshold_source: enum[static, learned, adaptive]
    update_frequency: string (weekly, monthly)
    rollback_conditions: object
  audit:
    owner: string
    created_at: datetime

EquivalenceMethod:
  name: enum[exact, cosine_similarity, llm_rubric_judge, ast_normalized, canonical_json, test_execution]
  params: object
    threshold: float (for similarity methods)
    embedding: string (model name)
    prompt_id: string (for LLM judges)
    pass_threshold: float
    max_tokens: integer
    timeout_ms: integer

Validator:
  name: enum[small_diff_bias_guard, content_loss_detector, format_preservation_check]
  params: object
    max_chars: integer (for small diff guard)
    loss_threshold: float
```

#### ResolutionPolicy
```yaml
ResolutionPolicy:
  id: string
  version: string
  matrix: array[PolicyRule]
  rollbacks:
    trigger: object (conditions for auto-disable)
    action: enum[disable_auto_resolve, shadow_mode, alert_only]
  audit:
    owner: string
    created_at: datetime
    approved_by: array[string]

PolicyRule:
  mismatch_type: enum[whitespace, json_ordering, markdown_formatting, semantics_text, semantics_code, nondeterminism, policy_violation, env_drift]
  environment: array[enum[dev, stage, prod]]
  allowed_actions: array[enum[canonicalize_json, reserialize, rewrite_formatting, normalize_whitespace, ignore_mismatch]]
  safety_level: enum[experimental, advisory, automatic]
  required_evidence: array[string] (diff.json, equivalence.json, llm_rubric, cosine_sim)
  confidence_min: float (0.0-1.0)
  dual_key_required: boolean (for destructive actions)
```

#### ResolutionAction
```yaml
ResolutionAction:
  type: enum[replace_artifact, update_metadata, apply_transform, ignore_mismatch]
  target_artifact_id: string
  transformation: string (function name or AI prompt)
  parameters: object
  reversible: boolean
  destructive: boolean (requires dual-key approval)
  preview_diff: string (required before application)
```

## Requirements

### Requirement 1: Intelligent Mismatch Analysis

**User Story:** As a developer using the record-replay system, I want the system to automatically analyze replay mismatches and provide intelligent insights about why they occurred, so that I can quickly understand and resolve issues without manual investigation.

#### Acceptance Criteria

1. WHEN a replay mismatch occurs THEN the system SHALL automatically analyze the mismatch using AI-powered analysis
2. WHEN analyzing a mismatch THEN the system SHALL categorize the mismatch type (semantic, syntactic, temporal, environmental, etc.)
3. WHEN analyzing a mismatch THEN the system SHALL provide a confidence score for the mismatch categorization
4. WHEN analyzing a mismatch THEN the system SHALL generate human-readable explanations of the root cause
5. WHEN analyzing a mismatch THEN the system SHALL suggest potential resolution strategies
6. WHEN multiple similar mismatches occur THEN the system SHALL identify patterns and common causes
7. WHEN analyzing a mismatch THEN the system SHALL preserve all original mismatch data for audit purposes

### Requirement 2: Semantic Equivalence Detection

**User Story:** As a developer, I want the system to recognize when outputs are semantically equivalent even if they differ syntactically, so that minor variations don't cause false positive mismatch alerts.

#### Acceptance Criteria

1. WHEN comparing text outputs THEN the system SHALL detect semantic equivalence using natural language understanding
2. WHEN comparing code outputs THEN the system SHALL detect functional equivalence using code analysis
3. WHEN comparing structured data THEN the system SHALL detect logical equivalence accounting for ordering and formatting differences
4. WHEN semantic equivalence is detected THEN the system SHALL mark the mismatch as "semantically equivalent" with confidence score
5. WHEN semantic equivalence is uncertain THEN the system SHALL provide detailed comparison analysis
6. WHEN semantic equivalence detection fails THEN the system SHALL fall back to traditional exact matching
7. WHEN semantic equivalence is detected THEN the system SHALL log the analysis for learning and improvement

### Requirement 3: Automated Resolution Strategies

**User Story:** As a developer, I want the system to automatically resolve certain types of mismatches when it's safe to do so, so that I don't have to manually intervene for trivial differences.

#### Acceptance Criteria

1. WHEN a mismatch is categorized as "safe to auto-resolve" THEN the system SHALL automatically apply the appropriate resolution strategy
2. WHEN auto-resolving THEN the system SHALL only resolve mismatches with high confidence scores (>90%)
3. WHEN auto-resolving THEN the system SHALL log all resolution actions with full audit trail
4. WHEN auto-resolving THEN the system SHALL provide rollback capabilities for any automated changes
5. WHEN auto-resolution fails THEN the system SHALL fall back to manual resolution mode
6. WHEN auto-resolving THEN the system SHALL respect user-defined safety policies and constraints
7. WHEN auto-resolving THEN the system SHALL update the recorded data with the resolved values when appropriate

### Requirement 4: Learning and Adaptation System

**User Story:** As a system administrator, I want the mismatch resolution system to learn from past resolutions and improve its accuracy over time, so that the system becomes more effective with usage.

#### Acceptance Criteria

1. WHEN a mismatch is resolved (manually or automatically) THEN the system SHALL record the resolution pattern for learning
2. WHEN similar mismatches occur THEN the system SHALL apply learned patterns to improve analysis accuracy
3. WHEN resolution patterns are learned THEN the system SHALL validate them against historical data
4. WHEN confidence in learned patterns is high THEN the system SHALL suggest promoting manual patterns to automatic resolution
5. WHEN learned patterns prove incorrect THEN the system SHALL automatically demote or remove them
6. WHEN learning from resolutions THEN the system SHALL respect privacy and security constraints
7. WHEN learning patterns THEN the system SHALL provide explainable AI insights into the learning process

### Requirement 5: Interactive Resolution Interface

**User Story:** As a developer, I want an interactive interface to review, approve, or modify AI-suggested mismatch resolutions, so that I maintain control over the resolution process while benefiting from AI assistance.

#### Acceptance Criteria

1. WHEN a mismatch requires manual review THEN the system SHALL present an interactive resolution interface
2. WHEN presenting resolution options THEN the system SHALL show the original mismatch, AI analysis, and suggested resolutions
3. WHEN presenting resolution options THEN the system SHALL allow users to approve, modify, or reject AI suggestions
4. WHEN users modify AI suggestions THEN the system SHALL learn from the modifications for future improvements
5. WHEN users approve resolutions THEN the system SHALL apply them and update the replay state
6. WHEN users reject resolutions THEN the system SHALL maintain the original mismatch state and log the rejection
7. WHEN presenting the interface THEN the system SHALL provide clear explanations of the impact of each resolution option

### Requirement 6: Mismatch Prevention and Prediction

**User Story:** As a developer, I want the system to predict potential mismatches before they occur and suggest preventive measures, so that I can avoid replay issues proactively.

#### Acceptance Criteria

1. WHEN recording new sessions THEN the system SHALL analyze patterns that historically lead to mismatches
2. WHEN potential mismatch risks are detected THEN the system SHALL warn users during recording
3. WHEN analyzing recorded data THEN the system SHALL identify environmental factors that may cause replay issues
4. WHEN predicting mismatches THEN the system SHALL suggest recording best practices to minimize future issues
5. WHEN environmental changes are detected THEN the system SHALL recommend recording updates or re-recording
6. WHEN prediction confidence is high THEN the system SHALL automatically adjust recording parameters to prevent issues
7. WHEN predictions prove accurate THEN the system SHALL improve its predictive models based on the outcomes

### Requirement 7: Advanced Replay Modes

**User Story:** As a developer, I want advanced replay modes that can handle different types of mismatches intelligently, so that I can choose the appropriate level of strictness for different testing scenarios.

#### Acceptance Criteria

1. WHEN configuring replay THEN the system SHALL support "intelligent" mode that uses AI-powered mismatch resolution
2. WHEN configuring replay THEN the system SHALL support "adaptive" mode that learns and adjusts during replay
3. WHEN configuring replay THEN the system SHALL support "semantic" mode that focuses on semantic equivalence
4. WHEN configuring replay THEN the system SHALL support "progressive" mode that becomes more lenient over time
5. WHEN using intelligent modes THEN the system SHALL provide real-time feedback on resolution decisions
6. WHEN using advanced modes THEN the system SHALL maintain compatibility with existing strict/warn/hybrid modes
7. WHEN switching between modes THEN the system SHALL preserve replay state and allow mode changes mid-replay

### Requirement 8: Integration with Existing Systems

**User Story:** As a system integrator, I want the AI-powered mismatch resolution to integrate seamlessly with existing Phase 1 components and telemetry systems, so that I can adopt the new capabilities without disrupting current workflows.

#### Acceptance Criteria

1. WHEN integrating with Phase 1 THEN the system SHALL maintain full backward compatibility with existing APIs
2. WHEN integrating with telemetry THEN the system SHALL extend existing event schemas with AI analysis data
3. WHEN integrating with recording THEN the system SHALL enhance existing recording with mismatch prediction data
4. WHEN integrating with replay THEN the system SHALL extend existing replay modes with AI-powered capabilities
5. WHEN integrating with streaming THEN the system SHALL support AI analysis of streaming data mismatches
6. WHEN integrating with existing dashboards THEN the system SHALL provide new visualizations for AI analysis results
7. WHEN upgrading from Phase 1 THEN the system SHALL provide smooth migration paths with no data loss

### Requirement 9: Performance and Scalability

**User Story:** As a system administrator, I want the AI-powered mismatch resolution to perform efficiently at scale, so that it doesn't significantly impact system performance or user experience.

#### Acceptance Criteria

1. WHEN analyzing mismatches THEN the system SHALL complete analysis within 5 seconds for typical mismatches
2. WHEN processing multiple mismatches THEN the system SHALL support parallel analysis with configurable concurrency
3. WHEN using AI models THEN the system SHALL support both local and cloud-based AI services
4. WHEN AI services are unavailable THEN the system SHALL gracefully fall back to traditional mismatch handling
5. WHEN analyzing large datasets THEN the system SHALL use efficient algorithms and caching to minimize resource usage
6. WHEN learning from patterns THEN the system SHALL use incremental learning to avoid performance degradation
7. WHEN scaling to multiple users THEN the system SHALL maintain consistent performance across concurrent sessions

### Requirement 10: Security and Privacy

**User Story:** As a security administrator, I want the AI-powered mismatch resolution to maintain the same security and privacy standards as the existing system, so that sensitive data remains protected during AI analysis.

#### Acceptance Criteria

1. WHEN analyzing mismatches THEN the system SHALL apply existing redaction policies to data sent to AI services
2. WHEN using external AI services THEN the system SHALL support on-premises deployment options for sensitive environments
3. WHEN learning from patterns THEN the system SHALL anonymize and aggregate data to protect individual privacy
4. WHEN storing AI analysis results THEN the system SHALL apply the same retention and encryption policies as other telemetry data
5. WHEN accessing AI features THEN the system SHALL enforce existing authentication and authorization mechanisms
6. WHEN AI analysis fails THEN the system SHALL not expose sensitive information in error messages or logs
7. WHEN auditing AI decisions THEN the system SHALL provide complete audit trails while protecting sensitive data