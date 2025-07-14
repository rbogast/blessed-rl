"""
Prefab system for spawning predefined structures in the world.
"""

from .loader import PrefabLoader
from .spawner import PrefabSpawner
from .manager import PrefabManager

__all__ = ['PrefabLoader', 'PrefabSpawner', 'PrefabManager']
