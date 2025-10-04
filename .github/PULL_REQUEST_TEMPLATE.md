## Summary
- What does this PR do?
- Which orchestrators/adapters are affected?

## Checklist (must pass before merge)
- [ ] **Adapter contract**: Any touched adapter implements `common.agent_api.AgentAdapter` (name, run_task, events) and passes contract tests.
- [ ] **Safety**: All code/FS/network tool paths route through `common/safety/*` (deny-by-default network). New tools covered by safety unit tests.
- [ ] **VCS**: Uses `common/vcs/*` (retry/backoff). For VCS changes, include a dry-run/advisory log.
- [ ] **Bench**: 5 benchmark tasks pass (or exceptions noted) with artifacts attached (JSON + logs) and `--seed` recorded.
- [ ] **Telemetry**: JSON events and (if enabled) OTel spans present (trace_id visible in artifacts).
- [ ] **Replay**: Provide one `record` run id and a `replay` run id; metrics within tolerance (time ±20%, tokens ±10%).
- [ ] **Docs**: Updated READMEs/guides; no references to `run_benchmarks.py`; parity matrix updated when relevant.
- [ ] **Config**: `.env.example` parity maintained; config precedence (env > YAML > defaults) unchanged.
- [ ] **CI**: Lint (ruff/mypy/eslint), tests (unit+contract), and smoke pass; coverage not reduced.
- [ ] **Security**: No secrets committed; PAT scopes minimal; allowlist changes documented.

## Artifacts / Evidence
- Benchmark results: `comparison-results/<path>`
- Replay manifest: `benchmark/replay/<path>`
- Telemetry sample: `artifacts/events/*.jsonl`
- Screenshots: dashboard/Jaeger (optional)