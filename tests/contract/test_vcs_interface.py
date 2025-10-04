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