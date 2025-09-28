"""
Query Agent for LlamaIndex Implementation

This agent handles query processing and semantic search operations
using LlamaIndex's query engine capabilities.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class QueryAgent:
    """
    Query Processing Agent
    
    Handles query parsing, semantic search, and result ranking
    using LlamaIndex's query engine.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the query agent."""
        self.config = config
        self.name = "Query Agent"
        self.description = "Query processing and semantic search"
        self.query_engine = None
        self.index = None
        
        logger.info(f"Initialized {self.name}")
    
    async def query(self, query_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query and return relevant results.
        
        Args:
            query_text: The query to process
            context: Additional context for query processing
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            logger.info(f"Processing query: {query_text[:100]}...")
            
            # Parse and analyze the query
            parsed_query = await self._parse_query(query_text, context)
            
            # Execute semantic search
            search_results = await self._execute_search(parsed_query, context)
            
            # Rank and filter results
            ranked_results = await self._rank_results(search_results, parsed_query)
            
            result = {
                'original_query': query_text,
                'parsed_query': parsed_query,
                'search_results': ranked_results,
                'result_count': len(ranked_results),
                'search_method': 'semantic_vector_search',
                'processing_time': 0.15  # Mock processing time
            }
            
            logger.info(f"Query processed: {len(ranked_results)} results found")
            return result
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                'original_query': query_text,
                'error': str(e),
                'search_results': [],
                'result_count': 0
            }
    
    async def _parse_query(self, query_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and analyze the query."""
        # Mock query parsing
        parsed = {
            'text': query_text,
            'intent': self._detect_intent(query_text),
            'entities': self._extract_entities(query_text),
            'keywords': self._extract_keywords(query_text),
            'query_type': self._classify_query_type(query_text),
            'complexity': self._assess_complexity(query_text)
        }
        
        logger.info(f"Query parsed: intent={parsed['intent']}, type={parsed['query_type']}")
        return parsed
    
    def _detect_intent(self, query_text: str) -> str:
        """Detect the intent of the query."""
        query_lower = query_text.lower()
        
        if any(word in query_lower for word in ['create', 'generate', 'build', 'implement']):
            return 'creation'
        elif any(word in query_lower for word in ['find', 'search', 'locate', 'get']):
            return 'retrieval'
        elif any(word in query_lower for word in ['explain', 'describe', 'what', 'how']):
            return 'explanation'
        elif any(word in query_lower for word in ['fix', 'debug', 'error', 'issue']):
            return 'debugging'
        else:
            return 'general'
    
    def _extract_entities(self, query_text: str) -> List[str]:
        """Extract entities from the query."""
        # Mock entity extraction
        entities = []
        
        # Look for common programming entities
        if 'function' in query_text.lower():
            entities.append('function')
        if 'class' in query_text.lower():
            entities.append('class')
        if 'api' in query_text.lower():
            entities.append('api')
        if 'database' in query_text.lower():
            entities.append('database')
        if 'test' in query_text.lower():
            entities.append('test')
        
        return entities
    
    def _extract_keywords(self, query_text: str) -> List[str]:
        """Extract keywords from the query."""
        # Mock keyword extraction
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = query_text.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:10]  # Limit to top 10 keywords
    
    def _classify_query_type(self, query_text: str) -> str:
        """Classify the type of query."""
        query_lower = query_text.lower()
        
        if '?' in query_text:
            return 'question'
        elif any(word in query_lower for word in ['create', 'generate', 'build']):
            return 'creation_request'
        elif any(word in query_lower for word in ['find', 'search', 'show']):
            return 'search_request'
        else:
            return 'statement'
    
    def _assess_complexity(self, query_text: str) -> str:
        """Assess the complexity of the query."""
        word_count = len(query_text.split())
        
        if word_count < 5:
            return 'simple'
        elif word_count < 15:
            return 'medium'
        else:
            return 'complex'
    
    async def _execute_search(self, parsed_query: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute semantic search based on parsed query."""
        # Mock search execution
        mock_results = [
            {
                'content': f'# Code Example\n\ndef handle_query(query):\n    """Handle user query processing."""\n    return process_semantic_search(query)',
                'source': 'src/query_handler.py',
                'score': 0.92,
                'metadata': {
                    'type': 'code',
                    'language': 'python',
                    'relevance': 'high'
                }
            },
            {
                'content': f'# Query Processing Documentation\n\nThis section covers query processing and semantic search implementation.',
                'source': 'docs/query_processing.md',
                'score': 0.88,
                'metadata': {
                    'type': 'documentation',
                    'section': 'query_processing',
                    'relevance': 'high'
                }
            },
            {
                'content': f'# Test Cases\n\ndef test_query_processing():\n    query = "test query"\n    result = handle_query(query)\n    assert result["status"] == "success"',
                'source': 'tests/test_query_handler.py',
                'score': 0.85,
                'metadata': {
                    'type': 'test',
                    'framework': 'pytest',
                    'relevance': 'medium'
                }
            },
            {
                'content': f'# Configuration Example\n\nquery_config = {{\n    "search_method": "semantic",\n    "max_results": 10\n}}',
                'source': 'config/query_config.py',
                'score': 0.78,
                'metadata': {
                    'type': 'configuration',
                    'format': 'python',
                    'relevance': 'medium'
                }
            }
        ]
        
        # Filter based on query intent and keywords
        filtered_results = []
        for result in mock_results:
            if self._is_relevant(result, parsed_query):
                filtered_results.append(result)
        
        logger.info(f"Search executed: {len(filtered_results)} relevant results")
        return filtered_results
    
    def _is_relevant(self, result: Dict[str, Any], parsed_query: Dict[str, Any]) -> bool:
        """Check if a result is relevant to the parsed query."""
        # Mock relevance checking
        content = result['content'].lower()
        keywords = parsed_query.get('keywords', [])
        
        # Check if any keywords appear in the content
        keyword_matches = sum(1 for keyword in keywords if keyword in content)
        
        # Consider relevant if at least 1 keyword matches or score is high
        return keyword_matches > 0 or result['score'] > 0.85
    
    async def _rank_results(self, results: List[Dict[str, Any]], parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank search results by relevance."""
        # Mock result ranking
        def calculate_relevance_score(result):
            base_score = result['score']
            
            # Boost based on content type preference
            content_type = result['metadata'].get('type', 'unknown')
            if parsed_query['intent'] == 'creation' and content_type == 'code':
                base_score += 0.1
            elif parsed_query['intent'] == 'explanation' and content_type == 'documentation':
                base_score += 0.1
            
            # Boost based on keyword matches
            content = result['content'].lower()
            keywords = parsed_query.get('keywords', [])
            keyword_matches = sum(1 for keyword in keywords if keyword in content)
            base_score += keyword_matches * 0.02
            
            return base_score
        
        # Sort by relevance score
        ranked_results = sorted(results, key=calculate_relevance_score, reverse=True)
        
        # Add ranking information
        for i, result in enumerate(ranked_results):
            result['rank'] = i + 1
            result['relevance_score'] = calculate_relevance_score(result)
        
        logger.info(f"Results ranked: top score = {ranked_results[0]['relevance_score']:.3f}")
        return ranked_results
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'features': [
                'query_parsing',
                'intent_detection',
                'entity_extraction',
                'semantic_search',
                'result_ranking',
                'relevance_scoring'
            ],
            'supported_query_types': ['question', 'creation_request', 'search_request', 'statement'],
            'search_methods': ['semantic_vector_search', 'keyword_search', 'hybrid_search'],
            'ranking_algorithms': ['relevance_score', 'keyword_matching', 'content_type_preference']
        }