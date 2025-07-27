"""
Graveyard template with moderate density.
"""

from typing import Dict
from .base import MapTemplate, ParameterDef
from ..layers import NoiseLayer, CellularAutomataLayer, ConnectivityLayer


class GraveyardTemplate(MapTemplate):
    """Graveyard template with moderate density."""
    
    name = "graveyard"
    
    def get_parameters(self) -> Dict[str, ParameterDef]:
        """Return the parameters this template exposes for editing."""
        return {
            'wall_probability': ParameterDef(float, 0.0, 1.0, 0.45),
            'ca_iterations': ParameterDef(int, 0, 10, 4),
        }
    
    def _setup_layers(self) -> None:
        """Set up the generation layers for graveyard generation."""
        self.layers = [
            NoiseLayer(wall_probability=0.45),
            CellularAutomataLayer(iterations=4),
            ConnectivityLayer()
        ]
