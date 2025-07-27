"""
Modular world generation system for the ECS Roguelike Engine.

This package provides a plugin-based world generation system that supports:
- Biome-based generation with configurable parameters
- Layer-based generation pipeline
- Scheduler-driven content progression
- Seamless chunk generation with halos
"""

from .core import Tile, Chunk
from .scheduler import WorldScheduler
# Removed old biome registry - now using template system

__all__ = ['Tile', 'Chunk', 'WorldScheduler']
