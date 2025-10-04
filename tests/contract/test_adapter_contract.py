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
        try:
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return mod
        except ImportError as e:
            # Skip modules that have import errors (missing dependencies, etc.)
            pytest.skip(f"Cannot import {path}: {e}")
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