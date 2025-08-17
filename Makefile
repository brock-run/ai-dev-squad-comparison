# =============================================================================
# AI Dev Squad Comparison Makefile
# =============================================================================
# This Makefile helps with installation, testing, and execution of the project.
# It provides targets for setting up each framework implementation, running tests,
# executing benchmarks, and visualizing results.
#
# Author: AI Dev Squad Team
# Date: August 14, 2025
# =============================================================================

# =============================================================================
# Configuration Variables
# =============================================================================

# Shell to use for commands
SHELL := /bin/bash

# Interpreters and commands
PYTHON := python3      # Python interpreter
NODE := node           # Node.js interpreter
DOTNET := dotnet       # .NET CLI
OLLAMA := ollama       # Ollama command for LLM management

# Directory paths
ROOT_DIR := $(shell pwd)
AUTOGEN_DIR := $(ROOT_DIR)/autogen-implementation
CREWAI_DIR := $(ROOT_DIR)/crewai-implementation
LANGGRAPH_DIR := $(ROOT_DIR)/langgraph-implementation
N8N_DIR := $(ROOT_DIR)/n8n-implementation
SEMANTIC_KERNEL_DIR := $(ROOT_DIR)/semantic-kernel-implementation
BENCHMARK_DIR := $(ROOT_DIR)/benchmark
COMPARISON_DIR := $(ROOT_DIR)/comparison-results
COMMON_DIR := $(ROOT_DIR)/common

# =============================================================================
# Help Target (Default)
# =============================================================================
# This is the default target that runs when you type 'make' without arguments.
# It displays help information about available targets.
.PHONY: help
help:
	@echo "AI Dev Squad Comparison Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make help                 Show this help message"
	@echo ""
	@echo "Installation:"
	@echo "  make install              Install all dependencies"
	@echo "  make install-framework F=<framework>  Install dependencies for a specific framework"
	@echo "  make install-benchmark    Install benchmark dependencies"
	@echo "  make install-dashboard    Install dashboard dependencies"
	@echo "  make venv                 Create a virtual environment"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run all tests"
	@echo "  make test-framework F=<framework>  Run tests for a specific framework"
	@echo ""
	@echo "Execution:"
	@echo "  make benchmark            Run all benchmarks"
	@echo "  make benchmark-framework F=<framework>  Run benchmarks for a specific framework"
	@echo "  make dashboard            Start the comparison dashboard"
	@echo "  make run-example F=<framework>  Run an example for a specific framework"
	@echo ""
	@echo "Utilities:"
	@echo "  make setup-ollama         Setup Ollama with required models"
	@echo "  make clean                Clean up temporary files"
	@echo "  make clean-all            Clean up all build artifacts and virtual environments"
	@echo ""
	@echo "Available frameworks: autogen, crewai, langgraph, n8n, semantic-kernel"
	@echo ""
	@echo "Examples:"
	@echo "  make install-framework F=autogen"
	@echo "  make test-framework F=langgraph"
	@echo "  make benchmark-framework F=crewai"
	@echo "  make run-example F=semantic-kernel"
	@echo ""

# Default target when just running 'make'
.DEFAULT_GOAL := help

# =============================================================================
# Installation Targets
# =============================================================================
# These targets handle the installation of dependencies for each framework
# implementation, benchmarking tools, and visualization dashboard.
.PHONY: install install-autogen install-crewai install-langgraph install-n8n install-semantic-kernel install-benchmark install-dashboard install-common

# Main installation target - installs all dependencies
install: install-common install-autogen install-crewai install-langgraph install-n8n install-semantic-kernel install-benchmark install-dashboard
	@echo "All dependencies installed successfully"

# Install dependencies for a specific framework (specified by F=<framework>)
install-framework:
	@if [ "$(F)" = "autogen" ]; then \
		$(MAKE) install-autogen; \
	elif [ "$(F)" = "crewai" ]; then \
		$(MAKE) install-crewai; \
	elif [ "$(F)" = "langgraph" ]; then \
		$(MAKE) install-langgraph; \
	elif [ "$(F)" = "n8n" ]; then \
		$(MAKE) install-n8n; \
	elif [ "$(F)" = "semantic-kernel" ]; then \
		$(MAKE) install-semantic-kernel; \
	else \
		echo "Unknown framework: $(F). Available options: autogen, crewai, langgraph, n8n, semantic-kernel"; \
		exit 1; \
	fi

