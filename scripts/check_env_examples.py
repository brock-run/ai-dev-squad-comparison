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