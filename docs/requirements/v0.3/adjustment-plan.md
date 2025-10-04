# Decision brief — how to adjust remaining tasks in the v0.2 workstream

**Scope covered:** Self-Consistency Evaluation + Record-Replay + related backlog items (CLI, seeds, compose).

| Option                            | What it means                                                                                                                                                                        | Pros                                                                             | Cons                                                                                           | When to pick                                           |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| A. Ship as-is (no changes)        | Implement plans verbatim                                                                                                                                                             | Fast to start                                                                    | Risk of parallel subsystems: duplicated event schemas, replay logic per adapter, harder parity | If you had no v1 common layers (you do)                |
| **B. Adjust to v1 (recommended)** | Rebase both features on **common/telemetry** (events), **common/agent_api** (adapters), **common/config** (seeds), **common/safety** (exec). Keep your algorithms, slim the surface. | One event stream, one storage format, simpler adapters, better CI gates & replay | A few refactors now                                                                            | You want maintainable parity + traceability            |
| C. Abandon & rewrite later        | Defer both features to after parity                                                                                                                                                  | Simplifies short-term                                                            | You lose determinism + evaluation signal that justify the whole comparison                     | Only if you’re schedule-blocked by parity (you aren’t) |

**Recommendation:** **B. Adjust**. Constrain both features to the shared layers we already defined. That gives you record→replay→consistency with minimal glue per adapter and makes CI/observability painless.

---

# What to change (surgical deltas)

## 1) Record-Replay System (keep, but adjust)

**Design deltas**

* **Single event stream:** Do not invent a new payload. Reuse `common/telemetry/schema.py` and add 3 new event types: `replay_checkpoint`, `recording_note`, `replay_assert`. Emit **JSONL** (one event per line) with a **manifest.yaml**.
* **Storage format:** One folder per run:

  ```
  artifacts/<run_id>/
    events.jsonl.zst         # all telemetry (compressed)
    manifest.yaml            # hashes, versions, seeds, adapter, framework
    inputs/…                 # task inputs, fixtures
    outputs/…                # agent artifacts, files, patches
    diffs/…                  # git diffs if VCS used
  ```

  Use content hashes (BLAKE3) in `manifest.yaml` for integrity.
* **Interception points (uniform across adapters):**

  * LLM/tool IO (`llm_call`, `tool_call`) — wrap in common decorator `@telemetry.capture_io(mode=record|replay)`.
  * Sandbox exec (`common/safety/execute.py`) — log `exec_start/exec_end` with command, limits, rc, bytes in/out.
  * VCS ops (`common/vcs/*`) — log `vcs_action` with request/response summaries.
* **Replay engine:** Deterministic mode replaces **only** IO edges (LLM output, tool results, network) with recorded outputs based on a stable **lookup key**: `{event_type, adapter, agent_id, tool_name, call_index}` plus a short **fingerprint** of inputs (hash of prompt+params). Fail fast on mismatch.

**Acceptance (v1):**

* `replay` of a recorded run produces identical `events.jsonl` except for `timestamp`/durations (allow list).
* 95%+ of steps deterministic on CPU-only Ollama tasks with seeds fixed.
* Integrity: modified `events.jsonl` is detected by manifest hash check.

**ETA:** **1 week** (foundation + LangGraph & CrewAI wired), add **2–3 days** to wire remaining adapters as they come online.

---

## 2) Self-Consistency Evaluation (keep, but adjust)

**Design deltas**

* **Live on top of BenchmarkSuite:** Put all code under `benchmark/consistency/*`, but **don’t** define a new result type. Wrap/aggregate existing `BenchmarkResult`; add a thin `ConsistencyEnvelope` for aggregations only.
* **Seeds first, temperature optional:** Default to **seed variation** via `common/config` seed graph; make temperature/prompt variation opt-in flags to avoid conflating sources of variance.
* **Consensus strategy (keep simple, visible):**

  * Default: **Majority vote** on `verified_pass` (from the verifier).
  * Weighted option: multiply votes by **verification score** ∈ [0,1] (if present) — no bespoke quality scorer until later.
* **Reliability score (bounded, interpretable):**

  ```
  success_rate = passes / N
  stdev_time   = std(zscore(duration))
  stdev_tokens = std(zscore(tokens))
  score = 0.6*success_rate + 0.2*(1 - clamp(stdev_time,0,1)) + 0.2*(1 - clamp(stdev_tokens,0,1))
  ```

  Label: High (≥0.8), Medium (0.6–0.8), Low (<0.6).
* **Outliers:** Tukey fences over verification score or duration. Report indexes + seeds; don’t auto-exclude from consensus unless `--exclude-outliers` is set.
* **Output:** one `consistency.json` alongside per-run artifacts. Dashboard reads it to plot violin plots and confidence bars.

**CLI (examples)**

```bash
python -m benchmark.benchmark_suite \
  --framework langgraph --tasks bugfix --provider github \
  --mode autonomous --seed 42 --consistency.runs 5 \
  --consistency.strategy majority --out results/
```

**Acceptance (v1):**

* Runs **N=5** complete on a single dev box with Ollama; total time overhead ≤ 20% vs N serial runs thanks to parallelism.
* Produces: consensus pass/fail, 95% CI for time/tokens, reliability label.
* Backward compatible: `--consistency.runs 1` behaves like single run.

