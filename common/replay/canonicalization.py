"""
Canonical Input Hashing for Deterministic Record-Replay

Provides stable, cross-platform input fingerprinting using BLAKE3 hashing
with normalized JSON serialization for consistent replay key generation.

Following ADR-009 specifications for input canonicalization and key stability.
"""

import json
import re
from typing import Any, Dict, List, Union
import hashlib

try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False


class CanonicalHasher:
    """Generates stable hashes for inputs across platforms and Python versions."""
    
    def __init__(self, use_blake3: bool = True):
        """
        Initialize canonical hasher.
        
        Args:
            use_blake3: Use BLAKE3 if available, fallback to SHA256
        """
        self.use_blake3 = use_blake3 and BLAKE3_AVAILABLE
    
    def hash_input(self, data: Any) -> str:
        """
        Generate canonical hash for any input data.
        
        Args:
            data: Input data to hash (dict, list, str, etc.)
            
        Returns:
            Hex-encoded hash string
        """
        canonical_bytes = self._canonicalize_to_bytes(data)
        
        if self.use_blake3:
            hasher = blake3.blake3()
            hasher.update(canonical_bytes)
            return hasher.hexdigest()
        else:
            return hashlib.sha256(canonical_bytes).hexdigest()
    
    def _canonicalize_to_bytes(self, data: Any) -> bytes:
        """Convert data to canonical byte representation."""
        canonical_json = self._canonicalize_json(data)
        return canonical_json.encode('utf-8')
    
    def _canonicalize_json(self, data: Any) -> str:
        """
        Convert data to canonical JSON string.
        
        Ensures consistent serialization across platforms:
        - Sorted keys
        - No extra whitespace
        - Consistent float precision
        - Normalized line endings
        - Trimmed strings
        """
        # Recursively canonicalize the data structure
        canonical_data = self._canonicalize_structure(data)
        
        # Serialize with consistent options
        return json.dumps(
            canonical_data,
            ensure_ascii=True,
            sort_keys=True,
            separators=(',', ':'),  # No extra whitespace
            default=self._json_serializer
        )
    
    def _canonicalize_structure(self, data: Any) -> Any:
        """Recursively canonicalize data structures."""
        if isinstance(data, dict):
            # Sort keys and canonicalize values
            return {
                key: self._canonicalize_structure(value)
                for key, value in sorted(data.items())
            }
        elif isinstance(data, (list, tuple)):
            # Canonicalize list elements
            return [self._canonicalize_structure(item) for item in data]
        elif isinstance(data, str):
            # Normalize whitespace and line endings
            return self._normalize_string(data)
        elif isinstance(data, float):
            # Consistent float precision (6 decimal places)
            return round(data, 6)
        else:
            # Return as-is for other types
            return data
    
    def _normalize_string(self, text: str) -> str:
        """
        Normalize string for consistent hashing.
        
        - Normalize line endings to \n
        - Trim leading/trailing whitespace
        - Collapse multiple spaces to single space
        """
        # Normalize line endings
        text = re.sub(r'\r\n|\r', '\n', text)
        
        # Trim whitespace
        text = text.strip()
        
        # Collapse multiple spaces (but preserve intentional formatting)
        # Only collapse spaces that aren't part of code indentation
        lines = text.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Preserve leading whitespace (indentation) but normalize internal spaces
            leading_space = len(line) - len(line.lstrip())
            content = line.lstrip()
            
            if content:
                # Collapse multiple spaces in content
                normalized_content = re.sub(r' +', ' ', content)
                normalized_lines.append(' ' * leading_space + normalized_content)
            else:
                # Empty line
                normalized_lines.append('')
        
        return '\n'.join(normalized_lines)
    
    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-standard types."""
        if hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Custom objects
            return obj.__dict__
        else:
            return str(obj)


class IOKey:
    """Represents a unique key for IO operations in record-replay."""
    
    def __init__(self, 
                 event_type: str,
                 adapter: str,
                 agent_id: str,
                 tool_name: str,
                 call_index: int,
                 input_fingerprint: str):
        """
        Initialize IO key.
        
        Args:
            event_type: Type of IO operation (llm_call, tool_call, etc.)
            adapter: Framework adapter name
            agent_id: Unique agent identifier
            tool_name: Name of the tool being called
            call_index: Monotonic call index for this agent/tool combination
            input_fingerprint: Canonical hash of input parameters
        """
        self.event_type = event_type
        self.adapter = adapter
        self.agent_id = agent_id
        self.tool_name = tool_name
        self.call_index = call_index
        self.input_fingerprint = input_fingerprint
    
    def to_string(self) -> str:
        """Generate string representation for lookup."""
        return f"{self.event_type}:{self.adapter}:{self.agent_id}:{self.tool_name}:{self.call_index}:{self.input_fingerprint}"
    
    def __str__(self) -> str:
        return self.to_string()
    
    def __hash__(self) -> int:
        return hash(self.to_string())
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, IOKey):
            return False
        return self.to_string() == other.to_string()


def create_io_key(event_type: str,
                  adapter: str,
                  agent_id: str,
                  tool_name: str,
                  call_index: int,
                  input_data: Any) -> IOKey:
    """
    Create an IO key for record-replay lookup.
    
    Args:
        event_type: Type of IO operation
        adapter: Framework adapter name
        agent_id: Unique agent identifier
        tool_name: Name of the tool being called
        call_index: Monotonic call index
        input_data: Input parameters to hash
        
    Returns:
        IOKey for this operation
    """
    hasher = CanonicalHasher()
    input_fingerprint = hasher.hash_input(input_data)
    
    return IOKey(
        event_type=event_type,
        adapter=adapter,
        agent_id=agent_id,
        tool_name=tool_name,
        call_index=call_index,
        input_fingerprint=input_fingerprint
    )


# Convenience functions
def hash_prompt(prompt: str, **params) -> str:
    """Hash a prompt with parameters for consistent lookup."""
    hasher = CanonicalHasher()
    data = {"prompt": prompt, "params": params}
    return hasher.hash_input(data)


def hash_tool_call(tool_name: str, **kwargs) -> str:
    """Hash a tool call with arguments for consistent lookup."""
    hasher = CanonicalHasher()
    data = {"tool": tool_name, "args": kwargs}
    return hasher.hash_input(data)


def normalize_json_for_comparison(data: Any) -> str:
    """Normalize JSON data for comparison across runs."""
    hasher = CanonicalHasher()
    return hasher._canonicalize_json(data)