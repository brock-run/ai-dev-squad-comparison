Great momentum. You’re ~90% of the way to a clean shadow soak. Here’s the blunt state + fixes.

# State of play

* Infra, adapters, budgets, redaction, metrics: ✅
* Deterministic analyzers + transforms: ✅
* Judge CLI runs on dataset: ✅
* CI gates: ❌ Kappa gate fails (tiny dataset + methods used)

# Why the gate is red

1. **Dataset is only 8 items.** Any κ is noisy; CI lower bound will stay low no matter what.
2. **Methods run ≠ methods that lift κ.** Your gate ran `exact, cosine_similarity, canonical_json` (no LLM rubric), so semantic cases are missed → κ≈0.
3. **Embedding client**: looks unconfigured in CI (cosine shows 850 ms, 0.00 confidence). With a real embedding model + threshold calibration, you’ll recover some κ.

# Fix-now checklist (fast)

1. **Run with the methods that matter**

   * For TEXT: `exact + cosine_similarity + llm_rubric_judge`
   * For JSON: `canonical_json (+ exact)`
   * For CODE: `ast_normalized (+ tests_pass if you have it)`
   * CLI UX tweak (accept comma OR space-delimited):

     ```python
     # in cli_judge: parse --methods
     if len(methods)==1 and (',' in methods[0]):
         methods = [m.strip() for m in methods[0].split(',') if m.strip()]
     ```

2. **Configure embeddings in CI**

   * Point `EmbeddingClient` to a deterministic dev model (or your mock) and set a real threshold in `eqc.text.v1` (e.g., cosine ≥ 0.86).
   * Log model id in `Evaluation.metadata.model_version`.

3. **Include LLM rubric in CI shadow**

   * Add `llm_rubric_judge` with a small max tokens + `temperature=0` + fixed `seed`.
   * Keep in **shadow** (no mutations) and enforce cost/latency budgets.

4. **Kappa CI script: compare like-for-like**

   * Ensure predictions are strictly `{"equivalent","not_equivalent"}`; drop/ignore “uncertain”.
   * Require a prediction for every dataset item in the test split; skip train/dev.
   * If you haven’t already, pass **both** dataset + results so the script can align by `id`:

     ```bash
     python scripts/kappa_ci.py --dataset benchmark/datasets/phase2_mismatch_labels.jsonl \
                                --results judge_results.json --split test
     ```

# Near-term to green

* **Scale dataset** to ≥200 with the target class mix; re-run CI. Your κ will stabilize.
* **Calibrate thresholds** once on the 200+ set; pin in `calibration_manifest.json` and refuse drift without a new manifest.
* **Per-type κ**: export `phase2:kappa_by_type{mismatch_type=…}` so Grafana can show where κ is weak.

# Small hardening nits

* **Success flag consistency**: you changed `successful`→`success`; scan for any callers still using the old param (`.complete(success=True)`) and add a deprecation shim to avoid silent failures.
* **Method label hygiene**: align naming across enums/CLI (`CANONICAL_JSON` ↔ `canonical_json`). Add a canonicalization step in CLI to map both forms, and warn on unknown methods.
* **Confusion matrix/exporter**: emit `judge_confusion_total{label,predicted,artifact_type}` for Grafana. That lets you see FP/FN by class.

# Suggested CI gate targets (for the 200+ dataset)

* **Overall κ ≥ 0.80**, 95% CI lower bound ≥ 0.75.
* **Per-top-type κ ≥ 0.75** (text/code/json).
* **FP ≤ 2%** on test split.
* **Budget**: p95 LLM < 5 s; cost < $0.02 / 1k tokens.

# If you want a quick patch set

* I can produce:

  * a tiny CLI diff to parse `--methods` robustly (comma/space mixed),
  * an updated `kappa_ci.py` that takes dataset+results, filters to `split=test`, and prints per-type κ + confusion table,
  * a Prometheus exporter snippet for `kappa_by_type` and `judge_confusion_total`.

Otherwise: proceed to **7-day shadow soak** with LLM rubric enabled (shadow-only) and start **Task 5 (Operator UX)** in parallel.
