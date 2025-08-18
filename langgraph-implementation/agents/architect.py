"""
Architect Agent for LangGraph Implementation

This agent is responsible for system design and architecture decisions.
It analyzes requirements and creates high-level designs.
"""

import os
from typing import Dict, List, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.chat_models import ChatOllama

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_ARCHITECT", "llama3.1:8b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Define the architect's system prompt
ARCHITECT_SYSTEM_PROMPT = """
You are an expert software architect with deep knowledge of software design patterns, 
system architecture, and best practices. Your role is to:

1. Analyze requirements and create high-level designs
2. Make architectural decisions based on requirements
3. Define interfaces between components
4. Consider scalability, maintainability, and performance
5. Provide clear design documentation

Always think step-by-step and consider trade-offs in your design decisions.
Explain your reasoning clearly and provide diagrams or pseudocode when helpful.
"""

class ArchitectAgent:
    """
    Architect agent responsible for system design and architecture decisions.
    """
    
    def __init__(self):
        """Initialize the architect agent with the appropriate model and prompt."""
        self.model = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=TEMPERATURE
        )
        self.system_prompt = ARCHITECT_SYSTEM_PROMPT
    
    def analyze_requirements(self, requirements: List[str]) -> Dict[str, Any]:
        """
        Analyze the given requirements and extract key architectural considerations.
        
        Args:
            requirements: List of requirement statements
            
        Returns:
            Dictionary containing architectural considerations
        """
        # Format the requirements as a bulleted list
        requirements_text = "\n".join([f"- {req}" for req in requirements])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Analyze the following requirements and extract key architectural considerations:\n\nRequirements:\n{requirements_text}")
        ])
        
        response = self.model.invoke(prompt)
        
        # Process the response to extract structured information
        # This is a simplified implementation
        return {
            "raw_response": response.content,
            "considerations": self._extract_considerations(response.content)
        }
    
    def create_design(self, task: str, requirements: List[str]) -> Dict[str, Any]:
        """
        Create a high-level design based on the task and requirements.
        
        Args:
            task: The main task description
            requirements: List of requirement statements
            
        Returns:
            Dictionary containing the design details
        """
        requirements_text = "\n".join([f"- {req}" for req in requirements])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Create a high-level design for the following task:
            
            Task: {task}
            
            Requirements:
            {requirements_text}
            
            Please provide:
            1. Component breakdown
            2. Interface definitions
            3. Data flow
            4. Key design patterns to use
            5. Potential challenges and solutions
            """)
        ])
        
        response = self.model.invoke(prompt)
        
        # Process the response to extract structured information
        # This is a simplified implementation
        return {
            "raw_response": response.content,
            "design": self._extract_design_components(response.content)
        }
    
    def _extract_considerations(self, text: str) -> List[str]:
        """Extract architectural considerations from text."""
        # This is a simplified implementation
        # In a real implementation, this would use more sophisticated parsing
        lines = text.split("\n")
        considerations = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith("-") or line.startswith("*") or 
                        (len(line) > 2 and line[0].isdigit() and line[1] == ".")):
                considerations.append(line)
        
        return considerations
    
    def _extract_design_components(self, text: str) -> Dict[str, Any]:
        """Extract design components from text."""
        # This is a simplified implementation
        # In a real implementation, this would use more sophisticated parsing
        
        # Simple extraction of sections
        components = []
        interfaces = []
        data_flow = []
        design_patterns = []
        challenges = []
        
        current_section = None
        
        for line in text.split("\n"):
            line = line.strip()
            
            if not line:
                continue
            
            # Check for section headers with more robust patterns
            # Look for markdown headers (##) or section names followed by colons
            if line.startswith("##") or line.startswith("#"):
                # Reset current section
                current_section = None
                
                # Check for specific section headers
                lower_line = line.lower()
                if "component" in lower_line:
                    current_section = "components"
                    continue
                elif "interface" in lower_line:
                    current_section = "interfaces"
                    continue
                elif "data flow" in lower_line:
                    current_section = "data_flow"
                    continue
                elif "design pattern" in lower_line:
                    current_section = "design_patterns"
                    continue
                elif "challenge" in lower_line:
                    current_section = "challenges"
                    continue
            # Also check for section headers without markdown formatting
            elif ":" in line:
                lower_line = line.lower()
                if "component" in lower_line:
                    current_section = "components"
                    continue
                elif "interface" in lower_line:
                    current_section = "interfaces"
                    continue
                elif "data flow" in lower_line:
                    current_section = "data_flow"
                    continue
                elif "design pattern" in lower_line:
                    current_section = "design_patterns"
                    continue
                elif "challenge" in lower_line:
                    current_section = "challenges"
                    continue
            
            # Check if the line is a bullet point or numbered item
            is_list_item = (line.startswith("-") or line.startswith("*") or 
                           (len(line) > 2 and line[0].isdigit() and line[1] == "."))
            
            # Add the line to the appropriate section if it's a list item
            if is_list_item:
                if current_section == "components":
                    components.append(line)
                elif current_section == "interfaces":
                    interfaces.append(line)
                elif current_section == "data_flow":
                    data_flow.append(line)
                elif current_section == "design_patterns":
                    design_patterns.append(line)
                elif current_section == "challenges":
                    challenges.append(line)
        
        return {
            "components": components,
            "interfaces": interfaces,
            "data_flow": data_flow,
            "design_patterns": design_patterns,
            "challenges": challenges
        }