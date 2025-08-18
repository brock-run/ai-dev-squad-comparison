"""
Check the structure of the autogen-agentchat package to find the correct import path for AssistantAgent.
"""

import inspect
import sys
import importlib

def check_module_structure(module_name):
    """Check the structure of a module and look for AssistantAgent class."""
    try:
        module = importlib.import_module(module_name)
        print(f"\n{module_name} module structure:")
        print(f"{module_name} version: {module.__version__ if hasattr(module, '__version__') else 'unknown'}")
        print(f"{module_name} path: {module.__file__}")
        
        # Check if AssistantAgent is directly in this module
        if hasattr(module, 'AssistantAgent'):
            print(f"Found AssistantAgent in {module_name} module")
            print(f"Import statement: from {module_name} import AssistantAgent")
            return True
        
        # Look for any agent-related classes directly in this module
        print(f"\nSearching for agent-related classes in {module_name}:")
        for name in dir(module):
            if name.startswith('__'):
                continue
            
            try:
                attr = getattr(module, name)
                if inspect.isclass(attr):
                    if "Agent" in name:
                        print(f"  Found potential agent class: {name}")
                        print(f"  Import statement: from {module_name} import {name}")
            except Exception as e:
                print(f"  Error accessing {name}: {e}")
        
        # Look for AssistantAgent in submodules
        print(f"\nSearching for AssistantAgent in {module_name} submodules:")
        for name in dir(module):
            if name.startswith('__'):
                continue
                
            try:
                attr = getattr(module, name)
                if inspect.ismodule(attr):
                    submodule_name = f"{module_name}.{name}"
                    print(f"  Checking submodule: {submodule_name}")
                    
                    # Check if AssistantAgent is in this submodule
                    if hasattr(attr, 'AssistantAgent'):
                        print(f"  Found AssistantAgent in {submodule_name}")
                        print(f"  Import statement: from {submodule_name} import AssistantAgent")
                        return True
                    
                    # Print classes in this submodule
                    print(f"  Classes in {submodule_name}:")
                    agent_classes_found = False
                    for subname in dir(attr):
                        if subname.startswith('__'):
                            continue
                        try:
                            subattr = getattr(attr, subname)
                            if inspect.isclass(subattr):
                                # Check if this class has "Agent" in its name
                                if "Agent" in subname:
                                    print(f"    Potential agent class: {subname}")
                                    print(f"    Import statement: from {submodule_name} import {subname}")
                                    agent_classes_found = True
                        except Exception as e:
                            print(f"    Error accessing {subname}: {e}")
                    
                    # If no agent classes found in this submodule, check its submodules
                    if not agent_classes_found:
                        for subname in dir(attr):
                            if subname.startswith('__'):
                                continue
                            try:
                                subattr = getattr(attr, subname)
                                if inspect.ismodule(subattr):
                                    sub_submodule_name = f"{submodule_name}.{subname}"
                                    print(f"    Checking sub-submodule: {sub_submodule_name}")
                                    
                                    # Print classes in this sub-submodule
                                    for sub_subname in dir(subattr):
                                        if sub_subname.startswith('__'):
                                            continue
                                        try:
                                            sub_subattr = getattr(subattr, sub_subname)
                                            if inspect.isclass(sub_subattr):
                                                if "Agent" in sub_subname:
                                                    print(f"      Potential agent class: {sub_subname}")
                                                    print(f"      Import statement: from {sub_submodule_name} import {sub_subname}")
                                        except Exception as e:
                                            print(f"      Error accessing {sub_subname}: {e}")
                            except Exception as e:
                                print(f"    Error accessing {subname}: {e}")
            except Exception as e:
                print(f"  Error accessing {name}: {e}")
        
        return False
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")
        return False

# Check pyautogen
print("Checking pyautogen...")
found = check_module_structure("pyautogen")

# Check autogen-agentchat (try different import names)
if not found:
    print("\nChecking autogen_agentchat...")
    found = check_module_structure("autogen_agentchat")

if not found:
    print("\nChecking autogen.agentchat...")
    found = check_module_structure("autogen.agentchat")

if not found:
    print("\nChecking autogen...")
    found = check_module_structure("autogen")

if not found:
    print("\nAssistantAgent class not found in any of the checked modules")
    
    # Try to find any module that might contain AssistantAgent
    print("\nSearching for modules with 'autogen' in the name:")
    for module_name in sys.modules:
        if 'autogen' in module_name.lower():
            print(f"Found module: {module_name}")