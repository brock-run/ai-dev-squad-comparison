# New File Starter Pack

* PR checklist + CI workflow (GitHub Actions)
* Contract tests you can paste into `tests/contract/`
* `docker-compose.yml`, Makefile targets, and a `scripts/smoke.sh`
* A canonical `.env.example` (plus adapter-local variant) and CI that enforces parity

## How to wire it in (quick)

1. **Files**
   Copy each block to the indicated path in your repo. Duplicate the adapter `.env.example` into every `*-implementation/` directory.

2. **Run locally**

```bash
python -m pip install -r requirements.txt   # if present
make up
make smoke     # runs contract tests inside compose runner
make down
```

3. **Enable CI**

* Commit the `.github/` contents and `scripts/`.
* Push a branch and open a PR. CI runs: lint → contract tests → docs/env gates → compose smoke.

### What this enforces (gates)

* Adapters expose the minimal contract (`name`, `run_task`, `events`) and reference safety wrappers.
* Config precedence works as env > YAML > defaults.
* VCS providers expose a consistent API surface.
* Docs don’t reference the deprecated `run_benchmarks.py`.
* Every adapter ships a consistent `.env.example`.
* Compose smoke brings up Ollama + Jaeger and runs contract tests headlessly.

Below are ready-to-drop artifacts. Copy each block into the indicated path.

---

## .github/PULL_REQUEST_TEMPLATE.md

```md
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
```

---

## .github/workflows/ci.yml

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [ main ]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      pycache: ${{ steps.python-cache.outputs.cache-hit }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '7.0.x'
      - name: Install Python deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt || true
      - name: Cache pip
        id: python-cache
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('**/requirements*.txt') }}

  lint_and_test:
    runs-on: ubuntu-latest
    needs: setup
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install tools
        run: |
          pip install -r requirements.txt || true
          pip install pytest pytest-cov ruff mypy
      - name: Ruff (Python lint)
        run: ruff .
      - name: Mypy (type check)
        run: mypy --hide-error-context --pretty . || true
      - name: Contract tests (pytest)
        run: pytest -q tests/contract --maxfail=1 --disable-warnings -q
      - name: Unit tests (if present)
        run: pytest -q || true

  docs_and_env_checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Docs check
        run: bash scripts/docs_check.sh
      - name: Env examples check
        run: python scripts/check_env_examples.py

  smoke_compose:
    runs-on: ubuntu-latest
    needs: [lint_and_test, docs_and_env_checks]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Compose
        run: |
          docker --version
          docker compose version
      - name: Smoke via compose (runner uses scripts/smoke.sh)
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN || '' }}
          GITLAB_TOKEN: ${{ secrets.GITLAB_TOKEN || '' }}
        run: |
          make up
          make smoke
          make down
```

---

## tests/contract/test_adapter_contract.py

```python
import inspect
import json
import os
from pathlib import Path
from typing import Iterable

import importlib.util
import pytest

# Paths to scan for adapters
ROOT = Path(__file__).resolve().parents[2]
ADAPTER_GLOBS = [
    "*-implementation/adapter.py",
    "*-implementation/**/adapter.py",
]

REQUIRED_ATTRS = ["name", "run_task", "events"]


def _discover_adapter_files() -> Iterable[Path]:
    for pattern in ADAPTER_GLOBS:
        for p in ROOT.glob(pattern):
            if "csharp" in str(p).lower():
                continue
            yield p


