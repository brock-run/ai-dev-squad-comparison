# AI Dev Squad Comparison — Orchestrators & Platform Extensions PRD

---
Owner: @brock.butler
Last updated: 2025-09-20
Primary goals: parity across required orchestrators, add new orchestrators, central safety, GitHub/GitLab, expanded benchmarks, evaluation/determinism, observability, Ollama-first performance, reproducibility, docs.
---

## 0) TL;DR

	•	Upgrade & normalize LangGraph, CrewAI v1/v2, AutoGen, n8n, Semantic Kernel (Py & C#), Claude Code Subagents to a common interface and GitHub/GitLab parity.
	•	Add: Langroid, LlamaIndex Agents, Haystack Agents, Strands Agents with full benchmark & VCS parity.
	•	Ship a central safety sandbox (common/safety/) used by all.
	•	Expand benchmark tasks (5 categories), verification, self-consistency, record–replay, and dashboard.
	•	Ollama-first perf: model guidance, caching, fallbacks, streaming.
	•	Observability: unified logs, OpenTelemetry traces, token/cost accounting.
	•	Reproducibility: Docker Compose, lockfiles, seed control.
	•	Documentation, guides, PR checklists.

⸻

## 1) Objectives & Non-Objectives

Objectives
	1.	Cross-framework parity for VCS workflows (GitHub and GitLab), safety, evaluation hooks, and configuration.
	2.	Add four orchestrators (Langroid, LlamaIndex Agents, Haystack Agents, Strands Agents) with full benchmark + VCS parity.
	3.	Centralize safety (sandbox, FS/network policy, injection guards) and enforce use across all frameworks.
	4.	Benchmark suite v2: richer tasks, automatic correctness checks, self-consistency, record–replay, determinism options, CLI.
	5.	Observability: structured event logs, OpenTelemetry, dashboard drill-downs (per step/agent/tool), token & cost.
	6.	Ollama-first perf: model selection by task, caching, streaming, partial reruns, small-model fallbacks.
	7.	Reproducibility: Docker Compose, pinned deps/lockfiles, environment capture, seed control.
	8.	Documentation: parity status, guides, troubleshooting, model recommendations.

Non-Objectives
	•	Not building a hosted SaaS control plane.
	•	Not guaranteeing identical qualitative outputs across fundamentally different paradigms; we expose differences in the dashboard and parity matrix.

⸻

## 2) Success Metrics
	•	Parity coverage: 100% of required & new orchestrators pass the 5 benchmark tasks in autonomous mode with GitHub & GitLab flows (or documented advisory-mode exception + parity note).
	•	Safety adoption: 100% tool executions (code run, FS, network) route through common/safety/ guardrails.
	•	Determinism: Record–replay works on ≥ 80% of steps; seedable mode available for local models.
	•	Observability: 100% of LLM calls & tool calls captured with tokens/time; traces viewable in OTel/Jaeger.
	•	Perf: Local Ollama run of full benchmark suite completes on a single-GPU dev box in a documented time budget.
	•	Docs: All guides present; parity matrix published; PR checklist enforced in CI.

⸻

## 3) Scope & Deliverables

3.1 Code & Interfaces
	•	common/agent_api.py — Common interface used by all orchestrators:
```
class AgentAdapter(Protocol):
    name: str
    def configure(self, config: dict) -> None: ...
    def run_task(self, task: dict, context: dict) -> "RunResult": ...
    def events(self) -> Iterable["Event"]: ...
```

	•	common/vcs/ — GitHub + GitLab utilities (branching, commits, PR/MR, rate-limit backoff, scopes).
	•	common/safety/ — sandbox (exec in container/subprocess), FS allowlist, network allowlist, prompt-injection guards, policy config.
	•	benchmark/benchmark_suite.py — Tasks, runners, CLI; self-consistency, record–replay, verification.
	•	comparison-results/dashboard.py — Metrics, parity matrix, traces; add drill-down.
	•	Orchestrator adapters at */-implementation/adapter.py implementing AgentAdapter.

3.2 New Orchestrators
	•	langroid-implementation/
	•	llamaindex-implementation/
	•	haystack-implementation/
	•	strands-implementation/

3.3 Benchmarks

Five tasks with ground truth / checks:
	1.	Single-file Bug Fix
	2.	Multi-step Feature Addition
	3.	Question Answering (codebase/logs)
	4.	Code Optimization
	5.	Edge Case – Incorrect Issue

Each: inputs, expected outcome, automated tests, and manual verification notes.

3.4 Observability
	•	common/telemetry/ — JSON logs schema, OTel spans, token & cost accounting.
	•	Jaeger/OTel exporter config.

3.5 Reproducibility
	•	docker-compose.yml (agents, dashboard, Jaeger, optional n8n), pinned deps, seed controls.

3.6 Documentation
	•	docs/research/research_findings.md (top report), docs/research/landscapes/*.md, docs/research/proposals/*.md
	•	Guides: running locally, models via Ollama, safety policy, GitHub/GitLab setup, telemetry viewing, parity matrix.

⸻

## 4) Functional Requirements

FR-1 Common Agent API
	•	Provide a minimal adapter surface for configure / run_task / events.
	•	Uniform Task schema (id, type, inputs, repo path, VCS provider, mode: autonomous/advisory, seed, model prefs).
	•	Standard RunResult (status, artifacts, timings, tokens, costs, trace id).

FR-2 Central Safety
	•	All code exec goes through common/safety/execute_code() with time/CPU/mem limits and no internet.
	•	FS access limited to repo root and temp dirs.
	•	Network allowlist per task (default deny).
	•	Prompt input/output filters; optional LLM judge.
	•	Policy YAML with per-task overrides.

FR-3 VCS: GitHub & GitLab
	•	Common functions: open_branch, commit_files, open_pr_or_mr, comment, merge (optional).
	•	Backoff + jitter on 429/secondary limits; scoped tokens; advisory mode supported.
	•	PR/MR templates, commit message generator option (small local model).

FR-4 Benchmarks & Verification
	•	CLI: python benchmark/benchmark_suite.py --framework all --tasks all --provider github --mode autonomous --out results.json --seed 42
	•	Self-consistency: N runs + majority/score aggregation.
	•	Verification: pytest or script; lint/type checks; semantic checks for QA tasks.
	•	Record–replay: capture prompts & tool IO to artifacts; replay path for CI.

FR-5 Observability & Dashboard
	•	Structured events for every step (agent, llm_call, tool_call, vcs_action).
	•	OTel spans; Jaeger docker service; dashboard drill-downs; parity matrix view.

FR-6 Ollama-first Performance
	•	Task→model recommendations; streaming; caching; partial reruns; small-model fallbacks.
	•	Seedable generation where supported.

FR-7 Reproducibility & Packaging
	•	Docker Compose; pinned deps/locks; env capture; seeds; example hardware notes.

⸻

## 5) Non-Functional Requirements
	•	Secure by default (deny network, minimal scopes).
	•	Idempotent runners; timeouts and cancellation.
	•	Clear errors; metrics emitted on failure; CI-friendly exits.
	•	Documentation-first DX.

⸻

## 6) Risks & Mitigations
	•	Framework API churn (TaskWeaver-like): pin versions; adapter isolation; feature flags.
	•	n8n parity gaps: allow advisory mode + explicit parity callouts in matrix.
	•	Local model limitations: documented fallbacks; smaller tasks for CPU-only.
	•	Trace volume/perf: sampling + log rotation.

⸻

## 7) Milestones (suggested)
	1.	Foundation (Week 1–2): Common API, safety skeleton, VCS module (GH+GL), benchmark task scaffolds, Docker skeleton.
	2.	Parity Upgrade (Week 3–4): Update required orchestrators; wire safety/VCS/obs; smoke tests.
	3.	New Orchestrators (Week 5–7): Langroid, LlamaIndex, Haystack, Strands with benchmark/VCS parity.
	4.	Eval & Dashboard (Week 8): Self-consistency, record–replay, metrics, drill-downs.
	5.	Perf & Repro (Week 9): Ollama tuning, caching, seeds, Compose polish.
	6.	Docs & Release (Week 10): Research report, proposals, guides, PR checklist, parity matrix.

⸻

## 8) Acceptance Criteria (high-level)
	•	Each orchestrator runs all 5 tasks in autonomous mode on GitHub and GitLab, or has an advisory fallback with parity notes.
	•	Safety must wrap every execution/tool path (unit tests assert this).
	•	Benchmark CLI outputs JSON + artifacts, supports seed and replay.
	•	Dashboard shows per-step trace, tokens/costs, and parity matrix.
	•	docker-compose up --build yields a runnable environment.

⸻

## 9) Parity Matrix (tracked in docs)

Publish and maintain a matrix per orchestrator: Feature, Status (✅/⚠️/❌), Notes/Workaround.

⸻

## 10) PR Checklist (to include in PR template)
	•	Adapter implements AgentAdapter and passes adapter unit tests.
	•	All tool exec paths call common/safety/execute_code() or safe FS/network wrappers.
	•	GH/GL flows: branch ➜ commit ➜ PR/MR (advisory/autonomous) working.
	•	5 tasks pass verification (or documented failures + issues linked).
	•	Telemetry events + OTel spans present; tokens/cost recorded.
	•	Docker build & smoke test green.
	•	Docs updated (guides, parity matrix, model recs).
	•	Results added to dashboard data (optional snapshot).

⸻

## Appendix A — Implementation Sketches

A.1 Common VCS Module (GitHub/GitLab)
```
common/vcs/
  __init__.py
  base.py         # Provider protocol; rate limit/backoff middleware
  github.py       # PAT/App auth, branch/commit/PR, annotations
  gitlab.py       # PAT/App auth, branch/commit/MR, approvals
  commit_msgs.py  # Local small-model generator via Ollama
  config.py       # Scopes, endpoints, retry policies
```

A.2 Safety Sandbox
```
common/safety/
  execute.py      # subprocess/Docker exec, time/mem/CPU limits, no-net
  fs.py           # path allowlist, safe open/read/write
  net.py          # allowlist resolver; deny by default
  injection.py    # input/output heuristics; optional LLM judge call
  policy.yaml     # defaults + task-specific overrides
  tests/          # malicious patterns, escape attempts
```

A.3 Benchmark Suite Additions

```
benchmark/
  tasks/
    bugfix/...
    feature_add/...
    qa/...
    optimize/...
    edge_case/...
  verifier/
    code_tests.py
    lint_type.py
    semantic.py
  replay/
    recorder.py
    player.py
  benchmark_suite.py  # CLI, runners, N-run self-consistency
```

A.4 Observability

```
common/telemetry/
  schema.py       # event dataclasses
  logger.py       # JSON lines with context
  otel.py         # tracer setup & spans
```

A.5 Orchestrator Adapter Example (Python)

```
# */-implementation/adapter.py
from common.agent_api import AgentAdapter, RunResult
from common.telemetry import logger, trace

class CrewAIAdapter(AgentAdapter):
    name = "crewai_v2"
    def configure(self, config: dict) -> None: ...
    @trace.span("run_task")
    def run_task(self, task: dict, context: dict) -> RunResult:
        # build crew, wire tools -> common/safety + common/vcs
        # stream tokens, emit events
        # return standardized RunResult
        ...
    def events(self): ...
```

⸻

## Appendix B — Benchmark Tasks (condensed specs)

For each task: Inputs, Expected outcome, Verification, Artifacts, Notes.

1. Single-file Bug Fix
	•	Input: minimal repo; failing unit test; issue text.
	•	Expected: 1–2 line fix; tests pass.
	•	Verify: pytest -q; no lint errors; PR/MR opened.
2.	Multi-step Feature Addition
	•	Input: feature spec; code scaffold; missing tests.
	•	Expected: new function, docs, and tests; all pass.
	•	Verify: unit tests + docstring presence + PR template check.
3. Question Answering (codebase/logs)
	•	Input: indexed code or logs; question(s).
	•	Expected: accurate, grounded answer with references.
	•	Verify: reference match, judge rubric ≥ threshold.
4.	Code Optimization
	•	Input: slow function + perf test.
	•	Expected: faster implementation, same outputs.
	•	Verify: perf threshold met; unit tests green.
5.	Edge Case – Incorrect Issue
	•	Input: misleading issue.
	•	Expected: No change; comment explaining.
	•	Verify: no commit file changes; PR not opened (or advisory note).

⸻

## Appendix C — Model Guidance (Ollama-first)
	•	Code gen/review: code-specialized (e.g., codellama, deepseek-coder, qwen2.5-coder).
	•	Commit/PR texts, summaries: small instruct (e.g., llama2-7b-chat, gemma-2b/7b-it).
	•	QA over repo docs: general instruct 13B+; retrieval aug via LlamaIndex/Haystack.

⸻

## Appendix D — Parity Modes
	•	Autonomous mode: agent performs VCS actions itself.
	•	Advisory mode: agent produces diff/plan; harness applies.
	•	Both measured and compared; autonomous preferred default.

⸻

## Appendix E — Guides to Update
	•	Quickstart (Docker + Ollama)
	•	Safety policy & sandbox usage
	•	GitHub/GitLab setup (PAT/App, scopes)
	•	Benchmark CLI & replay
	•	Telemetry & Jaeger
	•	Orchestrator parity matrix
	•	Troubleshooting (common errors)

## Appendix F - Directory Structure

```
common/
  agent_api.py                 # Common adapter protocol (configure/run_task/events)
  config.py                    # Env/CLI/seed/model provider config merge
  ollama_integration.py        # (already present) + model routing, caching, streaming
  safety/
    execute.py                 # sandbox exec (subprocess/Docker), time/CPU/mem, no-net
    fs.py                      # allowlist paths, safe I/O
    net.py                     # network allowlist/deny-by-default
    injection.py               # input/output guards, optional LLM-judge
    policy.yaml                # central policy
  vcs/
    base.py                    # provider interface + retry/backoff
    github.py                  # GH branch/commit/PR + annotations
    gitlab.py                  # GL branch/commit/MR
    commit_msgs.py             # optional small-model commit subject generator
  telemetry/
    schema.py                  # event dataclasses (agent_start, llm_call, tool_call, etc.)
    logger.py                  # JSONL writer
    otel.py                    # OpenTelemetry tracer setup (Jaeger exporter)

benchmark/
  tasks/
    bugfix/...
    feature_add/...
    qa/...
    optimize/...
    edge_case/...
  verifier/
    code_tests.py
    lint_type.py
    semantic.py
  replay/
    recorder.py
    player.py
  benchmark_suite.py           # CLI: --framework --tasks --provider --mode --seed --out

comparison-results/
  dashboard.py                 # Add drill-down traces, parity matrix tab

# Orchestrator adapters (one thin file per framework)
langgraph-implementation/adapter.py
crewai-implementation/adapter.py
autogen-implementation/adapter.py
n8n-implementation/adapter.py
semantic-kernel-implementation/python/adapter.py
semantic-kernel-implementation/csharp/Adapter.cs
claude-subagents-implementation/adapter.py
langroid-implementation/adapter.py
llamaindex-implementation/adapter.py
haystack-implementation/adapter.py
strands-implementation/adapter.py

docs/
  guides/
    running_locally.md
    safety.md
    vcs_setup.md
    telemetry.md
    benchmark.md
  parity_matrix.md
  research/...
  requirements/...
docker-compose.yml
```



⸻

Machine-Readable Workplan (feed to Taskmaster/Codex)

Save as docs/requirements/workplan.yaml:

```
version: 1
owner: brock.butler@spreetail.com
epics:
  - id: EPIC-API
    title: Common Agent API & Wiring
    tasks:
      - id: T-API-001
        title: Define AgentAdapter protocol and RunResult/Event schemas
        files:
          - common/agent_api.py
        acceptance:
          - "Unit tests validate adapter conformance across mock adapters"
          - "Docstring examples render in README"
      - id: T-API-002
        title: Add task schema & config loader with seed/model prefs
        files:
          - common/config.py
        acceptance:
          - "Seed, model, provider, mode parsed and exposed to adapters"
    depends_on: []

  - id: EPIC-SAFETY
    title: Central Safety Module
    tasks:
      - id: T-SAFE-001
        title: Sandbox executor (no-net, time/mem/CPU limits)
        files:
          - common/safety/execute.py
          - common/safety/policy.yaml
        acceptance:
          - "Exec blocked on disallowed network"
          - "Exceeding limits raises SafetyTimeoutError"
      - id: T-SAFE-002
        title: FS allowlist & safe I/O wrappers
        files:
          - common/safety/fs.py
        acceptance:
          - "Writes outside repo root denied; tests cover escapes"
      - id: T-SAFE-003
        title: Network allowlist + resolver
        files:
          - common/safety/net.py
        acceptance:
          - "Denied by default; allowlist honored in tests"
      - id: T-SAFE-004
        title: Prompt injection guards (+ optional LLM judge)
        files:
          - common/safety/injection.py
        acceptance:
          - "Malicious patterns flagged; judge path stores rationale"
    depends_on: [EPIC-API]

  - id: EPIC-VCS
    title: GitHub & GitLab Modules
    tasks:
      - id: T-VCS-001
        title: Provider base + retry/backoff middleware
        files:
          - common/vcs/base.py
        acceptance:
          - "429 triggers exponential backoff with jitter (unit test)"
      - id: T-VCS-002
        title: GitHub provider (branch, commit, PR)
        files:
          - common/vcs/github.py
        acceptance:
          - "Opens branch+PR in sandbox repo; templates applied"
      - id: T-VCS-003
        title: GitLab provider (branch, commit, MR)
        files:
          - common/vcs/gitlab.py
        acceptance:
          - "Opens branch+MR; minimal scopes validated"
      - id: T-VCS-004
        title: Commit message generator (Ollama small model)
        files:
          - common/vcs/commit_msgs.py
        acceptance:
          - "Given diff, returns concise imperative subject (<60 chars)"
    depends_on: [EPIC-API]

  - id: EPIC-PARITY
    title: Upgrade Existing Orchestrators to Parity
    tasks:
      - id: T-PAR-001
        title: LangGraph adapter wiring (safety, VCS, telemetry)
        files:
          - langgraph-implementation/adapter.py
        acceptance:
          - "Runs 5 tasks (advisory+autonomous) on GH+GL"
      - id: T-PAR-002
        title: CrewAI v2 migration + adapter
        files:
          - crewai-implementation/adapter.py
        acceptance:
          - "Event hooks emit telemetry; guardrails active"
      - id: T-PAR-003
        title: AutoGen adapter
        files:
          - autogen-implementation/adapter.py
      - id: T-PAR-004
        title: n8n parity (advisory if needed) + API trigger
        files:
          - n8n-implementation/adapter.py
      - id: T-PAR-005
        title: Semantic Kernel (Py & C#) parity
        files:
          - semantic-kernel-implementation/python/adapter.py
          - semantic-kernel-implementation/csharp/Adapter.cs
      - id: T-PAR-006
        title: Claude Code Subagents adapter
        files:
          - claude-subagents-implementation/adapter.py
    depends_on: [EPIC-API, EPIC-SAFETY, EPIC-VCS, EPIC-TELEM]

  - id: EPIC-NEW
    title: New Orchestrators (Full Parity)
    tasks:
      - id: T-NEW-001
        title: Langroid adapter
        files:
          - langroid-implementation/adapter.py
      - id: T-NEW-002
        title: LlamaIndex Agents adapter (+ optional index build step)
        files:
          - llamaindex-implementation/adapter.py
      - id: T-NEW-003
        title: Haystack Agents adapter
        files:
          - haystack-implementation/adapter.py
      - id: T-NEW-004
        title: Strands Agents adapter
        files:
          - strands-implementation/adapter.py
    acceptance:
      - "Each runs 5 tasks on GH+GL; safety + telemetry enforced"
    depends_on: [EPIC-PARITY]

  - id: EPIC-BENCH
    title: Benchmark Suite v2
    tasks:
      - id: T-BENCH-001
        title: Task specs & fixtures for 5 tasks
        files:
          - benchmark/tasks/**/*
      - id: T-BENCH-002
        title: Verification runners (pytest, lint/type, semantic)
        files:
          - benchmark/verifier/*
      - id: T-BENCH-003
        title: Self-consistency (N runs, majority/score)
        files:
          - benchmark/benchmark_suite.py
      - id: T-BENCH-004
        title: Record–replay (recorder/player)
        files:
          - benchmark/replay/*
      - id: T-BENCH-005
        title: CLI & JSON artifact outputs
        files:
          - benchmark/benchmark_suite.py
    acceptance:
      - "CLI runs, outputs results.json + artifacts/, replay works"
    depends_on: [EPIC-API]

  - id: EPIC-TELEM
    title: Observability & Dashboard
    tasks:
      - id: T-TELEM-001
        title: Event schema + JSON logger
        files:
          - common/telemetry/schema.py
          - common/telemetry/logger.py
      - id: T-TELEM-002
        title: OpenTelemetry spans + Jaeger docker
        files:
          - common/telemetry/otel.py
          - docker-compose.yml
      - id: T-TELEM-003
        title: Dashboard drill-down (traces, tokens, parity)
        files:
          - comparison-results/dashboard.py
    acceptance:
      - "Per-run traces viewable; dashboard shows parity matrix"
    depends_on: [EPIC-BENCH]

  - id: EPIC-PERF
    title: Ollama-first Performance
    tasks:
      - id: T-PERF-001
        title: Model routing by task; streaming; caching
        files:
          - common/ollama_integration.py
      - id: T-PERF-002
        title: Small-model fallbacks & partial reruns
        files:
          - common/ollama_integration.py
    depends_on: [EPIC-PARITY, EPIC-BENCH]

  - id: EPIC-REPRO
    title: Reproducibility & Packaging
    tasks:
      - id: T-REPRO-001
        title: Docker Compose services (agents, Jaeger, dashboard)
        files:
          - docker-compose.yml
          - Dockerfile
      - id: T-REPRO-002
        title: Lockfiles/pins + env capture
        files:
          - requirements.txt
          - poetry.lock
          - requirements-csharp.txt
      - id: T-REPRO-003
        title: Seeds & config doc
        files:
          - docs/guides/running_locally.md
    depends_on: [EPIC-TELEM]

  - id: EPIC-DOCS
    title: Documentation & Guides
    tasks:
      - id: T-DOCS-001
        title: Parity matrix & orchestrator guides
        files:
          - docs/requirements/framework_selection_guide.md
          - docs/parity_matrix.md
      - id: T-DOCS-002
        title: Safety policy & sandbox guide
        files:
          - docs/guides/safety.md
      - id: T-DOCS-003
        title: GitHub/GitLab setup & scopes
        files:
          - docs/guides/vcs_setup.md
      - id: T-DOCS-004
        title: Telemetry & Jaeger guide
        files:
          - docs/guides/telemetry.md
      - id: T-DOCS-005
        title: Benchmark CLI + replay guide
        files:
          - docs/guides/benchmark.md
      - id: T-DOCS-006
        title: Research findings & proposals
        files:
          - docs/research/research_findings.md
          - docs/research/landscapes/*
          - docs/research/proposals/*
    depends_on: [EPIC-PARITY, EPIC-NEW, EPIC-BENCH, EPIC-TELEM, EPIC-PERF, EPIC-REPRO]
```
