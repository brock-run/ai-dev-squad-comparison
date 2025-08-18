"""
Check if the autogen module is available and how it should be imported.
"""

try:
    import autogen
    print("Successfully imported autogen module")
    print(f"autogen version: {autogen.__version__ if hasattr(autogen, '__version__') else 'unknown'}")
    print(f"autogen path: {autogen.__file__}")
except ImportError as e:
    print(f"Failed to import autogen: {e}")
    
    try:
        import pyautogen
        print("Successfully imported pyautogen module")
        print(f"pyautogen version: {pyautogen.__version__ if hasattr(pyautogen, '__version__') else 'unknown'}")
        print(f"pyautogen path: {pyautogen.__file__}")
    except ImportError as e:
        print(f"Failed to import pyautogen: {e}")