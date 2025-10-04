-- Phase 2 AI Mismatch Resolution - Core Schema Migration
-- Migration: 20251001_add_phase2_core.sql
-- Author: AI Dev Squad Platform Team
-- Date: 2025-10-01

-- Create custom types for Phase 2
CREATE TYPE mismatch_type AS ENUM (
    'whitespace',
    'markdown_formatting', 
    'json_ordering',
    'numeric_epsilon',
    'nondeterminism',
    'semantics_text',
    'semantics_code',
    'policy_violation',
    'infra_env_drift'
);

CREATE TYPE resolution_status AS ENUM (
    'proposed',
    'approved', 
    'applied',
    'rolled_back',
    'rejected',
    'error'
);

CREATE TYPE safety_level AS ENUM (
    'experimental',
    'advisory',
    'automatic'
);

-- Core mismatch table
CREATE TABLE mismatch (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    artifact_ids TEXT[] NOT NULL,
    type mismatch_type NOT NULL,
    detectors TEXT[] NOT NULL,
    evidence JSONB NOT NULL,           -- {diff_id, eval_ids[], cost_estimate, latency_ms}
    status TEXT NOT NULL DEFAULT 'detected',
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    error_code TEXT,
    error_message TEXT,
    provenance JSONB NOT NULL          -- {seeds[], model_versions{}, checkpoint_id}
);

-- Indexes for efficient querying
CREATE INDEX idx_mismatch_type ON mismatch (type);
CREATE INDEX idx_mismatch_run_id ON mismatch (run_id);
CREATE INDEX idx_mismatch_status ON mismatch (status);
CREATE INDEX idx_mismatch_confidence ON mismatch (confidence_score);
CREATE INDEX idx_mismatch_created_at ON mismatch (created_at);
CREATE INDEX idx_mismatch_diff_id ON mismatch ((evidence->>'diff_id'));
CREATE INDEX idx_mismatch_checkpoint ON mismatch ((provenance->>'checkpoint_id'));

-- Resolution plan table
CREATE TABLE resolution_plan (
    id TEXT PRIMARY KEY,
    mismatch_id TEXT NOT NULL REFERENCES mismatch(id) ON DELETE CASCADE,
    actions JSONB NOT NULL,            -- ordered, idempotent transforms
    safety_level safety_level NOT NULL,
    required_evidence TEXT[] NOT NULL,
    approvals JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{user, timestamp, type}]
    outcome JSONB,                     -- {status, artifacts[], logs[], validation}
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    applied_at TIMESTAMPTZ
);

-- Indexes for resolution plans
CREATE INDEX idx_resolution_plan_mismatch ON resolution_plan (mismatch_id);
CREATE INDEX idx_resolution_plan_safety ON resolution_plan (safety_level);
CREATE INDEX idx_resolution_plan_created ON resolution_plan (created_at);
CREATE INDEX idx_resolution_plan_status ON resolution_plan ((outcome->>'status'));

-- Equivalence criterion configuration table
CREATE TABLE equivalence_criterion (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    methods JSONB NOT NULL,            -- array of method configurations
    validators JSONB NOT NULL,         -- array of validator configurations
    calibration JSONB NOT NULL,        -- threshold management and rollback conditions
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_equivalence_criterion_type ON equivalence_criterion (artifact_type);
CREATE INDEX idx_equivalence_criterion_enabled ON equivalence_criterion (enabled);

-- Resolution policy table
CREATE TABLE resolution_policy (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    matrix JSONB NOT NULL,             -- array of policy rules
    rollbacks JSONB NOT NULL,          -- rollback triggers and actions
    audit JSONB NOT NULL,              -- ownership and approval info
    active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_at TIMESTAMPTZ
);

CREATE INDEX idx_resolution_policy_active ON resolution_policy (active);
CREATE INDEX idx_resolution_policy_version ON resolution_policy (version);

-- Learning pattern storage table
CREATE TABLE mismatch_pattern (
    id TEXT PRIMARY KEY,
    mismatch_type mismatch_type NOT NULL,
    pattern_signature TEXT NOT NULL,   -- hash of normalized pattern
    embedding VECTOR(1536),            -- OpenAI embedding for similarity search
    pattern_data JSONB NOT NULL,       -- full pattern information
    success_rate FLOAT NOT NULL DEFAULT 0.0,
    usage_count INTEGER NOT NULL DEFAULT 0,
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Vector similarity index (requires pgvector extension)
-- CREATE INDEX idx_mismatch_pattern_embedding ON mismatch_pattern 
-- USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX idx_mismatch_pattern_type ON mismatch_pattern (mismatch_type);
CREATE INDEX idx_mismatch_pattern_signature ON mismatch_pattern (pattern_signature);
CREATE INDEX idx_mismatch_pattern_success_rate ON mismatch_pattern (success_rate);

-- Audit log table for all AI decisions
CREATE TABLE ai_decision_log (
    id TEXT PRIMARY KEY,
    decision_type TEXT NOT NULL,       -- 'analysis', 'resolution', 'learning'
    entity_id TEXT NOT NULL,           -- mismatch_id, plan_id, etc.
    model_used TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10,6),
    latency_ms INTEGER,
    confidence_score FLOAT,
    decision_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ai_decision_log_type ON ai_decision_log (decision_type);
CREATE INDEX idx_ai_decision_log_entity ON ai_decision_log (entity_id);
CREATE INDEX idx_ai_decision_log_model ON ai_decision_log (model_used);
CREATE INDEX idx_ai_decision_log_created ON ai_decision_log (created_at);
CREATE INDEX idx_ai_decision_log_cost ON ai_decision_log (cost_usd);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_mismatch_updated_at BEFORE UPDATE ON mismatch
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equivalence_criterion_updated_at BEFORE UPDATE ON equivalence_criterion
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mismatch_pattern_updated_at BEFORE UPDATE ON mismatch_pattern
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE mismatch IS 'Core mismatch records from replay operations';
COMMENT ON TABLE resolution_plan IS 'AI-generated resolution plans with safety controls';
COMMENT ON TABLE equivalence_criterion IS 'Configuration for semantic equivalence detection';
COMMENT ON TABLE resolution_policy IS 'Environment-specific resolution policies';
COMMENT ON TABLE mismatch_pattern IS 'Learned patterns for mismatch resolution';
COMMENT ON TABLE ai_decision_log IS 'Audit log of all AI-powered decisions';

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO phase2_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO phase2_app_user;