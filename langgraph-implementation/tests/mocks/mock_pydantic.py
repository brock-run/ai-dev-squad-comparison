"""
Mock implementations of pydantic classes for testing.

This module provides mock implementations of the pydantic classes used in the code,
allowing tests to run without depending on the actual pydantic implementation.
"""

from typing import Dict, Any, Type, ClassVar


class BaseModel:
    """Mock implementation of pydantic.BaseModel."""
    
    # Class variable to store field definitions
    __fields__: ClassVar[Dict[str, Any]] = {}
    
    def __init__(self, **data):
        """Initialize a mock BaseModel with the given data."""
        for key, value in data.items():
            setattr(self, key, value)
    
    def dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {key: getattr(self, key) for key in self.__fields__ if hasattr(self, key)}
    
    def json(self) -> str:
        """Convert the model to a JSON string."""
        import json
        return json.dumps(self.dict())
    
    @classmethod
    def parse_obj(cls, obj: Dict[str, Any]) -> 'BaseModel':
        """Create a model instance from a dictionary."""
        return cls(**obj)
    
    @classmethod
    def parse_raw(cls, raw_data: str) -> 'BaseModel':
        """Create a model instance from a JSON string."""
        import json
        return cls.parse_obj(json.loads(raw_data))


class TypedDict(dict):
    """Mock implementation of TypedDict from typing."""
    pass


def create_model(name: str, **field_definitions) -> Type[BaseModel]:
    """Create a new model class with the given fields."""
    new_model = type(name, (BaseModel,), {
        '__fields__': field_definitions
    })
    return new_model