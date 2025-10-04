#!/usr/bin/env bash
set -euo pipefail

# Check for deprecated references, excluding meta-documentation files
if grep -R "run_benchmarks.py" -n docs comparison-results README* \
  --exclude-dir="docs/requirements" \
  --exclude="*starter-pack*" \
  --exclude="*scratchpad*" \
  --exclude="*analysis*" >/dev/null 2>&1; then
  echo "Found deprecated reference to run_benchmarks.py" >&2
  exit 1
fi

echo "Docs check passed"