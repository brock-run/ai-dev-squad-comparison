"""
Tester Agent for LangGraph Implementation

This agent is responsible for testing code implementations.
It creates test cases, validates functionality, and ensures code quality.
"""

import os
from typing import Dict, List, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.chat_models import ChatOllama

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_TESTER", "llama3.1:8b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Define the tester's system prompt
TESTER_SYSTEM_PROMPT = """
You are an expert software tester with deep knowledge of testing methodologies, 
test design, and quality assurance. Your role is to:

1. Create comprehensive test cases for code implementations
2. Identify edge cases and potential bugs
3. Validate that code meets requirements and specifications
4. Provide detailed feedback on code quality and test results
5. Suggest improvements based on test findings

Always think step-by-step and consider different testing approaches (unit tests, 
integration tests, edge case testing, etc.).
Explain your testing strategy and provide clear test cases with expected outputs.
"""

class TesterAgent:
    """
    Tester agent responsible for testing code implementations.
    """
    
    def __init__(self):
        """Initialize the tester agent with the appropriate model and prompt."""
        self.model = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=TEMPERATURE
        )
        self.system_prompt = TESTER_SYSTEM_PROMPT
    
    def create_test_plan(self, task: str, requirements: List[str]) -> Dict[str, Any]:
        """
        Create a test plan based on the task and requirements.
        
        Args:
            task: The main task description
            requirements: List of requirement statements
            
        Returns:
            Dictionary containing the test plan details
        """
        requirements_text = "\n".join([f"- {req}" for req in requirements])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Create a comprehensive test plan for the following task:
            
            Task: {task}
            
            Requirements:
            {requirements_text}
            
            Please provide:
            1. Test strategy overview
            2. Unit test cases
            3. Integration test cases
            4. Edge cases to test
            5. Performance considerations
            """)
        ])
        
        response = self.model.invoke(prompt)
        
        # Process the response to extract structured information
        return {
            "raw_response": response.content,
            "test_plan": self._extract_test_plan(response.content)
        }
    
    def create_test_cases(self, code: str, language: str, requirements: List[str]) -> Dict[str, Any]:
        """
        Create test cases for the given code.
        
        Args:
            code: The code to test
            language: The programming language
            requirements: List of requirement statements
            
        Returns:
            Dictionary containing the test cases
        """
        requirements_text = "\n".join([f"- {req}" for req in requirements])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Create test cases for the following {language} code:
            
            ```{language}
            {code}
            ```
            
            Requirements:
            {requirements_text}
            
            Please provide:
            1. Unit tests that cover all functionality
            2. Tests for edge cases
            3. Tests for error conditions
            4. Any necessary test setup and teardown
            
            Write the tests in {language} using an appropriate testing framework.
            """)
        ])
        
        response = self.model.invoke(prompt)
        
        # Process the response to extract structured information
        return {
            "raw_response": response.content,
            "test_code": self._extract_code(response.content, language)
        }
    
    def evaluate_code(self, code: str, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate code based on test results.
        
        Args:
            code: The code being tested
            test_results: Results of running tests
            
        Returns:
            Dictionary containing evaluation and feedback
        """
        # Format test results for the prompt
        test_results_text = "\n".join([f"- {test}: {result}" for test, result in test_results.items()])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Evaluate the following code based on test results:
            
            Code:
            ```
            {code}
            ```
            
            Test Results:
            {test_results_text}
            
            Please provide:
            1. Overall assessment of code quality
            2. Identified issues or bugs
            3. Suggestions for improvement
            4. Code coverage analysis
            """)
        ])
        
        response = self.model.invoke(prompt)
        
        # Process the response to extract structured information
        return {
            "raw_response": response.content,
            "evaluation": self._extract_evaluation(response.content)
        }
    
    def _extract_test_plan(self, text: str) -> Dict[str, List[str]]:
        """Extract test plan components from text."""
        # This is a simplified implementation
        # In a real implementation, this would use more sophisticated parsing
        
        # Simple extraction of sections
        strategy = []
        unit_tests = []
        integration_tests = []
        edge_cases = []
        performance = []
        
        current_section = None
        
        for line in text.split("\n"):
            line = line.strip()
            
            if not line:
                continue
                
            # Check for markdown headers (## Section) or regular headers (Section:)
            if ("test strategy" in line.lower() or "strategy" in line.lower()) and (line.startswith("#") or ":" in line):
                current_section = "strategy"
                continue
            elif "unit test" in line.lower() and (line.startswith("#") or ":" in line):
                current_section = "unit_tests"
                continue
            elif "integration test" in line.lower() and (line.startswith("#") or ":" in line):
                current_section = "integration_tests"
                continue
            elif "edge case" in line.lower() and (line.startswith("#") or ":" in line):
                current_section = "edge_cases"
                continue
            elif "performance" in line.lower() and (line.startswith("#") or ":" in line):
                current_section = "performance"
                continue
            
            if current_section == "strategy" and (line.startswith("-") or line.startswith("*") or 
                                               (len(line) > 2 and line[0].isdigit() and line[1] == ".")):
                strategy.append(line)
            elif current_section == "unit_tests" and (line.startswith("-") or line.startswith("*") or 
                                                   (len(line) > 2 and line[0].isdigit() and line[1] == ".")):
                unit_tests.append(line)
            elif current_section == "integration_tests" and (line.startswith("-") or line.startswith("*") or 
                                                          (len(line) > 2 and line[0].isdigit() and line[1] == ".")):
                integration_tests.append(line)
            elif current_section == "edge_cases" and (line.startswith("-") or line.startswith("*") or 
                                                   (len(line) > 2 and line[0].isdigit() and line[1] == ".")):
                edge_cases.append(line)
            elif current_section == "performance" and (line.startswith("-") or line.startswith("*") or 
                                                    (len(line) > 2 and line[0].isdigit() and line[1] == ".")):
                performance.append(line)
        
        return {
            "strategy": strategy,
            "unit_tests": unit_tests,
            "integration_tests": integration_tests,
            "edge_cases": edge_cases,
            "performance": performance
        }
    
    def _extract_code(self, text: str, language: str) -> str:
        """Extract code blocks from text."""
        # Look for code blocks with language-specific markers
        code_blocks = []
        in_code_block = False
        current_block = []
        
        for line in text.split("\n"):
            if line.strip().startswith(f"```{language}") or line.strip() == "```" and not in_code_block:
                in_code_block = True
                continue
            elif line.strip() == "```" and in_code_block:
                in_code_block = False
                code_blocks.append("\n".join(current_block))
                current_block = []
                continue
            
            if in_code_block:
                current_block.append(line)
        
        # If we found code blocks, return them joined together
        if code_blocks:
            return "\n\n".join(code_blocks)
        
        # If no code blocks with markers were found, return the entire text
        return text
    
    def _extract_evaluation(self, text: str) -> Dict[str, List[str]]:
        """Extract evaluation components from text."""
        # This is a simplified implementation
        # In a real implementation, this would use more sophisticated parsing
        
        # Simple extraction of sections
        assessment = []
        issues = []
        suggestions = []
        coverage = []
        
        current_section = None
        
        for line in text.split("\n"):
            line = line.strip()
            
            if not line:
                continue
                
            # Check for markdown headers (## Section) or regular headers (Section:)
            if ("assessment" in line.lower() or "overall" in line.lower()) and (line.startswith("#") or ":" in line):
                current_section = "assessment"
                continue
            elif ("issue" in line.lower() or "bug" in line.lower()) and (line.startswith("#") or ":" in line):
                current_section = "issues"
                continue
            elif ("suggestion" in line.lower() or "improvement" in line.lower()) and (line.startswith("#") or ":" in line):
                current_section = "suggestions"
                continue
            elif "coverage" in line.lower() and (line.startswith("#") or ":" in line):
                current_section = "coverage"
                continue
            
            if current_section == "assessment" and line:
                assessment.append(line)
            elif current_section == "issues" and (line.startswith("-") or line.startswith("*") or 
                                               (len(line) > 2 and line[0].isdigit() and line[1] == ".")):
                issues.append(line)
            elif current_section == "suggestions" and (line.startswith("-") or line.startswith("*") or 
                                                    (len(line) > 2 and line[0].isdigit() and line[1] == ".")):
                suggestions.append(line)
            elif current_section == "coverage" and line:
                coverage.append(line)
        
        return {
            "assessment": assessment,
            "issues": issues,
            "suggestions": suggestions,
            "coverage": coverage
        }