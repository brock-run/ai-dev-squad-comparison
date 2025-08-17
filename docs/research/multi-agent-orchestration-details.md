# AI Agent Orchestration Setup Guide: Detailed Implementation with Ollama, GitHub Integration & Configurations

This comprehensive guide provides detailed setup instructions, configuration examples, sample workflows, GitHub integration examples, and Ollama configuration for each major AI agent orchestration framework.

## Prerequisites - Common Setup Requirements

### 1. **Ollama Installation & Configuration**

**Install Ollama** (for all frameworks):
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
winget install Ollama.Ollama
```

**Start Ollama service**:
```bash
ollama serve  # Runs on http://localhost:11434
```

**Download recommended models for development workflows**:
```bash
# For code generation and analysis
ollama pull llama3.1:8b        # Great for general tasks
ollama pull codellama:13b       # Specialized for coding
ollama pull deepseek-coder:6.7b # Optimized for programming
ollama pull mistral:7b          # Good balance of speed/performance

# For faster testing/development
ollama pull llama3.2:3b         # Smaller, faster model
```

### 2. **Python Environment Setup**

```bash
# Create isolated environment
python -m venv ai-agent-env
source ai-agent-env/bin/activate  # Linux/Mac
# ai-agent-env\Scripts\activate   # Windows

# Upgrade pip
pip install --upgrade pip
```

### 3. **GitHub Configuration**

Create a GitHub Personal Access Token:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with these scopes:
   - `repo` (full control of private repositories)
   - `workflow` (update GitHub Action workflows) 
   - `read:org` (read org and team membership)

Save the token as environment variable:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

***

## 1. LangGraph Setup & Configuration

### **Installation**

```bash
pip install langgraph langchain-ollama langchain-community langchain-github
```

### **Basic Configuration with Ollama**

Create `config/langgraph_config.py`:
```python
import os
from langchain_ollama import ChatOllama

# Ollama configuration
def get_ollama_llm(model_name="llama3.1:8b"):
    return ChatOllama(
        model=model_name,
        base_url="http://localhost:11434",
        temperature=0.1,
        num_predict=2048,
        repeat_penalty=1.1,
        top_k=40,
        top_p=0.9,
    )

# GitHub configuration  
GITHUB_CONFIG = {
    "token": os.getenv("GITHUB_TOKEN"),
    "repo_owner": "your-username",
    "repo_name": "your-repo"
}
```

### **Complete Development Squad Implementation**

Create `langgraph_dev_squad.py`:
```python
import os
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.tools.github.tool import GitHubAction
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_ollama import ChatOllama
from langchain_core.tools import tool

# State definition
class DevSquadState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], "The messages in the conversation"]
    requirements: str
    code: str
    tests: str
    documentation: str
    github_pr_url: str
    review_feedback: str

# Initialize LLM
llm = ChatOllama(
    model="deepseek-coder:6.7b",
    base_url="http://localhost:11434",
    temperature=0.1
)

# GitHub tools setup
github = GitHubAPIWrapper(
    github_app_id=None,
    github_app_private_key=None,
    github_token=os.getenv("GITHUB_TOKEN")
)

@tool
def create_github_file(file_path: str, content: str, commit_message: str) -> str:
    """Create a new file in the GitHub repository."""
    try:
        result = github.create_file(
            file_path=file_path,
            file_contents=content,
            commit_message=commit_message
        )
        return f"File created successfully: {result}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

@tool
def create_pull_request(title: str, body: str, head_branch: str, base_branch: str = "main") -> str:
    """Create a pull request."""
    try:
        result = github.create_pull_request(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch
        )
        return f"Pull request created: {result.get('html_url', 'Unknown URL')}"
    except Exception as e:
        return f"Error creating PR: {str(e)}"

# Agent nodes
def requirements_analyst(state: DevSquadState) -> DevSquadState:
    """Analyze requirements and create technical specifications."""
    messages = state["messages"]
    
    prompt = f"""You are a Senior Business Analyst. Analyze these requirements and create detailed technical specifications:

Requirements: {messages[-1].content if messages else 'No requirements provided'}

Provide:
1. Clear functional requirements
2. Technical specifications
3. Acceptance criteria
4. Architecture recommendations

Be specific and actionable."""

    response = llm.invoke(prompt)
    
    return {
        **state,
        "requirements": response.content,
        "messages": messages + [AIMessage(content=response.content)]
    }

def code_developer(state: DevSquadState) -> DevSquadState:
    """Generate code based on requirements."""
    requirements = state.get("requirements", "")
    
    prompt = f"""You are a Senior Full-Stack Developer. Create production-ready code based on these requirements:

Requirements:
{requirements}

Generate:
1. Complete, well-structured code
2. Proper error handling
3. Clear comments and documentation
4. Follow best practices and coding standards

Provide the complete code implementation."""

    response = llm.invoke(prompt)
    
    return {
        **state,
        "code": response.content,
        "messages": state["messages"] + [AIMessage(content=response.content)]
    }

def test_engineer(state: DevSquadState) -> DevSquadState:
    """Create comprehensive tests for the code."""
    code = state.get("code", "")
    requirements = state.get("requirements", "")
    
    prompt = f"""You are a Senior QA Engineer. Create comprehensive tests for this code:

Requirements:
{requirements}

Code:
{code}

Generate:
1. Unit tests
2. Integration tests
3. Edge case tests
4. Performance tests where applicable
5. Clear test documentation

Use appropriate testing frameworks and ensure good coverage."""

    response = llm.invoke(prompt)
    
    return {
        **state,
        "tests": response.content,
        "messages": state["messages"] + [AIMessage(content=response.content)]
    }

def code_reviewer(state: DevSquadState) -> DevSquadState:
    """Review code and provide feedback."""
    code = state.get("code", "")
    tests = state.get("tests", "")
    
    prompt = f"""You are a Senior Code Reviewer. Review this code and tests:

Code:
{code}

Tests:
{tests}

Provide:
1. Code quality assessment
2. Security considerations
3. Performance optimizations
4. Best practices recommendations
5. Specific improvement suggestions

Be constructive and detailed in your feedback."""

    response = llm.invoke(prompt)
    
    return {
        **state,
        "review_feedback": response.content,
        "messages": state["messages"] + [AIMessage(content=response.content)]
    }

def github_integrator(state: DevSquadState) -> DevSquadState:
    """Create GitHub repository files and PR."""
    code = state.get("code", "")
    tests = state.get("tests", "")
    requirements = state.get("requirements", "")
    
    try:
        # Create main code file
        create_github_file(
            file_path="src/main.py",
            content=code,
            commit_message="Add main implementation"
        )
        
        # Create test file
        create_github_file(
            file_path="tests/test_main.py", 
            content=tests,
            commit_message="Add comprehensive tests"
        )
        
        # Create documentation
        create_github_file(
            file_path="README.md",
            content=f"# Project Documentation\n\n## Requirements\n{requirements}\n\n## Code Review Feedback\n{state.get('review_feedback', '')}",
            commit_message="Add project documentation"
        )
        
        # Create pull request
        pr_url = create_pull_request(
            title="AI Generated Development Squad Implementation",
            body=f"## Requirements\n{requirements}\n\n## Review Feedback\n{state.get('review_feedback', '')}",
            head_branch="ai-dev-implementation",
            base_branch="main"
        )
        
        return {
            **state,
            "github_pr_url": pr_url,
            "messages": state["messages"] + [AIMessage(content=f"GitHub integration completed. PR: {pr_url}")]
        }
        
    except Exception as e:
        error_msg = f"GitHub integration failed: {str(e)}"
        return {
            **state,
            "github_pr_url": "",
            "messages": state["messages"] + [AIMessage(content=error_msg)]
        }

