"""
Glyph configuration loader for centralized visual element management.
"""

import json
import yaml
from typing import Dict, Any, Tuple


class GlyphConfig:
    """Manages loading and accessing glyph configurations from YAML or JSON."""
    
    def __init__(self, config_path: str = 'data/glyphs.yaml'):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load glyph configuration from YAML or JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    self.config = yaml.safe_load(f)
                else:
                    self.config = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Glyph config file '{self.config_path}' not found. Using defaults.")
            self._load_defaults()
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            print(f"Warning: Invalid format in '{self.config_path}': {e}. Using defaults.")
            self._load_defaults()
    
    def _load_defaults(self) -> None:
        """Load default glyph configuration as fallback."""
        self.config = {
            "terrain": {
                "floor": {
                    "char": ".",
                    "visible_color": "white",
                    "explored_color": "bright_black"
                },
                "wall": {
                    "char": "#",
                    "visible_color": "white",
                    "explored_color": "bright_black"
                }
            },
            "entities": {
                "player": {
                    "char": "@",
                    "color": "yellow"
                }
            }
        }
    
    def get_terrain_glyph(self, terrain_type: str, visible: bool = True) -> Tuple[str, str]:
        """
        Get terrain glyph and color.
        
        Args:
            terrain_type: Type of terrain ('floor', 'wall', etc.)
            visible: Whether the terrain is currently visible
            
        Returns:
            Tuple of (character, color)
        """
        terrain_config = self.config.get("terrain", {}).get(terrain_type, {})
        
        if not terrain_config:
            # Fallback for unknown terrain types
            return "?", "white"
        
        char = terrain_config.get("char", "?")
        
        if visible:
            color = terrain_config.get("visible_color", "white")
        else:
            color = terrain_config.get("explored_color", "bright_black")
        
        return char, color
    
    def get_entity_glyph(self, entity_type: str) -> Tuple[str, str]:
        """
        Get entity glyph and color.
        
        Args:
            entity_type: Type of entity ('player', etc.)
            
        Returns:
            Tuple of (character, color)
        """
        entity_config = self.config.get("entities", {}).get(entity_type, {})
        
        if not entity_config:
            # Fallback for unknown entity types
            return "?", "white"
        
        char = entity_config.get("char", "?")
        color = entity_config.get("color", "white")
        
        return char, color
    
    def reload_config(self) -> None:
        """Reload configuration from file (useful for hot-swapping)."""
        self._load_config()
    
    def get_all_terrain_types(self) -> list:
        """Get list of all defined terrain types."""
        return list(self.config.get("terrain", {}).keys())
    
    def get_all_entity_types(self) -> list:
        """Get list of all defined entity types."""
        return list(self.config.get("entities", {}).keys())