# Install common utilities and shared code
install-common:
	@echo "Installing common dependencies..."
	@cd $(COMMON_DIR) && $(PYTHON) -m pip install -e .

# Install AutoGen framework dependencies
install-autogen:
	@echo "Installing AutoGen dependencies..."
	@cd $(AUTOGEN_DIR) && $(PYTHON) -m pip install -r requirements.txt

# Install CrewAI framework dependencies
install-crewai:
	@echo "Installing CrewAI dependencies..."
	@cd $(CREWAI_DIR) && $(PYTHON) -m pip install -r requirements.txt

# Install LangGraph framework dependencies
install-langgraph:
	@echo "Installing LangGraph dependencies..."
	@cd $(LANGGRAPH_DIR) && $(PYTHON) -m pip install -r requirements.txt

# Install n8n framework dependencies
install-n8n:
	@echo "Installing n8n dependencies..."
	@cd $(N8N_DIR) && npm install

# Install Semantic Kernel framework dependencies (both Python and C#)
install-semantic-kernel:
	@echo "Installing Semantic Kernel Python dependencies..."
	@cd $(SEMANTIC_KERNEL_DIR) && $(PYTHON) -m pip install -r requirements.txt
	@echo "Installing Semantic Kernel C# dependencies..."
	@cd $(SEMANTIC_KERNEL_DIR) && $(DOTNET) restore

# Install benchmark suite dependencies
install-benchmark:
	@echo "Installing benchmark dependencies..."
	@cd $(BENCHMARK_DIR) && $(PYTHON) -m pip install -r requirements.txt

# Install dashboard visualization dependencies
install-dashboard:
	@echo "Installing dashboard dependencies..."
	@cd $(COMPARISON_DIR) && $(PYTHON) -m pip install -r requirements.txt

# =============================================================================
# Testing Targets
# =============================================================================
# These targets run tests for each framework implementation to ensure
# functionality is working as expected.
.PHONY: test test-autogen test-crewai test-langgraph test-n8n test-semantic-kernel

# Main testing target - runs all tests across all frameworks
test: test-autogen test-crewai test-langgraph test-n8n test-semantic-kernel
	@echo "All tests completed"

# Run tests for a specific framework (specified by F=<framework>)
test-framework:
	@if [ "$(F)" = "autogen" ]; then \
		$(MAKE) test-autogen; \
	elif [ "$(F)" = "crewai" ]; then \
		$(MAKE) test-crewai; \
	elif [ "$(F)" = "langgraph" ]; then \
		$(MAKE) test-langgraph; \
	elif [ "$(F)" = "n8n" ]; then \
		$(MAKE) test-n8n; \
	elif [ "$(F)" = "semantic-kernel" ]; then \
		$(MAKE) test-semantic-kernel; \
	else \
		echo "Unknown framework: $(F). Available options: autogen, crewai, langgraph, n8n, semantic-kernel"; \
		exit 1; \
	fi

# Run tests for AutoGen implementation
test-autogen:
	@echo "Running AutoGen tests..."
	@cd $(AUTOGEN_DIR) && $(PYTHON) -m pytest -xvs

# Run tests for CrewAI implementation
test-crewai:
	@echo "Running CrewAI tests..."
	@cd $(CREWAI_DIR) && $(PYTHON) -m pytest -xvs

# Run tests for LangGraph implementation
test-langgraph:
	@echo "Running LangGraph tests..."
	@cd $(LANGGRAPH_DIR) && $(PYTHON) -m pytest -xvs

# Run tests for n8n implementation
test-n8n:
	@echo "Running n8n tests..."
	@cd $(N8N_DIR) && npm test

