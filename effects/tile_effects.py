"""
Tile effects system for handling blood splatter and other tile modifications.
"""

import random
from typing import TYPE_CHECKING
from .core import Effect
from components.effects import TileModification

if TYPE_CHECKING:
    from ecs.world import World


class TileEffectsSystem:
    """Handles tile modifications like blood splatter."""
    
    def __init__(self, world: 'World', message_log):
        self.world = world
        self.message_log = message_log
        self._tile_modification_entity = None
        self._ensure_tile_modification_entity()
    
    def _ensure_tile_modification_entity(self) -> None:
        """Ensure we have a global entity to track tile modifications."""
        if self._tile_modification_entity is None:
            # Create a global entity to hold tile modifications
            self._tile_modification_entity = self.world.create_entity()
            self.world.add_component(self._tile_modification_entity, TileModification())
    
    def get_tile_modification(self) -> TileModification:
        """Get the global tile modification component."""
        self._ensure_tile_modification_entity()
        return self.world.get_component(self._tile_modification_entity, TileModification)
    
    def add_blood_splatter(self, center_x: int, center_y: int, intensity: int, radius: int = 1) -> None:
        """Add blood splatter around a center point."""
        tile_mod = self.get_tile_modification()
        if not tile_mod:
            self.message_log.add_debug("ERROR: No tile modification component found!")
            return
        
        # Add blood to center tile
        tile_mod.add_blood_tile(center_x, center_y, intensity)
        self.message_log.add_debug(f"Added blood to center tile ({center_x}, {center_y}) with intensity {intensity}")
        
        # Add blood to surrounding tiles based on intensity and radius
        tiles_affected = 0
        max_tiles = intensity * 2  # Higher intensity affects more tiles
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue  # Skip center tile (already done)
                
                if tiles_affected >= max_tiles:
                    break
                
                # Chance decreases with distance from center
                distance = max(abs(dx), abs(dy))
                chance = max(0.1, 1.0 - (distance * 0.3))  # 70% at distance 1, 40% at distance 2, etc.
                
                if random.random() < chance:
                    blood_x = center_x + dx
                    blood_y = center_y + dy
                    
                    # Intensity decreases with distance
                    blood_intensity = max(1, intensity - distance)
                    tile_mod.add_blood_tile(blood_x, blood_y, blood_intensity)
                    tiles_affected += 1
                    self.message_log.add_debug(f"Added blood to tile ({blood_x}, {blood_y}) with intensity {blood_intensity}")
        
        # Debug: Show total bloody tiles
        total_bloody = len(tile_mod.get_all_bloody_tiles())
        self.message_log.add_debug(f"Total bloody tiles now: {total_bloody}")
        
        if tiles_affected > 0:
            self.message_log.add_info(f"Blood splatters across {tiles_affected + 1} tiles!")
    
    def is_tile_bloody(self, x: int, y: int) -> bool:
        """Check if a tile is bloody."""
        tile_mod = self.get_tile_modification()
        if tile_mod:
            result = tile_mod.is_bloody(x, y)
            if result:
                print(f"DEBUG: is_tile_bloody({x}, {y}) = True")
            return result
        else:
            print(f"DEBUG: is_tile_bloody({x}, {y}) = False (no tile_mod)")
            return False
    
    def get_blood_intensity(self, x: int, y: int) -> int:
        """Get blood intensity at a tile."""
        tile_mod = self.get_tile_modification()
        return tile_mod.get_blood_intensity(x, y) if tile_mod else 0
    
    def get_all_bloody_tiles(self) -> dict:
        """Get all bloody tiles for rendering."""
        tile_mod = self.get_tile_modification()
        return tile_mod.get_all_bloody_tiles() if tile_mod else {}


class BloodSplatterEffect(Effect):
    """Effect that creates blood splatter on tiles."""
    
    def __init__(self, tile_effects_system: TileEffectsSystem):
        super().__init__("blood_splatter")
        self.tile_effects_system = tile_effects_system
    
    def apply(self, world: 'World', **context) -> None:
        """Apply blood splatter effect."""
        center_x = context.get('center_x', 0)
        center_y = context.get('center_y', 0)
        intensity = context.get('intensity', 1)
        radius = context.get('radius', 1)
        
        self.tile_effects_system.add_blood_splatter(center_x, center_y, intensity, radius)
