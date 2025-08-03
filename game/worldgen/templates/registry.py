"""
Template registry for managing map templates.
"""

from typing import Dict, List
from .base import MapTemplate
from .forest import ForestTemplate
from .maze import MazeTemplate
from .graveyard import GraveyardTemplate
from .rogue import RogueTemplate
from .rooms import RoomsTemplate


class TemplateRegistry:
    """Registry for map templates."""
    
    def __init__(self):
        self._templates: Dict[str, MapTemplate] = {}
        self._register_default_templates()
    
    def register(self, template: MapTemplate) -> None:
        """Register a template."""
        self._templates[template.name] = template
    
    def get(self, name: str) -> MapTemplate:
        """Get a template by name - returns a fresh instance each time. Case-insensitive."""
        # Try exact match first
        template_class = self._templates.get(name)
        
        # If no exact match, try case-insensitive search
        if not template_class:
            name_lower = name.lower()
            for template_name, template_instance in self._templates.items():
                if template_name.lower() == name_lower:
                    template_class = template_instance
                    break
        
        # Fallback to forest if not found
        if not template_class:
            template_class = self._templates.get('forest')
        
        if template_class:
            # Create a new instance to avoid state issues
            return template_class.__class__()
        return None
    
    def list_templates(self) -> List[str]:
        """List all registered template names."""
        return list(self._templates.keys())
    
    def _register_default_templates(self) -> None:
        """Register default templates."""
        self.register(ForestTemplate())
        self.register(MazeTemplate())
        self.register(GraveyardTemplate())
        self.register(RogueTemplate())
        self.register(RoomsTemplate())


# Global registry instance
_registry = TemplateRegistry()


def get_template(name: str) -> MapTemplate:
    """Get a template by name from the global registry."""
    return _registry.get(name)


def register_template(template: MapTemplate) -> None:
    """Register a template in the global registry."""
    _registry.register(template)


def list_templates() -> List[str]:
    """List all registered template names."""
    return _registry.list_templates()
