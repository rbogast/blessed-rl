"""
Rogue template using the classic room-and-corridor algorithm.
"""

from typing import Dict
from .base import MapTemplate, ParameterDef
from ..layers import BorderWallLayer
from ..layers.rogue_layers import RogueRoomLayer, RogueCorridorLayer, RogueDoorLayer


class RogueTemplate(MapTemplate):
    """
    Rogue template using the classic room-and-corridor algorithm.
    
    Creates dungeons similar to the original Rogue:
    - Divides map into 3x3 grid of potential room areas
    - Randomly places 4-7 rooms in the grid cells
    - Connects rooms with straight or L-shaped corridors
    - Places doors where corridors meet room walls
    - Adapted for 23x45 grid dimensions
    """
    
    name = "rogue"
    
    def get_parameters(self) -> Dict[str, ParameterDef]:
        """Return the parameters this template exposes for editing."""
        return {
            'min_rooms': ParameterDef(int, 4, 8, 5),
            'max_rooms': ParameterDef(int, 5, 9, 7),
            'min_room_size': ParameterDef(int, 3, 6, 4),
            'max_room_size': ParameterDef(int, 6, 12, 8),
            'extra_connections': ParameterDef(int, 0, 3, 1),
        }
    
    def _setup_layers(self) -> None:
        """Set up the generation layers for Rogue-style generation."""
        self.layers = [
            RogueRoomLayer(),
            RogueCorridorLayer(),
            RogueDoorLayer(),
            BorderWallLayer(),  # Ensure border integrity
        ]
