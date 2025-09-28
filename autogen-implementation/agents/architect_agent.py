"""
Architect Agent for AutoGen Implementation

This agent is responsible for system design and architecture decisions.
It analyzes requirements and creates high-level designs.
"""

import os
import logging
from typing import Dict, List, Any

# Try to import AutoGen with fallback
try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    try:
        import pyautogen as autogen
        AUTOGEN_AVAILABLE = True
    except ImportError:
        AUTOGEN_AVAILABLE = False
        logging.warning("AutoGen not available")

logger = logging.getLogger(__name__)

class MockArchitectAgent:
    """Mock architect agent when AutoGen is not available."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mock architect agent."""
        self.config = config
        self.name = "Architect"
        self.system_message = ARCHITECT_SYSTEM_MESSAGE
        
        logger.info("Initialized mock architect agent")
    
    async def generate_reply(self, messages: List[Dict[str, Any]], sender=None, **kwargs) -> Dict[str, Any]:
        """Generate a reply as the architect."""
        if not messages:
            return {
                "content": "I'm ready to help with system architecture and design.",
                "role": "assistant"
            }
        
        last_message = messages[-1] if messages else {}
        content = last_message.get("content", "")
        
        # Mock architect response
        response = f"""
# System Architecture Design

Based on the requirements, I propose the following architecture:

## High-Level Design
- **Modular Architecture**: Clean separation of concerns
- **Layered Structure**: Presentation, Business Logic, Data Access
- **Scalable Design**: Designed for future growth

## Key Components
1. **Core Module**: Main business logic
2. **Data Layer**: Database interactions
3. **API Layer**: External interfaces
4. **Utility Module**: Helper functions

## Technology Stack
- **Language**: Python (as specified)
- **Framework**: FastAPI for APIs
- **Database**: SQLite for development, PostgreSQL for production
- **Testing**: pytest for unit tests

## Design Patterns
- Repository pattern for data access
- Factory pattern for object creation
- Observer pattern for event handling

This architecture provides a solid foundation for the implementation phase.
"""
        
        return {
            "content": response,
            "role": "assistant"
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "name": self.name,
            "type": "architect",
            "features": [
                "system_design",
                "architecture_planning",
                "technology_selection",
                "design_patterns",
                "scalability_analysis"
            ],
            "specializations": ["software_architecture", "system_design", "technical_planning"]
        }

# Load environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_ARCHITECT", "llama3.1:8b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Define the architect's system message
ARCHITECT_SYSTEM_MESSAGE = """
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

def create_architect_agent(config: Dict[str, Any] = None):
    """
    Create an architect agent for the AutoGen implementation.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured architect agent
    """
    if not AUTOGEN_AVAILABLE:
        logger.warning("AutoGen not available, creating mock architect agent")
        return MockArchitectAgent(config or {})
    
    # Default configuration
    default_config = {
        "name": "Architect",
        "llm_config": {
            "config_list": [
                {
                    "model": OLLAMA_MODEL,
                    "api_base": OLLAMA_BASE_URL,
                    "api_type": "ollama",
                    "temperature": TEMPERATURE
                }
            ]
        },
        "system_message": ARCHITECT_SYSTEM_MESSAGE
    }
    
    # Override with provided config
    if config:
        for key, value in config.items():
            if key == "llm_config" and isinstance(value, dict):
                default_config["llm_config"].update(value)
            else:
                default_config[key] = value
    
    # Create the agent
    try:
        return autogen.AssistantAgent(**default_config)
    except Exception as e:
        logger.error(f"Failed to create AutoGen AssistantAgent: {e}")
        return MockArchitectAgent(config or {})

def create_design_prompt(task: str, requirements: List[str]) -> str:
    """
    Create a design prompt for the architect agent.
    
    Args:
        task: The main task description
        requirements: List of requirement statements
        
    Returns:
        Formatted prompt for the architect agent
    """
    requirements_text = "\n".join([f"- {req}" for req in requirements])
    
    return f"""
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
    
    Think step-by-step and consider trade-offs in your design decisions.
    Explain your reasoning clearly and provide diagrams or pseudocode when helpful.
    """

def analyze_requirements_prompt(requirements: List[str]) -> str:
    """
    Create a requirements analysis prompt for the architect agent.
    
    Args:
        requirements: List of requirement statements
        
    Returns:
        Formatted prompt for the architect agent
    """
    requirements_text = "\n".join([f"- {req}" for req in requirements])
    
    return f"""
    Analyze the following requirements and extract key architectural considerations:
    
    Requirements:
    {requirements_text}
    
    Please identify:
    1. Key functional requirements
    2. Non-functional requirements (performance, scalability, etc.)
    3. Technical constraints
    4. Potential architectural approaches
    5. Trade-offs to consider
    
    Think step-by-step and be thorough in your analysis.
    """