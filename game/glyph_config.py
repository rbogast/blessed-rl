"""
Glyph configuration loader for centralized visual element management.
"""

import json
import yaml
import os
from typing import Dict, Any, Tuple
from utils.platform_detection import PlatformDetector


class GlyphConfig:
    """Manages loading and accessing glyph configurations from YAML or JSON."""
    
    def __init__(self, config_path: str = 'data/glyphs.yaml', character_set: str = None, charset_override: str = None):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.platform_detector = PlatformDetector()
        
        # Determine character set to use - charset_override takes precedence
        if charset_override:
            self.character_set = charset_override
        elif character_set:
            self.character_set = character_set
        else:
            self.character_set = self.platform_detector.get_recommended_character_set()
        
        self._load_config()
        self._log_platform_info()
    
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
                    "unicode": "·",
                    "ascii": ".",
                    "cp437": "·",
                    "visible_color": "white",
                    "explored_color": "bright_black"
                },
                "wall": {
                    "unicode": "▒",
                    "ascii": "#",
                    "cp437": "▒",
                    "visible_color": "white",
                    "explored_color": "bright_black"
                }
            },
            "entities": {
                "player": {
                    "unicode": "@",
                    "ascii": "@",
                    "cp437": "@",
                    "color": "yellow"
                }
            }
        }
    
    def _log_platform_info(self) -> None:
        """Log platform detection information for debugging."""
        if os.environ.get('BLESSED_RL_DEBUG'):
            platform_info = self.platform_detector.get_platform_info()
            print(f"Platform: {platform_info['system']}")
            print(f"Encoding: {platform_info['encoding']}")
            print(f"Character set: {self.character_set}")
            print(f"Unicode support: {platform_info['supports_unicode']}")
    
    def get_terrain_glyph(self, terrain_type: str, visible: bool = True, lit: bool = True) -> Tuple[str, str]:
        """
        Get terrain glyph and color.
        
        Args:
            terrain_type: Type of terrain ('floor', 'wall', etc.)
            visible: Whether the terrain is currently visible
            lit: Whether the terrain is currently lit (only matters if visible)
            
        Returns:
            Tuple of (character, color)
        """
        terrain_config = self.config.get("terrain", {}).get(terrain_type, {})
        
        if not terrain_config:
            # Fallback for unknown terrain types
            return "?", "white"
        
        # Get character based on current character set
        char = self._get_character_for_set(terrain_config, "?")
        
        if visible:
            if lit:
                color = terrain_config.get("visible_color", "white")
            else:
                color = terrain_config.get("visible_unlit_color", "blue")
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
        
        # Get character based on current character set
        char = self._get_character_for_set(entity_config, "?")
        color = entity_config.get("color", "white")
        
        return char, color
    
    def _get_character_for_set(self, config: Dict[str, Any], fallback: str) -> str:
        """
        Get the appropriate character for the current character set.
        
        Args:
            config: Configuration dictionary containing character definitions
            fallback: Fallback character if none found
            
        Returns:
            Character string for the current character set
        """
        # Try to get character for current character set
        char = config.get(self.character_set)
        if char:
            return char
        
        # Fallback hierarchy: unicode -> ascii -> cp437 -> fallback
        fallback_order = ['unicode', 'ascii', 'cp437']
        for charset in fallback_order:
            char = config.get(charset)
            if char:
                return char
        
        # Legacy support - check for old 'char' key
        char = config.get('char')
        if char:
            return char
        
        return fallback
    
    def get_character_set(self) -> str:
        """Get the current character set being used."""
        return self.character_set
    
    def set_character_set(self, character_set: str) -> None:
        """
        Set the character set to use.
        
        Args:
            character_set: Character set name ('unicode', 'ascii', 'cp437')
        """
        if character_set in ['unicode', 'ascii', 'cp437']:
            self.character_set = character_set
        else:
            print(f"Warning: Unknown character set '{character_set}'. Using 'ascii'.")
            self.character_set = 'ascii'
    
    def get_available_character_sets(self) -> list:
        """Get list of available character sets."""
        return ['unicode', 'ascii', 'cp437']
    
    def reload_config(self) -> None:
        """Reload configuration from file (useful for hot-swapping)."""
        self._load_config()
    
    def get_all_terrain_types(self) -> list:
        """Get list of all defined terrain types."""
        return list(self.config.get("terrain", {}).keys())
    
    def get_all_entity_types(self) -> list:
        """Get list of all defined entity types."""
        return list(self.config.get("entities", {}).keys())
