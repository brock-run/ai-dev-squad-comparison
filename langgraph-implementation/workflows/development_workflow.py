"""
Development Workflow for LangGraph Implementation

This module defines the state graph and transitions for the AI development squad workflow.
It orchestrates the architect, developer, and tester agents to complete software development tasks.
"""

import os
from typing import Dict, List, Any, Annotated, TypedDict, Literal
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

# Import agents
from agents.architect import ArchitectAgent
from agents.developer import DeveloperAgent
from agents.tester import TesterAgent

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ENABLE_HUMAN_FEEDBACK = os.getenv("ENABLE_HUMAN_FEEDBACK", "true").lower() == "true"

# Define the state schema
class DevelopmentState(TypedDict):
    """State for the development workflow."""
    task: str
    requirements: List[str]
    design: Dict[str, Any]
    code: str
    tests: str
    test_results: Dict[str, Any]
    feedback: str
    status: Literal["design", "implementation", "testing", "review", "complete", "error"]
    error: str

# Initialize agents
architect_agent = ArchitectAgent()
developer_agent = DeveloperAgent()
tester_agent = TesterAgent()

def create_design(state: DevelopmentState) -> DevelopmentState:
    """
    Create a design for the given task and requirements.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated state with design information
    """
    try:
        # Get the task and requirements from the state
        task = state["task"]
        requirements = state["requirements"]
        
        # Create a design using the architect agent
        design_result = architect_agent.create_design(task, requirements)
        
        # Update the state with the design
        return {
            **state,
            "design": design_result["design"],
            "status": "implementation"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Error in design phase: {str(e)}",
            "status": "error"
        }

def implement_code(state: DevelopmentState) -> DevelopmentState:
    """
    Implement code based on the design.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated state with implemented code
    """
    try:
        # Get the task and design from the state
        task = state["task"]
        design = state["design"]
        
        # Implement code using the developer agent
        implementation_result = developer_agent.implement_code(task, design)
        
        # Update the state with the implemented code
        return {
            **state,
            "code": implementation_result["code"],
            "status": "testing"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Error in implementation phase: {str(e)}",
            "status": "error"
        }

def create_and_run_tests(state: DevelopmentState) -> DevelopmentState:
    """
    Create and run tests for the implemented code.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated state with test results
    """
    try:
        # Get the code and requirements from the state
        code = state["code"]
        requirements = state["requirements"]
        
        # Create test cases using the tester agent
        test_result = tester_agent.create_test_cases(code, "python", requirements)
        
        # In a real implementation, we would actually run the tests here
        # For this example, we'll simulate test results
        test_results = {
            "passed": 8,
            "failed": 0,
            "total": 8,
            "coverage": "85%"
        }
        
        # Update the state with the tests and results
        return {
            **state,
            "tests": test_result["test_code"],
            "test_results": test_results,
            "status": "review" if ENABLE_HUMAN_FEEDBACK else "complete"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Error in testing phase: {str(e)}",
            "status": "error"
        }

def human_review(state: DevelopmentState) -> DevelopmentState:
    """
    Simulate human review of the implementation.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated state with review feedback
    """
    # In a real implementation, this would wait for human input
    # For this example, we'll simulate a positive review
    return {
        **state,
        "feedback": "Implementation looks good. All tests pass with good coverage.",
        "status": "complete"
    }

def handle_error(state: DevelopmentState) -> DevelopmentState:
    """
    Handle errors in the workflow.
    
    Args:
        state: The current workflow state
        
    Returns:
        Updated state with error handling
    """
    # In a real implementation, this might try to recover or notify a human
    print(f"Error in workflow: {state['error']}")
    return state

def should_end(state: DevelopmentState) -> Literal["continue", "end"]:
    """
    Determine if the workflow should end.
    
    Args:
        state: The current workflow state
        
    Returns:
        "end" if the workflow should end, "continue" otherwise
    """
    if state["status"] == "complete" or state["status"] == "error":
        return "end"
    return "continue"

def development_workflow() -> StateGraph:
    """
    Create the development workflow state graph.
    
    Returns:
        The configured state graph for the development workflow
    """
    # Create a new state graph
    workflow = StateGraph(DevelopmentState)
    
    # Add nodes for each step in the workflow
    workflow.add_node("design", create_design)
    workflow.add_node("implementation", implement_code)
    workflow.add_node("testing", create_and_run_tests)
    workflow.add_node("review", human_review)
    workflow.add_node("error", handle_error)
    
    # Add edges to connect the nodes
    workflow.add_edge("design", "implementation")
    workflow.add_edge("implementation", "testing")
    workflow.add_edge("testing", "review")
    workflow.add_edge("review", END)
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "testing",
        should_end,
        {
            "end": END,
            "continue": "review"
        }
    )
    
    # Connect error handling
    workflow.add_edge("error", END)
    
    # Set the entry point
    workflow.set_entry_point("design")
    
    return workflow

def run_development_workflow(task: str, requirements: List[str]) -> Dict[str, Any]:
    """
    Run the development workflow for a given task and requirements.
    
    Args:
        task: The development task to complete
        requirements: List of requirements for the task
        
    Returns:
        The final state of the workflow
    """
    # Create the workflow
    workflow = development_workflow()
    
    # Create the initial state
    initial_state = {
        "task": task,
        "requirements": requirements,
        "design": {},
        "code": "",
        "tests": "",
        "test_results": {},
        "feedback": "",
        "status": "design",
        "error": ""
    }
    
    # Run the workflow
    result = workflow.invoke(initial_state)
    
    return result

if __name__ == "__main__":
    # Example usage
    task = "Build a Python function to calculate Fibonacci numbers"
    requirements = [
        "Must handle negative numbers",
        "Should be optimized for performance",
        "Should include proper error handling",
        "Should have clear documentation"
    ]
    
    result = run_development_workflow(task, requirements)
    
    print(f"Task: {result['task']}")
    print(f"Status: {result['status']}")
    
    if result['status'] == "complete":
        print("\nImplemented Code:")
        print(result['code'])
        
        print("\nTest Results:")
        for key, value in result['test_results'].items():
            print(f"  {key}: {value}")
    elif result['status'] == "error":
        print(f"Error: {result['error']}")