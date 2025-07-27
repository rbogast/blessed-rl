"""
Forest template with trees and open areas.
"""

from typing import Dict
from .base import MapTemplate, ParameterDef
from ..layers import (
    NoiseLayer, CellularAutomataLayer, BorderWallLayer, 
    ConnectivityLayer, TreeScatterLayer, SparseTreeLayer
)


class ForestTemplate(MapTemplate):
    """Forest template with more open areas and trees."""
    
    name = "forest"
    
    def get_parameters(self) -> Dict[str, ParameterDef]:
        """Return the parameters this template exposes for editing."""
        return {
            'wall_probability': ParameterDef(float, 0.0, 1.0, 0.25),
            'ca_iterations': ParameterDef(int, 0, 10, 1),
            'tree_density': ParameterDef(float, 0.0, 1.0, 0.3),
            'tree_count': ParameterDef(int, 0, 50, 12),
        }
    
    def _setup_layers(self) -> None:
        """Set up the generation layers for forest generation."""
        self.layers = [
            NoiseLayer(wall_probability=0.25),  # Much lower wall probability for open areas
            BorderWallLayer(),  # Add canyon walls before CA smoothing
            CellularAutomataLayer(iterations=1, birth_limit=5, death_limit=2),  # Less aggressive CA
            ConnectivityLayer(),
            TreeScatterLayer(tree_type='pine_tree', density=0.3, cluster_iterations=1),
            SparseTreeLayer(tree_type='oak_tree', count=12)
        ]
