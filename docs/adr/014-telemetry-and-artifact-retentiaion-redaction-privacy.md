# docs/adr/ADR-014-telemetry-artifact-retention-redaction-privacy.md

## ADR-014: Telemetry & Artifact Retention, Redaction, and Privacy

**Status:** Proposed
**Date:** 2025-09-28
**Related:** ADR-001 (Security), ADR-008 (Telemetry)

### Context

Logs and artifacts may include secrets and proprietary code. We need retention and redaction policies.

### Decision

1. **Redaction filters (default on):** Remove/replace tokens, bearer headers, keys from `.env`, credentials in URLs, and common secret patterns **before** persist.
2. **Retention classes:**

   * Dev: 7 days
   * CI: 30 days
   * Release snapshots: 180 days
3. **Sharing policy:** Hashes kept always; content export is opt‑in and tracked in manifest.
4. **Access control:** Local FS by default; optional S3/Blob with bucket policies.
5. **Audit:** All redactions and deletions are themselves logged as `recording_note` events.

### Consequences

* Reduced leakage risk; predictable storage growth.
* Slight overhead for redaction pass.

### Alternatives Considered

* No redaction (unsafe); encrypt‑everything (operationally heavy, not needed locally).

### Implementation Notes

* Implement filters in `common/telemetry/logger.py` pipeline; unit tests with synthetic secrets.
