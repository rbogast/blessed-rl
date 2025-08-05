"""
Examine system for inspecting tiles and entities.
"""

from ecs.system import System
from components.core import Position, Player, Renderable, Door
from components.examine import ExamineCursor
from components.combat import Health
from components.ai import AI
from components.items import Item, Pickupable
from components.corpse import Corpse, Species, Disposition
from typing import Optional, Tuple, List, Dict, Any
import json
import os


class ExamineSystem(System):
    """Handles examine mode mechanics and entity inspection."""
    
    def __init__(self, world, fov_system, message_log, world_generator=None):
        super().__init__(world)
        self.fov_system = fov_system
        self.message_log = message_log
        self.world_generator = world_generator
        self._character_data = self._load_character_data()
    
    def update(self, dt: float = 0.0) -> None:
        """Update examine system - no automatic updates needed."""
        pass
    
    def start_examine_mode(self, player_entity: int) -> bool:
        """Start examine mode with cursor at player position."""
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return False
        
        # Create examine cursor component at player position
        cursor = ExamineCursor(player_pos.x, player_pos.y)
        self.world.add_component(player_entity, cursor)
        
        self.message_log.add_info("Examine mode - use arrow keys to move cursor, Enter to select, Escape to exit.")
        return True
    
    def move_cursor(self, player_entity: int, dx: int, dy: int) -> bool:
        """Move the examine cursor."""
        cursor = self.world.get_component(player_entity, ExamineCursor)
        if not cursor:
            return False
        
        new_x = cursor.cursor_x + dx
        new_y = cursor.cursor_y + dy
        
        # Check if new position is within FOV or has been explored
        if not self._is_position_examinable(new_x, new_y):
            return False
        
        cursor.move_cursor(new_x, new_y)
        return True
    
    def exit_examine_mode(self, player_entity: int) -> bool:
        """Exit examine mode."""
        cursor = self.world.get_component(player_entity, ExamineCursor)
        if cursor:
            self.world.remove_component(player_entity, ExamineCursor)
            self.message_log.add_info("Examine mode ended.")
            return True
        return False
    
    def is_examine_active(self, player_entity: int) -> bool:
        """Check if player is currently in examine mode."""
        return self.world.has_component(player_entity, ExamineCursor)
    
    def get_cursor_position(self, player_entity: int) -> Optional[Tuple[int, int]]:
        """Get current cursor position."""
        cursor = self.world.get_component(player_entity, ExamineCursor)
        if cursor:
            return (cursor.cursor_x, cursor.cursor_y)
        return None
    
    def get_entities_at_cursor(self, player_entity: int) -> List[int]:
        """Get all entities at the cursor position."""
        cursor = self.world.get_component(player_entity, ExamineCursor)
        if not cursor:
            return []
        
        # Find all entities at cursor position
        entities_at_pos = []
        all_entities = self.world.get_entities_with_components(Position)
        
        for entity_id in all_entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == cursor.cursor_x and position.y == cursor.cursor_y:
                entities_at_pos.append(entity_id)
        
        # Sort entities by priority (player, NPCs, corpses, items)
        return self._sort_entities_by_priority(entities_at_pos)
    
    def get_entity_description(self, entity_id: int) -> str:
        """Get detailed description of an entity."""
        # Check if it's the player
        if self.world.has_component(entity_id, Player):
            return self._get_player_description(entity_id)
        
        # Check if it's an NPC/monster
        ai = self.world.get_component(entity_id, AI)
        if ai:
            return self._get_character_description(entity_id, ai)
        
        # Check if it's a corpse
        corpse = self.world.get_component(entity_id, Corpse)
        if corpse:
            return self._get_corpse_description(entity_id, corpse)
        
        # Check if it's a door
        door = self.world.get_component(entity_id, Door)
        if door:
            return self._get_door_description(entity_id, door)
        
        # Check if it's an item
        item = self.world.get_component(entity_id, Item)
        if item:
            return self._get_item_description(entity_id, item)
        
        # Fallback for unknown entities
        renderable = self.world.get_component(entity_id, Renderable)
        if renderable:
            return f"Unknown entity ({renderable.char})"
        
        return "Unknown entity"
    
    def get_terrain_description(self, x: int, y: int) -> str:
        """Get description of terrain at position."""
        if not self.world_generator:
            return "empty ground"
        
        # Get the tile to check its type first (before checking is_wall_at)
        tile = self.world_generator.get_tile_at(x, y)
        if tile:
            tile_type = tile.tile_type
            
            # Map tile types to descriptions
            terrain_descriptions = {
                'floor': 'empty ground',
                'wall': 'a wall',
                'tree': 'a tree',
                'pine_tree': 'a pine tree',
                'oak_tree': 'an oak tree',
                'water': 'water',
                'grass': 'grass',
                'dirt': 'dirt',
                'stone': 'stone floor',
                'stairs_down': 'stairs leading down',
                'stairs_up': 'stairs leading up'
            }
            
            return terrain_descriptions.get(tile_type, 'empty ground')
        
        # Fallback: check if it's a wall (for cases where tile info isn't available)
        if self.world_generator.is_wall_at(x, y):
            return "a wall"
        
        return "empty ground"
    
    def _load_character_data(self) -> Dict[str, Any]:
        """Load character data from JSON file."""
        try:
            data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'characters.json')
            with open(data_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _is_position_examinable(self, x: int, y: int) -> bool:
        """Check if a position can be examined (visible or explored)."""
        # Allow examination of visible tiles or previously explored tiles
        return self.fov_system.is_visible(x, y) or self.fov_system.is_explored(x, y)
    
    def _sort_entities_by_priority(self, entities: List[int]) -> List[int]:
        """Sort entities by examination priority."""
        def get_priority(entity_id: int) -> int:
            if self.world.has_component(entity_id, Player):
                return 0  # Highest priority
            elif self.world.has_component(entity_id, AI):
                return 1  # NPCs/monsters
            elif self.world.has_component(entity_id, Corpse):
                return 2  # Corpses
            elif self.world.has_component(entity_id, Door):
                return 3  # Doors
            elif self.world.has_component(entity_id, Pickupable):
                return 4  # Items
            else:
                return 5  # Other entities
        
        return sorted(entities, key=get_priority)
    
    def _get_player_description(self, entity_id: int) -> str:
        """Get description of the player."""
        health = self.world.get_component(entity_id, Health)
        if health:
            return f"You\nHP: {health.current_health}/{health.max_health}"
        return "You"
    
    def _get_character_description(self, entity_id: int, ai: AI) -> str:
        """Get description of an NPC/monster."""
        # Try to get species and disposition from components first
        species = self.world.get_component(entity_id, Species)
        disposition = self.world.get_component(entity_id, Disposition)
        
        if species:
            char_name = species.species_name.capitalize()
        else:
            # Fallback to AI type if no species component
            ai_type = ai.ai_type.value if hasattr(ai.ai_type, 'value') else str(ai.ai_type)
            char_name = ai_type.capitalize()
        
        if disposition:
            disposition_str = disposition.disposition.value if hasattr(disposition.disposition, 'value') else str(disposition.disposition)
        else:
            # Fallback to JSON lookup if no disposition component
            species_name = species.species_name if species else ai.ai_type.value
            char_data = self._character_data.get(species_name, {})
            disposition_str = char_data.get('disposition', 'unknown')
        
        # Get health info
        health = self.world.get_component(entity_id, Health)
        health_info = ""
        if health:
            health_info = f"\nHP: {health.current_health}/{health.max_health}"
        
        return f"{char_name} ({disposition_str}){health_info}"
    
    def _get_corpse_description(self, entity_id: int, corpse: Corpse) -> str:
        """Get description of a corpse."""
        # Use the original_entity_type from the corpse component
        if hasattr(corpse, 'original_entity_type'):
            species_name = corpse.original_entity_type
        else:
            # Try to get species from a Species component if it still exists
            species = self.world.get_component(entity_id, Species)
            species_name = species.species_name if species else "unknown"
        
        return f"The corpse of a {species_name}"
    
    def _get_door_description(self, entity_id: int, door: Door) -> str:
        """Get description of a door."""
        if door.is_open:
            return "An open door"
        else:
            return "A closed door"
    
    def _get_item_description(self, entity_id: int, item: Item) -> str:
        """Get description of an item."""
        return item.name if item.name else "Unknown item"