# Build the graph
def create_dev_squad_workflow():
    workflow = StateGraph(DevSquadState)
    
    # Add nodes
    workflow.add_node("requirements_analyst", requirements_analyst)
    workflow.add_node("code_developer", code_developer)
    workflow.add_node("test_engineer", test_engineer)
    workflow.add_node("code_reviewer", code_reviewer)
    workflow.add_node("github_integrator", github_integrator)
    
    # Define edges
    workflow.add_edge(START, "requirements_analyst")
    workflow.add_edge("requirements_analyst", "code_developer")
    workflow.add_edge("code_developer", "test_engineer")
    workflow.add_edge("test_engineer", "code_reviewer")
    workflow.add_edge("code_reviewer", "github_integrator")
    workflow.add_edge("github_integrator", END)
    
    return workflow.compile()

# Usage example
if __name__ == "__main__":
    app = create_dev_squad_workflow()
    
    result = app.invoke({
        "messages": [HumanMessage(content="Create a Python REST API for user management with CRUD operations, authentication, and data validation")],
        "requirements": "",
        "code": "",
        "tests": "",
        "documentation": "",
        "github_pr_url": "",
        "review_feedback": ""
    })
    
    print("Development Squad Workflow Completed!")
    print(f"GitHub PR: {result.get('github_pr_url', 'None created')}")
```

### **Docker Configuration for LangGraph**

Create `docker/langgraph.Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "langgraph_dev_squad.py"]
```

***

## 2. CrewAI Setup & Configuration

### **Installation**

```bash
pip install crewai[tools] langchain-ollama
```

### **CrewAI with Ollama Configuration**

Create `config/crewai_config.py`:
```python
import os
from crewai import LLM

# Ollama LLM configuration for different roles
def get_ollama_llm(model="llama3.1:8b"):
    return LLM(
        model=f"ollama/{model}",
        base_url="http://localhost:11434"
    )

# Specialized models for different roles
DEVELOPER_LLM = get_ollama_llm("deepseek-coder:6.7b")
REVIEWER_LLM = get_ollama_llm("llama3.1:8b")
TESTER_LLM = get_ollama_llm("codellama:13b")

# GitHub configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "your-username/your-repo"
```

### **Complete Development Squad with GitHub Integration**

Create `crewai_dev_squad.py`:
```python
import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import GithubSearchTool, FileWriterTool
from langchain_community.tools.github.tool import GitHubAction
from config.crewai_config import DEVELOPER_LLM, REVIEWER_LLM, TESTER_LLM

# Custom GitHub tools
class GitHubIntegrationTool:
    def __init__(self, token, repo):
        self.token = token
        self.repo = repo
    
    def create_issue(self, title, body):
        """Create a GitHub issue"""
        # Implementation for creating GitHub issue
        pass
    
    def create_pull_request(self, title, body, branch):
        """Create a pull request"""
        # Implementation for creating PR
        pass

# Initialize tools
github_tool = GitHubIntegrationTool(
    token=os.getenv("GITHUB_TOKEN"),
    repo="your-username/your-repo"
)

file_writer = FileWriterTool()

# Define Agents
product_manager = Agent(
    role='Senior Product Manager',
    goal='Define clear requirements and manage the development lifecycle',
    backstory="""You are an experienced Product Manager with 10+ years in software development. 
    You excel at breaking down complex requirements into actionable tasks and ensuring 
    all stakeholders are aligned. You have deep technical knowledge and can bridge 
    business requirements with technical implementation.""",
    llm=REVIEWER_LLM,
    verbose=True,
    allow_delegation=True,
    tools=[]
)

senior_developer = Agent(
    role='Senior Full-Stack Developer',
    goal='Write clean, efficient, and maintainable code',
    backstory="""You are a Senior Full-Stack Developer with 15+ years of experience. 
    You specialize in Python, JavaScript, and modern frameworks. You write production-ready 
    code with proper error handling, documentation, and following best practices. 
    You consider scalability, security, and maintainability in every line of code.""",
    llm=DEVELOPER_LLM,
    verbose=True,
    tools=[file_writer],
    allow_delegation=False
)

qa_engineer = Agent(
    role='Senior QA Engineer & Test Architect', 
    goal='Ensure code quality through comprehensive testing strategies',
    backstory="""You are a Senior QA Engineer with expertise in test automation, 
    performance testing, and quality assurance. You create comprehensive test suites 
    covering unit tests, integration tests, and end-to-end tests. You ensure code 
    coverage and identify edge cases that developers might miss.""",
    llm=TESTER_LLM,
    verbose=True,
    tools=[file_writer],
    allow_delegation=False
)

devops_engineer = Agent(
    role='DevOps Engineer & CI/CD Specialist',
    goal='Set up deployment pipelines and ensure code integration',
    backstory="""You are a DevOps Engineer specializing in CI/CD pipelines, 
    containerization, and deployment automation. You ensure smooth integration 
    of code changes and maintain high deployment velocity while ensuring reliability.""",
    llm=REVIEWER_LLM,
    verbose=True,
    tools=[file_writer],
    allow_delegation=False
)

code_reviewer = Agent(
    role='Senior Code Reviewer & Architect',
    goal='Review code quality, architecture, and provide constructive feedback',
    backstory="""You are a Senior Software Architect with deep expertise in code review, 
    system design, and best practices. You ensure code quality, security, performance, 
    and maintainability. You provide detailed, constructive feedback and mentor 
    team members through your reviews.""",
    llm=REVIEWER_LLM,
    verbose=True,
    tools=[],
    allow_delegation=False
)

# Define Tasks
requirements_task = Task(
    description="""Analyze the project requirements: {project_description}
    
    Create detailed specifications including:
    1. Functional requirements breakdown
    2. Technical specifications  
    3. API endpoints and data models
    4. Security considerations
    5. Performance requirements
    6. Acceptance criteria
    7. Timeline estimation
    
    Provide a comprehensive project brief that the development team can follow.""",
    agent=product_manager,
    expected_output="""Detailed project specification document with:
    - Clear functional requirements
    - Technical architecture overview
    - API specifications
    - Database schema design
    - Security requirements
    - Performance benchmarks
    - Detailed acceptance criteria""",
    output_file="requirements.md"
)

development_task = Task(
    description="""Based on the requirements, implement a complete solution:
    
    1. Set up proper project structure
    2. Implement all required functionality
    3. Add comprehensive error handling
    4. Include proper logging
    5. Write clean, documented code
    6. Follow coding best practices
    7. Ensure security best practices
    8. Add configuration management
    
    Create production-ready code that meets all requirements.""",
    agent=senior_developer,
    expected_output="""Complete code implementation including:
    - Main application code with proper structure
    - Configuration files
    - Requirements.txt/package.json
    - Environment setup instructions
    - API documentation
    - Code comments and docstrings""",
    context=[requirements_task],
    output_file="src/main.py"
)

testing_task = Task(
    description="""Create a comprehensive testing strategy and implementation:
    
    1. Unit tests for all functions/methods
    2. Integration tests for API endpoints
    3. End-to-end test scenarios
    4. Performance/load tests
    5. Security tests
    6. Mock external dependencies
    7. Test data fixtures
    8. Coverage reporting setup
    
    Ensure minimum 80% code coverage and all critical paths tested.""",
    agent=qa_engineer,
    expected_output="""Complete testing suite with:
    - Unit test files
    - Integration test scenarios
    - Test fixtures and mocks
    - Test configuration
    - Coverage reporting setup
    - Performance test scripts
    - Test documentation""",
    context=[development_task],
    output_file="tests/test_suite.py"
)

deployment_task = Task(
    description="""Set up deployment and CI/CD pipeline:
    
    1. Create Dockerfile for containerization
    2. Set up GitHub Actions workflow
    3. Configure environment variables
    4. Add health check endpoints
    5. Set up monitoring and logging
    6. Create deployment scripts
    7. Add database migration scripts
    8. Configure staging/production environments
    
    Ensure smooth deployment and rollback capabilities.""",
    agent=devops_engineer,
    expected_output="""Complete deployment setup:
    - Dockerfile and docker-compose.yml
    - GitHub Actions workflow files
    - Environment configuration templates
    - Deployment scripts
    - Monitoring configuration
    - Health check implementations""",
    context=[development_task, testing_task],
    output_file=".github/workflows/deploy.yml"
)

