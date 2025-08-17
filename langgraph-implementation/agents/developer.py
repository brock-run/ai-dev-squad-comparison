"""
Developer Agent for LangGraph Implementation

This agent is responsible for implementing code based on architectural designs.
It writes code, handles implementation details, and follows best practices.
"""

import os
from typing import Dict, List, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.chat_models import ChatOllama

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_DEVELOPER", "codellama:13b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Define the developer's system prompt
DEVELOPER_SYSTEM_PROMPT = """
You are an expert software developer with deep knowledge of programming languages, 
algorithms, data structures, and best practices. Your role is to:

1. Implement code based on architectural designs and requirements
2. Write clean, efficient, and maintainable code
3. Follow language-specific best practices and conventions
4. Handle edge cases and error conditions
5. Document your code thoroughly

Always think step-by-step and consider performance, readability, and maintainability.
Explain your implementation decisions and include comments in your code.
"""

class DeveloperAgent:
    """
    Developer agent responsible for implementing code based on designs.
    """
    
    def __init__(self):
        """Initialize the developer agent with the appropriate model and prompt."""
        self.model = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=TEMPERATURE
        )
        self.system_prompt = DEVELOPER_SYSTEM_PROMPT
    
    def implement_code(self, task: str, design: Dict[str, Any], language: str = "python") -> Dict[str, Any]:
        """
        Implement code based on the task and design.
        
        Args:
            task: The main task description
            design: The design dictionary from the architect
            language: The programming language to use
            
        Returns:
            Dictionary containing the implementation details
        """
        # Format the design information for the prompt
        components = "\n".join([f"- {comp}" for comp in design.get("components", [])])
        interfaces = "\n".join([f"- {intf}" for intf in design.get("interfaces", [])])
        design_patterns = "\n".join([f"- {pattern}" for pattern in design.get("design_patterns", [])])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Implement code for the following task:
            
            Task: {task}
            
            Design Information:
            
            Components:
            {components}
            
            Interfaces:
            {interfaces}
            
            Design Patterns:
            {design_patterns}
            
            Please implement this in {language}. Provide:
            1. Complete implementation with all necessary functions and classes
            2. Proper error handling
            3. Comments and documentation
            4. Any necessary imports
            """)
        ])
        
        response = self.model.invoke(prompt)
        
        # Process the response to extract structured information
        return {
            "raw_response": response.content,
            "code": self._extract_code(response.content, language)
        }
    
    def refine_code(self, code: str, feedback: str, language: str = "python") -> Dict[str, Any]:
        """
        Refine code based on feedback.
        
        Args:
            code: The original code
            feedback: Feedback to address
            language: The programming language
            
        Returns:
            Dictionary containing the refined implementation
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Refine the following {language} code based on the feedback:
            
            Original Code:
            ```{language}
            {code}
            ```
            
            Feedback:
            {feedback}
            
            Please provide the improved code with all necessary changes.
            Explain your changes and reasoning.
            """)
        ])
        
        response = self.model.invoke(prompt)
        
        # Process the response to extract structured information
        return {
            "raw_response": response.content,
            "refined_code": self._extract_code(response.content, language)
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
        
        # If no code blocks with markers were found, try to extract code heuristically
        # This is a simplified approach and might not work for all cases
        lines = text.split("\n")
        code_lines = []
        in_code_section = False
        
        for line in lines:
            # Heuristics to identify code sections without markers
            if (line.strip().startswith("def ") or 
                line.strip().startswith("class ") or 
                line.strip().startswith("import ") or 
                line.strip().startswith("from ") or
                "=" in line and not line.strip().startswith("#")):
                in_code_section = True
            
            if in_code_section:
                code_lines.append(line)
        
        if code_lines:
            return "\n".join(code_lines)
        
        # If all else fails, return the entire text
        return text