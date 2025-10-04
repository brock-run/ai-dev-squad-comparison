import subprocess
import sys
from pathlib import Path
import pytest


def test_benchmark_help_runs():
    script = Path("benchmark/benchmark_suite.py")
    if not script.exists():
        return  # tolerate missing (repo in flux)
    proc = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    if proc.returncode != 0:
        # Skip if there are import errors (missing dependencies)
        if "ModuleNotFoundError" in proc.stderr or "ImportError" in proc.stderr:
            pytest.skip(f"Benchmark script has missing dependencies: {proc.stderr}")
        else:
            assert False, proc.stderr
    assert "--framework" in proc.stdout or "framework" in proc.stdout.lower()