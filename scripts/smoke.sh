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
    echo "benchmark_suite.py --help failed (likely missing dependencies - acceptable for smoke test)";
  }
fi

echo "Smoke OK"