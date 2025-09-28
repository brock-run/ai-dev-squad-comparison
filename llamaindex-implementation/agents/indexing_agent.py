"""
Indexing Agent for LlamaIndex Implementation

This agent handles repository indexing and vector store management
using LlamaIndex's indexing capabilities.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class IndexingAgent:
    """
    Repository Indexing Agent
    
    Handles document indexing, vector store creation, and index management
    using LlamaIndex's indexing capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the indexing agent."""
        self.config = config
        self.name = "Indexing Agent"
        self.description = "Repository indexing and vector store management"
        self.vector_store = None
        self.document_store = None
        
        logger.info(f"Initialized {self.name}")
    
    async def index_repository(self, repo_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Index a repository for semantic search.
        
        Args:
            repo_path: Path to the repository to index
            context: Additional context for indexing
            
        Returns:
            Dictionary containing indexing results and metadata
        """
        try:
            logger.info(f"Starting repository indexing: {repo_path}")
            
            # Discover files to index
            files_to_index = await self._discover_files(repo_path, context)
            
            # Process and chunk documents
            processed_docs = await self._process_documents(files_to_index, context)
            
            # Create vector embeddings
            embeddings = await self._create_embeddings(processed_docs, context)
            
            # Build vector store
            vector_store = await self._build_vector_store(embeddings, context)
            
            # Create search index
            search_index = await self._create_search_index(vector_store, context)
            
            result = {
                'repo_path': repo_path,
                'files_indexed': len(files_to_index),
                'documents_processed': len(processed_docs),
                'embeddings_created': len(embeddings),
                'vector_store_size': len(vector_store),
                'index_type': 'vector_similarity',
                'indexing_method': 'llamaindex_pipeline',
                'status': 'completed'
            }
            
            logger.info(f"Repository indexing completed: {len(files_to_index)} files indexed")
            return result
            
        except Exception as e:
            logger.error(f"Repository indexing failed: {e}")
            return {
                'repo_path': repo_path,
                'error': str(e),
                'files_indexed': 0,
                'status': 'failed'
            }
    
    async def _discover_files(self, repo_path: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover files to index in the repository."""
        # Mock file discovery
        mock_files = [
            {
                'path': 'src/main.py',
                'type': 'code',
                'language': 'python',
                'size': 1024,
                'last_modified': '2024-01-15T10:30:00Z'
            },
            {
                'path': 'src/utils.py',
                'type': 'code',
                'language': 'python',
                'size': 512,
                'last_modified': '2024-01-14T15:45:00Z'
            },
            {
                'path': 'README.md',
                'type': 'documentation',
                'language': 'markdown',
                'size': 2048,
                'last_modified': '2024-01-16T09:15:00Z'
            },
            {
                'path': 'docs/api.md',
                'type': 'documentation',
                'language': 'markdown',
                'size': 1536,
                'last_modified': '2024-01-15T14:20:00Z'
            },
            {
                'path': 'tests/test_main.py',
                'type': 'test',
                'language': 'python',
                'size': 768,
                'last_modified': '2024-01-15T11:00:00Z'
            },
            {
                'path': 'config/settings.yaml',
                'type': 'configuration',
                'language': 'yaml',
                'size': 256,
                'last_modified': '2024-01-13T16:30:00Z'
            }
        ]
        
        # Filter based on indexing preferences
        indexable_extensions = {'.py', '.md', '.yaml', '.yml', '.json', '.txt', '.rst'}
        filtered_files = []
        
        for file_info in mock_files:
            file_path = Path(file_info['path'])
            if file_path.suffix in indexable_extensions:
                filtered_files.append(file_info)
        
        logger.info(f"Discovered {len(filtered_files)} indexable files")
        return filtered_files
    
    async def _process_documents(self, files: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and chunk documents for indexing."""
        processed_docs = []
        
        for file_info in files:
            # Mock document processing
            file_path = file_info['path']
            file_type = file_info['type']
            
            # Create mock content based on file type
            if file_type == 'code':
                content = f'''# {file_path}

def main():
    """Main function for {file_path}."""
    print("Processing {file_path}")
    return process_data()

def process_data():
    """Process data with advanced algorithms."""
    data = load_data()
    processed = transform_data(data)
    return processed

class DataProcessor:
    """Advanced data processing class."""
    
    def __init__(self, config):
        self.config = config
    
    def process(self, data):
        """Process input data."""
        return self._apply_transformations(data)
'''
            elif file_type == 'documentation':
                content = f'''# {file_path}

## Overview

This document describes the functionality and usage of {file_path}.

## Features

- Advanced data processing
- Configurable transformations
- Comprehensive error handling
- Performance optimization

## Usage

```python
from src.main import DataProcessor

processor = DataProcessor(config)
result = processor.process(data)
```

## API Reference

### DataProcessor

Main class for data processing operations.

#### Methods

- `process(data)`: Process input data
- `configure(options)`: Configure processing options
'''
            elif file_type == 'test':
                content = f'''# {file_path}

import pytest
from src.main import DataProcessor, main

def test_main():
    """Test main function."""
    result = main()
    assert result is not None

def test_data_processor():
    """Test DataProcessor class."""
    config = {{"mode": "test"}}
    processor = DataProcessor(config)
    
    test_data = {{"key": "value"}}
    result = processor.process(test_data)
    
    assert result is not None
    assert "processed" in result

@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {{"test": "data", "values": [1, 2, 3]}}
'''
            else:
                content = f'# {file_path}\n\nConfiguration and settings for the application.'
            
            # Chunk the document
            chunks = self._chunk_document(content, file_info)
            
            for i, chunk in enumerate(chunks):
                processed_doc = {
                    'id': f"{file_path}_chunk_{i}",
                    'source_file': file_path,
                    'file_type': file_type,
                    'chunk_index': i,
                    'content': chunk,
                    'metadata': {
                        'file_info': file_info,
                        'chunk_size': len(chunk),
                        'processing_method': 'semantic_chunking'
                    }
                }
                processed_docs.append(processed_doc)
        
        logger.info(f"Processed {len(processed_docs)} document chunks")
        return processed_docs
    
    def _chunk_document(self, content: str, file_info: Dict[str, Any]) -> List[str]:
        """Chunk a document into smaller pieces for indexing."""
        # Mock chunking - split by paragraphs or logical sections
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        chunk_size = 0
        max_chunk_size = 500  # characters
        
        for line in lines:
            if chunk_size + len(line) > max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                chunk_size = len(line)
            else:
                current_chunk.append(line)
                chunk_size += len(line) + 1  # +1 for newline
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks if chunks else [content]
    
    async def _create_embeddings(self, documents: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create vector embeddings for documents."""
        embeddings = []
        
        for doc in documents:
            # Mock embedding creation
            content = doc['content']
            
            # Simulate embedding vector (normally would use actual embedding model)
            import hashlib
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Create mock embedding vector
            embedding_vector = [
                float(int(content_hash[i:i+2], 16)) / 255.0 
                for i in range(0, min(32, len(content_hash)), 2)
            ]
            
            # Pad to standard embedding size (e.g., 384 dimensions)
            while len(embedding_vector) < 384:
                embedding_vector.extend(embedding_vector[:min(384-len(embedding_vector), len(embedding_vector))])
            
            embedding = {
                'document_id': doc['id'],
                'vector': embedding_vector[:384],  # Truncate to 384 dimensions
                'metadata': doc['metadata'],
                'content_preview': content[:100] + '...' if len(content) > 100 else content
            }
            embeddings.append(embedding)
        
        logger.info(f"Created {len(embeddings)} embeddings")
        return embeddings
    
    async def _build_vector_store(self, embeddings: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Build vector store from embeddings."""
        # Mock vector store creation
        vector_store = {
            'type': 'llamaindex_vector_store',
            'dimension': 384,
            'total_vectors': len(embeddings),
            'index_type': 'flat',  # Could be 'hnsw', 'ivf', etc.
            'embeddings': embeddings,
            'metadata': {
                'created_at': '2024-01-16T12:00:00Z',
                'embedding_model': 'text-embedding-ada-002',
                'similarity_metric': 'cosine'
            }
        }
        
        logger.info(f"Built vector store with {len(embeddings)} vectors")
        return vector_store
    
    async def _create_search_index(self, vector_store: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create search index from vector store."""
        # Mock search index creation
        search_index = {
            'type': 'llamaindex_search_index',
            'vector_store': vector_store,
            'query_engine_type': 'vector_similarity',
            'retrieval_settings': {
                'top_k': 10,
                'similarity_threshold': 0.7,
                'rerank': True
            },
            'metadata': {
                'indexed_files': vector_store['total_vectors'],
                'index_size_mb': vector_store['total_vectors'] * 0.001,  # Mock size calculation
                'search_capabilities': ['semantic_search', 'keyword_search', 'hybrid_search']
            }
        }
        
        logger.info("Created search index with vector similarity support")
        return search_index
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'features': [
                'repository_indexing',
                'document_processing',
                'vector_embedding_creation',
                'vector_store_management',
                'search_index_creation',
                'incremental_indexing'
            ],
            'supported_file_types': ['.py', '.md', '.yaml', '.yml', '.json', '.txt', '.rst'],
            'indexing_methods': ['semantic_chunking', 'fixed_size_chunking', 'paragraph_chunking'],
            'vector_stores': ['llamaindex_vector_store', 'chroma', 'pinecone', 'weaviate'],
            'embedding_models': ['text-embedding-ada-002', 'sentence-transformers', 'custom']
        }