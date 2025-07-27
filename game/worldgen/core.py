"""
Core world generation classes and interfaces.
"""

import random
from typing import List, Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from components.core import Position, Renderable, Blocking, Visible
from components.combat import Health, Stats
from components.character import CharacterAttributes, Experience, XPValue
from components.effects import Physics
from components.ai import AI, AIType
from components.corpse import Race
from game.character_stats import calculate_max_hp


@dataclass
class WorldConfig:
    """Configuration for world generation."""
    chunk_width: int = 80
    chunk_height: int = 23
    halo_size: int = 10
    seed: Optional[int] = None


class Tile:
    """Represents a single tile in the world."""
    
    def __init__(self, x: int, y: int, is_wall: bool = False):
        self.x = x
        self.y = y
        self.is_wall = is_wall
        self.visible = False
        self.explored = False
        self.tile_type = 'wall' if is_wall else 'floor'
        self.properties: Dict[str, Any] = {}


class Chunk:
    """Represents a chunk of the world with halo support."""
    
    def __init__(self, chunk_id: int, config: WorldConfig):
        self.chunk_id = chunk_id
        self.config = config
        self.width = config.chunk_width
        self.height = config.chunk_height
        self.halo_size = config.halo_size
        
        # Total size including halo
        self.total_width = self.width + 2 * self.halo_size
        self.total_height = self.height + 2 * self.halo_size
        
        self.tiles: List[List[Tile]] = []
        self.entities: List[int] = []  # Entity IDs in this chunk
        
        # Initialize tiles (including halo)
        for y in range(self.total_height):
            row = []
            for x in range(self.total_width):
                # Calculate global coordinates
                global_x = chunk_id * self.width + (x - self.halo_size)
                global_y = y - self.halo_size
                row.append(Tile(global_x, global_y))
            self.tiles.append(row)
    
    def get_tile(self, local_x: int, local_y: int, include_halo: bool = False) -> Optional[Tile]:
        """Get a tile by local coordinates."""
        if include_halo:
            # Coordinates include halo
            if 0 <= local_x < self.total_width and 0 <= local_y < self.total_height:
                return self.tiles[local_y][local_x]
        else:
            # Coordinates are within the actual chunk (no halo)
            halo_x = local_x + self.halo_size
            halo_y = local_y + self.halo_size
            if 0 <= halo_x < self.total_width and 0 <= halo_y < self.total_height:
                return self.tiles[halo_y][halo_x]
        return None
    
    def is_wall(self, local_x: int, local_y: int, include_halo: bool = False) -> bool:
        """Check if a position is a wall."""
        tile = self.get_tile(local_x, local_y, include_halo)
        return tile is None or tile.is_wall
    
    def get_core_tiles(self) -> List[List[Tile]]:
        """Get only the core tiles (without halo) for final output."""
        core_tiles = []
        for y in range(self.halo_size, self.halo_size + self.height):
            row = []
            for x in range(self.halo_size, self.halo_size + self.width):
                row.append(self.tiles[y][x])
            core_tiles.append(row)
        return core_tiles


@dataclass
class GenContext:
    """Context passed to generation layers."""
    chunk_id: int
    seed: int
    rng: random.Random
    config: WorldConfig
    parameters: Dict[str, Any]
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a parameter value with fallback."""
        return self.parameters.get(key, default)


class GenLayer(Protocol):
    """Interface for generation layers."""
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Generate or modify tiles using the given context."""
        ...


