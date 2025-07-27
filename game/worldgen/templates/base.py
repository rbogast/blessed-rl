"""
Base classes for map templates and parameter definitions.
"""

from typing import Dict, List, Any, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ParameterDef:
    """Definition of a template parameter."""
    param_type: type
    min_value: Union[int, float, None] = None
    max_value: Union[int, float, None] = None
    default_value: Any = None
    options: List[str] = None  # For string parameters with limited options
    
    def validate(self, value: Any) -> bool:
        """Validate a value against this parameter definition."""
        if not isinstance(value, self.param_type):
            return False
        
        if self.param_type in (int, float):
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        
        if self.param_type == str and self.options:
            if value not in self.options:
                return False
        
        return True


class MapTemplate(ABC):
    """Base class for map templates."""
    
    name: str = "unknown"
    
    def __init__(self):
        self.layers: List = []
        self._setup_layers()
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, ParameterDef]:
        """Return the parameters this template exposes for editing."""
        pass
    
    @abstractmethod
    def _setup_layers(self) -> None:
        """Set up the generation layers for this template."""
        pass
    
    def generate(self, tiles, ctx) -> None:
        """Generate terrain using all layers in sequence."""
        for layer in self.layers:
            layer.generate(tiles, ctx)
    
    def get_parameter_value(self, param_name: str, ctx) -> Any:
        """Get the current value of a parameter from context or default."""
        param_def = self.get_parameters().get(param_name)
        if not param_def:
            return None
        
        # Try to get from context first
        value = ctx.get_param(param_name, param_def.default_value)
        return value
