"""
Core world generation classes and interfaces.
"""

import random
from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass


@dataclass
class WorldConfig:
    """Configuration for world generation."""
    chunk_width: int = 80
    chunk_height: int = 23
    seed: Optional[int] = None


class Tile:
    """Represents a single tile in the world."""
    
    def __init__(self, x: int, y: int, is_wall: bool = False):
        self.x = x
        self.y = y
        self.is_wall = is_wall
        self.visible = False
        self.explored = False
        self.lit = False  # For lighting system: whether tile is currently lit
        self.penumbra = False  # For lighting system: whether tile is in penumbra (outer light ring)
        self.interesting = False  # For auto-explore: contains items, stairs, etc.
        self.tile_type = 'wall' if is_wall else 'floor'
        self.properties: Dict[str, Any] = {}


@dataclass
class GenContext:
    """Context passed to generation layers."""
    chunk_id: int
    seed: int
    rng: random.Random
    config: WorldConfig
    parameters: Dict[str, Any]
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a parameter value with fallback."""
        return self.parameters.get(key, default)


class GenLayer(Protocol):
    """Interface for generation layers."""
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Generate or modify tiles using the given context."""
        ...