class WorldGenerator:
    """Main world generator that coordinates biomes and scheduling."""
    
    def __init__(self, world, config: WorldConfig = None, scheduler=None):
        self.world = world
        self.config = config or WorldConfig()
        self.scheduler = scheduler
        self.chunks: Dict[int, Chunk] = {}
        
        # Set up master seed
        if self.config.seed is None:
            self.config.seed = random.randint(0, 1000000)
    
    def generate_chunk(self, chunk_id: int) -> Chunk:
        """Generate a new chunk using the scheduler and biome system."""
        if chunk_id in self.chunks:
            return self.chunks[chunk_id]
        
        # Create chunk with halo
        chunk = Chunk(chunk_id, self.config)
        
        # Get generation parameters from scheduler
        if self.scheduler:
            segment = self.scheduler.segment_at(chunk_id * self.config.chunk_width)
            biome = self.scheduler.get_biome(segment.biome)
            parameters = self.scheduler.params_at(chunk_id * self.config.chunk_width)
        else:
            # Fallback to simple generation
            from .templates import get_template
            biome = get_template('forest')  # Use forest as default
            parameters = {}
        
        # Create generation context
        chunk_rng = random.Random(self.config.seed + chunk_id)
        ctx = GenContext(
            chunk_id=chunk_id,
            seed=self.config.seed + chunk_id,
            rng=chunk_rng,
            config=self.config,
            parameters=parameters
        )
        
        # Generate using biome
        biome.generate(chunk.tiles, ctx)
        
        # Extract core tiles (no longer creating wall entities)
        core_tiles = chunk.get_core_tiles()
        
        # Spawn creatures using scheduler
        if self.scheduler:
            self._spawn_creatures(chunk, ctx)
        
        self.chunks[chunk_id] = chunk
        return chunk
    
    
    def _spawn_creatures(self, chunk: Chunk, ctx: GenContext) -> None:
        """Spawn creatures using scheduler."""
        if not self.scheduler:
            return
        
        # Get spawn count and types from scheduler
        spawn_data = self.scheduler.pick_spawns(
            chunk.chunk_id * self.config.chunk_width, 
            ctx.rng
        )
        
        # Find valid spawn positions
        core_tiles = chunk.get_core_tiles()
        valid_positions = []
        for y, row in enumerate(core_tiles):
            for x, tile in enumerate(row):
                if not tile.is_wall:
                    valid_positions.append((x, y))
        
        # Spawn creatures
        for spawn_info in spawn_data:
            if not valid_positions:
                break
            
            local_x, local_y = valid_positions.pop(ctx.rng.randint(0, len(valid_positions) - 1))
            global_x = chunk.chunk_id * self.config.chunk_width + local_x
            
            self._create_creature_entity(spawn_info, global_x, local_y, chunk)
    
    def _create_creature_entity(self, spawn_info: Dict[str, Any], x: int, y: int, chunk: Chunk) -> None:
        """Create a creature entity from spawn info."""
        entity_id = self.world.create_entity()
        
        # Check if spawn_info has new attribute format or old format
        if 'attributes' in spawn_info:
            # New format with attributes
            attrs = spawn_info['attributes']
            creature_attributes = CharacterAttributes(
                strength=attrs['strength'],
                agility=attrs['agility'],
                constitution=attrs['constitution'],
                intelligence=attrs['intelligence'],
                willpower=attrs['willpower'],
                aura=attrs['aura']
            )
            
            # Calculate HP from attributes (enemies are level 1)
            creature_level = 1
            max_hp = calculate_max_hp(creature_attributes, creature_level)
            
            # Add new components
            self.world.add_component(entity_id, creature_attributes)
            self.world.add_component(entity_id, Experience(current_xp=0, level=creature_level))
            self.world.add_component(entity_id, XPValue(spawn_info['xp_value']))
            self.world.add_component(entity_id, Health(max_hp))
        else:
            # Old format fallback - convert to new system
            creature_attributes = CharacterAttributes(
                strength=spawn_info.get('strength', 10),
                agility=spawn_info.get('speed', 100) // 10,  # Convert speed to agility
                constitution=spawn_info.get('defense', 5) * 2,  # Convert defense to constitution
                intelligence=8,
                willpower=8,
                aura=6
            )
            
            # Use old health value or calculate from attributes
            if 'health' in spawn_info:
                max_hp = spawn_info['health']
            else:
                max_hp = calculate_max_hp(creature_attributes, 1)
            
            # Add components with defaults
            self.world.add_component(entity_id, creature_attributes)
            self.world.add_component(entity_id, Experience(current_xp=0, level=1))
            self.world.add_component(entity_id, XPValue(10))  # Default XP value
            self.world.add_component(entity_id, Health(max_hp))
        
        # Add Physics component with weight from spawn data
        weight = spawn_info.get('weight', 150.0)  # Default weight if not specified
        self.world.add_component(entity_id, Physics(mass=weight))
        
        # Add common components
        self.world.add_component(entity_id, Position(x, y))
        self.world.add_component(entity_id, Renderable(spawn_info['char'], spawn_info['color']))
        self.world.add_component(entity_id, AI(AIType(spawn_info['ai_type'])))
        self.world.add_component(entity_id, Blocking())
        self.world.add_component(entity_id, Visible())
        
        # Add Race component - use the race from spawn_info
        race_name = spawn_info.get('race', 'unknown')
        self.world.add_component(entity_id, Race(race_name))
        
        chunk.entities.append(entity_id)
    
    def get_chunk(self, chunk_id: int) -> Chunk:
        """Get a chunk, generating it if necessary."""
        if chunk_id not in self.chunks:
            return self.generate_chunk(chunk_id)
        return self.chunks[chunk_id]
    
    def is_wall_at(self, global_x: int, global_y: int) -> bool:
        """Check if there's a wall at global coordinates."""
        # Check bounds first
        if global_y < 0 or global_y >= self.config.chunk_height:
            return True  # Out of bounds is considered a wall
        
        chunk_id = global_x // self.config.chunk_width
        local_x = global_x % self.config.chunk_width
        local_y = global_y  # Y is already local since chunks are full height
        
        chunk = self.get_chunk(chunk_id)
        return chunk.is_wall(local_x, local_y)
    
    def get_tile_at(self, global_x: int, global_y: int) -> Optional[Tile]:
        """Get tile at global coordinates."""
        # Check bounds first
        if global_y < 0 or global_y >= self.config.chunk_height:
            return None  # Out of bounds
        
        chunk_id = global_x // self.config.chunk_width
        local_x = global_x % self.config.chunk_width
        local_y = global_y  # Y is already local since chunks are full height
        
        chunk = self.get_chunk(chunk_id)
        return chunk.get_tile(local_x, local_y)
    
    @property
    def seed(self) -> int:
        """Get the world seed."""
        return self.config.seed