**ETA:** **1 week** (executor + analyzer + reporter) after record-replay foundation is in.

---

## 3) Enhanced Benchmark CLI (keep, tighten)

* Extend the existing CLI; don’t fork a new tool. New flags (all optional):
  `--consistency.runs`, `--consistency.strategy`, `--parallel`, `--replay <path>`, `--seed <int>`, `--seed.strategy <sequential|random|user>`, `--out <dir>`.
* Emits a **run manifest** (JSON) capturing: adapters, model ids, seeds, policy, git SHA, hardware.

**Acceptance:** one binary `results.json` (top-level summary) + per-run artifact dirs + optional `consistency.json`.

**ETA:** **0.5 week**.

---

## 4) Compose & CI tie-ins (augment what we already shipped)

* Add a `replay-smoke` CI job: record a tiny run (mocked LLM), then replay; assert equality on event fingerprints.
* Add a `consistency-smoke`: N=3 on a toy task with a stub verifier (always pass). Gate ensures JSON schema + CIs compute.
* Budget guard: fail if wall-clock for `consistency-smoke` > configured budget (e.g., 8 minutes).

---

# Concrete file map (drop-ins)

* `benchmark/consistency/multi_run_executor.py` — spins N runs; parallel using `concurrent.futures.ProcessPoolExecutor` (avoid GIL).
* `benchmark/consistency/consensus_analyzer.py` — majority/weighted, CI calc.
* `benchmark/consistency/variance_calculator.py` — stdevs, fences.
* `benchmark/consistency/consistency_reporter.py` — writes `consistency.json`.
* `benchmark/replay/recorder.py` — wraps telemetry logger to file+zstd.
* `benchmark/replay/player.py` — swaps IO with recorded payloads; asserts.
* `common/telemetry/schema.py` — add events (`replay_checkpoint`, `recording_note`, `replay_assert`) + version bump.
* `common/config.py` — seed graph + CLI merge helpers (`--seed.strategy`).
* `comparison-results/dashboard.py` — read `consistency.json` (violin plot of durations; stacked bars for pass counts).

---

# CI gates to add (lightweight, high value)

1. **Replay determinism (mocked)**

* Record 1 run with a **MockLLM** (deterministic outputs).
* Replay; assert `N_event_mismatches == 0`.

2. **Consistency envelope schema**

* JSONSchema validate `consistency.json`.

3. **Runtime budget**

* Fail if `make consistency-smoke` exceeds budget on CI runners.

4. **Provenance**

* Fail if manifest is missing `{git_sha, adapter_versions, model_ids, seeds, policy}`.

---

# Risks & mitigations (focused)

| Risk                                               | Likelihood | Impact | Mitigation                                                             | Trigger                 |
| -------------------------------------------------- | ---------- | ------ | ---------------------------------------------------------------------- | ----------------------- |
| Adapter drift (can’t intercept LLM/tool uniformly) | M          | H      | Central wrappers in `common/telemetry` + adapter conformance tests     | New adapter PR          |
| Event schema churn                                 | M          | M      | Versioned schema; JSONSchema + golden tests                            | Schema bump PR          |
| Replay key collisions (different calls, same hash) | L          | M      | Include `call_index` and agent/tool ids; assert uniqueness             | Replay mismatch         |
| Non-deterministic tools (timestamps, UUIDs)        | M          | M      | Normalize via filters (`output_sanitizers`) before hashing             | Test failures           |
| Ollama variability across models                   | M          | M      | Seeds + temperature clamp; document models with deterministic sampling | Inconsistent pass rates |
| Perf overhead from recording                       | M          | M      | Zstd streaming; buffered writes; selective fields in dev               | CI exceeds budget       |

---

# 2-week implementation plan (hybrid strangler)

**Week 1**

* Day 1–2: Telemetry event additions + `recorder.py` + seed control in `common/config`.
* Day 3: `player.py` (LLM/tool intercept) + LangGraph adapter wrap.
* Day 4: CrewAI wrap + replay smoke in CI + docs.
* Day 5: Harden: hashing, manifest integrity, failure modes.

**Week 2**

* Day 1–2: `multi_run_executor` + `consensus_analyzer` + variance calc.
* Day 3: Reporter + CLI flags + consistency smoke in CI.
* Day 4: Dashboard minimal integration (consistency tab).
* Day 5: Polish: examples, Make targets, write ADR “Replay & Consistency”.

---

# Go / No-Go per planned item

* **Record-Replay:** **GO (adjusted)** — base it on telemetry and the adapter contract; cut custom serialization beyond manifest + JSONL.zst.
* **Self-Consistency:** **GO (adjusted)** — keep algorithms, but derive all inputs from verifier + timings; avoid separate “quality” model for now.
* **Enhanced CLI:** **GO (tighten)** — extend existing CLI, don’t fork.
* **Seed Control:** **GO** — centralize in `common/config`, pass through adapter context.
* **Compose infra:** **GO (already started)** — augment with Jaeger only if you actually look at traces in week 2–3; otherwise stub exporter.

If you want, I can generate the skeleton files listed above (empty but compilable, with type stubs and TODOs) so you can paste them directly into the repo.
