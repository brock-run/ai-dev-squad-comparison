"""
Development Workflow for Semantic Kernel Implementation

This module orchestrates the plugins for the development process.
"""

import os
import semantic_kernel as sk
from typing import Dict, List, Any, Optional

# Import plugins
from plugins.architect_plugin import ArchitectPlugin
from plugins.developer_plugin import DeveloperPlugin
from plugins.tester_plugin import TesterPlugin

def create_development_kernel() -> sk.Kernel:
    """
    Create a kernel with all development plugins registered.
    
    Returns:
        Configured kernel
    """
    # Create a new kernel
    kernel = sk.Kernel()
    
    # Configure Ollama as the AI service
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    
    # Add Ollama as the AI service
    kernel.add_text_completion_service("ollama", 
                                      sk.ollama.OllamaTextCompletion(ollama_model, 
                                                                    base_url=ollama_base_url))
    
    # Register plugins
    kernel.register_plugin(ArchitectPlugin(kernel), "architect")
    kernel.register_plugin(DeveloperPlugin(kernel), "developer")
    kernel.register_plugin(TesterPlugin(kernel), "tester")
    
    return kernel

async def run_development_workflow(task: str, requirements: List[str], language: str = "python") -> Dict[str, Any]:
    """
    Run the development workflow for a given task and requirements.
    
    Args:
        task: Description of the development task
        requirements: List of requirements
        language: Programming language to use
        
    Returns:
        Results of the development process
    """
    # Create kernel with plugins
    kernel = create_development_kernel()
    
    # Format requirements as a string
    requirements_text = "\n".join(requirements)
    
    # Step 1: Create design with architect
    variables = sk.ContextVariables()
    variables["task"] = task
    variables["requirements"] = requirements_text
    
    design_result = await kernel.run_async("architect", "create_design", variables)
    design = str(design_result)
    
    # Step 2: Implement code with developer
    variables = sk.ContextVariables()
    variables["design"] = design
    variables["language"] = language
    
    code_result = await kernel.run_async("developer", "implement_code", variables)
    code = str(code_result)
    
    # Step 3: Create test cases with tester
    variables = sk.ContextVariables()
    variables["code"] = code
    variables["requirements"] = requirements_text
    variables["language"] = language
    
    test_cases_result = await kernel.run_async("tester", "create_test_cases", variables)
    test_cases = str(test_cases_result)
    
    # Step 4: Run tests with tester
    variables = sk.ContextVariables()
    variables["code"] = code
    variables["tests"] = test_cases
    variables["language"] = language
    
    test_results_result = await kernel.run_async("tester", "run_tests", variables)
    test_results = str(test_results_result)
    
    # Step 5: Evaluate code with tester
    variables = sk.ContextVariables()
    variables["code"] = code
    variables["requirements"] = requirements_text
    variables["test_results"] = test_results
    
    evaluation_result = await kernel.run_async("tester", "evaluate_code", variables)
    evaluation = str(evaluation_result)
    
    # Step 6: Refine code if needed
    if "improvements needed" in evaluation.lower() or "issues found" in evaluation.lower():
        variables = sk.ContextVariables()
        variables["code"] = code
        variables["feedback"] = evaluation
        
        refined_code_result = await kernel.run_async("developer", "refine_code", variables)
        code = str(refined_code_result)
        
        # Re-run tests and evaluation
        variables = sk.ContextVariables()
        variables["code"] = code
        variables["tests"] = test_cases
        variables["language"] = language
        
        test_results_result = await kernel.run_async("tester", "run_tests", variables)
        test_results = str(test_results_result)
        
        variables = sk.ContextVariables()
        variables["code"] = code
        variables["requirements"] = requirements_text
        variables["test_results"] = test_results
        
        evaluation_result = await kernel.run_async("tester", "evaluate_code", variables)
        evaluation = str(evaluation_result)
    
    # Return results
    return {
        "task": task,
        "requirements": requirements,
        "design": design,
        "code": code,
        "test_cases": test_cases,
        "test_results": test_results,
        "evaluation": evaluation
    }

if __name__ == "__main__":
    import asyncio
    
    # Example usage
    task = "Build a Python function to calculate Fibonacci numbers"
    requirements = [
        "Must handle negative numbers",
        "Should be optimized for performance",
        "Should include proper error handling",
        "Should have clear documentation"
    ]
    
    # Run the workflow
    result = asyncio.run(run_development_workflow(task, requirements))
    
    # Print results
    print(f"Task: {result['task']}")
    print("\nDesign:")
    print(result['design'])
    
    print("\nCode:")
    print(result['code'])
    
    print("\nTest Cases:")
    print(result['test_cases'])
    
    print("\nTest Results:")
    print(result['test_results'])
    
    print("\nEvaluation:")
    print(result['evaluation'])