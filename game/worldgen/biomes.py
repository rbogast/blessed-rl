"""
Biome system with plugin-based generation layers.
"""

from typing import List, Dict, Any, Type
from abc import ABC, abstractmethod
import random
from .core import GenLayer, GenContext, Tile


class Biome(ABC):
    """Base class for biomes."""
    
    name: str = "unknown"
    
    def __init__(self):
        self.layers: List[GenLayer] = []
        self._setup_layers()
    
    @abstractmethod
    def _setup_layers(self) -> None:
        """Set up the generation layers for this biome."""
        pass
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Generate terrain using all layers in sequence."""
        for layer in self.layers:
            layer.generate(tiles, ctx)


class BiomeRegistry:
    """Registry for biome plugins."""
    
    def __init__(self):
        self._biomes: Dict[str, Biome] = {}
        self._register_default_biomes()
    
    def register(self, biome: Biome) -> None:
        """Register a biome."""
        self._biomes[biome.name] = biome
    
    def get(self, name: str) -> Biome:
        """Get a biome by name."""
        return self._biomes.get(name, self._biomes.get('default'))
    
    def list_biomes(self) -> List[str]:
        """List all registered biome names."""
        return list(self._biomes.keys())
    
    def _register_default_biomes(self) -> None:
        """Register default biomes."""
        self.register(DefaultBiome())
        self.register(ForestBiome())
        self.register(GraveyardBiome())
        self.register(DungeonBiome())


# Generation Layers
class NoiseLayer:
    """Basic noise generation layer."""
    
    def __init__(self, wall_probability: float = 0.45):
        self.wall_probability = wall_probability
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Fill with random noise."""
        wall_prob = ctx.get_param('wall_probability', self.wall_probability)
        
        for row in tiles:
            for tile in row:
                tile.is_wall = ctx.rng.random() < wall_prob
                tile.tile_type = 'wall' if tile.is_wall else 'floor'


