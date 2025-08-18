"""
Test script to verify the correct import structure for pyautogen.
"""

print("Testing pyautogen imports...")

try:
    import pyautogen
    print(f"Successfully imported pyautogen")
    print(f"pyautogen version: {pyautogen.__version__ if hasattr(pyautogen, '__version__') else 'unknown'}")
    print(f"pyautogen path: {pyautogen.__file__}")
    
    # Try to import AssistantAgent directly from pyautogen
    try:
        from pyautogen import AssistantAgent
        print("Successfully imported AssistantAgent from pyautogen")
    except ImportError as e:
        print(f"Failed to import AssistantAgent from pyautogen: {e}")
    
    # Try to import AssistantAgent from autogen
    try:
        import autogen
        print(f"Successfully imported autogen")
        print(f"autogen version: {autogen.__version__ if hasattr(autogen, '__version__') else 'unknown'}")
        print(f"autogen path: {autogen.__file__}")
        
        try:
            from autogen import AssistantAgent
            print("Successfully imported AssistantAgent from autogen")
        except ImportError as e:
            print(f"Failed to import AssistantAgent from autogen: {e}")
    except ImportError as e:
        print(f"Failed to import autogen: {e}")
    
    # Try to create an AssistantAgent
    print("\nTrying to create an AssistantAgent...")
    try:
        # Try with pyautogen
        agent = pyautogen.AssistantAgent(name="TestAgent", system_message="You are a test agent")
        print("Successfully created AssistantAgent using pyautogen.AssistantAgent")
    except Exception as e:
        print(f"Failed to create AssistantAgent using pyautogen.AssistantAgent: {e}")
        
        # Try with autogen if available
        try:
            import autogen
            agent = autogen.AssistantAgent(name="TestAgent", system_message="You are a test agent")
            print("Successfully created AssistantAgent using autogen.AssistantAgent")
        except Exception as e:
            print(f"Failed to create AssistantAgent using autogen.AssistantAgent: {e}")
    
except ImportError as e:
    print(f"Failed to import pyautogen: {e}")