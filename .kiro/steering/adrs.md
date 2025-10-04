# Kiro IDE Steering Guide — ADR‑Backed Guardrails (v1)

> **Purpose**: Give Kiro a single, authoritative playbook so all generated code, configs, and tests align with our Architecture Decision Records (ADRs) and the v1 plan. Treat this as **policy + contracts**; deviations must be flagged in PRs.

**Repo**: `agentic-dev-squad`
**Owners**: Platform Team (@brock.butler)
**Date**: 2025‑09‑29
**Scope**: Orchestrator adapters, safety, VCS, benchmarking, record‑replay, determinism, telemetry, docs, CI.

---

## 0) Non‑Negotiable Invariants (from ADRs)

* **Safety first** (ADR‑001..005): All code execution, FS, and network I/O go through `common/safety/*`. Default‑deny network. FS allowlist. Sandbox required.
* **Unified adapter surface** (ADR‑015): Every framework implements `common.agent_api.AgentAdapter` and emits standardized events.
* **Determinism & provenance** (ADR‑011): Seeds are propagated, captured, and replayable. All runs carry a manifest with versions + hashes.
* **Record‑Replay** (ADR‑007/012): IO edges are decorated for recording and deterministic replay (strict/warn/hybrid). Streaming supported.
* **Telemetry as the source of truth** (ADR‑008): JSONL events + OTel spans for every LLM/tool/VCS action. No silent side effects.
* **Redaction & retention** (ADR‑014): Secrets never land in artifacts. Retain only what policy allows.
* **Parity modes** (ADR‑013): Adapters must support Autonomous and Advisory; dashboard reflects parity.
* **VCS abstraction** (ADR‑006): GitHub/GitLab ops only via `common/vcs/*` with retries, scopes, and audit.

> Kiro: Refuse to generate code that bypasses these invariants. If a user prompt conflicts, insert TODOs + warnings and propose compliant alternatives.

---

## 1) ADR Capsule Index (what to enforce)

* **ADR‑001 Security Architecture**: Layered defense (sandbox, FS, net, injection). Policy‑driven.
* **ADR‑002 Execution Sandbox**: Docker primary, subprocess fallback. No‑net by default, resource limits.
* **ADR‑003 Network Controls**: Allowlist, rate‑limits, audit. Default‑deny.
* **ADR‑004 Prompt Injection Guards**: Input/output scanning; threat levels; optional LLM judge.
* **ADR‑005 Security Policy Manager**: Unified YAML policies; levels: disabled→paranoid; violations logged.
* **ADR‑006 VCS Integration**: Provider protocol + GitHub/GitLab impl, retries/backoff, templates.
* **ADR‑007 Record‑Replay System**: Full‑fidelity recording and deterministic replay across frameworks.
* **ADR‑008 Event/Telemetry Schema**: JSONL events for `agent_start`, `llm_call[*]`, `tool_call`, `sandbox_exec`, `vcs_action`, `checkpoint`, `adapter_error` with streaming `chunk`s.
* **ADR‑009 Canonicalization & IO Keys**: Stable fingerprints (BLAKE3 over canonical input+params); ordering via `step/parent_step/call_index`.
* **ADR‑010 Self‑Consistency Evaluation**: Multi‑run, consensus strategies, variance, reliability scores.
* **ADR‑011 Determinism & Seed Bus**: Single seed authority; `ClockProvider`, `RngProvider`, UUID/path clamps.
* **ADR‑012 Replay Engine Modes**: `strict|warn|hybrid`, partial replay, mismatch diffs, streaming pacing.
* **ADR‑013 Parity Modes**: Autonomous vs Advisory behaviors and measurement.
* **ADR‑014 Redaction & Retention**: Secret scrubbing, storage classes (dev/ci/prod), size/PII guards.
* **ADR‑015 Adapter Contract & Conformance**: Interface + event emission + safety usage; contract tests in CI.

---

## 2) Adapter Contract (what Kiro must generate)

**File**: `*/-implementation/adapter.py`

```python
# common.agent_api
class AgentAdapter(Protocol):
    name: str
    def configure(self, config: dict) -> None: ...
    def run_task(self, task: dict, context: dict) -> "RunResult": ...
    def events(self) -> Iterable["Event"]: ...
```

**Requirements**