review_task = Task(
    description="""Conduct comprehensive code review:
    
    Review all code, tests, and configurations for:
    1. Code quality and best practices
    2. Security vulnerabilities
    3. Performance optimizations
    4. Architecture decisions
    5. Test coverage and quality
    6. Documentation completeness
    7. Deployment readiness
    
    Provide detailed feedback and recommendations.""",
    agent=code_reviewer,
    expected_output="""Comprehensive code review report:
    - Code quality assessment
    - Security analysis
    - Performance recommendations
    - Architecture review
    - Testing strategy evaluation
    - Documentation review
    - Deployment readiness checklist
    - Action items and recommendations""",
    context=[development_task, testing_task, deployment_task],
    output_file="code_review.md"
)

github_integration_task = Task(
    description="""Integrate all deliverables with GitHub:
    
    1. Create repository structure
    2. Commit all code and documentation
    3. Set up branch protection rules
    4. Create pull request templates
    5. Add issue templates
    6. Set up project boards
    7. Create comprehensive README
    8. Add contributing guidelines
    
    Ensure the repository is ready for collaborative development.""",
    agent=devops_engineer,
    expected_output="""Complete GitHub repository setup:
    - All code committed to appropriate branches
    - Pull request created with detailed description
    - Issue templates configured
    - Project board set up with tasks
    - Comprehensive README file
    - Contributing guidelines""",
    context=[requirements_task, development_task, testing_task, review_task],
    output_file="README.md"
)

# Create the Crew
dev_crew = Crew(
    agents=[
        product_manager,
        senior_developer, 
        qa_engineer,
        devops_engineer,
        code_reviewer
    ],
    tasks=[
        requirements_task,
        development_task,
        testing_task,
        deployment_task,
        review_task,
        github_integration_task
    ],
    process=Process.sequential,
    verbose=2,
    memory=True,
    embedder={
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            "base_url": "http://localhost:11434",
        }
    }
)

# Usage
if __name__ == "__main__":
    print("🚀 Starting AI Development Squad...")
    
    result = dev_crew.kickoff(inputs={
        "project_description": """
        Create a Python REST API for a task management system with the following features:
        - User authentication and authorization (JWT)
        - CRUD operations for tasks and projects
        - Task assignment and collaboration features
        - Email notifications for task updates
        - RESTful API with proper status codes
        - Input validation and error handling
        - PostgreSQL database integration
        - Docker containerization
        - Comprehensive test suite
        - API documentation with Swagger
        """
    })
    
    print("\n✅ Development Squad completed!")
    print(f"📋 Final output: {result}")
```

### **CrewAI Configuration Files**

Create `.env` for CrewAI:
```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# GitHub Configuration  
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=your-username/your-repo

# CrewAI Configuration
CREWAI_VERBOSE=True
CREWAI_MEMORY=True
```

***

## 3. AutoGen Setup & Configuration

### **Installation**

```bash
pip install pyautogen[ollama] langchain-github
```

### **AutoGen with Ollama Configuration**

Create `config/autogen_config.py`:
```python
import os

# Ollama configuration for AutoGen
OLLAMA_CONFIG = {
    "config_list": [
        {
            "model": "llama3.1:8b",
            "api_type": "ollama",
            "client_host": "http://localhost:11434",
            "stream": False,
            "native_tool_calls": False,
        },
        {
            "model": "deepseek-coder:6.7b",
            "api_type": "ollama", 
            "client_host": "http://localhost:11434",
            "stream": False,
            "native_tool_calls": False,
        },
        {
            "model": "codellama:13b",
            "api_type": "ollama",
            "client_host": "http://localhost:11434", 
            "stream": False,
            "native_tool_calls": False,
        }
    ],
    "temperature": 0.1,
    "timeout": 300,
}

# GitHub configuration
GITHUB_CONFIG = {
    "token": os.getenv("GITHUB_TOKEN"),
    "repo": "your-username/your-repo"
}
```

### **Complete AutoGen Development Squad**

Create `autogen_dev_squad.py`:
```python
import os
import autogen
from typing import Dict, List
from langchain_community.utilities.github import GitHubAPIWrapper
from config.autogen_config import OLLAMA_CONFIG, GITHUB_CONFIG

# Initialize GitHub wrapper
github = GitHubAPIWrapper(github_token=GITHUB_CONFIG["token"])

class GitHubManager:
    def __init__(self, token: str, repo: str):
        self.github = GitHubAPIWrapper(github_token=token)
        self.repo = repo
    
    def create_file(self, path: str, content: str, message: str):
        """Create a file in the repository"""
        try:
            return self.github.create_file(path, content, message)
        except Exception as e:
            return f"Error creating file: {str(e)}"
    
    def create_pull_request(self, title: str, body: str, head: str, base: str = "main"):
        """Create a pull request"""
        try:
            return self.github.create_pull_request(title, body, head, base)
        except Exception as e:
            return f"Error creating PR: {str(e)}"

# Initialize GitHub manager
gh_manager = GitHubManager(GITHUB_CONFIG["token"], GITHUB_CONFIG["repo"])

# Define specialized agents
project_manager = autogen.AssistantAgent(
    name="ProjectManager",
    system_message="""You are an experienced Project Manager and Business Analyst. 
    Your responsibilities include:
    - Analyzing requirements and creating detailed specifications
    - Breaking down complex projects into manageable tasks
    - Coordinating between team members
    - Ensuring all requirements are met
    - Managing timelines and deliverables
    
    Always ask clarifying questions if requirements are unclear.
    Provide detailed, actionable specifications.""",
    llm_config=OLLAMA_CONFIG
)

senior_developer = autogen.AssistantAgent(
    name="SeniorDeveloper", 
    system_message="""You are a Senior Full-Stack Developer with 15+ years of experience.
    Your expertise includes:
    - Writing clean, efficient, production-ready code
    - Following best practices and design patterns
    - Implementing proper error handling and logging
    - Creating scalable and maintainable solutions
    - Security best practices
    - Performance optimization
    
    Always include comprehensive documentation and comments in your code.
    Consider edge cases and error scenarios.""",
    llm_config={
        **OLLAMA_CONFIG,
        "config_list": [{"model": "deepseek-coder:6.7b", "api_type": "ollama", "client_host": "http://localhost:11434"}]
    }
)

qa_engineer = autogen.AssistantAgent(
    name="QAEngineer",
    system_message="""You are a Senior QA Engineer and Test Architect.
    Your responsibilities include:
    - Creating comprehensive test strategies
    - Writing unit, integration, and end-to-end tests
    - Ensuring high code coverage (80%+)
    - Performance and security testing
    - Test automation and CI/CD integration
    
    Focus on testing edge cases and potential failure scenarios.
    Create maintainable and reliable test suites.""",
    llm_config={
        **OLLAMA_CONFIG,
        "config_list": [{"model": "codellama:13b", "api_type": "ollama", "client_host": "http://localhost:11434"}]
    }
)

devops_engineer = autogen.AssistantAgent(
    name="DevOpsEngineer",
    system_message="""You are a DevOps Engineer specializing in CI/CD and deployment.
    Your expertise includes:
    - Docker containerization
    - GitHub Actions workflows
    - Infrastructure as Code
    - Monitoring and logging setup
    - Security and compliance
    - Deployment automation
    
    Focus on creating robust, scalable deployment pipelines.
    Ensure proper environment configuration and secrets management.""",
    llm_config=OLLAMA_CONFIG
)

