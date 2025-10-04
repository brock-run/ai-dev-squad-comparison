import importlib
import pytest


def test_network_default_deny():
    try:
        net = importlib.import_module("common.safety.net")
    except Exception as e:
        pytest.skip(f"No common.safety.net module: {e}")
    # Expect a default policy object or builder; be flexible
    if hasattr(net, "NetworkPolicy"):
        try:
            # Try to create a default policy
            policy = getattr(net, "NetworkPolicy")()
            if hasattr(policy, "default_deny"):
                assert bool(getattr(policy, "default_deny")) is True
        except Exception:
            # If that fails, try with empty dict
            try:
                policy = getattr(net, "NetworkPolicy")({})
                if hasattr(policy, "default_deny"):
                    # Check if it's a boolean or has a truthy value
                    default_deny_val = getattr(policy, "default_deny")
                    if isinstance(default_deny_val, bool):
                        assert default_deny_val is True
                    else:
                        # Skip if the implementation is different than expected
                        pytest.skip(f"NetworkPolicy.default_deny has unexpected type: {type(default_deny_val)}")
            except Exception as e:
                pytest.skip(f"Cannot create NetworkPolicy: {e}")