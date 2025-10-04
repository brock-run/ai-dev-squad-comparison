# docs/adr/ADR-008-telemetry-event-schema-and-otel-strategy.md

## ADR-008: Telemetry Event Schema & OTel Strategy

**Status:** Proposed
**Date:** 2025-09-28
**Owners:** AI Platform Dev Group
**Related:** ADR-001 (Security Architecture), ADR-005 (Security Policy), ADR-006 (VCS Integration), ADR-007 (Common Agent API)

### Context

We need a single event model spanning adapters, benchmarking, replay, and the dashboard. Fragmented schemas make replay, analysis, and audits unreliable.

### Decision

1. **Primary event format:** Versioned **JSON Lines** file `events.jsonl` (UTC timestamps, ISO-8601, monotonic step indices). Compression: **zstd**.
2. **Event types (v1.0):**

   * Lifecycle: `run_start`, `run_end`, `agent_start`, `agent_end`
   * Work: `llm_call`, `tool_call`, `sandbox_exec`, `vcs_action`
   * Errors: `error`, `policy_violation`
   * Replay: `replay_checkpoint`, `replay_assert`, `recording_note`
3. **Correlation:** Every event includes `{run_id, task_id, framework, adapter, agent_id, trace_id, span_id, step}`.
4. **OpenTelemetry:** Emit OTel spans mirroring major events. Exporter is optional; Jaeger provided via docker-compose.
5. **Schema versioning:** `schema_version: "1.0"` at file header (first line) and within each event. Minor bumps are additive; major bumps require a migration note.

### Consequences

* One source of truth; simpler replay and dashboards.
* Consumers (dashboard, CLI) must tolerate minor version drift; CI will validate schema.

### Alternatives Considered

* Parquet (heavyweight for stepwise streaming); raw OTel-only (harder for deterministic replay); ad‑hoc per adapter (unmaintainable).

### Implementation Notes

* `common/telemetry/schema.py` defines pydantic models + JSONSchema.
* `common/telemetry/logger.py` writes JSONL with zstd; rotates at 200MB.
* `comparison-results/dashboard.py` reads JSONL or pre-aggregated parquet (future).
* Redaction hooks (see ADR-014) run before write.

### Open Questions

* Span sampling defaults for local dev vs CI.
