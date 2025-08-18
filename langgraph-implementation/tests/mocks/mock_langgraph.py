"""
Mock implementations of langgraph classes for testing.

This module provides mock implementations of the langgraph classes used in the code,
allowing tests to run without depending on the actual langgraph implementation.
"""

from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic, Literal, Union

# Define a sentinel object for END
END = object()

# Type variable for state
T = TypeVar('T')

class StateGraph(Generic[T]):
    """Mock implementation of langgraph.graph.StateGraph."""
    
    def __init__(self, state_type: Any):
        """Initialize a mock StateGraph."""
        self.state_type = state_type
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}
        self.entry_point = None
        
    def add_node(self, name: str, node_func: Callable):
        """Add a node to the graph."""
        self.nodes[name] = node_func
        return self
        
    def add_edge(self, start_node: str, end_node: Union[str, object]):
        """Add an edge between nodes."""
        if start_node not in self.edges:
            self.edges[start_node] = []
        self.edges[start_node].append(end_node)
        return self
        
    def add_conditional_edges(self, start_node: str, condition_func: Callable, destinations: Dict[str, Union[str, object]]):
        """Add conditional edges from a node."""
        self.conditional_edges[start_node] = (condition_func, destinations)
        return self
        
    def set_entry_point(self, node_name: str):
        """Set the entry point of the graph."""
        self.entry_point = node_name
        return self
        
    def invoke(self, state: T) -> T:
        """Run the graph with the given state."""
        # Simple implementation that just executes nodes in sequence
        current_node = self.entry_point
        current_state = state
        
        # Keep track of visited nodes to prevent infinite loops in tests
        visited_nodes = set()
        
        while current_node != END and current_node is not None:
            # Prevent infinite loops
            if current_node in visited_nodes:
                break
            visited_nodes.add(current_node)
            
            # Execute the current node
            if current_node in self.nodes:
                node_func = self.nodes[current_node]
                current_state = node_func(current_state)
            
            # Determine the next node
            next_node = None
            
            # Check conditional edges
            if current_node in self.conditional_edges:
                condition_func, destinations = self.conditional_edges[current_node]
                condition_result = condition_func(current_state)
                if condition_result in destinations:
                    next_node = destinations[condition_result]
            
            # Check regular edges
            if next_node is None and current_node in self.edges:
                edges = self.edges[current_node]
                if edges:
                    next_node = edges[0]  # Take the first edge
            
            current_node = next_node
        
        return current_state