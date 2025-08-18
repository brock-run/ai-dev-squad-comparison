"""
Mock implementations of langchain classes for testing.

This module provides mock implementations of the langchain classes used in the code,
allowing tests to run without depending on the actual langchain implementation.
"""

from typing import Dict, List, Any, Optional, Callable


class SystemMessage:
    """Mock implementation of langchain.schema.SystemMessage."""
    
    def __init__(self, content: str):
        """Initialize a mock SystemMessage."""
        self.content = content


class HumanMessage:
    """Mock implementation of langchain.schema.HumanMessage."""
    
    def __init__(self, content: str):
        """Initialize a mock HumanMessage."""
        self.content = content


class AIMessage:
    """Mock implementation of langchain.schema.AIMessage."""
    
    def __init__(self, content: str):
        """Initialize a mock AIMessage."""
        self.content = content


class ChatPromptTemplate:
    """Mock implementation of langchain.prompts.ChatPromptTemplate."""
    
    @classmethod
    def from_messages(cls, messages: List[Any]):
        """Create a ChatPromptTemplate from a list of messages."""
        instance = cls()
        instance.messages = messages
        return instance


class ChatOllama:
    """Mock implementation of langchain_community.chat_models.ChatOllama."""
    
    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434", temperature: float = 0.7):
        """Initialize a mock ChatOllama."""
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        
    def invoke(self, prompt: Any) -> AIMessage:
        """Mock implementation of invoke method."""
        # For testing, we'll return a simple response based on the prompt
        if isinstance(prompt, ChatPromptTemplate):
            # Extract the content from the last message
            last_message = prompt.messages[-1]
            content = last_message.content
        else:
            content = str(prompt)
            
        # Generate a mock response based on the content
        # Check for specific phrases to determine the appropriate response
        if "create a high-level design" in content.lower() or "component breakdown" in content.lower():
            # This is for the ArchitectAgent.create_design method
            return AIMessage(content="""
            # Design
            
            ## Components
            - Component 1
            - Component 2
            
            ## Interfaces
            - Interface 1
            - Interface 2
            
            ## Data Flow
            - Data flows from Component 1 to Component 2
            
            ## Design Patterns
            - Factory Pattern
            - Observer Pattern
            
            ## Challenges
            - Challenge 1
            - Challenge 2
            """)
        elif "create test cases" in content.lower():
            # This is for the TesterAgent.create_test_cases method
            return AIMessage(content="""
            Here are the test cases:
            
            ```python
            import unittest
            
            class TestFibonacci(unittest.TestCase):
                def test_positive_numbers(self):
                    self.assertEqual(fibonacci(0), 0)
                    self.assertEqual(fibonacci(1), 1)
                    self.assertEqual(fibonacci(5), 5)
                    self.assertEqual(fibonacci(10), 55)
                
                def test_negative_numbers(self):
                    with self.assertRaises(ValueError):
                        fibonacci(-1)
            ```
            """)
        elif "implement" in content.lower() or "code" in content.lower():
            # This is for the DeveloperAgent.implement_code method
            return AIMessage(content="""
            Here's the implementation:
            
            ```python
            def fibonacci(n):
                \"\"\"
                Calculate the nth Fibonacci number.
                
                Args:
                    n: The position in the Fibonacci sequence
                    
                Returns:
                    The nth Fibonacci number
                \"\"\"
                if n < 0:
                    raise ValueError("Input must be a non-negative integer")
                if n <= 1:
                    return n
                    
                a, b = 0, 1
                for _ in range(2, n + 1):
                    a, b = b, a + b
                return b
            ```
            """)
        elif "design" in content.lower():
            return AIMessage(content="""
            # Design
            
            ## Components
            - Component 1
            - Component 2
            
            ## Interfaces
            - Interface 1
            - Interface 2
            
            ## Data Flow
            - Data flows from Component 1 to Component 2
            
            ## Design Patterns
            - Factory Pattern
            - Observer Pattern
            
            ## Challenges
            - Challenge 1
            - Challenge 2
            """)
        elif "test" in content.lower():
            return AIMessage(content="""
            Here are the test cases:
            
            ```python
            import unittest
            
            class TestFibonacci(unittest.TestCase):
                def test_positive_numbers(self):
                    self.assertEqual(fibonacci(0), 0)
                    self.assertEqual(fibonacci(1), 1)
                    self.assertEqual(fibonacci(5), 5)
                    self.assertEqual(fibonacci(10), 55)
                
                def test_negative_numbers(self):
                    with self.assertRaises(ValueError):
                        fibonacci(-1)
            ```
            """)
        elif "evaluate" in content.lower():
            return AIMessage(content="""
            # Code Evaluation
            
            ## Assessment
            The code is well-implemented and passes all tests.
            
            ## Issues
            - No issues found
            
            ## Suggestions
            - Add type hints
            - Consider memoization for better performance
            
            ## Coverage
            The test coverage is 100%.
            """)
        elif "analyze" in content.lower():
            return AIMessage(content="""
            # Architectural Considerations
            
            Based on the requirements, here are the key architectural considerations:
            
            ## Functional Requirements
            - Must handle negative numbers
            - Should include proper error handling
            - Should have clear documentation
            
            ## Non-functional Requirements
            - Should be optimized for performance
            
            ## Technical Constraints
            - None specified
            
            ## Potential Approaches
            - Iterative approach for better performance
            - Recursive approach for clarity
            - Memoization for optimization
            
            ## Trade-offs
            - Performance vs. readability
            - Simplicity vs. robustness
            """)
        else:
            return AIMessage(content="I don't have a specific response for this prompt.")