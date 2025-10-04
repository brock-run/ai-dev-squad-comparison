# Current State Analysis and Refactor Plan

## Adapter readiness snapshot (static signals)

(Score is a quick heuristic: +adapter, +common imports, +safety/vcs imports, +tests, +readme, –TODOs. Max ~8)

| Adapter dir                    |   Score | TODOs | .env.example | Tests |
| ------------------------------ | ------: | ----: | :----------: | :---: |
| crewai-implementation          | **7.0** |     0 |       ✅      |   ✅   |
| llamaindex-implementation      | **6.5** |     0 |       ❌      |   ✅   |
| strands-implementation         | **6.5** |     0 |       ❌      |   ✅   |
| haystack-implementation        |     6.0 |     1 |       ❌      |   ✅   |
| langgraph-implementation       |     6.0 |     2 |       ✅      |   ✅   |
| autogen-implementation         |     5.5 |     3 |       ✅      |   ✅   |
| n8n-implementation             |     5.5 |     3 |       ✅      |   ✅   |
| semantic-kernel-implementation |     5.5 |     6 |       ✅      |   ✅   |
| langroid-implementation        |     5.0 |     5 |       ❌      |   ✅   |
| claude-code-subagents          | **3.5** |     3 |       ❌      |   ❌   |

> Repo stats (high-level): ~75k lines Python, 10 JS files (n8n nodes), 4 C# files; tests present across most adapters (80 test files found). Docker Compose **not present**. Several `.env.example` files missing.


## Recommendation

