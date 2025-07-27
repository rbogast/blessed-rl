"""
Maze template using Recursive Backtracking algorithm.
"""

from typing import Dict
from .base import MapTemplate, ParameterDef
from ..layers import RecursiveBacktrackingLayer, MazeInterconnectionLayer, MazeBorderLayer


class MazeTemplate(MapTemplate):
    """
    Maze template using Recursive Backtracking algorithm.
    
    Creates a perfect maze where:
    - Even coordinates are walls
    - Odd coordinates are corridors
    - Full border of walls
    - Exactly one path between any two points
    - Stairs are placed at dead ends for optimal gameplay
    """
    
    name = "maze"
    
    def get_parameters(self) -> Dict[str, ParameterDef]:
        """Return the parameters this template exposes for editing."""
        return {
            'maze_openings': ParameterDef(int, 0, 20, 5),
        }
    
    def _setup_layers(self) -> None:
        """Set up the generation layers for maze generation."""
        self.layers = [
            RecursiveBacktrackingLayer(),
            MazeInterconnectionLayer(),  # Add interconnections for tactical options
            MazeBorderLayer(),  # Ensure border integrity
        ]
