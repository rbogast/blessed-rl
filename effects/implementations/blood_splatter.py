"""
Blood splatter effect implementation.
"""

import random
from typing import Any


class BloodSplatterEffect:
    """An effect that splatters blood on nearby tiles based on a power level."""
    
    def __init__(self, level: int = 1):
        """
        Initialize the blood splatter effect with a power level.
        
        Args:
            level (int): The power level of the effect, from 1 to 9. 
                         Determines how many nearby tiles are affected (1 to 8 tiles).
        """
        self.level = max(1, min(level, 9))  # Clamp level between 1 and 9
    
    def trigger(self, x: int, y: int, game_state: Any, world_generator: Any) -> None:
        """
        Trigger the blood splatter effect at the specified coordinates.
        Randomly selects up to `level` nearby tiles to add to the current level's blood_tiles.
        
        Args:
            x (int): The x-coordinate where the effect is triggered.
            y (int): The y-coordinate where the effect is triggered.
            game_state (Any): The game state instance (unused, kept for compatibility).
            world_generator (Any): The world generator to check map boundaries and add blood tiles.
        """
        # Select up to `level` adjacent tiles to splatter (excluding center tile)
        nearby = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                  if not (dx == 0 and dy == 0)]
        random.shuffle(nearby)
        splatter_tiles = nearby[:self.level]
        
        # Add valid coordinates to the current level's blood_tiles
        for tile_x, tile_y in splatter_tiles:
            # Check if the tile exists and is valid
            tile = world_generator.get_tile_at(tile_x, tile_y)
            if tile:  # Allow blood on both floor and wall tiles
                world_generator.add_blood_tile(tile_x, tile_y)