1. **Safety wiring (ADR‑001/002/003/004/005)**

   * All code execution through `common/safety/execute.py`.
   * FS ops via `common/safety/fs.py`; net via `common/safety/net.py`.
   * Scan inputs/outputs with `common/safety/injection.py`.
2. **VCS (ADR‑006)**

   * Branch/commit/PR/MR only via `common/vcs/*` utilities.
3. **Telemetry (ADR‑008/009)**

   * Emit events with fields: `run_id`, `framework`, `agent_id`, `task_id`, `step`, `parent_step`, `call_index`, `ts`, `type`, `model`, `seed`, `inputs_fingerprint`, `duration_ms`, `token_in/out`, `cost_estimate`, `result_ref`.
4. **Record‑Replay decorators (ADR‑007/012)**

   * Wrap **IO edges**: LLM, tools, sandbox, VCS. Avoid wrapping orchestration control‑flow.
5. **Parity (ADR‑013)**

   * Support `mode=autonomous|advisory`. Advisory produces diffs/plans; harness applies.
6. **Determinism (ADR‑011)**

   * Use `ClockProvider`/`RngProvider`/`UuidProvider` from `common/*`.

**Adapter Done‑When**

* Contract tests in `tests/contract/adapter_*.py` pass.
* Replay of a golden run succeeds in `strict` mode.
* Safety unit tests demonstrate blocked net/FS without policy allow.

---

## 3) Event & Manifest Contracts

**Event JSON (ADR‑008/009)**

```json
{
  "run_id": "uuid",
  "framework": "crewai_v2",
  "agent_id": "developer",
  "task_id": "T-BUGFIX-001",
  "type": "llm_call.started|chunk|finished|tool_call|vcs_action|sandbox_exec|checkpoint|adapter_error",
  "step": 42,
  "parent_step": 41,
  "call_index": 3,
  "ts": "2025-09-29T12:34:56.789Z",
  "model": "llama3.1:8b",
  "seed": 42,
  "inputs_fingerprint": "b3:...",
  "payload": {"redacted": true},
  "duration_ms": 1280,
  "token_in": 512,
  "token_out": 256,
  "cost_estimate": 0.0012,
  "result_ref": "artifacts/xyz.json"
}
```

**Manifest (written per run)**

```yaml
run_id: uuid
adapter_version: semver
git_sha: abcdef1
config_digest: b3:...
seed: 42
models:
  llm: llama3.1:8b
policies:
  safety: strict
  network: default_deny
artifacts:
  - path: artifacts/events.jsonl.zst
  - path: artifacts/manifest.yaml
redaction_log:
  - pattern: GITHUB_TOKEN
```

---

## 4) Record‑Replay Requirements (what to instrument)

* **Canonicalization** (ADR‑009): sort keys, trim whitespace, normalize line endings before hashing.
* **Replay modes** (ADR‑012): `strict` (fail on first miss), `warn` (surface miss, allow live), `hybrid` (per‑domain policy).
* **Partial replay**: `--from-checkpoint`, `--until-step`.
* **Streaming**: store `llm_call.chunk` events; replay with original pacing or `--fast`.
* **Clamps** (ADR‑011): time/UUID/temp paths reproduced from recording.
* **Policy**: replay executes with **no network**, FS allowlist only; any attempted bypass is a failure.

---

## 5) Self‑Consistency (how Kiro wires evaluation)

* **Config** (ADR‑010):

  * `num_runs`, `randomization_strategy = seed|prompt|temperature`, `consensus_strategy = majority|weighted|mode|confidence|hybrid`.
* **Outputs**: `ConsistencyResult` with `consensus_result`, `confidence`, `variance_metrics`, `reliability_score`, `stability_rating`.
* **CLI**: `--consistency.runs N --consistency.strategy weighted_majority --seed 42`.
* **Replay integration**: `--consistency.use-recordings` and `--consistency.record-once --replay-n`.

---

## 6) Safety & Policy (what Kiro enforces by default)

* **Default policy**: `standard` (ADR‑005): Docker sandbox, default‑deny network, FS allowlist.
* **Escalation**: If a feature request needs net/FS broader access, require explicit policy diff and justification comment.
* **Injection guard** (ADR‑004): attach to all LLM inputs/outputs.

---

## 7) VCS Rules (ADR‑006)

* Only use `common/vcs/github.py` and `gitlab.py` for repo ops.
* Respect rate limits; retries with jitter; minimal scopes.
* PR/MR templates via provider config; advisory mode produces patchset + template body.