# Run tests for Semantic Kernel implementation (both Python and C#)
test-semantic-kernel:
	@echo "Running Semantic Kernel Python tests..."
	@cd $(SEMANTIC_KERNEL_DIR)/python && $(PYTHON) -m pytest -xvs
	@echo "Running Semantic Kernel C# tests..."
	@cd $(SEMANTIC_KERNEL_DIR) && $(DOTNET) test

# =============================================================================
# Execution Targets
# =============================================================================
# These targets run benchmarks, start the visualization dashboard, and execute
# example workflows for each framework implementation.
.PHONY: benchmark benchmark-framework dashboard run-example

# Run all benchmarks across all frameworks
benchmark:
	@echo "Running all benchmarks..."
	@cd $(BENCHMARK_DIR) && $(PYTHON) benchmark_suite.py --all

# Run benchmarks for a specific framework (specified by F=<framework>)
benchmark-framework:
	@if [ -z "$(F)" ]; then \
		echo "Please specify a framework with F=<framework>"; \
		exit 1; \
	fi
	@echo "Running benchmarks for $(F)..."
	@cd $(BENCHMARK_DIR) && $(PYTHON) benchmark_suite.py $(F) $(ROOT_DIR)/$(F)-implementation

# Start the comparison dashboard web application
dashboard:
	@echo "Starting comparison dashboard..."
	@cd $(COMPARISON_DIR) && $(PYTHON) dashboard.py

# Run an example workflow for a specific framework (specified by F=<framework>)
run-example:
	@if [ "$(F)" = "autogen" ]; then \
		echo "Running AutoGen example..."; \
		cd $(AUTOGEN_DIR)/workflows && $(PYTHON) group_chat_manager.py; \
	elif [ "$(F)" = "crewai" ]; then \
		echo "Running CrewAI example..."; \
		cd $(CREWAI_DIR)/workflows && $(PYTHON) development_process.py; \
	elif [ "$(F)" = "langgraph" ]; then \
		echo "Running LangGraph example..."; \
		cd $(LANGGRAPH_DIR)/workflows && $(PYTHON) development_workflow.py; \
	elif [ "$(F)" = "n8n" ]; then \
		echo "Running n8n example..."; \
		cd $(N8N_DIR) && npx n8n start; \
	elif [ "$(F)" = "semantic-kernel" ]; then \
		echo "Running Semantic Kernel Python example..."; \
		cd $(SEMANTIC_KERNEL_DIR)/python/workflows && $(PYTHON) development_workflow.py; \
	else \
		echo "Unknown framework: $(F). Available options: autogen, crewai, langgraph, n8n, semantic-kernel"; \
		exit 1; \
	fi

# =============================================================================
# Utility Targets
# =============================================================================
# These targets provide utility functions such as setting up Ollama models,
# cleaning temporary files, and creating virtual environments.
.PHONY: setup-ollama clean clean-all venv

# Set up Ollama with the required models for the project
setup-ollama:
	@echo "Setting up Ollama with required models..."
	@$(OLLAMA) pull llama3.1:8b
	@$(OLLAMA) pull codellama:13b
	@echo "Ollama models installed successfully"

# Clean up temporary Python and test files
clean:
	@echo "Cleaning temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +
	@find . -type f -name "*.log" -delete
	@echo "Temporary files cleaned"

# Clean up all build artifacts including virtual environments and dependencies
clean-all: clean
	@echo "Cleaning all build artifacts and virtual environments..."
	@find . -type d -name "venv" -exec rm -rf {} +
	@find . -type d -name "node_modules" -exec rm -rf {} +
	@find . -type d -name "bin" -exec rm -rf {} +
	@find . -type d -name "obj" -exec rm -rf {} +
	@find . -type d -name "dist" -exec rm -rf {} +
	@find . -type d -name "build" -exec rm -rf {} +
	@echo "All build artifacts cleaned"

# Create a Python virtual environment in the project root
venv:
	@echo "Creating virtual environment..."
	@$(PYTHON) -m venv venv
	@echo "Virtual environment created at ./venv"
	@echo "Activate it with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"