code_reviewer = autogen.AssistantAgent(
    name="CodeReviewer",
    system_message="""You are a Senior Software Architect and Code Reviewer.
    Your responsibilities include:
    - Reviewing code for quality, security, and performance
    - Ensuring architectural consistency
    - Identifying potential issues and improvements
    - Mentoring team members through detailed feedback
    - Ensuring adherence to coding standards
    
    Provide constructive, detailed feedback with specific examples.
    Focus on maintainability, scalability, and security.""",
    llm_config=OLLAMA_CONFIG
)

# User proxy with enhanced code execution
user_proxy = autogen.UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=15,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "autogen_workspace",
        "use_docker": False,
        "last_n_messages": 3,
    },
    system_message="""You are a User Proxy representing the client.
    You coordinate the development team and ensure deliverables meet requirements.
    When all tasks are completed successfully, reply TERMINATE."""
)

# Create group chat for team coordination
def create_dev_team():
    groupchat = autogen.GroupChat(
        agents=[
            user_proxy,
            project_manager, 
            senior_developer,
            qa_engineer,
            devops_engineer,
            code_reviewer
        ],
        messages=[],
        max_round=50,
        speaker_selection_method="round_robin"
    )
    
    manager = autogen.GroupChatManager(
        groupchat=groupchat, 
        llm_config=OLLAMA_CONFIG
    )
    
    return manager

# Enhanced workflow function
def run_development_workflow(project_description: str):
    """Run the complete development workflow"""
    
    manager = create_dev_team()
    
    workflow_prompt = f"""
    🚀 DEVELOPMENT PROJECT KICKOFF
    
    Project Description: {project_description}
    
    WORKFLOW PHASES:
    
    1. REQUIREMENTS ANALYSIS (ProjectManager)
       - Analyze requirements and create detailed specifications
       - Define acceptance criteria and technical requirements
       - Create project timeline and milestone breakdown
    
    2. CODE DEVELOPMENT (SeniorDeveloper) 
       - Implement the solution following best practices
       - Include comprehensive error handling and logging
       - Add proper documentation and comments
       - Create modular, maintainable code structure
    
    3. TESTING STRATEGY (QAEngineer)
       - Design comprehensive test strategy
       - Implement unit, integration, and e2e tests
       - Set up test automation and coverage reporting
       - Create performance and security tests
    
    4. DEPLOYMENT SETUP (DevOpsEngineer)
       - Create Docker configuration
       - Set up GitHub Actions CI/CD pipeline  
       - Configure environment management
       - Add monitoring and health checks
    
    5. CODE REVIEW (CodeReviewer)
       - Review all code for quality and security
       - Provide detailed feedback and recommendations
       - Ensure architectural consistency
       - Verify deployment readiness
    
    6. GITHUB INTEGRATION (UserProxy)
       - Create repository structure
       - Commit all code and documentation
       - Set up pull request with detailed description
       - Configure issue and PR templates
    
    Each team member should complete their phase and hand off to the next team member.
    When all phases are complete, say TERMINATE.
    
    Let's begin with requirements analysis!
    """
    
    # Start the conversation
    chat_result = user_proxy.initiate_chat(
        manager,
        message=workflow_prompt
    )
    
    return chat_result

# GitHub integration functions
def integrate_with_github(files_to_create: Dict[str, str], pr_details: Dict[str, str]):
    """Integrate deliverables with GitHub"""
    
    print("🔗 Starting GitHub integration...")
    
    created_files = []
    
    # Create files in repository
    for file_path, content in files_to_create.items():
        print(f"📝 Creating {file_path}...")
        result = gh_manager.create_file(
            file_path, 
            content, 
            f"Add {file_path} - AI Generated"
        )
        created_files.append((file_path, result))
    
    # Create pull request
    if pr_details:
        print("🔄 Creating pull request...")
        pr_result = gh_manager.create_pull_request(
            title=pr_details.get("title", "AI Generated Development Squad Implementation"),
            body=pr_details.get("body", "Implementation created by AI Development Squad"),
            head=pr_details.get("head", "ai-dev-squad"),
            base=pr_details.get("base", "main")
        )
        print(f"✅ Pull request created: {pr_result}")
    
    return created_files

# Usage example
if __name__ == "__main__":
    print("🤖 Starting AutoGen Development Squad...")
    
    project_description = """
    Create a Python REST API for a comprehensive task management system with:
    
    CORE FEATURES:
    - User registration, authentication, and authorization (JWT)
    - CRUD operations for tasks, projects, and teams
    - Task assignment, prioritization, and status tracking
    - Real-time notifications and email alerts
    - File attachments and comments on tasks
    - Time tracking and reporting
    - Dashboard with analytics and metrics
    
    TECHNICAL REQUIREMENTS:
    - RESTful API with proper HTTP status codes
    - Input validation and comprehensive error handling
    - PostgreSQL database with proper indexing
    - Redis for caching and session management
    - Celery for background tasks
    - Docker containerization
    - Comprehensive test suite (80%+ coverage)
    - API documentation with Swagger/OpenAPI
    - GitHub Actions CI/CD pipeline
    - Environment-based configuration
    - Logging and monitoring setup
    
    QUALITY REQUIREMENTS:
    - Production-ready code with proper error handling
    - Security best practices (SQL injection prevention, XSS protection)
    - Performance optimization and caching
    - Scalable architecture
    - Comprehensive documentation
    """
    
    # Run the development workflow
    result = run_development_workflow(project_description)
    
    print("\n✅ Development workflow completed!")
    print("📊 Summary:")
    print(f"   - Total messages exchanged: {len(result.chat_history)}")
    print("   - All phases completed successfully")
    
    # Example of GitHub integration
    sample_files = {
        "src/main.py": "# Main application code will be generated here",
        "tests/test_main.py": "# Test suite will be generated here", 
        "Dockerfile": "# Docker configuration will be generated here",
        ".github/workflows/ci.yml": "# CI/CD pipeline will be generated here",
        "README.md": "# Project documentation will be generated here"
    }
    
    pr_details = {
        "title": "AI Generated Task Management API",
        "body": "Complete implementation of task management API created by AI Development Squad",
        "head": "ai-dev-squad-implementation"
    }
    
    # Uncomment to actually create GitHub files
    # integrate_with_github(sample_files, pr_details)
```

### **AutoGen Docker Configuration**

Create `docker/autogen.Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy configuration and source
COPY config/ ./config/
COPY autogen_dev_squad.py .

# Create workspace directory
RUN mkdir -p autogen_workspace

CMD ["python", "autogen_dev_squad.py"]
```

***

## 4. n8n Setup & Configuration

### **Installation Options**

**Option 1: npm installation**
```bash
npm install n8n -g
n8n start
```

**Option 2: Docker setup (recommended)**
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n
    container_name: n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_EDITOR_BASE_URL=http://localhost:5678
      - WEBHOOK_URL=http://localhost:5678
      - NODE_FUNCTION_ALLOW_EXTERNAL=*
    volumes:
      - n8n_/home/node/.n8n
    networks:
      - ai-network

  ollama:
    image: ollama/ollama
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_/root/.ollama
    networks:
      - ai-network

  postgres:
    image: postgres:15
    container_name: postgres
    environment:
      - POSTGRES_DB=n8n_dev_squad
      - POSTGRES_USER=n8n_user
      - POSTGRES_PASSWORD=n8n_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_/var/lib/postgresql/data
    networks:
      - ai-network

networks:
  ai-network:

volumes:
  n8n_
  ollama_
  postgres_
```

### **Start the stack**
```bash
docker-compose up -d

# Pull required models
docker exec -it ollama ollama pull llama3.1:8b
docker exec -it ollama ollama pull deepseek-coder:6.7b
docker exec -it ollama ollama pull codellama:13b
```

### **n8n Workflow Configuration**

Create the development squad workflow by importing this JSON configuration into n8n:

```json
{
  "name": "AI Development Squad Workflow",
  "nodes": [
    {
      "parameters": {
        "options": {}
      },
      "id": "webhook-trigger",
      "name": "Development Request Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300],
      "webhookId": "dev-squad-webhook"
    },
    {
      "parameters": {
        "agent": {
          "systemMessage": "You are a Senior Product Manager. Analyze requirements and create detailed technical specifications with acceptance criteria, timeline, and architecture recommendations.",
          "tools": []
        },
        "model": {
          "resource": "llama3.1:8b",
          "credentials": "ollama"
        }
      },
      "id": "requirements-analyst-agent",
      "name": "Requirements Analyst Agent",
      "type": "n8n-nodes-base.aiAgent",
      "typeVersion": 1,
      "position": [460, 300]
    },
    {
      "parameters": {
        "agent": {
          "systemMessage": "You are a Senior Full-Stack Developer. Create production-ready code with proper error handling, documentation, and best practices. Focus on clean, maintainable, and scalable solutions.",
          "tools": [
            {
              "name": "codeWriter",
              "description": "Write code files",
              "parameters": {
                "type": "object",
                "properties": {
                  "filename": {"type": "string"},
                  "content": {"type": "string"}
                }
              }
            }
          ]
        },
        "model": {
          "resource": "deepseek-coder:6.7b", 
          "credentials": "ollama"
        }
      },
      "id": "senior-developer-agent",
      "name": "Senior Developer Agent", 
      "type": "n8n-nodes-base.aiAgent",
      "typeVersion": 1,
      "position": [680, 300]
    },
    {
      "parameters": {
        "agent": {
          "systemMessage": "You are a Senior QA Engineer. Create comprehensive test suites including unit tests, integration tests, and end-to-end tests. Ensure 80%+ code coverage and test edge cases.",
          "tools": [
            {
              "name": "testWriter",
              "description": "Write test files",
              "parameters": {
                "type": "object", 
                "properties": {
                  "testFile": {"type": "string"},
                  "testContent": {"type": "string"}
                }
              }
            }
          ]
        },
        "model": {
          "resource": "codellama:13b",
          "credentials": "ollama"
        }
      },
      "id": "qa-engineer-agent",
      "name": "QA Engineer Agent",
      "type": "n8n-nodes-base.aiAgent", 
      "typeVersion": 1,
      "position": [900, 300]
    },
    {
      "parameters": {
        "agent": {
          "systemMessage": "You are a Senior Code Reviewer and Software Architect. Review code for quality, security, performance, and architectural consistency. Provide detailed, constructive feedback.",
          "tools": []
        },
        "model": {
          "resource": "llama3.1:8b",
          "credentials": "ollama"
        }
      },
      "id": "code-reviewer-agent", 
      "name": "Code Reviewer Agent",
      "type": "n8n-nodes-base.aiAgent",
      "typeVersion": 1,
      "position": [1120, 300]
    },
    {
      "parameters": {
        "resource": "file",
        "operation": "write",
        "fileName": "={{ $json.filename }}",
        "data": "={{ $json.content }}",
        "options": {}
      },
      "id": "write-code-file",
      "name": "Write Code File",
      "type": "n8n-nodes-base.filesys",
      "typeVersion": 1,
      "position": [680, 480]
    },
    {
      "parameters": {
        "resource": "file", 
        "operation": "write",
        "fileName": "={{ $json.testFile }}",
        "data": "={{ $json.testContent }}",
        "options": {}
      },
      "id": "write-test-file",
      "name": "Write Test File", 
      "type": "n8n-nodes-base.filesys",
      "typeVersion": 1,
      "position": [900, 480]
    },
    {
      "parameters": {
        "resource": "repository",
        "operation": "createFile",
        "owner": "your-username",
        "repository": "your-repo",
        "filePath": "={{ $json.filepath }}",
        "fileContent": "={{ $json.content }}",
        "commitMessage": "={{ $json.message }}"
      },
      "id": "create-github-file",
      "name": "Create GitHub File",
      "type": "n8n-nodes-base.github",
      "typeVersion": 1,
      "position": [1340, 300],
      "credentials": "github"
    },
    {
      "parameters": {
        "resource": "pullRequest",
        "operation": "create", 
        "owner": "your-username",
        "repository": "your-repo",
        "title": "AI Development Squad Implementation",
        "body": "={{ $json.prDescription }}",
        "head": "ai-dev-squad",
        "base": "main"
      },
      "id": "create-pull-request",
      "name": "Create Pull Request",
      "type": "n8n-nodes-base.github", 
      "typeVersion": 1,
      "position": [1560, 300],
      "credentials": "github"
    },
    {
      "parameters": {
        "jsCode": "// Aggregate all outputs and prepare GitHub integration\nconst requirements = $input.first().json.requirements;\nconst code = $input.item(1).json.code;\nconst tests = $input.item(2).json.tests; \nconst review = $input.item(3).json.review;\n\nconst files = [\n  {\n    filepath: 'src/main.py',\n    content: code,\n    message: 'Add main application code'\n  },\n  {\n    filepath: 'tests/test_main.py', \n    content: tests,\n    message: 'Add comprehensive test suite'\n  },\n  {\n    filepath: 'requirements.md',\n    content: requirements,\n    message: 'Add project requirements'\n  },\n  {\n    filepath: 'code_review.md',\n    content: review,\n    message: 'Add code review feedback'\n  }\n];\n\nconst prDescription = `# AI Development Squad Implementation\\n\\n## Requirements\\n${requirements}\\n\\n## Code Review\\n${review}`;\n\nreturn files.map(file => ({...file, prDescription}));"
      },
      "id": "aggregate-outputs",
      "name": "Aggregate Outputs",
      "type": "n8n-nodes-base.code",
      "typeVersion": 1,
      "position": [1340, 180]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "INSERT INTO project_history (project_name, requirements, code, tests, review, github_pr) VALUES ($1, $2, $3, $4, $5, $6)",
        "additionalFields": {
          "parameters": ["={{ $json.projectName }}", "={{ $json.requirements }}", "={{ $json.code }}", "={{ $json.tests }}", "={{ $json.review }}", "={{ $json.prUrl }}"]
        }
      },
      "id": "save-to-database", 
      "name": "Save to Database",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 1,
      "position": [1780, 300],
      "credentials": "postgres"
    }
  ],
  "connections": {
    "Development Request Webhook": {
      "main": [
        [
          {
            "node": "Requirements Analyst Agent",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Requirements Analyst Agent": {
      "main": [
        [
          {
            "node": "Senior Developer Agent",
            "type": "main", 
            "index": 0
          }
        ]
      ]
    },
    "Senior Developer Agent": {
      "main": [
        [
          {
            "node": "QA Engineer Agent",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "QA Engineer Agent": {
      "main": [
        [
          {
            "node": "Code Reviewer Agent",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Code Reviewer Agent": {
      "main": [
        [
          {
            "node": "Aggregate Outputs", 
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Aggregate Outputs": {
      "main": [
        [
          {
            "node": "Create GitHub File",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Create GitHub File": {
      "main": [
        [
          {
            "node": "Create Pull Request",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Create Pull Request": {
      "main": [
        [
          {
            "node": "Save to Database",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### **n8n Credentials Setup**

1. **Ollama Credential:**
   - Go to Settings → Credentials → Add credential
   - Select "Ollama" 
   - Base URL: `http://ollama:11434` (if using Docker network) or `http://localhost:11434`
   - Test connection

2. **GitHub Credential:**
   - Add credential → GitHub
   - Access Token: Your GitHub token
   - Test connection

3. **PostgreSQL Credential:**
   - Add credential → PostgreSQL
   - Host: `postgres` (Docker) or `localhost`
   - Database: `n8n_dev_squad`
   - User: `n8n_user`
   - Password: `n8n_password`

### **PostgreSQL Database Setup**

Connect to PostgreSQL and create the required table:
```sql
-- Create projects table to store workflow results
CREATE TABLE project_history (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    requirements TEXT,
    code TEXT,
    tests TEXT,
    review TEXT,
    github_pr VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX idx_project_name ON project_history(project_name);
CREATE INDEX idx_created_at ON project_history(created_at);
```

***

## 5. Testing the Implementations

### **Test Data for All Frameworks**

Create `test_data.json`:
```json
{
  "project_description": "Create a Python REST API for a blog management system with user authentication, CRUD operations for posts and comments, file upload functionality, search capabilities, and email notifications. Include comprehensive tests, Docker containerization, and GitHub Actions CI/CD pipeline.",
  "requirements": {
    "functional": [
      "User registration and authentication (JWT)",
      "CRUD operations for blog posts and comments",
      "File upload for images and documents", 
      "Full-text search functionality",
      "Email notifications for comments",
      "User roles and permissions"
    ],
    "technical": [
      "Python Flask/FastAPI framework",
      "PostgreSQL database",
      "Redis for caching",
      "Celery for background tasks",
      "Docker containerization",
      "Comprehensive test suite (80%+ coverage)",
      "GitHub Actions CI/CD",
      "API documentation with Swagger"
    ]
  }
}
```

### **Testing Scripts**

Create `test_frameworks.py`:
```python
import json
import time
import subprocess
from pathlib import Path

def test_langgraph():
    """Test LangGraph implementation"""
    print("🔍 Testing LangGraph...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["python", "langgraph_dev_squad.py"],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        duration = time.time() - start_time
        
        print(f"✅ LangGraph completed in {duration:.2f}s")
        print(f"📊 Exit code: {result.returncode}")
        
        if result.stdout:
            print("📝 Output preview:")
            print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            
    except subprocess.TimeoutExpired:
        print("⏰ LangGraph test timed out")
    except Exception as e:
        print(f"❌ LangGraph test failed: {str(e)}")

def test_crewai():
    """Test CrewAI implementation"""
    print("🔍 Testing CrewAI...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["python", "crewai_dev_squad.py"],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        duration = time.time() - start_time
        
        print(f"✅ CrewAI completed in {duration:.2f}s")
        print(f"📊 Exit code: {result.returncode}")
        
        # Check for output files
        output_files = [
            "requirements.md",
            "src/main.py", 
            "tests/test_suite.py",
            "code_review.md"
        ]
        
        for file_path in output_files:
            if Path(file_path).exists():
                print(f"✅ Created: {file_path}")
            else:
                print(f"❌ Missing: {file_path}")
                
    except subprocess.TimeoutExpired:
        print("⏰ CrewAI test timed out")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")

def test_autogen():
    """Test AutoGen implementation"""
    print("🔍 Testing AutoGen...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["python", "autogen_dev_squad.py"],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        duration = time.time() - start_time
        
        print(f"✅ AutoGen completed in {duration:.2f}s")
        print(f"📊 Exit code: {result.returncode}")
        
        # Check autogen workspace
        workspace_dir = Path("autogen_workspace")
        if workspace_dir.exists():
            files = list(workspace_dir.glob("*"))
            print(f"📁 Workspace files: {len(files)}")
            for file in files[:5]:  # Show first 5 files
                print(f"   - {file.name}")
                
    except subprocess.TimeoutExpired:
        print("⏰ AutoGen test timed out")
    except Exception as e:
        print(f"❌ AutoGen test failed: {str(e)}")

def test_n8n():
    """Test n8n implementation"""
    print("🔍 Testing n8n...")
    
    try:
        # Check if n8n is running
        result = subprocess.run(
            ["curl", "-f", "http://localhost:5678/healthz"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ n8n is running and accessible")
            
            # Test webhook endpoint
            webhook_result = subprocess.run([
                "curl", "-X", "POST", 
                "http://localhost:5678/webhook/dev-squad-webhook",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "project_description": "Create a simple task management API",
                    "requirements": ["User auth", "CRUD operations", "PostgreSQL"]
                })
            ], capture_output=True, text=True)
            
            if webhook_result.returncode == 0:
                print("✅ n8n webhook responded successfully")
            else:
                print("❌ n8n webhook failed")
                
        else:
            print("❌ n8n is not accessible")
            print("💡 Start n8n with: docker-compose up -d")
            
    except Exception as e:
        print(f"❌ n8n test failed: {str(e)}")

def run_all_tests():
    """Run tests for all frameworks"""
    print("🚀 Starting comprehensive framework testing...\n")
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    # Check Ollama
    try:
        result = subprocess.run(["curl", "-f", "http://localhost:11434"], 
                              capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ Ollama is running")
        else:
            print("❌ Ollama is not accessible - start with: ollama serve")
            return
    except:
        print("❌ Ollama connection failed")
        return
    
    print()
    
    # Run framework tests
    test_langgraph()
    print()
    test_crewai() 
    print()
    test_autogen()
    print()
    test_n8n()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    run_all_tests()
```

***

## 6. Performance Optimization & Best Practices

### **Resource Management**

Create `utils/resource_monitor.py`:
```python
import psutil
import time
from typing import Dict, List

class ResourceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.start_memory = psutil.virtual_memory().used
        self.start_cpu = psutil.cpu_percent()
    
    def get_current_usage(self) -> Dict[str, float]:
        """Get current system resource usage"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_gb": psutil.virtual_memory().used / (1024**3),
            "memory_percent": psutil.virtual_memory().percent,
            "elapsed_time": time.time() - self.start_time
        }
    
    def log_usage(self, framework_name: str):
        """Log resource usage for a framework"""
        usage = self.get_current_usage()
        print(f"📊 {framework_name} Resource Usage:")
        print(f"   CPU: {usage['cpu_percent']:.1f}%")
        print(f"   Memory: {usage['memory_gb']:.2f}GB ({usage['memory_percent']:.1f}%)")
        print(f"   Runtime: {usage['elapsed_time']:.2f}s")
```

### **Model Optimization Configuration**

Create `config/model_optimization.py`:
```python
# Optimized model configurations for different use cases
DEVELOPMENT_MODELS = {
    "fast": {
        "model": "llama3.2:3b",
        "temperature": 0.1,
        "max_tokens": 1024,
        "timeout": 30
    },
    "balanced": {
        "model": "llama3.1:8b", 
        "temperature": 0.1,
        "max_tokens": 2048,
        "timeout": 60
    },
    "quality": {
        "model": "deepseek-coder:6.7b",
        "temperature": 0.05,
        "max_tokens": 4096,
        "timeout": 120
    }
}

# Framework-specific optimizations
FRAMEWORK_CONFIGS = {
    "langgraph": {
        "concurrent_agents": 3,
        "memory_limit": "2GB",
        "checkpoint_frequency": 5
    },
    "crewai": {
        "process": "sequential",  # vs hierarchical
        "memory": True,
        "embedder_model": "nomic-embed-text:latest"
    },
    "autogen": {
        "max_consecutive_auto_reply": 10,
        "code_execution_timeout": 60,
        "use_docker": False  # Set to True for production
    },
    "n8n": {
        "execution_timeout": 300,
        "max_nodes": 50,
        "memory_limit": "1GB"
    }
}
```

***

## 7. Repository Structure & Deployment

### **Complete Repository Structure**

```
ai-dev-squad-comparison/
├── README.md
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── 
├── config/
│   ├── __init__.py
│   ├── langgraph_config.py
│   ├── crewai_config.py
│   ├── autogen_config.py
│   ├── n8n_config.json
│   └── model_optimization.py
│
├── langgraph-implementation/
│   ├── requirements.txt
│   ├── langgraph_dev_squad.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── requirements_analyst.py
│   │   ├── senior_developer.py
│   │   ├── qa_engineer.py
│   │   └── code_reviewer.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── github_tools.py
│   │   └── file_tools.py
│   └── workflows/
│       ├── __init__.py
│       └── dev_squad_workflow.py
│
├── crewai-implementation/
│   ├── requirements.txt
│   ├── crewai_dev_squad.py
│   ├── agents.yaml
│   ├── tasks.yaml
│   ├── crews/
│   │   ├── __init__.py
│   │   └── development_crew.py
│   └── tools/
│       ├── __init__.py
│       ├── github_integration.py
│       └── code_tools.py
│
├── autogen-implementation/
│   ├── requirements.txt
│   ├── autogen_dev_squad.py
│   ├── config/
│   │   └── autogen_config.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── project_manager.py
│   │   ├── senior_developer.py
│   │   ├── qa_engineer.py
│   │   └── devops_engineer.py
│   └── workflows/
│       ├── __init__.py
│       └── group_chat_workflow.py
│
├── n8n-implementation/
│   ├── workflows/
│   │   ├── dev-squad-workflow.json
│   │   ├── github-integration-workflow.json
│   │   └── testing-workflow.json
│   ├── docker-compose.yml
│   ├── credentials/
│   │   ├── ollama-credential.json
│   │   ├── github-credential.json
│   │   └── postgres-credential.json
│   └── database/
│       ├── schema.sql
│       └── seed_data.sql
│
├── utils/
│   ├── __init__.py
│   ├── resource_monitor.py
│   ├── performance_tester.py
│   └── github_helper.py
│
├── tests/
│   ├── __init__.py
│   ├── test_frameworks.py
│   ├── test_langgraph.py
│   ├── test_crewai.py
│   ├── test_autogen.py
│   └── test_n8n.py
│
├── scripts/
│   ├── setup.sh
│   ├── start_all.sh
│   ├── stop_all.sh
│   └── test_all.sh
│
├── docs/
│   ├── setup-guide.md
│   ├── configuration-guide.md
│   ├── troubleshooting.md
│   └── performance-comparison.md
│
└── comparison-results/
    ├── performance-metrics.md
    ├── ease-of-use-analysis.md
    ├── feature-comparison.md
    └── cost-analysis.md
```

### **Setup Scripts**

Create `scripts/setup.sh`:
```bash
#!/bin/bash

echo "🚀 Setting up AI Development Squad Comparison Repository..."

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    exit 1
fi

# Check Node.js (for n8n)
if ! command -v node &> /dev/null; then
    echo "⚠️ Node.js not found - required for n8n npm installation"
fi

echo "✅ Prerequisites check completed"

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv ai-agent-env
source ai-agent-env/bin/activate

# Install requirements for each framework
echo "📦 Installing framework dependencies..."

# LangGraph
pip install -r langgraph-implementation/requirements.txt

# CrewAI  
pip install -r crewai-implementation/requirements.txt

# AutoGen
pip install -r autogen-implementation/requirements.txt

echo "✅ Python dependencies installed"

# Set up Ollama
echo "🤖 Setting up Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &

# Wait for Ollama to start
sleep 5

# Pull required models
echo "📥 Downloading AI models..."
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b  
ollama pull codellama:13b
ollama pull llama3.2:3b  # Faster model for testing

echo "✅ Ollama models downloaded"

# Set up Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 30

# Set up n8n models in Ollama container
echo "🔧 Configuring n8n Ollama models..."
docker exec ollama ollama pull llama3.1:8b
docker exec ollama ollama pull deepseek-coder:6.7b

# Initialize PostgreSQL database
echo "🗄️ Setting up database..."
docker exec postgres psql -U n8n_user -d n8n_dev_squad -f /docker-entrypoint-initdb.d/schema.sql

echo "✅ Database initialized"

# Create .env file from template
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "⚠️ Please update .env with your GitHub token and other credentials"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env with your GitHub token"
echo "2. Run 'source ai-agent-env/bin/activate' to activate Python environment"
echo "3. Access n8n at http://localhost:5678"
echo "4. Run 'python tests/test_frameworks.py' to test all implementations"
echo ""
echo "🔗 Service URLs:"
echo "   n8n: http://localhost:5678"
echo "   Ollama: http://localhost:11434"
echo "   PostgreSQL: localhost:5432"
echo ""
```

### **Environment Configuration**

Create `.env.example`:
```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=your-username/your-repo

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODELS=llama3.1:8b,deepseek-coder:6.7b,codellama:13b

# Database Configuration
POSTGRES_DB=n8n_dev_squad
POSTGRES_USER=n8n_user  
POSTGRES_PASSWORD=n8n_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# n8n Configuration
N8N_HOST=localhost
N8N_PORT=5678
N8N_EDITOR_BASE_URL=http://localhost:5678

# Framework Configuration
LANGGRAPH_VERBOSE=true
CREWAI_VERBOSE=true
AUTOGEN_VERBOSE=true

# Performance Settings
MAX_CONCURRENT_AGENTS=3
EXECUTION_TIMEOUT=600
MEMORY_LIMIT=4GB
```

Sources
[1] Llama 3.1 Agent using LangGraph and Ollama - Pinecone https://www.pinecone.io/learn/langgraph-ollama-llama/
[2] Run models locally - ️   LangChain https://python.langchain.com/docs/how_to/local_llms/
[3] Open Source Observability for LangGraph - Langfuse https://langfuse.com/docs/integrations/langchain/example-python-langgraph
[4] Ollama - ️   LangChain https://python.langchain.com/docs/integrations/providers/ollama/
[5] Build a RAG application with LangChain and Local LLMs powered ... https://devblogs.microsoft.com/cosmosdb/build-a-rag-application-with-langchain-and-local-llms-powered-by-ollama/
[6] langchain-ai/langgraph-example - GitHub https://github.com/langchain-ai/langgraph-example
[7] Local LangGraph Agents with Llama 3.1 + Ollama - YouTube https://www.youtube.com/watch?v=5a-NuqTaC20
[8] A tutorial on building local agent using LangGraph, LLaMA3 ... - Elastic https://www.elastic.co/search-labs/blog/local-rag-agent-elasticsearch-langgraph-llama3
[9] von-development/awesome-LangGraph - GitHub https://github.com/von-development/awesome-LangGraph
[10] OllamaLLM - ️   LangChain https://python.langchain.com/docs/integrations/llms/ollama/
[11] Start with a prebuilt agent - GitHub Pages https://langchain-ai.github.io/langgraph/agents/agents/
[12] langchain-ai/langgraph: Build resilient language agents as graphs. https://github.com/langchain-ai/langgraph
[13] A Guide to LangGraph, AI Agents, and Ollama | DigitalOcean https://www.digitalocean.com/community/tutorials/local-ai-agents-with-langgraph-and-ollama
[14] Self-RAG using local LLMs - GitHub Pages https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag_local/
[15] Examples - GitHub Pages https://langchain-ai.github.io/langgraph/examples/
[16] Coding Local AI Agent in Python (Ollama + LangGraph) - YouTube https://www.youtube.com/watch?v=9mLzD997JsU
[17] langgraph with local llm #187 - GitHub https://github.com/langchain-ai/langgraph/discussions/187
[18] Use the Graph API - GitHub Pages https://langchain-ai.github.io/langgraph/how-tos/graph-api/
[19] How to Build a Local AI Agent With Python (Ollama ... - YouTube https://www.youtube.com/watch?v=E4l91XKQSgw
[20] Is it possible to connect to a local LLM in LangGraph Studio ... - Reddit https://www.reddit.com/r/LangChain/comments/1htz3lq/is_it_possible_to_connect_to_a_local_llm_in/
[21] Getting Started with Ollama and CrewAI - DEV Community https://dev.to/rajeev_3ce9f280cbae73b234/getting-started-with-ollama-and-crewai-16pk
[22] GitHub Integration - CrewAI Docs https://docs.crewai.com/enterprise/integrations/github
[23] Local LLMs tools calling - CrewAI Community Support https://community.crewai.com/t/local-llms-tools-calling/5004
[24] LLMs - CrewAI Docs https://docs.crewai.com/concepts/llms
[25] Building a Github repo summarizer with CrewAI - Wandb https://wandb.ai/byyoung3/crewai_git_documenter/reports/Building-a-Github-repo-summarizer-with-CrewAI--VmlldzoxMjY5Mzc5Ng
[26] Crew ai, Local LLM connection issue - Stack Overflow https://stackoverflow.com/questions/78424761/crew-ai-local-llm-connection-issue
[27] 100% LOCAL AI Agents with CrewAI and Ollama - YouTube https://www.youtube.com/watch?v=d-eJr2aS_BQ
[28] Integrations - CrewAI Docs https://docs.crewai.com/en/enterprise/features/integrations
[29] Can't get a working LLM with CrewAI — need simple setup ... - Reddit https://www.reddit.com/r/crewai/comments/1lhrjio/cant_get_a_working_llm_with_crewai_need_simple/
[30] FREE Local LLM - AI Agents With CrewAI And Ollama Easy Tutorial https://www.youtube.com/watch?v=XkS4ifkLwwQ
[31] 10 Best CrewAI Projects You Must Build in 2025 - ProjectPro https://www.projectpro.io/article/crew-ai-projects-ideas-and-examples/1117
[32] Help ::: How to use a custom (local) LLM with vLLM - LLMs - CrewAI https://community.crewai.com/t/help-how-to-use-a-custom-local-llm-with-vllm/5746
[33] The Complete Guide to Building Your Free Local AI Assistant with ... https://www.reddit.com/r/ollama/comments/1jbkbai/the_complete_guide_to_building_your_free_local_ai/
[34] crewAIInc/crewAI-examples - GitHub https://github.com/crewAIInc/crewAI-examples
[35] Connect to any LLM - CrewAI Docs https://docs.crewai.com/en/learn/llm-connections
[36] Connecting Ollama with crewai - Crews https://community.crewai.com/t/connecting-ollama-with-crewai/2222
[37] crewAIInc/crewAI - GitHub https://github.com/crewAIInc/crewAI
[38] Building crewAI agents with locally run ollama llm https://community.crewai.com/t/building-crewai-agents-with-locally-run-ollama-llm/3763
[39] Creating Free, Local AI Agents with OpenRouter, Ollama, and CrewAI https://spr.com/free-local-ai-agents-with-openrouter-ollama-and-crewai/
[40] kenhuangus/crewAI-Examples - GitHub https://github.com/kenhuangus/crewAI-Examples
[41] Ollama | AutoGen 0.2 - Microsoft Open Source https://microsoft.github.io/autogen/0.2/docs/topics/non-openai-models/local-ollama
[42] LLM Configuration | AutoGen 0.2 - Microsoft Open Source https://microsoft.github.io/autogen/0.2/docs/topics/llm_configuration/
[43] Linear Github Integration: Create Issues from Code Commits using ... https://composio.dev/blog/linear-github-integration
[44] Local LLMs with LiteLLM & Ollama — AutoGen https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/cookbook/local-llms-ollama-litellm.html
[45] Use AutoGen for Local LLMs - Microsoft Open Source https://microsoft.github.io/autogen/0.2/blog/2023/07/14/Local-LLMs/
[46] Observability for AutoGen with Langfuse Integration https://langfuse.com/docs/integrations/autogen
[47] AutoGen + Ollama: Using OllamaChatCompletionClient https://www.gettingstarted.ai/run-autogen-agents-with-ollama-locally/
[48] How to Use ANY Local Open-Source LLM with AutoGen ... - YouTube https://www.youtube.com/watch?v=OJFvBQQI9ME
[49] Getting Started | AutoGen 0.2 - Microsoft Open Source https://microsoft.github.io/autogen/0.2/docs/Getting-Started
[50] AutoGen + Ollama Instructions - GitHub Gist https://gist.github.com/mberman84/ea207e7d9e5f8c5f6a3252883ef16df3
[51] Are there any guides to using a local llm with Autogen or Chatdev? https://www.reddit.com/r/LocalLLaMA/comments/17811ai/are_there_any_guides_to_using_a_local_llm_with/
[52] I built a Github PR Agent with Autogen and 4 other frameworks, Here ... https://www.reddit.com/r/AutoGenAI/comments/1ds56y2/i_built_a_github_pr_agent_with_autogen_and_4/
[53] AutoGen + Ollama + Gemma: How to Create LLM Agents Locally https://www.youtube.com/watch?v=bkBOuBxsxeM
[54] How To Use AutoGen STUDIO with ANY Open-Source LLM Tutorial https://www.youtube.com/watch?v=IjqAMWUI0r8
[55] AutoGen Studio - Microsoft Open Source https://microsoft.github.io/autogen/dev/user-guide/autogenstudio-user-guide/index.html
[56] Autogen: Ollama integration Step by Step Tutorial. Mind-blowing! https://www.youtube.com/watch?v=UQw04VW60U0
[57] Sample repo using AutoGen with a local LLM - GitHub https://github.com/trezero/autogen-local-llm
[58] AutoGen https://microsoft.github.io/autogen/stable/index.html
[59] AutoGen + Ollama Instructions - GitHub Gist https://gist.github.com/hustshawn/8638ebbb0f7eec8d75b046f036c069c1
[60] AutoGen with Local LLM setup - Build and execute code - LinkedIn https://www.linkedin.com/pulse/autogen-local-llm-setup-build-execute-code-soumen-mondal-lvmtf
[61] How to Run a Local LLM: Complete Guide to Setup & Best Models ... https://blog.n8n.io/local-llm/
[62] GitHub and YouTube: Automate Workflows with n8n https://n8n.io/integrations/github/and/youtube/
[63] How to Correctly Integrate Ollama and Local Large Language ... https://aleksandarhaber.com/how-to-correctly-integrate-ollama-and-local-large-language-models-with-the-n8n-ai-agent-software-and-run-local-ai-agents/
[64] How do you integrate n8n with Ollama for local LLM workflows? https://www.hostinger.com/tutorials/n8n-ollama-integration
[65] GitHub integrations | Workflow automation with n8n https://n8n.io/integrations/github/
[66] How to Build a Local AI Agent With n8n (NO CODE!) - YouTube https://www.youtube.com/watch?v=qqjzohCle48
[67] Integration of n8n Agents with Local Ollama LLMs - Tutorial - YouTube https://www.youtube.com/watch?v=X6rR7nJulLA
[68] Top 2567 AI automation workflows - N8N https://n8n.io/workflows/categories/ai/
[69] N8n with self hosted llm - Reddit https://www.reddit.com/r/n8n/comments/1iocyh6/n8n_with_self_hosted_llm/
[70] The Ultimate Guide to Running n8n with Ollama LLM Locally Using ... https://dev.to/apuchakraborty/the-ultimate-guide-to-running-n8n-with-ollama-llm-locally-using-docker-m5f
[71] Never pay again for N8N workflows automation... All Free - YouTube https://www.youtube.com/watch?v=FsG2_ScIYBA
[72] AI Agent with Local LLM - Questions - n8n Community https://community.n8n.io/t/ai-agent-with-local-llm/90810
[73] I created a complete, production-ready guide for running local LLMs ... https://www.reddit.com/r/n8n/comments/1m44pwj/i_created_a_complete_productionready_guide_for/
[74] enescingoz/awesome-n8n-templates - GitHub https://github.com/enescingoz/awesome-n8n-templates
[75] How to connect custom LLM to the AI agent module - n8n Community https://community.n8n.io/t/how-to-connect-custom-llm-to-the-ai-agent-module/52274
[76] THE ULTIMATE LOCAL AI SETUP IS HERE: n8n, Ollama & Qdrant https://www.youtube.com/watch?v=7qrruzYC0b4&vl=en-US
[77] Github Trigger integrations | Workflow automation with n8n https://n8n.io/integrations/github-trigger/
[78] Connecting self-hosted LLM to AI Agent : r/n8n - Reddit https://www.reddit.com/r/n8n/comments/1idlalt/connecting_selfhosted_llm_to_ai_agent/
[79] Create 100% Local No Code AI Agents with N8N and Ollama in 10 ... https://www.youtube.com/watch?v=y9m3i12qkms
[80] n8n - Workflow Automation - GitHub https://github.com/n8n-io