**C) Hybrid strangler**. The common layer is worth keeping and polishing. At least 5 adapters are “green-ish” for convergence. We should **rewrite only what’s hollow** (replay/verify, Compose, some SK C# glue, parts of n8n bridging), and **refactor** the rest behind a strict adapter contract and safety layer.

The Hybrid strangler pattern will keep and harden the **common/ core**, migrate the top-ready adapters first, cordon the weak ones behind an **advisory mode**, and rebuild missing ops (replay/verify, Compose, dashboard drill-down) alongside.

* Pro: fastest path to v1 parity; risk isolated; continuous value.
* Con: requires discipline on “cut lines” and acceptance gates.

---

## Risk log 

| Risk                                                      | Likelihood | Impact | Mitigation                                                                                        | Owner         | Trigger                          |
| --------------------------------------------------------- | ---------: | -----: | ------------------------------------------------------------------------------------------------- | ------------- | -------------------------------- |
| API drift in orchestrators (CrewAI v2, LangGraph updates) |        Med |    Med | Pin versions; adapter feature flags; weekly check in CI                                           | Adapter leads | Build breaks on minor bumps      |
| Safety not actually wrapping **all** tool exec paths      |        Med |   High | Unit tests assert `common/safety/execute` used; deny-by-default net; “unsafe override” flag gated | Safety owner  | Tool runs without safety span    |
| VCS rate-limits / permission failures in CI               |        Med |    Med | Central retry/backoff; least-privilege PAT scopes docs; dry-run/advisory mode                     | VCS owner     | 429s / permission errors         |
| n8n parity: bridging Node↔Python adapter                  |        Med |    Med | REST shim + contract tests; advisory mode allowed; isolate in container                           | n8n owner     | E2E fails on PR flows            |
| Replay/Verifier stubs cause non-reproducible benchmarks   |       High |   High | Prioritize recorder/player + deterministic seeds; CI runner with artifacts                        | Bench owner   | Inconsistent benchmark outcomes  |
| Semantic Kernel C# glue lags (OTel, safety)               |        Med |    Med | Minimal adapter first; map to `common/` via thin interop; advisory mode                           | SK owner      | Telemetry/safety missing in runs |
| Docker Compose absent → higher setup friction             |       High |    Med | Add Compose with agents, Jaeger, dashboard; smoke test target                                     | DevEx owner   | Onboarding >30 min               |
| Config drift (.env/.yaml precedence)                      |        Med |    Low | Document precedence (env > YAML > defaults); config validator in CI                               | Config owner  | Conflicting env vs file          |
| Docs inconsistencies (old script names)                   |        Med |    Low | “Docs check” CI job; search & replace; PR template gate                                           | Docs owner    | New PR failing docs check        |

---

## Strangler migration plan — per adapter

**Cut lines for everyone:**

* Implements `common/agent_api.AgentAdapter` contract; returns standardized `RunResult`; emits `Event`s.
* All code/FS/net exec flows go through `common/safety/*`.
* All GitHub/GitLab interactions use `common/vcs/*`.
* Telemetry: emit JSON events + optional OTel spans.
* Config: respect `common/config` precedence (env > YAML > defaults).

Below, each adapter has: **Tasks → Acceptance → ETA** (focused dev days; single engineer).

### 1) LangGraph

**Tasks**

* Wire graph nodes to `AgentAdapter.run_task`; add **advisory/autonomous** modes.
* Ensure tool calls (code exec, FS, net) traverse `common/safety/*`.
* Emit per-edge/per-node events; attach `trace_id` from config.
* Add **state snapshot** artifact per iteration.
* Expand tests: transitions, retry on failure; goldens for Fibonacci + bugfix.

**Acceptance**

* 5 benchmark tasks pass in **advisory** and **autonomous** on GH **and** GL sandboxes.
* Safety tests prove deny-by-default network; FS confined to repo root.
* Telemetry shows per-step events with tokens & timings.

**ETA:** **3 days**

## 2) CrewAI (v2)

**Tasks**

* Move to CrewAI v2 API (if applicable); map crew tasks → `AgentAdapter` ops.
* Centralize model routing via `common/ollama_integration` (streaming/caching).
* Ensure HIL checkpoints (accept/reject) surface in events.

**Acceptance**

* Same as LangGraph; plus human-in-the-loop gate tested.

**ETA:** **3 days**

### 3) AutoGen

**Tasks**

* GroupChatManager → `run_task`; gate code execution via sandbox; capture conversation log to artifacts.
* Add stopping conditions (max turns / convergence).
* Tests for refinement loop determinism (seeded).

**Acceptance**

* Converges within N turns on simple tasks; record–replay reproduces prompts.

**ETA:** **4 days**

### 4) n8n

**Tasks**

* Stabilize custom nodes (architect/developer/tester); expose a **single webhook** entry that maps to `AgentAdapter`.
* Add **Python bridge** service (thin FastAPI) or make the adapter a REST client to n8n; all FS/net executed in Python side with safety.
* Credentials mapping doc + `.env.example` parity.

**Acceptance**

* End-to-end PR flow works in advisory mode; dashboard events show node→tool mapping.

**ETA:** **4 days**

### 5) Semantic Kernel — Python

**Tasks**

* Implement plugins → adapter; wire safety wrappers around “skills.”
* Add minimal examples for each benchmark task; test orchestration.

**Acceptance**

* 5 tasks pass in advisory; tokens/time recorded.

**ETA:** **4 days**

### 6) Semantic Kernel — C#

**Tasks**

* Implement `Adapter.cs` to mirror Python `AgentAdapter` via a small gRPC/HTTP shim to share telemetry + safety policy (or duplicate minimal safety in C# with subprocess sandbox calls).
* Add OTel spans; GitHub/GitLab via `common/vcs` from Python (bridge) or native C# client (longer).

**Acceptance**

* Advisory mode passes 3 of 5 tasks with events and safety; PR/MR created successfully.

**ETA:** **5 days** (bridge-first)

### 7) Langroid

**Tasks**

* Minimal agent config; retrieval optional. Map tool invocations through safety.
* Contract tests with shared fixtures.

**Acceptance**

* 4 core tasks pass (skip QA/logs if RAG not set); events present.

**ETA:** **3 days**

### 8) LlamaIndex Agents

**Tasks**

* Build optional index step; cache artifacts under `artifacts/index/`; adapter drives agents.
* Ensure no internet by default; local FS sources only unless allowlisted.

**Acceptance**

* QA task passes with reference grounding; tokens/time emitted.

**ETA:** **3 days**

### 9) Haystack Agents

**Tasks**

* Configure in-memory doc store for tests; standard tools via safety.
* Contract tests.

**Acceptance**

* 4/5 tasks pass in advisory; QA task uses added docs.

**ETA:** **3 days**

### 10) Strands Agents

**Tasks**

* Implement adapter around strands agent loop; ensure events stream.
* Safety/VCS hooks as above.

**Acceptance**

* 4/5 tasks pass; PR advisory works.

**ETA:** **4 days**

### 11) Claude Code Subagents (prompt library)

**Tasks**

* Provide a thin adapter that **injects prompt modules** into other adapters (flags to enable subagent personas).
* Document how to enable in each orchestrator.

**Acceptance**

* When enabled, prompts are visible in artifacts; at least one adapter shows measurable diffs in code-review task (logged).

**ETA:** **2 days**

---

## Cross-cutting work (platform)

| Workstream               | Tasks                                                                                                                                             | Acceptance                                                                                | ETA        |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------- |
| **Replay & Verifier**    | Implement `benchmark/replay/{recorder,player}.py`; `verifier/{code_tests,lint_type,semantic}.py` with real checks; seed control; per-run manifest | `--seed` works; recorder captures prompts/tools; replay matches; verifier gates pass/fail | **5 days** |
| **Compose & DevEx**      | Add `docker-compose.yml` (agents runner, Jaeger, dashboard, optional n8n); smoke test target; pin versions/lockfiles                              | `make up` brings stack; `make smoke` runs LangGraph & CrewAI advisory                     | **2 days** |
| **Telemetry drill-down** | Extend `comparison-results/dashboard.py` for per-span drilldown, parity matrix tab; log ingestion from JSONL                                      | Filterable timelines with tokens/costs; parity matrix view                                | **3 days** |
| **Config & .env parity** | Standardize `.env.example` across all adapters; document precedence (env > YAML > defaults); validator warns missing                              | Lint target fails if example missing or keys drift                                        | **1 day**  |
| **Docs cleanup**         | Replace references to `run_benchmarks.py`; add VCS setup, safety, telemetry guides; PR checklist gate                                             | Docs CI passes; new PR template checklist enforced                                        | **2 days** |
| **Safety tests**         | Malicious patterns suite; FS escape attempts; net default-deny check; time/mem limit tests                                                        | All safety tests green across adapters that execute code                                  | **2 days** |

**Total critical path (sequential, 1 engineer): ~** 36–40 dev-days. Parallelization across owners can collapse to **2–3 weeks** elapsed.

---

## What to do next (order of operations)

1. **Lock the cut lines** (adapter contract, safety/VCS hooks, telemetry requirements) in `common/` and publish a **mini spec** + contract tests.
2. **Finish platform gaps** first: Replay/Verifier + Compose + Docs fixes (unblocks reliable benchmarking).
3. **Migrate top-4 adapters** (CrewAI, LangGraph, LlamaIndex, Strands) to green with acceptance.
4. **Backfill n8n & SK** (bridge-first), then **Langroid/Haystack**.
5. Turn on **parity matrix** in dashboard; run the full suite against GH & GL sandboxes; publish snapshot.

