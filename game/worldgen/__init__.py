"""
World generation system for blessed-rl.

Features:
- Biome-based generation with configurable templates
- Layered generation system for composable effects
- Scheduling system for progressive world changes
- Level-based generation for dungeon exploration
"""

from .core import Tile, Chunk
from .scheduler import WorldScheduler
# Removed old biome registry - now using template system

__all__ = ['Tile', 'Chunk', 'WorldScheduler']
