# Maze Generator Plugin

A new map generator plugin that creates perfect mazes using the Recursive Backtracking algorithm (randomized depth-first search).

## Features

- **Perfect Maze Generation**: Creates mazes with exactly one path between any two points
- **Dead-End Stair Placement**: Stairs are always placed at dead ends (positions with only one travel direction)
- **Tactical Interconnections**: Optional parameter to add openings for increased tactical combat options
- **Grid-Based Layout**: Uses a structured grid system where:
  - Even coordinates (0, 2, 4, ...) are walls
  - Odd coordinates (1, 3, 5, ...) are corridors/intersections
  - This ensures corners and intersections only occur on odd coordinates
- **Full Border**: Complete wall border around the entire map
- **Deterministic**: Uses the game's seeded random number generator for reproducible results
- **Integrated**: Works seamlessly with the existing biome and level generation system

## Algorithm Details

The maze generator uses the **Recursive Backtracking** algorithm:

1. Start with a grid where all cells are walls
2. Choose a random starting cell on odd coordinates
3. Mark the current cell as a corridor
4. Look for unvisited neighboring cells (2 steps away on odd coordinates)
5. If unvisited neighbors exist:
   - Choose a random unvisited neighbor
   - Carve a passage between current cell and neighbor
   - Recursively visit the neighbor
6. Backtrack when no unvisited neighbors remain

## Grid System

The maze uses a specific coordinate system:

```
0123456789...  (x coordinates)
0##########...  (row 0: all walls - border)
1#.#.#.#.#.#..  (row 1: odd cols can be corridors)
2#.#.#.#.#.#..  (row 2: connecting passages)  
3#.#.#.#.#.#..  (row 3: odd cols can be corridors)
4#############  (row 4: connecting passages)
...
```

Where:
- `#` = wall
- `.` = corridor/passage

## Usage

### 1. Using in Level Generation

```python
from game.level_generator import LevelGenerator
from game.worldgen.scheduler import WorldScheduler, Segment
from ecs.world import World

# Create world and scheduler
world = World()
scheduler = WorldScheduler()

# Add maze segment
maze_segment = Segment(
    x0=0,
    x1=50,  # 50 levels of maze
    biome='maze',
    overrides={}
)
scheduler.segments = [maze_segment]

# Generate maze level
generator = LevelGenerator(world, scheduler, seed=42)
level = generator.generate_level(level_id=0)
```

### 2. Using in Schedule Configuration

You can also configure maze levels in the schedule YAML file:

```yaml
- from: 0
  to: 100
  biome: maze
```

### 3. Direct Biome Usage

```python
from game.worldgen.maze_generator import MazeBiome
from game.worldgen.core import WorldConfig, GenContext, Tile
import random

# Create tiles grid
config = WorldConfig(chunk_width=45, chunk_height=23, halo_size=0, seed=12345)
tiles = [[Tile(x, y) for x in range(45)] for y in range(23)]

# Create generation context
rng = random.Random(12345)
ctx = GenContext(
    chunk_id=0,
    seed=12345,
    rng=rng,
    config=config,
    parameters={}
)

# Generate maze
maze_biome = MazeBiome()
maze_biome.generate(tiles, ctx)
```

## Files Added

- `game/worldgen/maze_generator.py` - Main maze generation implementation
- `test_maze.py` - Test script for verification
- `example_maze_usage.py` - Usage examples
- `MAZE_GENERATOR_README.md` - This documentation

## Files Modified

- `game/worldgen/biomes.py` - Added import and registration of MazeBiome

## Testing

Run the test script to verify the maze generator:

```bash
python3 test_maze.py
```

This will:
- Generate a test maze
- Verify border walls are intact
- Check that corridors follow the grid constraint
- Verify maze connectivity (all areas reachable)
- Display the generated maze

## Integration

The maze biome is automatically registered and available as `'maze'` in the biome system. It can be used anywhere other biomes are used:

- Level generation
- World scheduling
- Custom map creation

## Properties

- **Dimensions**: Works with any dimensions ≥ 3x3
- **Connectivity**: Guarantees all corridor cells are reachable
- **Deterministic**: Same seed produces same maze
- **Performance**: Efficient O(n) generation where n is number of cells
- **Memory**: Minimal memory overhead

## Stair Placement

The maze generator uses an intelligent stair placement system:

1. **Starting Point**: For levels > 0, the upstairs position from the previous level is used as the starting point for maze generation
2. **Algorithm Integration**: The recursive backtracking algorithm begins from the upstairs position
3. **Dead-End Guarantee**: The last cell visited during maze generation becomes the downstairs position
4. **Natural Dead Ends**: Both stairs are guaranteed to be at dead ends (only one travel direction) by design

This approach ensures optimal gameplay where stairs provide strategic chokepoints and safe retreat positions.

## Interconnection System

The maze generator supports tactical interconnections via the `maze_openings` parameter:

### Usage
```python
parameters = {
    'maze_openings': 8  # Create 8 additional openings in the maze
}
```

### How It Works
1. **Wall Detection**: After maze generation, the system identifies walls that separate corridor areas
2. **Smart Selection**: Only walls with at least 2 corridor neighbors are considered (ensures meaningful connections)
3. **Random Placement**: The specified number of walls are randomly selected and converted to floor tiles
4. **Stair Preservation**: Interconnections don't affect the dead-end property of stairs

### Benefits
- **Tactical Options**: Creates alternative routes for combat positioning
- **Reduced Chokepoints**: Prevents overly linear gameplay
- **Balanced Complexity**: Maintains maze-like feel while adding strategic depth

### Example Results
- `maze_openings: 0` - Perfect maze (default)
- `maze_openings: 5` - Light interconnection for tactical variety
- `maze_openings: 15` - Heavy interconnection for complex combat scenarios

## Customization

The maze generator can be extended by:

1. **Adding parameters** to the generation context
2. **Creating custom layers** that modify the maze post-generation
3. **Subclassing MazeBiome** to add additional features

Example custom parameters:
```python
parameters = {
    'maze_openings': 8,     # Number of interconnections to create
    'maze_density': 0.8,    # Custom parameter for future extensions
    'wall_thickness': 1     # Could control wall thickness
}
```

## Testing

Additional test scripts are available:

```bash
# Test stair placement at dead ends
python3 test_maze_stairs.py

# Test interconnection feature
python3 test_maze_interconnections_fixed.py
```

The maze generator is now fully integrated and ready for use in your roguelike game!
