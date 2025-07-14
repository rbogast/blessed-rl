"""
Prefab loader for reading and parsing prefab definitions from YAML files.
"""

import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PrefabDefinition:
    """Represents a loaded prefab definition."""
    id: str
    name: str
    description: str
    width: int
    height: int
    spawn_chance: float
    min_distance_from_edge: int
    layout: List[str]  # Each string is a row
    legend: Dict[str, str]  # Character -> tile type mapping


class PrefabLoader:
    """Loads prefab definitions from YAML files."""
    
    def __init__(self, prefab_file: str = 'data/prefabs.yaml'):
        self.prefab_file = prefab_file
        self.prefabs: Dict[str, PrefabDefinition] = {}
        self._load_prefabs()
    
    def _load_prefabs(self) -> None:
        """Load all prefab definitions from the YAML file."""
        try:
            with open(self.prefab_file, 'r') as f:
                data = yaml.safe_load(f)
            
            if 'prefabs' not in data:
                print(f"Warning: No 'prefabs' section found in {self.prefab_file}")
                return
            
            for prefab_id, prefab_data in data['prefabs'].items():
                try:
                    prefab = self._parse_prefab(prefab_id, prefab_data)
                    self.prefabs[prefab_id] = prefab
                except Exception as e:
                    print(f"Error loading prefab '{prefab_id}': {e}")
            
            print(f"Loaded {len(self.prefabs)} prefabs from {self.prefab_file}")
        
        except FileNotFoundError:
            print(f"Prefab file {self.prefab_file} not found")
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {self.prefab_file}: {e}")
    
    def _parse_prefab(self, prefab_id: str, data: Dict[str, Any]) -> PrefabDefinition:
        """Parse a single prefab definition."""
        # Parse layout string into rows
        layout_str = data.get('layout', '').strip()
        layout_rows = [row for row in layout_str.split('\n') if row.strip()]
        
        # Validate dimensions
        if not layout_rows:
            raise ValueError("Layout cannot be empty")
        
        actual_height = len(layout_rows)
        actual_width = max(len(row) for row in layout_rows) if layout_rows else 0
        
        expected_width = data.get('width', actual_width)
        expected_height = data.get('height', actual_height)
        
        if actual_width != expected_width or actual_height != expected_height:
            print(f"Warning: Prefab '{prefab_id}' dimensions mismatch. "
                  f"Expected {expected_width}x{expected_height}, got {actual_width}x{actual_height}")
        
        # Pad rows to consistent width
        padded_rows = []
        for row in layout_rows:
            if len(row) < expected_width:
                row += ' ' * (expected_width - len(row))
            padded_rows.append(row[:expected_width])  # Truncate if too long
        
        return PrefabDefinition(
            id=prefab_id,
            name=data.get('name', prefab_id),
            description=data.get('description', ''),
            width=expected_width,
            height=expected_height,
            spawn_chance=data.get('spawn_chance', 0.1),
            min_distance_from_edge=data.get('min_distance_from_edge', 1),
            layout=padded_rows,
            legend=data.get('legend', {})
        )
    
    def get_prefab(self, prefab_id: str) -> Optional[PrefabDefinition]:
        """Get a prefab definition by ID."""
        return self.prefabs.get(prefab_id)
    
    def get_all_prefabs(self) -> Dict[str, PrefabDefinition]:
        """Get all loaded prefab definitions."""
        return self.prefabs.copy()
    
    def list_prefab_ids(self) -> List[str]:
        """Get a list of all prefab IDs."""
        return list(self.prefabs.keys())
    
    def reload(self) -> None:
        """Reload prefabs from file."""
        self.prefabs.clear()
        self._load_prefabs()
