You’re in great shape. Ship Task 4 next. Below is a tight, implementation-ready plan for **AI Service Integration (Semantic Judge, shadow mode)** plus a few tiny hardening items to close out Task 3.

---

# Pre-Task-4 nits (fast, high value)

* **DB CAS + uniqueness**: enforce one applied plan per mismatch (`PARTIAL UNIQUE INDEX (mismatch_id) WHERE outcome->>'status'='applied'`). Gate apply with `UPDATE … WHERE status='approved'`.
* **Transform audit**: persist `{transform_id, config_fingerprint, before_hash, after_hash, idempotent}` into plan outcome; add checksum validation on rollback.
* **Metrics**: counters `resolution_apply_total{action}`, `resolution_noop_total{action}`, histogram `resolution_latency_ms{action}`. Alarms on apply error rate.

---

# Task 4 — AI Service Integration (Semantic Judge, SHADOW)

## Outcomes / gates

* Runs over the ≥200 labeled dataset in **shadow** (no mutations).
* Overall κ ≥ 0.8 (95% CI lower bound ≥ 0.75). FP ≤ 2% on held-out test set.
* Budgets enforced: `judge_usd_per_1k_tokens`, p95 latency caps per method.
* Zero policy or sandbox violations in logs.

## Components to implement

### 1) Provider adapters (version-pinned)

Create `common/phase2/ai/clients.py`:

```python
class LLMClient:
    def __init__(self, provider_id: str, model: str, max_tps: float, timeout_s: int, redact: bool): ...
    def chat(self, messages: list[dict], max_tokens: int, temperature: float, seed: int | None) -> dict: ...
    def count_tokens(self, messages: list[dict]) -> dict: ...

class EmbeddingClient:
    def __init__(self, provider_id: str, model: str): ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...
```

Adapters: `OpenAIAdapter`, `AzureOpenAIAdapter`, `OllamaAdapter` (dev).
Pin `{provider, model, version}` in config; log them into **Evaluation.metadata**.

### 2) Equivalence runner (method registry)

`common/phase2/judge.py`:

```python
from enum import Enum
from .diff_entities import Evaluation, EvaluationResult, EvaluationStatus
from .enums import EquivalenceMethod, ArtifactType

class EquivalenceRunner:
    def __init__(self, llm: LLMClient, embed: EmbeddingClient, budgets, sandbox):
        self.llm, self.embed, self.budgets, self.sandbox = llm, embed, budgets, sandbox

    def run(self, diff, src_text, tgt_text, atype: ArtifactType, methods: list[EquivalenceMethod]) -> Evaluation:
        ev = create_evaluation(diff.id, diff.source_artifact_id, diff.target_artifact_id, atype)
        ev.status = EvaluationStatus.RUNNING
        try:
            for m in methods:
                r = self._run_method(m, src_text, tgt_text, atype)
                ev.add_result(r)
                self._enforce_budgets(ev)  # cost/latency circuit breakers
            return ev.complete(True)
        except Exception as e:
            ev.error_message = str(e)
            return ev.complete(False)

    def _run_method(self, m, src, tgt, atype):
        if m == EquivalenceMethod.EXACT: ...
        elif m == EquivalenceMethod.CANONICAL_JSON: ...
        elif m == EquivalenceMethod.AST_NORMALIZED and atype == ArtifactType.CODE: ...
        elif m == EquivalenceMethod.COSINE_SIMILARITY: ...
        elif m == EquivalenceMethod.LLM_RUBRIC_JUDGE: return self._llm_rubric(src, tgt, atype)
        elif m == EquivalenceMethod.TEST_EXECUTION and atype == ArtifactType.CODE: ...
        else: raise ValueError(f"Unsupported method {m}")

    def _llm_rubric(self, src, tgt, atype):
        prompt = build_rubric_prompt(src, tgt, atype)  # below
        resp = self.llm.chat([{"role":"user","content":prompt}], max_tokens=256, temperature=0.0, seed=7)
        parsed = parse_json(resp)  # {"equivalent":bool,"confidence":0..1,"reasoning":str}
        return EvaluationResult(method=EquivalenceMethod.LLM_RUBRIC_JUDGE, **parsed, cost=resp["cost_usd"], latency_ms=resp["latency_ms"])
```

* **Budget enforcement**: drop to deterministic only if token/latency ceilings are exceeded; mark `ev.status=COMPLETED` and set `ev.metadata["downgrade"]="budget_exceeded"`.

### 3) Rubric prompt (strict JSON schema)

`common/phase2/prompts/judge_rubric.txt`:

```
You are an equivalence judge. Decide if TARGET is semantically equivalent to SOURCE.

Rules:
- Ignore formatting, ordering, markdown cosmetics.
- Preserve facts, units, and constraints. If any fact changes, it's NOT equivalent.
- For code: equivalence means same behavior; ignore whitespace/comment changes.

Return ONLY this JSON:
{"equivalent": <true|false>, "confidence": <0..1>, "reasoning": "<<=180 chars>", "violations": ["<short keywords>"]}

SOURCE:
<<<
{SOURCE_TEXT}
>>>
TARGET:
<<<
{TARGET_TEXT}
>>>
```

### 4) Embedding + cosine similarity

* Cache embeddings by `sha256(content)` (LRU + disk).
* For TEXT, compute similarity and map to confidence via a calibrated piecewise function (fit from your dataset). Log calibration version in metadata.

