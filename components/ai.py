"""
AI-related components.
"""

from ecs.component import Component
from enum import Enum


class AIType(Enum):
    """Types of AI behavior."""
    AGGRESSIVE = "aggressive"  # Moves toward player when visible
    PATROL = "patrol"         # Moves in patterns, attacks when close
    GUARD = "guard"           # Stays in area, attacks when approached


class AI(Component):
    """AI behavior component for NPCs."""
    
    def __init__(self, ai_type: AIType, detection_range: int = 8):
        self.ai_type = ai_type
        self.detection_range = detection_range
        self.target_entity = None  # Current target (usually player)
        self.last_known_position = None  # Last known position of target
        self.patrol_points = []  # For patrol AI
        self.current_patrol_index = 0
        self.home_position = None  # For guard AI