---

## 8) CI Gates (what must pass)

* **contract‑adapter** (ADR‑015): adapter interface + event emission + safety usage.
* **record‑replay‑strict** (ADR‑007/012): golden runs replay bit‑exact.
* **redaction‑audit** (ADR‑014): no secrets in JSONL/artifacts.
* **policy‑enforce** (ADR‑005): net default‑deny enforced by tests.
* **bench‑consistency‑smoke** (ADR‑010): runs=3 with stable reliability score.

> Kiro: Whenever you scaffold a new adapter or feature, also generate/patch the CI config to include these gates.

---

## 9) File & Service Layout (targets Kiro should honor)

```
common/
  agent_api.py
  safety/{execute.py,fs.py,net.py,injection.py,policy.yaml}
  vcs/{base.py,github.py,gitlab.py,commit_msgs.py}
  telemetry/{schema.py,logger.py,otel.py}
benchmark/
  replay/{recorder.py,player.py,manifest.py}
  consistency/{multi_run_executor.py,consensus_analyzer.py}
  benchmark_suite.py
comparison-results/dashboard.py
*/-implementation/adapter.py
```

**Compose services**: `ollama`, `jaeger`, `dashboard`, `adapter-*` (per framework), `api` (optional).

---

## 10) Standard Env & Config (what Kiro injects by default)

* `.env.example` baseline: `OLLAMA_BASE_URL`, `LLM_MODEL_DEFAULT`, per‑role models, `GITHUB_TOKEN`, `GITLAB_TOKEN`, `SAFETY_POLICY=standard`, `REPLAY_MODE`, `SEED`.
* Config precedence: **CLI > ENV > config file defaults**.

---

## 11) “Do Not” List (automatic guardrails)

* ❌ Direct `requests`/`open()` bypassing `common/safety/*`.
* ❌ Raw GitHub/GitLab REST calls outside `common/vcs/*`.
* ❌ LLM/tool calls without telemetry + recorder decorators.
* ❌ Writing secrets or full prompts into logs/artifacts.
* ❌ New adapter without contract tests and golden recording.

Kiro should replace such patterns with compliant wrappers and leave review comments in code with `ADR‑XXXX` references.

---

## 12) Snippets Kiro Can Reuse

**LLM call wrapper (record+telemetry+redaction)**

```python
@record_io(domain="llm")
@telemetry.span("llm_call")
def call_llm(prompt: dict, model: str, seed: int) -> dict:
    safe_in = injection.scan_input(prompt)
    out = llm_client.generate(prompt=safe_in, model=model, seed=seed)
    return injection.scan_output(out)
```

**Sandboxed exec (no‑net)**

```python
result = safety.execute(code, language="python", policy=policy.strict())
```

**VCS commit via provider**

```python
pr = vcs.github.create_pull_request(owner, repo, title, body, source_branch, target_branch)
```

---

## 13) Authoring Rules for Kiro

* Start every generated file with a lightweight provenance header (run_id, ADR refs).
* Emit TODOs when an ADR requirement cannot be satisfied; include suggested compliant approach.
* Prefer small, composable modules; wire via adapters.
* Always add/update tests + CI with the code.

---

## 14) Acceptance Checklists (quick copy‑paste)

**Adapter**

* [ ] Implements `AgentAdapter`
* [ ] All IO edges wrapped with record+telemetry
* [ ] Uses safety FS/net/exec wrappers
* [ ] Emits required events (incl. streaming)
* [ ] Supports autonomous & advisory
* [ ] Golden run recorded + strict replay green

**Feature touching LLM/tool**

* [ ] Canonicalization + fingerprint
* [ ] Seeds propagated
* [ ] Injection guard enabled
* [ ] Redaction verified

**VCS Flow**

* [ ] Uses provider API only
* [ ] Handles rate limits
* [ ] Template applied; advisory diff available

---

## 15) Change Control

* Any deviation from ADRs requires an explicit PR section: *ADR Impact*. Include a proposed ADR amendment or a temporary waiver with expiry.

---

### Final Note

This guide is the **ground truth** for Kiro. Generate code that satisfies these contracts by default; when a user asks for shortcuts, produce compliant scaffolds plus an explanation and minimal safe example. If unsure, link the relevant ADR section identifier in a comment and stop before generating unsafe code.