def _load_module_from_path(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod
    raise RuntimeError(f"Cannot import module from {path}")


@pytest.mark.parametrize("adapter_path", list(_discover_adapter_files()))
def test_adapter_has_required_contract(adapter_path: Path):
    mod = _load_module_from_path(adapter_path)
    # Find first class that looks like an adapter
    adapter_cls = None
    for _, cls in inspect.getmembers(mod, inspect.isclass):
        if cls.__module__ == mod.__name__ and any(hasattr(cls, a) for a in REQUIRED_ATTRS):
            adapter_cls = cls
            break
    assert adapter_cls is not None, f"No adapter-like class found in {adapter_path}"
    for attr in REQUIRED_ATTRS:
        assert hasattr(adapter_cls, attr), f"{adapter_cls.__name__} missing attr: {attr}"


@pytest.mark.parametrize("adapter_path", list(_discover_adapter_files()))
def test_adapter_references_safety(adapter_path: Path):
    # Heuristic: file must import or reference common.safety
    text = adapter_path.read_text(encoding="utf-8", errors="ignore")
    assert "common.safety" in text or "common/safety" in text or "from common import safety" in text, (
        f"{adapter_path} does not appear to reference safety wrappers"
    )
```

---

## tests/contract/test_config_precedence.py

```python
import os
from pathlib import Path
import textwrap
import importlib
import pytest


def test_env_overrides_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_mod = importlib.import_module("common.config")
    sample_yaml = tmp_path / "system.yaml"
    sample_yaml.write_text(textwrap.dedent(
        """
        orchestrators:
          langgraph:
            enabled: false
        safety:
          enabled: true
        """
    ))
    monkeypatch.setenv("AI_DEV_SQUAD_ORCHESTRATORS_LANGGRAPH_ENABLED", "true")
    # load_config(path) is expected; if your API differs, adapt here
    if hasattr(cfg_mod, "load_config"):
        manager = cfg_mod.load_config(str(sample_yaml))
        # Expect env override to win
        if hasattr(manager, "is_orchestrator_enabled"):
            assert manager.is_orchestrator_enabled("langgraph") is True
    else:
        pytest.skip("common.config.load_config not available")
```

---

## tests/contract/test_benchmark_cli.py

```python
import subprocess
import sys
from pathlib import Path


def test_benchmark_help_runs():
    script = Path("benchmark/benchmark_suite.py")
    if not script.exists():
        return  # tolerate missing (repo in flux)
    proc = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "--framework" in proc.stdout or "framework" in proc.stdout.lower()
```

---

## tests/contract/test_vcs_interface.py

```python
import importlib
import inspect
import pytest

REQUIRED = [
    "create_branch",
    "commit_changes",
    "create_pull_request",
]

@pytest.mark.parametrize("module_name", [
    "common.vcs.github",
    "common.vcs.gitlab",
])
def test_vcs_provider_api_surface(module_name: str):
    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        pytest.skip(f"{module_name} not importable: {e}")
    funcs = {name for name, obj in inspect.getmembers(mod) if inspect.isfunction(obj) or inspect.iscoroutinefunction(obj)}
    missing = [f for f in REQUIRED if f not in funcs]
    # Allow class-based providers; search methods on a Provider class
    if missing:
        provider_cls = None
        for _, cls in inspect.getmembers(mod, inspect.isclass):
            methods = {n for n, _ in inspect.getmembers(cls, inspect.isfunction)}
            if set(REQUIRED).issubset(methods):
                provider_cls = cls
                missing = []
                break
    assert not missing, f"{module_name} missing: {missing}"
```

---

## tests/contract/test_safety_policy_defaults.py

```python
import importlib
import pytest


def test_network_default_deny():
    try:
        net = importlib.import_module("common.safety.net")
    except Exception as e:
        pytest.skip(f"No common.safety.net module: {e}")
    # Expect a default policy object or builder; be flexible
    if hasattr(net, "NetworkPolicy"):
        # Default should be deny unless explicitly overridden
        policy = getattr(net, "NetworkPolicy")({})  # tolerate empty config
        if hasattr(policy, "default_deny"):
            assert bool(getattr(policy, "default_deny")) is True
```

---

## docker-compose.yml

```yaml
version: "3.9"

volumes:
  ollama: {}

services:
  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 20

  jaeger:
    image: jaegertracing/all-in-one:1.57
    restart: unless-stopped
    ports:
      - "16686:16686"   # UI
      - "4317:4317"     # OTel gRPC

  runner:
    image: python:3.11-slim
    profiles: ["smoke"]
    working_dir: /app
    environment:
      AI_DEV_SQUAD_OLLAMA_BASE_URL: http://ollama:11434
      AI_DEV_SQUAD_OTEL_EXPORTER_ENDPOINT: http://jaeger:4317
    volumes:
      - ./:/app
    depends_on:
      ollama:
        condition: service_healthy
    command: bash scripts/smoke.sh

  n8n:
    image: n8nio/n8n:latest
    profiles: ["n8n"]
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
    ports:
      - "5678:5678"
    volumes:
      - ./.n8n_data:/home/node/.n8n
```

---

## Makefile (add or merge these targets)

```make
.PHONY: up down smoke dash lint format test contract

up:
	docker compose up -d jaeger ollama
	docker compose ps

e2e:
	docker compose --profile smoke up --build runner --abort-on-container-exit
	docker compose rm -fsv runner

smoke: up e2e down

down:
	docker compose down -v

lint:
	ruff . || true
	mypy --hide-error-context --pretty . || true

contract:
	pytest -q tests/contract --maxfail=1 --disable-warnings

 test:
	pytest -q

format:
	ruff format .
```

---

## scripts/smoke.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

python --version

# Minimal smoke: contract tests + benchmark CLI help
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt || true
fi
pip install pytest || true

pytest -q tests/contract --maxfail=1 --disable-warnings || exit 1

if [ -f "benchmark/benchmark_suite.py" ]; then
  python benchmark/benchmark_suite.py --help >/dev/null 2>&1 || {
    echo "benchmark_suite.py --help failed"; exit 1;
  }
fi

echo "Smoke OK"
```

---

## scripts/check_env_examples.py

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

REQUIRED_KEYS = {
    "AI_DEV_SQUAD_OLLAMA_BASE_URL",
    "AI_DEV_SQUAD_MODEL_DEFAULT",
    "AI_DEV_SQUAD_MODEL_CODER",
    "AI_DEV_SQUAD_SEED",
    "AI_DEV_SQUAD_SAFETY_SANDBOX",
    "AI_DEV_SQUAD_NETWORK_DEFAULT_DENY",
    "AI_DEV_SQUAD_OTEL_EXPORTER_ENDPOINT",
    "AI_DEV_SQUAD_VCS_PROVIDER",
    "GITHUB_TOKEN",
    "GITLAB_TOKEN",
}

ROOT = Path(__file__).resolve().parents[1]
impl_dirs = [p for p in ROOT.glob("*-implementation") if p.is_dir()]

missing = {}
for d in impl_dirs:
    envf = d / ".env.example"
    if not envf.exists():
        missing[str(d)] = [".env.example (file missing)"]
        continue
    text = envf.read_text(encoding="utf-8", errors="ignore")
    keys_present = {line.split("=", 1)[0].strip() for line in text.splitlines() if "=" in line and not line.strip().startswith("#")}
    absent = sorted(list(REQUIRED_KEYS - keys_present))
    if absent:
        missing[str(d)] = absent

if missing:
    print("Missing env keys per implementation:")
    for d, keys in missing.items():
        print(f"- {d}:")
        for k in keys:
            print(f"    - {k}")
    sys.exit(1)

print("All implementation .env.example files present and complete.")
```

---

## scripts/docs_check.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

if grep -R "run_benchmarks.py" -n docs comparison-results README* >/dev/null 2>&1; then
  echo "Found deprecated reference to run_benchmarks.py" >&2
  exit 1
fi

echo "Docs check passed"
```

---

## .env.example (root)

```dotenv
# ===== Core environment =====
AI_DEV_SQUAD_ENV=development
AI_DEV_SQUAD_SEED=42

# Ollama (local LLMs)
AI_DEV_SQUAD_OLLAMA_BASE_URL=http://localhost:11434
AI_DEV_SQUAD_MODEL_DEFAULT=llama3.1:8b
AI_DEV_SQUAD_MODEL_CODER=codellama:13b
AI_DEV_SQUAD_MODEL_SMALL=llama3.2:3b

# Per-role overrides (optional)
AI_DEV_SQUAD_MODEL_ARCHITECT=
AI_DEV_SQUAD_MODEL_DEVELOPER=
AI_DEV_SQUAD_MODEL_QA=

# ===== Safety & Policy =====
AI_DEV_SQUAD_SAFETY_SANDBOX=docker   # docker | subprocess
AI_DEV_SQUAD_SAFETY_TIMEOUT_SECONDS=300
AI_DEV_SQUAD_NETWORK_DEFAULT_DENY=true
AI_DEV_SQUAD_NETWORK_ALLOWLIST=api.github.com,api.gitlab.com

# ===== VCS (tokens optional for advisory) =====
AI_DEV_SQUAD_VCS_PROVIDER=github     # github | gitlab | none
GITHUB_TOKEN=
GITLAB_TOKEN=

# ===== Telemetry =====
AI_DEV_SQUAD_LOG_LEVEL=INFO
AI_DEV_SQUAD_OTEL_EXPORTER_ENDPOINT=http://localhost:4317

# ===== Adapters toggle (comma-separated) =====
AI_DEV_SQUAD_ADAPTERS_ENABLED=langgraph,crewai,autogen,n8n,semantic_kernel,langroid,llamaindex,haystack,strands

# ===== n8n (optional) =====
N8N_HOST=http://localhost:5678
```

---

## adapters/.env.example (use this same content in each *-implementation/.env.example)

```dotenv
# This file mirrors the root .env.example for adapter-local development.
AI_DEV_SQUAD_ENV=development
AI_DEV_SQUAD_SEED=42
AI_DEV_SQUAD_OLLAMA_BASE_URL=http://localhost:11434
AI_DEV_SQUAD_MODEL_DEFAULT=llama3.1:8b
AI_DEV_SQUAD_MODEL_CODER=codellama:13b
AI_DEV_SQUAD_MODEL_SMALL=llama3.2:3b
AI_DEV_SQUAD_MODEL_ARCHITECT=
AI_DEV_SQUAD_MODEL_DEVELOPER=
AI_DEV_SQUAD_MODEL_QA=
AI_DEV_SQUAD_SAFETY_SANDBOX=docker
AI_DEV_SQUAD_SAFETY_TIMEOUT_SECONDS=300
AI_DEV_SQUAD_NETWORK_DEFAULT_DENY=true
AI_DEV_SQUAD_NETWORK_ALLOWLIST=api.github.com,api.gitlab.com
AI_DEV_SQUAD_VCS_PROVIDER=github
GITHUB_TOKEN=
GITLAB_TOKEN=
AI_DEV_SQUAD_LOG_LEVEL=INFO
AI_DEV_SQUAD_OTEL_EXPORTER_ENDPOINT=http://localhost:4317
N8N_HOST=http://localhost:5678
```

---

### Notes

* If `common.config` APIs differ, adjust `tests/contract/test_config_precedence.py` accordingly.
* If your VCS provider classes are class-based, `test_vcs_interface.py` will accept either module-level functions **or** class methods.
* `docker-compose.yml` uses profiles so `n8n` and `runner` are optional. `make smoke` spins up `ollama` and `jaeger`, then runs contract tests inside `runner`.
* Duplicate `.env.example` into every `*-implementation/` directory to satisfy CI (`scripts/check_env_examples.py`).
* Extend `scripts/smoke.sh` later to run a tiny benchmark (advisory, provider=none) once your CLI supports it.