### 5) Sandbox & redaction

* Deny file/network/tool access in judge; only LLM/embedding endpoints allowed.
* Redact PII/secrets from prompts (`[EMAIL]`, `[API_KEY]`), store `redaction_applied=true` in **Evaluation.metadata**; keep original hashes for provenance.

### 6) CLI (shadow only)

* `bench judge --run <run_id>|--dataset <path> --shadow --methods cosine,llm_rubric --report out.json`
* `bench report judge --last N` → κ by type, ROC curve (if you compute thresholds), cost and p95 latency.

### 7) Config (budgets + methods per artifact)

`entities/eqc/eqc.text.v1.yaml` (example):

```yaml
id: eqc.text.v1
version: 1
artifact_type: text
methods: [exact, cosine_similarity, llm_rubric_judge]
thresholds:
  cosine_similarity: 0.86
  llm_confidence_min: 0.70
calibration:
  version: 1
  source: benchmark/datasets/phase2_mismatch_labels.jsonl
budgets:
  usd_per_1k_tokens_max: 0.02
  latency_ms_p95: 1200
```

(Repeat for `eqc.json.v1` and `eqc.code.v1`, swapping in `canonical_json`, `ast_normalized`, `test_execution`.)

### 8) Tests (no external calls)

* Fake providers that return deterministic token counts and payloads.
* Golden cases:

  * TEXT: paraphrase (equivalent), subtle unit change (not).
  * CODE: comment/indent changes (equivalent), behavior change (not), plus AST-normalized.
  * JSON: key order vs. value change.
* Budget tests: force token explosion → runner downgrades gracefully.
* Schema tests: rubric returns invalid JSON → robust parse with fail-closed result.

---

## Minimal code you can drop in (stubs)

**Prompt builder / parser**

```python
def build_rubric_prompt(src: str, tgt: str, atype):
    return open("common/phase2/prompts/judge_rubric.txt","r",encoding="utf-8").read()\
        .replace("{SOURCE_TEXT}", src[:6000]).replace("{TARGET_TEXT}", tgt[:6000])

def parse_json(resp):
    # resp from adapter: {"text": "...", "tokens": {...}, "latency_ms": int, "cost_usd": float}
    import json
    try:
        obj = json.loads(extract_json(resp["text"]))
        eq = bool(obj.get("equivalent", False))
        conf = float(obj.get("confidence", 0.0))
        reason = str(obj.get("reasoning",""))[:180]
        return {"equivalent": eq, "confidence": max(0.0, min(1.0, conf)), "similarity_score": 1.0 if eq else 0.0, "reasoning": reason}
    except Exception as e:
        return {"equivalent": False, "confidence": 0.0, "similarity_score": 0.0, "reasoning": f"parse_error:{e}"}

def extract_json(text: str) -> str:
    import re
    m = re.search(r'\{.*\}', text, re.S)
    return m.group(0) if m else '{"equivalent": false, "confidence": 0.0, "reasoning":"no-json"}'
```

**Embedding cache**

```python
class EmbeddingCache:
    def __init__(self, path=".cache/embeddings"): ...
    def get(self, key: str): ...
    def put(self, key: str, vec: list[float]): ...

def embed_cosine(embed_client, cache, text1, text2):
    import hashlib, math
    k1 = hashlib.sha256(text1.encode()).hexdigest()
    k2 = hashlib.sha256(text2.encode()).hexdigest()
    v1 = cache.get(k1) or cache.put(k1, embed_client.embed([text1])[0])
    v2 = cache.get(k2) or cache.put(k2, embed_client.embed([text2])[0])
    dot = sum(a*b for a,b in zip(v1,v2)); n1 = math.sqrt(sum(a*a for a in v1)); n2 = math.sqrt(sum(b*b for b in v2))
    return dot/(n1*n2) if n1 and n2 else 0.0
```

---

## Monitoring to add

* `judge_evaluations_total{method,artifact_type,status}`
* `judge_cost_usd_sum{method}` (counter), `judge_latency_ms` (histogram)
* `judge_budget_downgrade_total{reason}`
* `judge_kappa_overall` (CI exports from dataset runs)

---

## Risks & mitigations

| Risk                                | Likelihood | Impact | Mitigation                                                                       |
| ----------------------------------- | ---------- | ------ | -------------------------------------------------------------------------------- |
| Rubric over-accepts pretty rewrites | Med        | High   | Deterministic validators post-check; calibration set; sample human audit.        |
| Cost drift                          | Med        | Med    | Hard budgets + cache; per-run cost caps; alerts.                                 |
| Prompt injection in TARGET/SOURCE   | Low        | Med    | Neutralize/quote inputs; judge prompt forbids tool use; sandbox; redact secrets. |
| Adapter instability                 | Low        | Med    | Dual provider configs (local + cloud); graceful fallback to deterministic only.  |

---

## “Done” checklist for Task 4

* [ ] Judge runs in **shadow** across dataset and real runs; no mutations.
* [ ] κ, FP, cost, latency dashboards green; 95% CI printed in CI.
* [ ] Budgets + circuit breakers exercised in tests.
* [ ] All prompts, adapters, models **version-pinned** and recorded in Evaluation.metadata.
* [ ] No PII/secret leakage in prompts/logs (redaction flag on).

---

Proceed with Task 4 using the above—keep it **shadow-only** until the expanded dataset clears the κ/FP gates.
