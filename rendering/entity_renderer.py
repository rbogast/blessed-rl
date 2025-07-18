"""Entity rendering and caching system."""

from typing import Tuple, Optional, Dict
from components.core import Position, Renderable, Player
from components.items import Pickupable
from components.ai import AI
from components.corpse import Corpse


class EntityRenderer:
    """Handles entity display logic with caching for performance."""
    
    def __init__(self, world):
        self.world = world
        self.entity_position_cache = {}
        self.cache_dirty = True
    
    def get_entity_at_position(self, world_x: int, world_y: int) -> Tuple[Optional[str], Optional[str]]:
        """Get the renderable entity at a position using cache."""
        self._update_entity_cache()
        return self.entity_position_cache.get((world_x, world_y), (None, None))
    
    def invalidate_cache(self) -> None:
        """Mark the entity cache as dirty."""
        self.cache_dirty = True
    
    def _update_entity_cache(self) -> None:
        """Update the entity position cache for fast lookups."""
        if not self.cache_dirty:
            return
            
        self.entity_position_cache.clear()
        entities = self.world.get_entities_with_components(Position, Renderable)
        
        # Group entities by position
        position_entities = {}
        
        for entity_id in entities:
            position = self.world.get_component(entity_id, Position)
            renderable = self.world.get_component(entity_id, Renderable)
            
            if position and renderable:
                pos_key = (position.x, position.y)
                if pos_key not in position_entities:
                    position_entities[pos_key] = []
                position_entities[pos_key].append((entity_id, renderable.char, renderable.color))
        
        # Process each position
        for pos_key, entities_at_pos in position_entities.items():
            # Categorize entities by priority
            player_entity = None
            character_entities = []  # NPCs/monsters with AI
            corpse_entities = []     # Corpses
            item_entities = []       # Regular items
            other_entities = []
            
            for entity_id, char, color in entities_at_pos:
                if self.world.has_component(entity_id, Player):
                    player_entity = (entity_id, char, color)
                elif self.world.has_component(entity_id, AI):
                    character_entities.append((entity_id, char, color))
                elif self.world.has_component(entity_id, Corpse):
                    corpse_entities.append((entity_id, char, color))
                elif self.world.has_component(entity_id, Pickupable):
                    item_entities.append((entity_id, char, color))
                else:
                    other_entities.append((entity_id, char, color))
            
            # Count total pickupable entities (corpses + items)
            total_pickupable = len(corpse_entities) + len(item_entities)
            has_corpses = len(corpse_entities) > 0
            
            # Determine what to display based on priority:
            # 1. Player (highest priority)
            # 2. Character entities (NPCs/monsters)
            # 3. Corpses (between NPCs and items)
            # 4. Multiple pickupable entities (show '%' - red if corpses present)
            # 5. Single pickupable entity
            # 6. Other entities
            if player_entity:
                # Player takes highest priority
                self.entity_position_cache[pos_key] = (player_entity[1], player_entity[2])
            elif character_entities:
                # Character entities (NPCs/monsters) take priority over corpses and items
                self.entity_position_cache[pos_key] = (character_entities[0][1], character_entities[0][2])
            elif total_pickupable > 1:
                # Multiple pickupable entities - show red '%' if corpses present, white '%' otherwise
                stack_color = 'red' if has_corpses else 'white'
                self.entity_position_cache[pos_key] = ('%', stack_color)
            elif len(corpse_entities) == 1 and len(item_entities) == 0:
                # Single corpse, no items
                self.entity_position_cache[pos_key] = (corpse_entities[0][1], corpse_entities[0][2])
            elif len(item_entities) == 1 and len(corpse_entities) == 0:
                # Single item, no corpses
                self.entity_position_cache[pos_key] = (item_entities[0][1], item_entities[0][2])
            elif other_entities:
                # Other entities (lowest priority)
                self.entity_position_cache[pos_key] = (other_entities[0][1], other_entities[0][2])
        
        self.cache_dirty = False
