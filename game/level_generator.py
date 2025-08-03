




















"""
Level-based world generator for dungeon diving roguelike.
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from game.dungeon_level import DungeonLevel
from game.worldgen.core import WorldGenerator as BaseWorldGenerator, WorldConfig, Tile, GenContext
from game.worldgen.scheduler import WorldScheduler
from game.config import GameConfig
from components.core import Position, Renderable, Blocking, Visible
from components.combat import Health
from components.character import CharacterAttributes, Experience, XPValue
from components.effects import Physics
from components.ai import AI, AIType
from components.corpse import Species, Disposition, DispositionType
from game.character_stats import calculate_max_hp
from game.tile_entity_converter import TileEntityConverter


class LevelGenerator:
    """Generates individual dungeon levels."""
    
    def __init__(self, world, scheduler: WorldScheduler = None, seed: int = None):
        self.world = world
        self.scheduler = scheduler
        self.seed = seed or random.randint(0, 1000000)
        
        # Create world config for level generation
        self.config = WorldConfig(
            chunk_width=GameConfig.LEVEL_WIDTH,
            chunk_height=GameConfig.LEVEL_HEIGHT,
            halo_size=0,  # No halo needed for single levels
            seed=self.seed
        )
        
        # Create base generator for biome generation
        self.base_generator = BaseWorldGenerator(world, self.config, scheduler)
    
    def generate_level(self, level_id: int, stairs_up_pos: Optional[Tuple[int, int]] = None, turn_count: int = 0) -> DungeonLevel:
        """Generate a complete dungeon level."""
        # Create the level
        level = DungeonLevel(
            level_id=level_id,
            width=GameConfig.LEVEL_WIDTH,
            height=GameConfig.LEVEL_HEIGHT
        )
        
        # Get generation parameters from scheduler
        if self.scheduler:
            segment = self.scheduler.segment_at(level_id)
            biome = self.scheduler.get_biome(segment.biome)
            parameters = self.scheduler.params_at(level_id)
        else:
            # Fallback to simple generation
            from game.worldgen.templates import get_template
            biome = get_template('forest')  # Use forest as default instead of 'default'
            parameters = {}
        
        # Create generation context with turn-based seed
        level_seed = self.seed + turn_count + (level_id * 1000)  # Include level_id for uniqueness
        level_rng = random.Random(level_seed)
        
        
        # Update the config seed for this generation
        generation_config = WorldConfig(
            chunk_width=self.config.chunk_width,
            chunk_height=self.config.chunk_height,
            halo_size=self.config.halo_size,
            seed=level_seed  # Use the turn-based seed
        )
        
        ctx = GenContext(
            chunk_id=level_id,  # Use level_id as chunk_id
            seed=level_seed,
            rng=level_rng,
            config=generation_config,  # Use the updated config
            parameters=parameters
        )
        
        # Check if this is a maze biome that handles its own stair placement
        if hasattr(biome, 'generate_with_stairs') and biome.name.lower() == 'maze':
            # Maze biome handles stair-aware generation
            suggested_downstairs = biome.generate_with_stairs(level.tiles, ctx, stairs_up_pos)
            
            # Place stairs using maze suggestions (no path carving needed)
            self._place_maze_stairs(level, level_id, stairs_up_pos, suggested_downstairs)
        else:
            # Standard biome generation
            biome.generate(level.tiles, ctx)
            
            # Add stairs using standard placement
            self._place_stairs(level, level_id, stairs_up_pos, level_rng)
        
        # Convert special tiles to entities (doors, chests, etc.)
        tile_converter = TileEntityConverter(self.world)
        tile_converter.convert_level_tiles(level)
        
        # Spawn creatures
        if self.scheduler:
            self._spawn_creatures(level, ctx)
        
        return level
    
    def _place_stairs(self, level: DungeonLevel, level_id: int, 
                     stairs_up_pos: Optional[Tuple[int, int]], rng: random.Random) -> None:
        """Place stairs on the level."""
        # Find valid positions for stairs (not walls)
        valid_positions = []
        for y in range(level.height):
            for x in range(level.width):
                if not level.is_wall(x, y):
                    valid_positions.append((x, y))
        
        if not valid_positions:
            return  # No valid positions found
        
        # Place upward stairs if this isn't level 0
        up_pos = None
        if level_id > 0:
            if stairs_up_pos:
                # ENFORCE the exact position - make it walkable if it's a wall
                x, y = stairs_up_pos
                if level.is_wall(x, y):
                    # Force the position to be walkable
                    tile = level.get_tile(x, y)
                    if tile:
                        tile.is_wall = False
                        tile.tile_type = 'floor'
                        tile.properties = {}
                
                # Use the specified position (now guaranteed to be valid)
                level.set_stairs_up(x, y)
                up_pos = stairs_up_pos
                # Remove this position from valid positions for downward stairs
                if stairs_up_pos in valid_positions:
                    valid_positions.remove(stairs_up_pos)
            else:
                # Pick a random position for upward stairs
                up_pos = rng.choice(valid_positions)
                level.set_stairs_up(up_pos[0], up_pos[1])
                valid_positions.remove(up_pos)
        
        # Place downward stairs with path connectivity validation
        if valid_positions:
            # Try to find a downward stairs position that has a path from upward stairs
            max_attempts = 50
            down_pos = None
            
            for attempt in range(max_attempts):
                candidate_pos = rng.choice(valid_positions)
                
                # Check if there's a path between stairs (if both exist)
                if up_pos and self._has_path(level, up_pos, candidate_pos):
                    down_pos = candidate_pos
                    break  # Found a valid position with connectivity
                elif not up_pos:
                    down_pos = candidate_pos
                    break  # No upward stairs to connect to, any position is fine
                
                # If this is the last attempt, use this position and ensure connectivity
                if attempt == max_attempts - 1:
                    down_pos = candidate_pos
                    if up_pos:
                        self._ensure_path(level, up_pos, down_pos)
                    break
            
            # Set the stairs only once we've found the final position
            if down_pos:
                level.set_stairs_down(down_pos[0], down_pos[1])
    
    def _place_maze_stairs(self, level: DungeonLevel, level_id: int, 
                          stairs_up_pos: Optional[Tuple[int, int]], 
                          suggested_downstairs: Optional[Tuple[int, int]]) -> None:
        """Place stairs on maze levels using maze-generated suggestions."""
        # Place upward stairs if this isn't level 0
        if level_id > 0 and stairs_up_pos:
            # For maze levels, the upstairs position was used as the starting point
            # for maze generation, so it should already be a valid floor tile
            level.set_stairs_up(stairs_up_pos[0], stairs_up_pos[1])
        
        # Place downward stairs using the maze's suggestion
        if suggested_downstairs:
            x, y = suggested_downstairs
            # The suggested position should already be a valid floor tile from maze generation
            level.set_stairs_down(x, y)
    
    def _has_path(self, level: DungeonLevel, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Check if there's a walkable path between two positions using BFS."""
        if start == end:
            return True
        
        from collections import deque
        
        queue = deque([start])
        visited = {start}
        
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                # Check bounds
                if 0 <= nx < level.width and 0 <= ny < level.height:
                    if (nx, ny) not in visited and not level.is_wall(nx, ny):
                        if (nx, ny) == end:
                            return True
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        
        return False
    
    def _ensure_path(self, level: DungeonLevel, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """Carve a simple path between two positions if none exists."""
        if self._has_path(level, start, end):
            return  # Path already exists
        
        # Simple path carving: move towards target, carving walls as needed
        x, y = start
        target_x, target_y = end
        
        # Carve a path using Manhattan distance approach
        while (x, y) != (target_x, target_y):
            # Move towards target
            if x < target_x:
                x += 1
            elif x > target_x:
                x -= 1
            elif y < target_y:
                y += 1
            elif y > target_y:
                y -= 1
            
            # Ensure this position is walkable (but don't change stairs)
            if 0 <= x < level.width and 0 <= y < level.height:
                # Don't modify stairs positions
                if (x, y) != start and (x, y) != end:
                    tile = level.get_tile(x, y)
                    if tile and tile.is_wall:
                        tile.is_wall = False
                        tile.tile_type = 'floor'
                        tile.properties = {}
    
    def _spawn_creatures(self, level: DungeonLevel, ctx: GenContext) -> None:
        """Spawn creatures on the level using scheduler."""
        if not self.scheduler:
            return
        
        # Get spawn count and types from scheduler
        spawn_data = self.scheduler.pick_spawns(level.level_id, ctx.rng)
        
        # Find valid spawn positions (not walls, not stairs)
        valid_positions = []
        for y in range(level.height):
            for x in range(level.width):
                if (not level.is_wall(x, y) and 
                    level.is_stairs_at(x, y) is None):
                    valid_positions.append((x, y))
        
        # Spawn creatures
        for spawn_info in spawn_data:
            if not valid_positions:
                break
            
            pos_index = ctx.rng.randint(0, len(valid_positions) - 1)
            x, y = valid_positions.pop(pos_index)
            
            entity_id = self._create_creature_entity(spawn_info, x, y)
            if entity_id:
                level.add_entity(entity_id)
    
    def _create_creature_entity(self, spawn_info: Dict[str, Any], x: int, y: int) -> Optional[int]:
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
        
        # Add Species component - use the species from spawn_info
        species_name = spawn_info.get('species', 'unknown')
        self.world.add_component(entity_id, Species(species_name))
        
        # Add Disposition component - use the disposition from spawn_info
        disposition_str = spawn_info.get('disposition', 'neutral')
        if disposition_str == 'hostile':
            disposition = DispositionType.HOSTILE
        elif disposition_str == 'friendly':
            disposition = DispositionType.FRIENDLY
        else:
            disposition = DispositionType.NEUTRAL
        self.world.add_component(entity_id, Disposition(disposition))
        
        return entity_id
    
    def get_biome_for_level(self, level_id: int) -> str:
        """Get the biome name for a given level."""
        if self.scheduler:
            segment = self.scheduler.segment_at(level_id)
            return segment.biome
        return 'default'
