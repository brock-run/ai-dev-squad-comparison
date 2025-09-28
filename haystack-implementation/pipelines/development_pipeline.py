"""
Development Pipeline for Haystack Implementation

This module provides specialized pipelines for RAG-enhanced development workflows,
integrating document retrieval with code generation and analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from haystack import Pipeline
    from haystack.components.generators import OpenAIGenerator
    from haystack.components.retrievers import InMemoryBM25Retriever
    from haystack.components.builders import PromptBuilder
    HAYSTACK_AVAILABLE = True
except ImportError:
    HAYSTACK_AVAILABLE = False
    logger.warning("Haystack not available for pipeline creation")


class DevelopmentPipeline:
    """RAG-enhanced development pipeline orchestrator."""
    
    def __init__(self, document_store=None, openai_api_key=None, model_name="gpt-3.5-turbo"):
        self.document_store = document_store
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.pipelines = {}
        self.execution_count = 0
        
        if HAYSTACK_AVAILABLE and document_store and openai_api_key:
            self._create_pipelines()
    
    def _create_pipelines(self):
        """Create specialized RAG pipelines."""
        try:
            # Research Pipeline
            self.pipelines['research'] = self._create_research_pipeline()
            
            # Implementation Pipeline
            self.pipelines['implementation'] = self._create_implementation_pipeline()
            
            # Review Pipeline
            self.pipelines['review'] = self._create_review_pipeline()
            
            # Testing Pipeline
            self.pipelines['testing'] = self._create_testing_pipeline()
            
            logger.info(f"Created {len(self.pipelines)} development pipelines")
            
        except Exception as e:
            logger.error(f"Failed to create pipelines: {e}")
            self.pipelines = {}
    
    def _create_research_pipeline(self):
        """Create research pipeline for knowledge gathering."""
        pipeline = Pipeline()
        
        # Add components
        pipeline.add_component("retriever", InMemoryBM25Retriever(document_store=self.document_store))
        pipeline.add_component("prompt_builder", PromptBuilder(
            template="""
            Research Task: {{query}}
            
            Based on the following knowledge base documents, provide comprehensive research insights:
            
            {% for document in documents %}
            Document {{loop.index}}:
            Category: {{document.meta.category if document.meta.category else 'General'}}
            Content: {{document.content}}
            
            {% endfor %}
            
            Please provide:
            1. Key insights relevant to the research task
            2. Best practices and recommendations
            3. Potential risks and considerations
            4. Implementation strategies
            5. Quality assurance approaches
            
            Research Query: {{query}}
            """
        ))
        pipeline.add_component("llm", OpenAIGenerator(
            api_key=self.openai_api_key,
            model=self.model_name,
            generation_kwargs={"max_tokens": 1000, "temperature": 0.7}
        ))
        
        # Connect components
        pipeline.connect("retriever", "prompt_builder.documents")
        pipeline.connect("prompt_builder", "llm")
        
        return pipeline
    
    def _create_implementation_pipeline(self):
        """Create implementation pipeline for code generation."""
        pipeline = Pipeline()
        
        # Add components
        pipeline.add_component("retriever", InMemoryBM25Retriever(document_store=self.document_store))
        pipeline.add_component("prompt_builder", PromptBuilder(
            template="""
            Implementation Task: {{task_description}}
            
            Requirements:
            {% for req in requirements %}
            - {{req}}
            {% endfor %}
            
            Best Practices from Knowledge Base:
            {% for document in documents %}
            [{{document.meta.category if document.meta.category else 'General'}}] {{document.content}}
            
            {% endfor %}
            
            Please generate a complete, production-ready implementation that:
            1. Addresses all specified requirements
            2. Follows the retrieved best practices
            3. Includes proper error handling
            4. Has comprehensive documentation
            5. Includes basic testing structure
            6. Follows security best practices
            
            Generate clean, well-documented code with appropriate comments.
            """
        ))
        pipeline.add_component("llm", OpenAIGenerator(
            api_key=self.openai_api_key,
            model=self.model_name,
            generation_kwargs={"max_tokens": 1500, "temperature": 0.3}
        ))
        
        # Connect components
        pipeline.connect("retriever", "prompt_builder.documents")
        pipeline.connect("prompt_builder", "llm")
        
        return pipeline
    
    def _create_review_pipeline(self):
        """Create review pipeline for code analysis."""
        pipeline = Pipeline()
        
        # Add components
        pipeline.add_component("retriever", InMemoryBM25Retriever(document_store=self.document_store))
        pipeline.add_component("prompt_builder", PromptBuilder(
            template="""
            Code Review Task for: {{code_description}}
            
            Code to Review:
            {{code_content}}
            
            Review Guidelines from Knowledge Base:
            {% for document in documents %}
            [{{document.meta.category if document.meta.category else 'General'}}] {{document.content}}
            
            {% endfor %}
            
            Please provide a comprehensive code review covering:
            1. Code quality and best practices adherence
            2. Security considerations and vulnerabilities
            3. Performance implications and optimizations
            4. Testing coverage and quality
            5. Documentation completeness
            6. Maintainability and readability
            7. Specific improvement recommendations
            
            Provide both positive feedback and areas for improvement.
            """
        ))
        pipeline.add_component("llm", OpenAIGenerator(
            api_key=self.openai_api_key,
            model=self.model_name,
            generation_kwargs={"max_tokens": 1200, "temperature": 0.4}
        ))
        
        # Connect components
        pipeline.connect("retriever", "prompt_builder.documents")
        pipeline.connect("prompt_builder", "llm")
        
        return pipeline
    
    def _create_testing_pipeline(self):
        """Create testing pipeline for test generation."""
        pipeline = Pipeline()
        
        # Add components
        pipeline.add_component("retriever", InMemoryBM25Retriever(document_store=self.document_store))
        pipeline.add_component("prompt_builder", PromptBuilder(
            template="""
            Test Generation Task for: {{code_description}}
            
            Code to Test:
            {{code_content}}
            
            Testing Best Practices from Knowledge Base:
            {% for document in documents %}
            [{{document.meta.category if document.meta.category else 'General'}}] {{document.content}}
            
            {% endfor %}
            
            Please generate comprehensive tests including:
            1. Unit tests for individual functions/methods
            2. Integration tests for component interactions
            3. Edge case and error condition tests
            4. Performance tests where applicable
            5. Security tests for input validation
            6. Mock objects and test fixtures as needed
            
            Follow testing best practices and include proper test documentation.
            """
        ))
        pipeline.add_component("llm", OpenAIGenerator(
            api_key=self.openai_api_key,
            model=self.model_name,
            generation_kwargs={"max_tokens": 1300, "temperature": 0.3}
        ))
        
        # Connect components
        pipeline.connect("retriever", "prompt_builder.documents")
        pipeline.connect("prompt_builder", "llm")
        
        return pipeline
    
    async def execute_research(self, query: str) -> Dict[str, Any]:
        """Execute research pipeline."""
        if 'research' not in self.pipelines:
            return {"error": "Research pipeline not available"}
        
        try:
            self.execution_count += 1
            result = self.pipelines['research'].run({
                "retriever": {"query": query},
                "prompt_builder": {"query": query}
            })
            
            return {
                "success": True,
                "research_output": result.get('llm', {}).get('replies', [''])[0],
                "documents_retrieved": len(result.get('retriever', {}).get('documents', [])),
                "execution_id": self.execution_count
            }
            
        except Exception as e:
            logger.error(f"Research pipeline execution failed: {e}")
            return {"error": str(e), "success": False}
    
    async def execute_implementation(self, task_description: str, requirements: List[str]) -> Dict[str, Any]:
        """Execute implementation pipeline."""
        if 'implementation' not in self.pipelines:
            return {"error": "Implementation pipeline not available"}
        
        try:
            self.execution_count += 1
            result = self.pipelines['implementation'].run({
                "retriever": {"query": f"implementation patterns for {task_description}"},
                "prompt_builder": {
                    "task_description": task_description,
                    "requirements": requirements
                }
            })
            
            return {
                "success": True,
                "implementation_code": result.get('llm', {}).get('replies', [''])[0],
                "documents_retrieved": len(result.get('retriever', {}).get('documents', [])),
                "execution_id": self.execution_count
            }
            
        except Exception as e:
            logger.error(f"Implementation pipeline execution failed: {e}")
            return {"error": str(e), "success": False}
    
    async def execute_review(self, code_description: str, code_content: str) -> Dict[str, Any]:
        """Execute review pipeline."""
        if 'review' not in self.pipelines:
            return {"error": "Review pipeline not available"}
        
        try:
            self.execution_count += 1
            result = self.pipelines['review'].run({
                "retriever": {"query": f"code review guidelines for {code_description}"},
                "prompt_builder": {
                    "code_description": code_description,
                    "code_content": code_content
                }
            })
            
            return {
                "success": True,
                "review_feedback": result.get('llm', {}).get('replies', [''])[0],
                "documents_retrieved": len(result.get('retriever', {}).get('documents', [])),
                "execution_id": self.execution_count
            }
            
        except Exception as e:
            logger.error(f"Review pipeline execution failed: {e}")
            return {"error": str(e), "success": False}
    
    async def execute_testing(self, code_description: str, code_content: str) -> Dict[str, Any]:
        """Execute testing pipeline."""
        if 'testing' not in self.pipelines:
            return {"error": "Testing pipeline not available"}
        
        try:
            self.execution_count += 1
            result = self.pipelines['testing'].run({
                "retriever": {"query": f"testing strategies for {code_description}"},
                "prompt_builder": {
                    "code_description": code_description,
                    "code_content": code_content
                }
            })
            
            return {
                "success": True,
                "test_code": result.get('llm', {}).get('replies', [''])[0],
                "documents_retrieved": len(result.get('retriever', {}).get('documents', [])),
                "execution_id": self.execution_count
            }
            
        except Exception as e:
            logger.error(f"Testing pipeline execution failed: {e}")
            return {"error": str(e), "success": False}
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about available pipelines."""
        return {
            "available_pipelines": list(self.pipelines.keys()),
            "total_executions": self.execution_count,
            "haystack_available": HAYSTACK_AVAILABLE,
            "document_store_available": self.document_store is not None,
            "api_key_configured": bool(self.openai_api_key)
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline execution metrics."""
        return {
            "pipeline_count": len(self.pipelines),
            "total_executions": self.execution_count,
            "average_executions_per_pipeline": (
                self.execution_count / len(self.pipelines) if self.pipelines else 0
            ),
            "pipelines_available": list(self.pipelines.keys())
        }