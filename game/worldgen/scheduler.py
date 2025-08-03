"""
World scheduler system for managing biome progression and content pacing.
"""

import yaml
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import random
import json


class Curve(ABC):
    """Base class for parameter curves."""
    
    @abstractmethod
    def at(self, x: float) -> float:
        """Evaluate the curve at position x."""
        pass


class LinearCurve(Curve):
    """Linear interpolation between two values."""
    
    def __init__(self, start: float, end: float):
        self.start = start
        self.end = end
    
    def at(self, x: float) -> float:
        """Linear interpolation from start to end over [0, 1]."""
        return self.start + (self.end - self.start) * x


class ConstantCurve(Curve):
    """Constant value curve."""
    
    def __init__(self, value: float):
        self.value = value
    
    def at(self, x: float) -> float:
        return self.value


class NoiseCurve(Curve):
    """Noise-based curve for variation."""
    
    def __init__(self, base: float, amplitude: float, frequency: float = 1.0):
        self.base = base
        self.amplitude = amplitude
        self.frequency = frequency
    
    def at(self, x: float) -> float:
        # Simple noise implementation - in practice you'd use proper noise
        import math
        noise = math.sin(x * self.frequency * 2 * math.pi) * 0.5 + 0.5
        return self.base + (noise - 0.5) * self.amplitude


@dataclass
class Segment:
    """Represents a segment of the world with specific biome and parameters."""
    x0: int
    x1: int
    biome: str
    overrides: Dict[str, Curve] = field(default_factory=dict)
    
    def contains(self, x: int) -> bool:
        """Check if x coordinate is within this segment."""
        if self.x0 == self.x1:
            # Single level segment
            return x == self.x0
        else:
            # Range segment
            return self.x0 <= x < self.x1
    
    def get_progress(self, x: int) -> float:
        """Get progress through segment [0.0, 1.0]."""
        if self.x1 == self.x0:
            return 0.0
        return max(0.0, min(1.0, (x - self.x0) / (self.x1 - self.x0)))


class WorldScheduler:
    """Manages world progression through segments and biomes."""
    
    def __init__(self, schedule_file: str = None):
        self.segments: List[Segment] = []
        self.biome_registry = None
        self.character_data: Dict[str, Any] = {}
        
        if schedule_file:
            self.load_schedule(schedule_file)
        else:
            self._create_default_schedule()
        
        self._load_character_data()
    
    def _create_default_schedule(self) -> None:
        """Create a default schedule for testing."""
        self.segments = [
            Segment(0, 800, 'forest'),
            Segment(800, 1600, 'graveyard', {
                'enemy_density': LinearCurve(0.3, 0.7),
                'wall_probability': ConstantCurve(0.45)
            }),
            Segment(1600, 2400, 'dungeon', {
                'enemy_density': ConstantCurve(0.8),
                'wall_probability': LinearCurve(0.5, 0.6)
            })
        ]
    
    def load_schedule(self, filename: str) -> None:
        """Load schedule from YAML file."""
        self.schedule_filename = filename  # Store filename for reloading
        try:
            with open(filename, 'r') as f:
                # Create a custom loader with curve constructor
                loader = yaml.SafeLoader(f)
                loader.add_constructor('!!curve', curve_constructor)
                data = loader.get_single_data()
            
            self.segments = []
            for segment_data in data:
                overrides = {}
                if 'overrides' in segment_data:
                    for key, curve_data in segment_data['overrides'].items():
                        overrides[key] = self._parse_curve(curve_data)
                
                segment = Segment(
                    x0=segment_data['from'],
                    x1=segment_data['to'],
                    biome=segment_data['biome'],
                    overrides=overrides
                )
                self.segments.append(segment)
        
        except FileNotFoundError:
            print(f"Schedule file {filename} not found, using default schedule")
            self._create_default_schedule()
    
    def reload_schedule(self) -> None:
        """Reload the schedule from the original file."""
        if hasattr(self, 'schedule_filename') and self.schedule_filename:
            self.load_schedule(self.schedule_filename)
    
    def _parse_curve(self, curve_data: Any) -> Curve:
        """Parse curve data from YAML."""
        if isinstance(curve_data, (int, float)):
            return ConstantCurve(float(curve_data))
        elif isinstance(curve_data, dict):
            curve_type = curve_data.get('type', 'constant')
            if curve_type == 'linear':
                return LinearCurve(curve_data['start'], curve_data['end'])
            elif curve_type == 'noise':
                return NoiseCurve(
                    curve_data['base'],
                    curve_data['amplitude'],
                    curve_data.get('frequency', 1.0)
                )
            else:
                return ConstantCurve(curve_data.get('value', 0.0))
        else:
            return ConstantCurve(0.0)
    
    def _load_character_data(self) -> None:
        """Load character definitions from JSON file."""
        try:
            with open('data/characters.json', 'r') as f:
                self.character_data = json.load(f)
        except FileNotFoundError:
            self.character_data = {}
    
    def set_biome_registry(self, registry) -> None:
        """Set the biome registry for biome lookup."""
        self.biome_registry = registry
    
    def segment_at(self, level_id: int) -> Segment:
        """Get the segment containing the given level ID."""
        for segment in self.segments:
            if segment.contains(level_id):
                return segment
        
        # Return last segment if level_id is beyond all segments
        return self.segments[-1] if self.segments else Segment(0, 1000, 'default')
    
    def params_at(self, level_id: int) -> Dict[str, float]:
        """Get evaluated parameters at the given level ID."""
        segment = self.segment_at(level_id)
        progress = segment.get_progress(level_id)
        
        params = {}
        for key, curve in segment.overrides.items():
            params[key] = curve.at(progress)
        
        return params
    
    def get_biome(self, biome_name: str):
        """Get a template instance by name (renamed from biome for compatibility)."""
        # Use the new template system
        from .templates import get_template
        return get_template(biome_name)
    
    def pick_spawns(self, level_id: int, rng: random.Random) -> List[Dict[str, Any]]:
        """Pick character spawns for the given level."""
        segment = self.segment_at(level_id)
        params = self.params_at(level_id)
        
        # Get character density (renamed from enemy_density for compatibility)
        character_density = params.get('enemy_density', 0.3)
        base_count = int(character_density * 5)  # Base spawn count
        spawn_count = max(0, base_count + rng.randint(-1, 2))
        
        spawns = []
        if self.character_data and spawn_count > 0:
            character_types = list(self.character_data.keys())
            for _ in range(spawn_count):
                character_type = rng.choice(character_types)
                character_def = self.character_data[character_type].copy()
                # The species and disposition are already in the character data
                spawns.append(character_def)
        
        return spawns


# YAML constructor for curves
def curve_constructor(loader, node):
    """YAML constructor for !!curve tags."""
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
        return ConstantCurve(float(value))
    elif isinstance(node, yaml.SequenceNode):
        values = loader.construct_sequence(node)
        if len(values) == 2:
            return LinearCurve(float(values[0]), float(values[1]))
        else:
            return ConstantCurve(float(values[0]))
    elif isinstance(node, yaml.MappingNode):
        data = loader.construct_mapping(node)
        curve_type = data.get('type', 'constant')
        if curve_type == 'linear':
            return LinearCurve(data['start'], data['end'])
        elif curve_type == 'noise':
            return NoiseCurve(
                data['base'],
                data['amplitude'],
                data.get('frequency', 1.0)
            )
        else:
            return ConstantCurve(data.get('value', 0.0))
    
    return ConstantCurve(0.0)


# Register the curve constructor
yaml.add_constructor('!!curve', curve_constructor)
