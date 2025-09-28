# LangGraph Implementation - Installation and Testing Guide

This guide provides step-by-step instructions for installing all dependencies and running comprehensive tests to validate the LangGraph implementation.

## 🎯 Overview

This installation process will:
1. **Install all dependencies** (LangGraph, safety systems, VCS integration)
2. **Set up the environment** (API keys, Docker, configuration)
3. **Run comprehensive tests** (unit tests, integration tests, full workflow)
4. **Validate production readiness** (safety controls, performance, monitoring)

## 📋 Prerequisites

### System Requirements
- **Python 3.8+** (recommended: Python 3.10+)
- **Docker** (for execution sandbox - optional but recommended)
- **Git** (for VCS integration)
- **4GB+ RAM** (for running multiple agents)
- **Internet connection** (for package installation and API access)

### API Keys (Optional but Recommended)
- **OpenAI API Key** - For LLM access (required for full functionality)
- **GitHub Token** - For GitHub integration (optional)
- **GitLab Token** - For GitLab integration (optional)

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Navigate to the LangGraph implementation directory
cd langgraph-implementation

# Run the automated setup and test script
python setup_and_test.py
```

This script will:
- ✅ Check Python version compatibility
- ✅ Install all required dependencies
- ✅ Set up environment configuration
- ✅ Run comprehensive tests
- ✅ Generate detailed validation report

### Option 2: Manual Setup

If you prefer manual control or the automated script fails:

```bash
# 1. Install core dependencies
pip install -r requirements.txt

# 2. Install optional dependencies
pip install docker pytest pytest-asyncio black flake8

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 4. Run tests
python final_validation.py
pytest tests/ -v
```

## 📦 Detailed Installation Steps

### Step 1: Environment Setup

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.8+
```

### Step 2: Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Verify core installations
python -c "import langgraph; print('LangGraph:', langgraph.__version__)"
python -c "import langchain; print('LangChain:', langchain.__version__)"
python -c "import docker; print('Docker client available')"
```

### Step 3: Docker Setup (Optional but Recommended)

```bash
# Install Docker (if not already installed)
# Follow instructions at: https://docs.docker.com/get-docker/

# Verify Docker installation
docker --version
docker run --rm hello-world

# Pull Python image for sandbox
docker pull python:3.10-slim
```

### Step 4: Environment Configuration

```bash
# Create environment file
cat > .env << EOF
# Required for LLM access
OPENAI_API_KEY=your_openai_api_key_here

# Optional for VCS integration
GITHUB_TOKEN=your_github_token_here
GITLAB_TOKEN=your_gitlab_token_here

# Optional for local models
OLLAMA_BASE_URL=http://localhost:11434
EOF

# Set up security policies
python -c "
from common.safety.policy import get_policy_manager
pm = get_policy_manager()
pm.set_active_policy('standard')
print('Security policy configured')
"
```

### Step 5: Run Validation Tests

```bash
# Run structure validation
python simple_test.py

# Run comprehensive validation
python final_validation.py

# Run full implementation tests (with dependencies)
python setup_and_test.py

# Run unit test suite
pytest tests/ -v --tb=short
```

## 🧪 Testing Levels

### Level 1: Structure Tests (No Dependencies)
```bash
python simple_test.py
```
- ✅ Code structure validation
- ✅ Required classes and methods
- ✅ Import structure
- ✅ Documentation completeness

### Level 2: Implementation Tests (Basic Dependencies)
```bash
python final_validation.py
```
- ✅ File structure validation
- ✅ Code quality metrics
- ✅ Documentation quality
- ✅ Requirements validation

### Level 3: Integration Tests (Full Dependencies)
```bash
python setup_and_test.py
```
- ✅ Dependency installation
- ✅ Real import testing
- ✅ Adapter creation with real components
- ✅ Safety system integration
- ✅ Workflow execution
- ✅ VCS integration
- ✅ Health and capabilities

### Level 4: Unit Test Suite (Comprehensive)
```bash
pytest tests/ -v
```
- ✅ 18+ unit test methods
- ✅ Mock-based testing
- ✅ Edge case coverage
- ✅ Error handling validation

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Python Version Issues
```bash
# Error: Python version too old
# Solution: Install Python 3.8+
pyenv install 3.10.0  # Using pyenv
# or download from python.org
```

#### 2. LangGraph Installation Issues
```bash
# Error: No module named 'langgraph'
# Solution: Install from correct source
pip install langgraph langchain langchain-community

