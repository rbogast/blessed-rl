"""
Rooms template that generates connected rooms starting from a downstairs location.
"""

from typing import Dict
from .base import MapTemplate, ParameterDef
from ..layers import BorderWallLayer
from ..layers.rogue_layers import RoomsLayer


class RoomsTemplate(MapTemplate):
    """
    Rooms template that generates organically connected rooms.
    
    Creates dungeons by:
    - Starting at downstairs location from previous floor (if available) or random location
    - Generating rooms of random sizes within specified bounds
    - Each new room is placed adjacent to an existing room
    - Doors connect adjacent rooms
    - Respects 1-tile border around the entire map
    """
    
    name = "rooms"
    
    def get_parameters(self) -> Dict[str, ParameterDef]:
        """Return the parameters this template exposes for editing."""
        return {
            'num_rooms': ParameterDef(int, 3, 15, 6),
            'min_room_size': ParameterDef(int, 3, 8, 4),
            'max_room_size': ParameterDef(int, 5, 15, 8),
        }
    
    def _setup_layers(self) -> None:
        """Set up the generation layers for rooms generation."""
        self.layers = [
            RoomsLayer(),
            BorderWallLayer(),  # Ensure border integrity
        ]
