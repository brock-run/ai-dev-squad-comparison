"""
Development Process for CrewAI Implementation

This module defines the development process workflow for the AI development squad.
It orchestrates the architect, developer, and tester agents to complete software development tasks.
"""

import os
from typing import List, Dict, Any
from crewai import Crew, Task, Process

# Import agent factories
from agents.architect import ArchitectAgent
from agents.developer import DeveloperAgent
from agents.tester import TesterAgent

# Load environment variables
ENABLE_HUMAN_FEEDBACK = os.getenv("ENABLE_HUMAN_FEEDBACK", "true").lower() == "true"

def create_development_tasks(task_description: str, requirements: List[str], language: str = "python") -> List[Task]:
    """
    Create tasks for the development process.
    
    Args:
        task_description: Description of the development task
        requirements: List of requirements
        language: Programming language to use
        
    Returns:
        List of tasks for the development process
    """
    # Create agents
    architect_agent = ArchitectAgent.create()
    developer_agent = DeveloperAgent.create()
    tester_agent = TesterAgent.create()
    
    # Create tasks
    design_task = Task(
        description=ArchitectAgent.create_design_task(architect_agent, task_description, requirements),
        agent=architect_agent,
        expected_output="A comprehensive software design document including component breakdown, interfaces, data flow, design patterns, and potential challenges."
    )
    
    implementation_task = Task(
        description=DeveloperAgent.create_implementation_task(
            developer_agent, 
            task_description, 
            "{design_output}", 
            language
        ),
        agent=developer_agent,
        expected_output=f"Complete {language} implementation of the software according to the design.",
        context=[design_task]
    )
    
    testing_task = Task(
        description=TesterAgent.create_test_cases_task(
            tester_agent,
            "{implementation_output}",
            language,
            requirements
        ),
        agent=tester_agent,
        expected_output=f"Comprehensive test suite for the {language} implementation with unit tests, edge case tests, and error condition tests.",
        context=[implementation_task]
    )
    
    evaluation_task = Task(
        description=TesterAgent.create_evaluation_task(
            tester_agent,
            "{implementation_output}",
            "{testing_output}"
        ),
        agent=tester_agent,
        expected_output="Detailed evaluation of the code quality, identified issues, suggestions for improvement, and code coverage analysis.",
        context=[implementation_task, testing_task]
    )
    
    # If human feedback is enabled, add a refinement task
    if ENABLE_HUMAN_FEEDBACK:
        refinement_task = Task(
            description=DeveloperAgent.create_refine_task(
                developer_agent,
                "{implementation_output}",
                "{evaluation_output}",
                language
            ),
            agent=developer_agent,
            expected_output=f"Refined {language} implementation addressing the feedback from the evaluation.",
            context=[implementation_task, evaluation_task]
        )
        
        return [design_task, implementation_task, testing_task, evaluation_task, refinement_task]
    
    return [design_task, implementation_task, testing_task, evaluation_task]

def create_development_crew(task_description: str, requirements: List[str], language: str = "python") -> Crew:
    """
    Create a crew for the development process.
    
    Args:
        task_description: Description of the development task
        requirements: List of requirements
        language: Programming language to use
        
    Returns:
        Configured crew for the development process
    """
    tasks = create_development_tasks(task_description, requirements, language)
    
    return Crew(
        agents=[task.agent for task in tasks],
        tasks=tasks,
        verbose=True,
        process=Process.sequential
    )

def run_development_process(task_description: str, requirements: List[str], language: str = "python") -> Dict[str, Any]:
    """
    Run the development process for a given task and requirements.
    
    Args:
        task_description: Description of the development task
        requirements: List of requirements
        language: Programming language to use
        
    Returns:
        Results of the development process
    """
    crew = create_development_crew(task_description, requirements, language)
    result = crew.kickoff()
    
    # Process the result to extract the final outputs
    outputs = {}
    
    # In a real implementation, we would parse the result to extract specific outputs
    # For this example, we'll just return the raw result
    outputs["raw_result"] = result
    
    return outputs

if __name__ == "__main__":
    # Example usage
    task = "Build a Python function to calculate Fibonacci numbers"
    requirements = [
        "Must handle negative numbers",
        "Should be optimized for performance",
        "Should include proper error handling",
        "Should have clear documentation"
    ]
    
    result = run_development_process(task, requirements)
    print(result)