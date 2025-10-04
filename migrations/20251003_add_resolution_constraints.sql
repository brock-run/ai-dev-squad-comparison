-- Migration: Add resolution constraints and audit fields
-- Date: 2025-10-03
-- Purpose: Enforce one applied plan per mismatch and add transform audit fields

-- Add partial unique index to enforce one applied plan per mismatch
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_resolution_plan_applied_unique 
ON resolution_plan (mismatch_id) 
WHERE (outcome->>'status' = 'applied');

-- Add transform audit fields to resolution_plan outcome
-- Note: Using JSONB for flexible schema evolution
-- Example outcome structure:
-- {
--   "status": "applied",
--   "transform_audit": {
--     "transform_id": "canonicalize_json@1.1.0",
--     "config_fingerprint": "sha256:abc123...",
--     "before_hash": "sha256:def456...",
--     "after_hash": "sha256:ghi789...",
--     "idempotent": true,
--     "applied_at": "2025-10-03T12:34:56Z",
--     "checksum_validated": true
--   }
-- }

-- Add index for efficient rollback queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_resolution_plan_transform_audit 
ON resolution_plan USING GIN ((outcome->'transform_audit'));

-- Add index for before/after hash lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_resolution_plan_hashes 
ON resolution_plan ((outcome->'transform_audit'->>'before_hash'), (outcome->'transform_audit'->>'after_hash'));

-- Add function to validate transform checksums
CREATE OR REPLACE FUNCTION validate_transform_checksum(
    p_before_content TEXT,
    p_after_content TEXT,
    p_before_hash TEXT,
    p_after_hash TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    -- Validate that content hashes match stored hashes
    RETURN (
        encode(sha256(p_before_content::bytea), 'hex') = substring(p_before_hash from 8) AND
        encode(sha256(p_after_content::bytea), 'hex') = substring(p_after_hash from 8)
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add function for atomic resolution plan application
CREATE OR REPLACE FUNCTION apply_resolution_plan(
    p_plan_id UUID,
    p_transform_audit JSONB
) RETURNS BOOLEAN AS $$
DECLARE
    rows_updated INTEGER;
BEGIN
    -- Atomic update: only succeed if plan is in 'approved' status
    UPDATE resolution_plan 
    SET 
        outcome = jsonb_set(
            COALESCE(outcome, '{}'::jsonb),
            '{status}',
            '"applied"'::jsonb
        ) || jsonb_build_object('transform_audit', p_transform_audit),
        updated_at = NOW()
    WHERE 
        id = p_plan_id 
        AND status = 'approved'
        AND (outcome->>'status' IS NULL OR outcome->>'status' != 'applied');
    
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    
    -- Return true only if exactly one row was updated (single winner)
    RETURN rows_updated = 1;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON INDEX idx_resolution_plan_applied_unique IS 
'Ensures only one resolution plan can be applied per mismatch';

COMMENT ON FUNCTION apply_resolution_plan IS 
'Atomically applies a resolution plan with single-winner semantics';

COMMENT ON FUNCTION validate_transform_checksum IS 
'Validates that content matches stored SHA-256 hashes for rollback safety';