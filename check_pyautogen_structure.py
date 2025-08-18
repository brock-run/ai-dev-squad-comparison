"""
Check the structure of the pyautogen module to find the correct import path for AssistantAgent.
"""

import pyautogen
import inspect

# Print the module structure
print("pyautogen module structure:")
print(f"pyautogen version: {pyautogen.__version__ if hasattr(pyautogen, '__version__') else 'unknown'}")
print(f"pyautogen path: {pyautogen.__file__}")
print("\nAvailable attributes and submodules:")
for name in dir(pyautogen):
    if not name.startswith('__'):
        attr = getattr(pyautogen, name)
        if inspect.ismodule(attr):
            print(f"  Module: {name}")
            # Print submodule attributes
            for subname in dir(attr):
                if not subname.startswith('__'):
                    subattr = getattr(attr, subname)
                    if inspect.isclass(subattr):
                        print(f"    Class: {subname}")
                    elif inspect.isfunction(subattr):
                        print(f"    Function: {subname}")
        elif inspect.isclass(attr):
            print(f"  Class: {name}")
        elif inspect.isfunction(attr):
            print(f"  Function: {name}")

# Try to find AssistantAgent
print("\nSearching for AssistantAgent class:")
found = False

# Check in pyautogen module
if hasattr(pyautogen, 'AssistantAgent'):
    print(f"Found AssistantAgent in pyautogen module")
    found = True

# Check in submodules
for name in dir(pyautogen):
    if not name.startswith('__'):
        attr = getattr(pyautogen, name)
        if inspect.ismodule(attr):
            if hasattr(attr, 'AssistantAgent'):
                print(f"Found AssistantAgent in pyautogen.{name} module")
                found = True
                
                # Print the import statement to use
                print(f"Import statement: from pyautogen.{name} import AssistantAgent")

if not found:
    print("AssistantAgent class not found in pyautogen module or its submodules")