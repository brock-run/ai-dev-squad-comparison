"""
Tests for the development process module.

This module contains tests for the development process workflow,
including task creation, crew setup, and workflow execution.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to allow importing from the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import mock classes
from tests.mocks.mock_crewai import Agent, Task, Crew, Process
from tests.mocks.mock_langchain import BaseTool

# Patch the crewai and langchain modules with our mocks
sys.modules['crewai'] = MagicMock()
sys.modules['crewai'].Agent = Agent
sys.modules['crewai'].Task = Task
sys.modules['crewai'].Crew = Crew
sys.modules['crewai'].Process = Process
sys.modules['langchain.tools'] = MagicMock()
sys.modules['langchain.tools'].BaseTool = BaseTool

# Now import the development_process module
from workflows.development_process import (
    create_development_tasks,
    create_development_crew,
    run_development_process
)


class TestDevelopmentProcess:
    """Tests for the development process workflow."""
    
    def test_create_development_tasks(self):
        """Test creating development tasks."""
        task_description = "Build a Python function to calculate Fibonacci numbers"
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        language = "python"
        
        # Patch the agent creation methods to return mock agents
        with patch('workflows.development_process.ArchitectAgent.create') as mock_architect_create, \
             patch('workflows.development_process.DeveloperAgent.create') as mock_developer_create, \
             patch('workflows.development_process.TesterAgent.create') as mock_tester_create:
            
            # Configure the mocks to return specific agents
            mock_architect = MagicMock()
            mock_architect.role = "Software Architect"
            mock_architect_create.return_value = mock_architect
            
            mock_developer = MagicMock()
            mock_developer.role = "Software Developer"
            mock_developer_create.return_value = mock_developer
            
            mock_tester = MagicMock()
            mock_tester.role = "Software Tester"
            mock_tester_create.return_value = mock_tester
            
            # Call the function under test
            tasks = create_development_tasks(task_description, requirements, language)
            
            # Verify the results
            assert len(tasks) >= 4  # At least 4 tasks (design, implement, test, evaluate)
            assert all(isinstance(task, Task) for task in tasks)
            
            # Check that the tasks are assigned to the correct agents
            assert tasks[0].agent.role == "Software Architect"
            assert tasks[1].agent.role == "Software Developer"
            assert tasks[2].agent.role == "Software Tester"
            assert tasks[3].agent.role == "Software Tester"
            
            # Check that the task descriptions contain the expected content
            assert task_description in tasks[0].description
            assert "design" in tasks[0].description.lower()
            assert "implement" in tasks[1].description.lower()
            assert "test" in tasks[2].description.lower()
            assert "evaluate" in tasks[3].description.lower()
            
            # Check that the tasks have the expected context relationships
            assert tasks[1].context == [tasks[0]]  # Implementation depends on design
            assert tasks[2].context == [tasks[1]]  # Testing depends on implementation
            assert tasks[3].context == [tasks[1], tasks[2]]  # Evaluation depends on implementation and testing
    
    def test_create_development_crew(self):
        """Test creating a development crew."""
        task_description = "Build a Python function to calculate Fibonacci numbers"
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        language = "python"
        
        # Patch the create_development_tasks function to return mock tasks
        with patch('workflows.development_process.create_development_tasks') as mock_create_tasks:
            # Configure the mock to return specific tasks
            mock_agent1 = MagicMock()
            mock_agent2 = MagicMock()
            mock_agent3 = MagicMock()
            
            mock_task1 = MagicMock()
            mock_task1.agent = mock_agent1
            mock_task2 = MagicMock()
            mock_task2.agent = mock_agent2
            mock_task3 = MagicMock()
            mock_task3.agent = mock_agent3
            
            mock_create_tasks.return_value = [mock_task1, mock_task2, mock_task3]
            
            # Call the function under test
            crew = create_development_crew(task_description, requirements, language)
            
            # Verify the results
            assert isinstance(crew, Crew)
            assert len(crew.agents) == 3
            assert crew.agents == [mock_agent1, mock_agent2, mock_agent3]
            assert crew.tasks == [mock_task1, mock_task2, mock_task3]
            assert crew.verbose is True
            assert crew.process == Process.sequential
    
    def test_run_development_process(self):
        """Test running the development process."""
        task_description = "Build a Python function to calculate Fibonacci numbers"
        requirements = [
            "Must handle negative numbers",
            "Should be optimized for performance",
            "Should include proper error handling",
            "Should have clear documentation"
        ]
        language = "python"
        
        # Patch the create_development_crew function to return a mock crew
        with patch('workflows.development_process.create_development_crew') as mock_create_crew:
            # Configure the mock to return a specific crew
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = {
                "task_1": "Design document",
                "task_2": "Implementation code",
                "task_3": "Test cases",
                "task_4": "Evaluation report"
            }
            mock_create_crew.return_value = mock_crew
            
            # Call the function under test
            result = run_development_process(task_description, requirements, language)
            
            # Verify the results
            assert isinstance(result, dict)
            assert "raw_result" in result
            assert result["raw_result"] == {
                "task_1": "Design document",
                "task_2": "Implementation code",
                "task_3": "Test cases",
                "task_4": "Evaluation report"
            }
            
            # Verify that the crew was created and kickoff was called
            mock_create_crew.assert_called_once_with(task_description, requirements, language)
            mock_crew.kickoff.assert_called_once()