# If still failing, try development version
pip install git+https://github.com/langchain-ai/langgraph.git
```

#### 3. Docker Issues
```bash
# Error: Docker not available
# Solution 1: Install Docker Desktop
# Solution 2: Use subprocess fallback (automatic)

# Error: Permission denied
sudo usermod -aG docker $USER  # Linux
# Then logout and login again
```

#### 4. API Key Issues
```bash
# Error: OpenAI API key not found
# Solution: Set environment variable
export OPENAI_API_KEY="your-key-here"

# Or add to .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
```

#### 5. Import Path Issues
```bash
# Error: No module named 'common'
# Solution: Run from project root
cd /path/to/ai-dev-squad-comparison
python langgraph-implementation/setup_and_test.py
```

#### 6. Memory Issues
```bash
# Error: Out of memory during tests
# Solution: Increase available memory or reduce test scope
export PYTEST_ARGS="-k 'not memory_intensive'"
```

### Dependency-Specific Issues

#### LangChain/LangGraph
```bash
# Install specific versions if needed
pip install langchain==0.1.0 langgraph==0.0.20

# Clear cache if installation issues
pip cache purge
pip install --no-cache-dir langgraph
```

#### Docker Python Client
```bash
# Install Docker client
pip install docker

# Test Docker connectivity
python -c "import docker; client = docker.from_env(); print(client.version())"
```

#### VCS Integration
```bash
# GitHub integration
pip install PyGithub
export GITHUB_TOKEN="your-token"

# GitLab integration  
pip install python-gitlab
export GITLAB_TOKEN="your-token"
```

## 📊 Validation Criteria

### Success Criteria
- ✅ **95%+ test pass rate** across all test levels
- ✅ **All core dependencies** installed successfully
- ✅ **Adapter creation** works with real components
- ✅ **Safety systems** properly integrated
- ✅ **Workflow execution** completes successfully
- ✅ **Documentation** comprehensive and accurate

### Performance Benchmarks
- **Adapter Creation**: < 5 seconds
- **Simple Task Execution**: < 30 seconds
- **Test Suite**: < 2 minutes
- **Memory Usage**: < 1GB during normal operation

### Quality Metrics
- **Code Coverage**: 80%+ (where applicable)
- **Documentation**: All public APIs documented
- **Error Handling**: Comprehensive try-catch coverage
- **Type Hints**: 70%+ coverage
- **Logging**: Appropriate log levels and messages

## 🎯 Expected Results

### Successful Installation
```
🟢 STATUS: FULLY VALIDATED AND READY
✅ LangGraph implementation is production-ready
🚀 All systems operational with external dependencies

📊 Results Summary:
- Dependency Setup: 8/8 (100%)
- Implementation Tests: 15/15 (100%)
- Overall Score: 23/23 (100%)
```

### Partial Success (Acceptable)
```
🟡 STATUS: MOSTLY READY (MINOR ISSUES)
⚠️ Some optional components not available
✅ Core functionality validated

📊 Results Summary:
- Dependency Setup: 6/8 (75%)
- Implementation Tests: 14/15 (93%)
- Overall Score: 20/23 (87%)
```

### Failure (Needs Attention)
```
🔴 STATUS: NEEDS ATTENTION
❌ Critical components missing or failing
🔧 Address failed tests before production use

📊 Results Summary:
- Dependency Setup: 4/8 (50%)
- Implementation Tests: 10/15 (67%)
- Overall Score: 14/23 (61%)
```

## 📈 Next Steps After Successful Installation

### 1. Integration with Benchmark Suite
```bash
# Navigate to benchmark directory
cd ../benchmark

# Run LangGraph benchmark
python benchmark_suite.py --framework langgraph --tasks all
```

### 2. Production Deployment
```bash
# Set production environment variables
export ENVIRONMENT=production
export LOG_LEVEL=INFO

# Run with production configuration
python -m langgraph_implementation.adapter
```

### 3. Development and Extension
```bash
# Set up development environment
pip install -e .
pre-commit install

# Run development tests
pytest tests/ --cov=langgraph_implementation
```

## 📞 Support

If you encounter issues not covered in this guide:

1. **Check the logs** in the generated report files
2. **Review the troubleshooting section** above
3. **Run individual test components** to isolate issues
4. **Check system requirements** and dependencies
5. **Verify environment configuration** and API keys

## 📄 Generated Reports

After running tests, check these files for detailed information:

- `full_test_report.json` - Comprehensive test results
- `final_validation_report.json` - Implementation validation
- `structure_validation_report.json` - Code structure analysis

These reports contain detailed information about what passed, what failed, and how to address any issues.