class CellularAutomataLayer:
    """Cellular automata smoothing layer."""
    
    def __init__(self, iterations: int = 5, birth_limit: int = 4, death_limit: int = 3):
        self.iterations = iterations
        self.birth_limit = birth_limit
        self.death_limit = death_limit
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Apply cellular automata smoothing."""
        iterations = ctx.get_param('ca_iterations', self.iterations)
        
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        for _ in range(int(iterations)):
            new_tiles = [[None for _ in range(width)] for _ in range(height)]
            
            for y in range(height):
                for x in range(width):
                    wall_count = self._count_walls(tiles, x, y, width, height)
                    
                    if tiles[y][x].is_wall:
                        new_tiles[y][x] = wall_count >= self.death_limit
                    else:
                        new_tiles[y][x] = wall_count > self.birth_limit
            
            # Apply changes
            for y in range(height):
                for x in range(width):
                    tiles[y][x].is_wall = new_tiles[y][x]
                    tiles[y][x].tile_type = 'wall' if new_tiles[y][x] else 'floor'
    
    def _count_walls(self, tiles: List[List[Tile]], x: int, y: int, width: int, height: int) -> int:
        """Count walls in 3x3 neighborhood."""
        count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = x + dx, y + dy
                
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    count += 1  # Treat out-of-bounds as walls
                elif tiles[ny][nx].is_wall:
                    count += 1
        
        return count


class BorderWallLayer:
    """Forces walls on specified rows to create canyon-like boundaries."""
    
    def __init__(self, border_rows: List[int] = None):
        self.border_rows = border_rows or [0, 22]  # Default to top and bottom
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Force walls on specified rows."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        halo_size = ctx.config.halo_size
        
        # Get border rows from parameters or use defaults
        border_rows = ctx.get_param('border_rows', self.border_rows)
        
        # Apply to the full tile area (including halo for seamless borders)
        for y in range(height):
            # Convert from halo coordinates to core coordinates for checking
            core_y = y - halo_size
            
            if core_y in border_rows:
                for x in range(width):
                    tiles[y][x].is_wall = True
                    tiles[y][x].tile_type = 'wall'


class ConnectivityLayer:
    """Ensures east-west connectivity."""
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Create a path from west to east edge."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        halo_size = ctx.config.halo_size
        
        # Work within the core area (excluding halo)
        core_width = width - 2 * halo_size
        core_height = height - 2 * halo_size
        
        if core_width <= 0 or core_height <= 0:
            return
        
        # Find or create entrance on west edge
        west_x = halo_size
        west_y = self._find_or_create_entrance(tiles, west_x, halo_size, core_height, ctx.rng)
        
        # Find or create exit on east edge
        east_x = halo_size + core_width - 1
        east_y = self._find_or_create_entrance(tiles, east_x, halo_size, core_height, ctx.rng)
        
        # Create path between them
        self._create_path(tiles, (west_x, west_y), (east_x, east_y), ctx.rng)
    
    def _find_or_create_entrance(self, tiles: List[List[Tile]], x: int, y_start: int, height: int, rng: random.Random) -> int:
        """Find or create an entrance at the specified x coordinate."""
        # Look for existing opening
        for offset in range(height):
            y = y_start + offset
            if not tiles[y][x].is_wall:
                return y
        
        # Create opening in random position (avoid very edges)
        y = y_start + rng.randint(2, height - 3)
        tiles[y][x].is_wall = False
        tiles[y][x].tile_type = 'floor'
        return y
    
    def _create_path(self, tiles: List[List[Tile]], start: tuple, end: tuple, rng: random.Random) -> None:
        """Create a winding path between two points."""
        x1, y1 = start
        x2, y2 = end
        current_x, current_y = x1, y1
        
        while current_x != x2 or current_y != y2:
            # Clear current position
            tiles[current_y][current_x].is_wall = False
            tiles[current_y][current_x].tile_type = 'floor'
            
            # Choose direction with bias toward target
            if current_x < x2 and rng.random() < 0.7:
                current_x += 1
            elif current_x > x2 and rng.random() < 0.7:
                current_x -= 1
            elif current_y < y2 and rng.random() < 0.5:
                current_y += 1
            elif current_y > y2 and rng.random() < 0.5:
                current_y -= 1
            else:
                # Random movement
                direction = rng.choice(['north', 'south', 'east', 'west'])
                if direction == 'north' and current_y > 0:
                    current_y -= 1
                elif direction == 'south' and current_y < len(tiles) - 1:
                    current_y += 1
                elif direction == 'east' and current_x < len(tiles[0]) - 1:
                    current_x += 1
                elif direction == 'west' and current_x > 0:
                    current_x -= 1


class TreeScatterLayer:
    """Scatters trees on floor tiles using cellular automata for natural clustering."""
    
    def __init__(self, tree_type: str = 'pine_tree', density: float = 0.3, cluster_iterations: int = 1):
        self.tree_type = tree_type
        self.density = density
        self.cluster_iterations = cluster_iterations
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Place trees on floor tiles with natural clustering."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        # Get parameters from context
        tree_density = ctx.get_param('tree_density', self.density)
        tree_type = ctx.get_param('tree_type', self.tree_type)
        cluster_iterations = ctx.get_param('tree_cluster_iterations', self.cluster_iterations)
        
        # First pass: randomly place tree seeds on floor tiles
        tree_map = [[False for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                tile = tiles[y][x]
                # Only place trees on floor tiles
                if not tile.is_wall and ctx.rng.random() < tree_density:
                    tree_map[y][x] = True
        
        # Apply clustering iterations using cellular automata
        for _ in range(int(cluster_iterations)):
            new_tree_map = [[False for _ in range(width)] for _ in range(height)]
            
            for y in range(height):
                for x in range(width):
                    tile = tiles[y][x]
                    # Only consider floor tiles
                    if tile.is_wall:
                        continue
                    
                    tree_neighbors = self._count_tree_neighbors(tree_map, x, y, width, height)
                    
                    if tree_map[y][x]:
                        # Tree survives if it has at least 1 tree neighbor
                        new_tree_map[y][x] = tree_neighbors >= 1
                    else:
                        # Floor becomes tree if it has 3+ tree neighbors (creates small clusters)
                        new_tree_map[y][x] = tree_neighbors >= 3
            
            tree_map = new_tree_map
        
        # Apply trees to tiles
        for y in range(height):
            for x in range(width):
                if tree_map[y][x]:
                    tiles[y][x].tile_type = tree_type
                    # Trees block movement and vision like walls
                    tiles[y][x].is_wall = True
    
    def _count_tree_neighbors(self, tree_map: List[List[bool]], x: int, y: int, width: int, height: int) -> int:
        """Count trees in 3x3 neighborhood."""
        count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue  # Don't count self
                
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < width and 0 <= ny < height:
                    if tree_map[ny][nx]:
                        count += 1
        
        return count


class SparseTreeLayer:
    """Scatters a fixed number of trees randomly across the chunk."""
    
    def __init__(self, tree_type: str = 'oak_tree', count: int = 10):
        self.tree_type = tree_type
        self.count = count
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Place a fixed number of trees randomly on floor tiles."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        # Get parameters from context
        tree_count = ctx.get_param('sparse_tree_count', self.count)
        tree_type = ctx.get_param('sparse_tree_type', self.tree_type)
        
        # Find all available floor positions
        floor_positions = []
        for y in range(height):
            for x in range(width):
                tile = tiles[y][x]
                if not tile.is_wall:
                    floor_positions.append((x, y))
        
        # If we don't have enough floor tiles, place as many as we can
        actual_count = min(tree_count, len(floor_positions))
        
        # Randomly select positions for trees
        if floor_positions:
            selected_positions = ctx.rng.sample(floor_positions, actual_count)
            
            for x, y in selected_positions:
                tiles[y][x].tile_type = tree_type
                tiles[y][x].is_wall = True


# Biome Implementations
class DefaultBiome(Biome):
    """Simple default biome for testing."""
    
    name = "default"
    
    def _setup_layers(self) -> None:
        self.layers = [
            NoiseLayer(wall_probability=0.45),
            CellularAutomataLayer(iterations=3),
            ConnectivityLayer()
        ]


class ForestBiome(Biome):
    """Forest biome with more open areas."""
    
    name = "forest"
    
    def _setup_layers(self) -> None:
        self.layers = [
            NoiseLayer(wall_probability=0.35),
            BorderWallLayer(),  # Add canyon walls before CA smoothing
            CellularAutomataLayer(iterations=2),
            ConnectivityLayer(),
            TreeScatterLayer(tree_type='pine_tree', density=0.4, cluster_iterations=1),
            SparseTreeLayer(tree_type='oak_tree', count=15)
        ]


class GraveyardBiome(Biome):
    """Graveyard biome with moderate density."""
    
    name = "graveyard"
    
    def _setup_layers(self) -> None:
        self.layers = [
            NoiseLayer(wall_probability=0.45),
            CellularAutomataLayer(iterations=4),
            ConnectivityLayer()
        ]


class DungeonBiome(Biome):
    """Dense dungeon biome."""
    
    name = "dungeon"
    
    def _setup_layers(self) -> None:
        self.layers = [
            NoiseLayer(wall_probability=0.55),
            CellularAutomataLayer(iterations=5),
            ConnectivityLayer()
        ]


# Global registry instance
_registry = BiomeRegistry()


def get_biome(name: str) -> Biome:
    """Get a biome by name from the global registry."""
    return _registry.get(name)


def register_biome(biome: Biome) -> None:
    """Register a biome in the global registry."""
    _registry.register(biome)


def list_biomes() -> List[str]:
    """List all registered biome names."""
    return _registry.list_biomes()
