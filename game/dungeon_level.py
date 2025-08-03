"""
Dungeon level management for the roguelike.
"""

from typing import List, Set, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from game.worldgen.core import Tile


@dataclass
class DungeonLevel:
    """Represents a single dungeon level with all its data."""
    
    level_id: int
    width: int
    height: int
    tiles: List[List[Tile]] = field(default_factory=list)
    entities: List[int] = field(default_factory=list)
    blood_tiles: Set[Tuple[int, int]] = field(default_factory=set)
    stairs_down: Optional[Tuple[int, int]] = None
    stairs_up: Optional[Tuple[int, int]] = None
    entity_data: List[Dict[str, Any]] = field(default_factory=list)  # Serialized entity data
    
    def __post_init__(self):
        """Initialize tiles if not provided."""
        if not self.tiles:
            self.tiles = []
            for y in range(self.height):
                row = []
                for x in range(self.width):
                    row.append(Tile(x, y, is_wall=True))  # Start with walls for maze generation
                self.tiles.append(row)
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Get a tile at the specified coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return None
    
    def is_wall(self, x: int, y: int) -> bool:
        """Check if a position is a wall."""
        tile = self.get_tile(x, y)
        return tile is None or tile.is_wall
    
    def add_entity(self, entity_id: int) -> None:
        """Add an entity to this level."""
        if entity_id not in self.entities:
            self.entities.append(entity_id)
    
    def remove_entity(self, entity_id: int) -> None:
        """Remove an entity from this level."""
        if entity_id in self.entities:
            self.entities.remove(entity_id)
    
    def has_stairs_down(self) -> bool:
        """Check if this level has downward stairs."""
        return self.stairs_down is not None
    
    def has_stairs_up(self) -> bool:
        """Check if this level has upward stairs."""
        return self.stairs_up is not None
    
    def get_stairs_down_pos(self) -> Optional[Tuple[int, int]]:
        """Get the position of downward stairs."""
        return self.stairs_down
    
    def get_stairs_up_pos(self) -> Optional[Tuple[int, int]]:
        """Get the position of upward stairs."""
        return self.stairs_up
    
    def set_stairs_down(self, x: int, y: int) -> None:
        """Set the position of downward stairs."""
        self.stairs_down = (x, y)
        # Mark the tile as stairs
        tile = self.get_tile(x, y)
        if tile:
            tile.tile_type = 'stairs_down'
            tile.properties['stairs'] = 'down'
    
    def set_stairs_up(self, x: int, y: int) -> None:
        """Set the position of upward stairs."""
        self.stairs_up = (x, y)
        # Mark the tile as stairs
        tile = self.get_tile(x, y)
        if tile:
            tile.tile_type = 'stairs_up'
            tile.properties['stairs'] = 'up'
    
    def is_stairs_at(self, x: int, y: int) -> Optional[str]:
        """Check if there are stairs at the given position. Returns 'up', 'down', or None."""
        if self.stairs_up and self.stairs_up == (x, y):
            return 'up'
        if self.stairs_down and self.stairs_down == (x, y):
            return 'down'
        return None
    
    def validate_stair_connection(self, other_level: 'DungeonLevel', direction: str) -> bool:
        """Validate that stairs connect properly between this level and another.
        
        Args:
            other_level: The other level to check connection with
            direction: 'down' if other_level is below this one, 'up' if above
        
        Returns:
            True if stairs are properly connected, False otherwise
        """
        if direction == 'down':
            # This level's down stairs should match other level's up stairs
            return (self.stairs_down is not None and 
                    other_level.stairs_up is not None and
                    self.stairs_down == other_level.stairs_up)
        elif direction == 'up':
            # This level's up stairs should match other level's down stairs
            return (self.stairs_up is not None and 
                    other_level.stairs_down is not None and
                    self.stairs_up == other_level.stairs_down)
        return False
    
    def save_entity_data(self, world) -> List[Dict[str, Any]]:
        """Save entity data for all entities on this level (without preserving entity IDs)."""
        entity_data = []
        
        for entity_id in self.entities:
            if world.entities.is_alive(entity_id):
                # Get all components for this entity
                components = {}
                for component_type, component_dict in world.components._components.items():
                    if entity_id in component_dict:
                        component = component_dict[entity_id]
                        # Store component data as a dictionary
                        components[component_type.__name__] = component.__dict__.copy()
                
                # Store components without the entity ID
                entity_data.append(components)
        
        return entity_data
    
    def restore_entity_data(self, world, entity_data: List[Dict[str, Any]]) -> None:
        """Restore entity data for this level with fresh entity IDs."""
        # Import component classes
        from components.core import Position, Renderable, Player, Blocking, Visible, Door
        from components.combat import Health, Stats
        from components.character import CharacterAttributes, Experience, XPValue
        from components.effects import Physics
        from components.items import Inventory, EquipmentSlots, Item, Equipment, Consumable, Pickupable, Throwable
        from components.corpse import Race, Corpse
        from components.skills import Skills
        from components.ai import AI
        from components.throwing import ThrowingCursor, ThrownObject
        
        # Map component names to classes
        component_classes = {
            'Position': Position,
            'Renderable': Renderable,
            'Player': Player,
            'Blocking': Blocking,
            'Visible': Visible,
            'Door': Door,
            'Health': Health,
            'Stats': Stats,
            'CharacterAttributes': CharacterAttributes,
            'Experience': Experience,
            'XPValue': XPValue,
            'Physics': Physics,
            'Inventory': Inventory,
            'EquipmentSlots': EquipmentSlots,
            'Item': Item,
            'Equipment': Equipment,
            'Consumable': Consumable,
            'Pickupable': Pickupable,
            'Throwable': Throwable,
            'Race': Race,
            'Corpse': Corpse,
            'Skills': Skills,
            'AI': AI,
            'ThrowingCursor': ThrowingCursor,
            'ThrownObject': ThrownObject,
        }
        
        # First pass: Create all entities and build ID mapping
        entity_id_mapping = {}
        new_entities = []
        
        for i, components in enumerate(entity_data):
            new_entity_id = world.create_entity()
            new_entities.append((new_entity_id, components))
            # We'll use the index as a temporary identifier for mapping
            entity_id_mapping[i] = new_entity_id
        
        # Second pass: Restore components with updated references
        for new_entity_id, components in new_entities:
            # Handle entity reference updates in components
            updated_components = self._update_entity_references(components, entity_id_mapping, entity_data)
            
            # Restore all components with updated references
            for component_name, component_data in updated_components.items():
                if component_name in component_classes:
                    component_class = component_classes[component_name]
                    
                    # Create component instance and restore its data
                    component = component_class.__new__(component_class)
                    component.__dict__.update(component_data)
                    
                    # Add component to world
                    world.components.add_component(new_entity_id, component)
            
            # Add entity to this level's entity list
            self.entities.append(new_entity_id)
    
    def _update_entity_references(self, components: Dict[str, Any], entity_id_mapping: Dict[int, int], all_entity_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update entity references in component data to use new entity IDs."""
        updated_components = {}
        
        for component_name, component_data in components.items():
            updated_data = component_data.copy()
            
            # Handle Inventory component - update item entity IDs
            if component_name == 'Inventory' and 'items' in updated_data:
                updated_items = []
                for old_item_id in updated_data['items']:
                    # Find the item entity in the saved data and map to new ID
                    new_item_id = self._find_and_map_item_entity(old_item_id, entity_id_mapping, all_entity_data)
                    if new_item_id is not None:
                        updated_items.append(new_item_id)
                updated_data['items'] = updated_items
            
            # Handle EquipmentSlots component - update equipped item entity IDs
            elif component_name == 'EquipmentSlots':
                for slot_name in ['weapon', 'armor', 'accessory']:
                    if slot_name in updated_data and updated_data[slot_name] is not None:
                        old_item_id = updated_data[slot_name]
                        # Find the item entity in the saved data and map to new ID
                        new_item_id = self._find_and_map_item_entity(old_item_id, entity_id_mapping, all_entity_data)
                        updated_data[slot_name] = new_item_id
            
            updated_components[component_name] = updated_data
        
        return updated_components
    
    def _find_and_map_item_entity(self, old_item_id: int, entity_id_mapping: Dict[int, int], all_entity_data: List[Dict[str, Any]]) -> Optional[int]:
        """Find an item entity in the saved data and return its new mapped ID."""
        # Find the item in the saved entity data by matching its properties
        for i, entity_components in enumerate(all_entity_data):
            if 'Item' in entity_components:
                # This is an item entity, check if it matches what we're looking for
                # We'll use the index in the entity_data list to map to the new entity ID
                if i in entity_id_mapping:
                    return entity_id_mapping[i]
        
        # If we can't find a mapping, return None (item will be lost)
        return None
    
    def has_persistence_artifact(self, world) -> bool:
        """Check if this level contains a persistence artifact."""
        from components.items import Item
        
        # Check live entities first
        for entity_id in self.entities:
            if world.entities.is_alive(entity_id):
                item = world.get_component(entity_id, Item)
                if item and hasattr(item, 'special') and item.special == 'persistence':
                    return True
        
        # Check saved entity data for persistence artifacts
        for entity_components in self.entity_data:
            if 'Item' in entity_components:
                item_data = entity_components['Item']
                if item_data.get('special') == 'persistence':
                    return True
        
        return False
    
    def find_persistence_artifacts(self, world) -> List[int]:
        """Find all persistence artifact entities on this level."""
        from components.items import Item
        
        artifacts = []
        for entity_id in self.entities:
            if world.entities.is_alive(entity_id):
                item = world.get_component(entity_id, Item)
                if item and hasattr(item, 'special') and item.special == 'persistence':
                    artifacts.append(entity_id)
        return artifacts


class DungeonManager:
    """Manages all dungeon levels and level transitions."""
    
    def __init__(self, persistent_levels: bool = True):
        self.levels: Dict[int, DungeonLevel] = {}
        self.current_level_id: int = 0
        self.persistent_levels = persistent_levels
    
    def get_level(self, level_id: int) -> Optional[DungeonLevel]:
        """Get a level by ID, returning None if it doesn't exist."""
        return self.levels.get(level_id)
    
    def has_level(self, level_id: int) -> bool:
        """Check if a level exists in memory."""
        return level_id in self.levels
    
    def add_level(self, level: DungeonLevel) -> None:
        """Add a level to the manager."""
        self.levels[level.level_id] = level
    
    def remove_level(self, level_id: int) -> None:
        """Remove a level from memory."""
        if level_id in self.levels:
            del self.levels[level_id]
    
    def get_current_level(self) -> Optional[DungeonLevel]:
        """Get the current level."""
        return self.get_level(self.current_level_id)
    
    def set_current_level(self, level_id: int) -> None:
        """Set the current level ID."""
        self.current_level_id = level_id
    
    def change_level(self, new_level_id: int, old_level_id: Optional[int] = None, world=None) -> None:
        """Change to a new level, optionally cleaning up the old level."""
        if old_level_id is not None and not self.persistent_levels and world is not None:
            # Check if old level has persistence artifact before removing
            old_level = self.get_level(old_level_id)
            if old_level and not old_level.has_persistence_artifact(world):
                # Remove old level from memory if not persistent and no artifact
                self.remove_level(old_level_id)
        
        self.current_level_id = new_level_id
    
    def should_persist_level(self, level_id: int, world) -> bool:
        """Check if a level should be persisted based on artifacts."""
        if self.persistent_levels:
            return True
        
        level = self.get_level(level_id)
        if level:
            return level.has_persistence_artifact(world)
        
        return False
    
    def cleanup_distant_levels(self, current_level_id: int, keep_range: int = 2) -> None:
        """Remove levels that are far from the current level (for memory management)."""
        if self.persistent_levels:
            return  # Don't cleanup if levels are persistent
        
        levels_to_remove = []
        for level_id in self.levels.keys():
            if abs(level_id - current_level_id) > keep_range:
                levels_to_remove.append(level_id)
        
        for level_id in levels_to_remove:
            self.remove_level(level_id)
    
    def get_level_count(self) -> int:
        """Get the number of levels currently in memory."""
        return len(self.levels)
    
    def clear_all_levels(self) -> None:
        """Clear all levels from memory."""
        self.levels.clear()
        self.current_level_id = 0
