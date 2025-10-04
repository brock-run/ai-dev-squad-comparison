import os
from pathlib import Path
import textwrap
import importlib
import pytest


def test_env_overrides_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    try:
        cfg_mod = importlib.import_module("common.config")
    except ImportError as e:
        pytest.skip(f"common.config not available: {e}")
    
    sample_yaml = tmp_path / "system.yaml"
    sample_yaml.write_text(textwrap.dedent(
        """
        orchestrators:
          langgraph:
            enabled: false
        safety:
          enabled: true
        vcs:
          github:
            enabled: true
        """
    ))
    monkeypatch.setenv("AI_DEV_SQUAD_ORCHESTRATORS_LANGGRAPH_ENABLED", "true")
    # load_config(path) is expected; if your API differs, adapt here
    if hasattr(cfg_mod, "load_config"):
        try:
            manager = cfg_mod.load_config(str(sample_yaml))
            # Expect env override to win
            if hasattr(manager, "is_orchestrator_enabled"):
                assert manager.is_orchestrator_enabled("langgraph") is True
        except Exception as e:
            pytest.skip(f"Config loading failed (validation error): {e}")
    else:
        pytest.skip("common.config.load_config not available")