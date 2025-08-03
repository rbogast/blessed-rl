#!/usr/bin/env python3
"""
Test script to verify that maze interconnections work correctly.
"""

import random
from game.worldgen.templates.maze import MazeTemplate
from game.worldgen.core import WorldConfig, GenContext, Tile


def print_maze_with_openings(tiles, upstairs_pos, downstairs_pos):
    """Print the maze with stairs marked."""
    height = len(tiles)
    width = len(tiles[0]) if height > 0 else 0
    
    print("\nGenerated Maze (U=upstairs, D=downstairs, #=wall, .=floor):")
    print("=" * (width + 2))
    
    for y in range(height):
        row = ""
        for x in range(width):
            if upstairs_pos and (x, y) == upstairs_pos:
                row += "U"
            elif downstairs_pos and (x, y) == downstairs_pos:
                row += "D"
            elif tiles[y][x].is_wall:
                row += "#"
            else:
                row += "."
        print(f"|{row}|")
    
    print("=" * (width + 2))


def count_total_walls(tiles):
    """Count total number of walls in the maze."""
    height = len(tiles)
    width = len(tiles[0]) if height > 0 else 0
    
    wall_count = 0
    for y in range(height):
        for x in range(width):
            if tiles[y][x].is_wall:
                wall_count += 1
    
    return wall_count


def test_maze_interconnections():
    """Test that maze interconnections work correctly."""
    print("Testing Maze Interconnection Feature")
    print("=" * 50)
    
    # Test parameters
    width, height = 21, 15  # Odd dimensions work best for mazes
    seed = 42
    
    # Test 1: Maze without interconnections
    print("\nTest 1: Maze without interconnections")
    print("-" * 40)
    
    tiles = [[Tile(x, y) for x in range(width)] for y in range(height)]
    config = WorldConfig(chunk_width=width, chunk_height=height, seed=seed)
    rng = random.Random(seed)
    ctx = GenContext(
        chunk_id=0,
        seed=seed,
        rng=rng,
        config=config,
        parameters={}  # No maze_openings parameter
    )
    
    maze_template = MazeTemplate()
    downstairs_pos = maze_template.generate_with_stairs(tiles, ctx, None)
    
    walls_before = count_total_walls(tiles)
    print(f"Total walls: {walls_before}")
    print(f"Downstairs at: {downstairs_pos}")
    
    # Test 2: Maze with interconnections
    print("\nTest 2: Maze with 5 interconnections")
    print("-" * 40)
    
    tiles = [[Tile(x, y) for x in range(width)] for y in range(height)]
    rng = random.Random(seed)  # Reset RNG for consistent comparison
    ctx = GenContext(
        chunk_id=0,
        seed=seed,
        rng=rng,
        config=config,
        parameters={'maze_openings': 5}  # Request 5 interconnections
    )
    
    maze_template = MazeTemplate()
    downstairs_pos = maze_template.generate_with_stairs(tiles, ctx, None)
    
    walls_after_5 = count_total_walls(tiles)
    print(f"Total walls: {walls_after_5}")
    print(f"Reduction in walls: {walls_before - walls_after_5}")
    print(f"Downstairs at: {downstairs_pos}")
    
    print_maze_with_openings(tiles, None, downstairs_pos)
    
    # Test 3: Maze with many interconnections
    print("\nTest 3: Maze with 15 interconnections")
    print("-" * 40)
    
    tiles = [[Tile(x, y) for x in range(width)] for y in range(height)]
    rng = random.Random(seed)  # Reset RNG
    ctx = GenContext(
        chunk_id=0,
        seed=seed,
        rng=rng,
        config=config,
        parameters={'maze_openings': 15}  # Request 15 interconnections
    )
    
    maze_template = MazeTemplate()
    downstairs_pos = maze_template.generate_with_stairs(tiles, ctx, None)
    
    walls_after_15 = count_total_walls(tiles)
    print(f"Total walls: {walls_after_15}")
    print(f"Reduction in walls: {walls_before - walls_after_15}")
    print(f"Downstairs at: {downstairs_pos}")
    
    print_maze_with_openings(tiles, None, downstairs_pos)
    
    # Test 4: Verify stairs still at dead ends with interconnections
    print("\nTest 4: Verify stairs still at dead ends with interconnections")
    print("-" * 60)
    
    tiles = [[Tile(x, y) for x in range(width)] for y in range(height)]
    rng = random.Random(seed)
    ctx = GenContext(
        chunk_id=0,
        seed=seed,
        rng=rng,
        config=config,
        parameters={'maze_openings': 8}
    )
    
    upstairs_pos = (5, 5)  # Fixed upstairs position
    maze_template = MazeTemplate()
    downstairs_pos = maze_template.generate_with_stairs(tiles, ctx, upstairs_pos)
    
    # Check if stairs are still dead ends
    def count_walkable_neighbors(x, y):
        count = 0
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < width and 0 <= ny < height and not tiles[ny][nx].is_wall):
                count += 1
        return count
    
    up_neighbors = count_walkable_neighbors(upstairs_pos[0], upstairs_pos[1])
    down_neighbors = count_walkable_neighbors(downstairs_pos[0], downstairs_pos[1]) if downstairs_pos else 0
    
    print(f"Upstairs at {upstairs_pos}: {up_neighbors} walkable neighbors")
    print(f"Downstairs at {downstairs_pos}: {down_neighbors} walkable neighbors")
    
    stairs_still_dead_ends = (up_neighbors == 1 and down_neighbors == 1)
    print(f"Stairs still at dead ends: {stairs_still_dead_ends}")
    
    # Test 5: Debug - show what walls are being found
    print("\nTest 5: Debug interconnection wall detection")
    print("-" * 50)
    
    tiles = [[Tile(x, y) for x in range(width)] for y in range(height)]
    rng = random.Random(seed)
    ctx = GenContext(
        chunk_id=0,
        seed=seed,
        rng=rng,
        config=config,
        parameters={'maze_openings': 0}  # Generate base maze first
    )
    
    maze_template = MazeTemplate()
    downstairs_pos = maze_template.generate_with_stairs(tiles, ctx, None)
    
    # Manually check for valid interconnection walls
    interconnection_layer = maze_template.layers[2]  # MazeInterconnectionLayer
    stair_positions = interconnection_layer._find_stair_positions(tiles, width, height)
    valid_walls = interconnection_layer._find_valid_interconnection_walls(tiles, width, height, stair_positions)
    
    print(f"Valid walls for interconnection: {len(valid_walls)}")
    if len(valid_walls) > 0:
        print(f"First 10 valid walls: {valid_walls[:10]}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Original maze total walls: {walls_before}")
    print(f"With 5 interconnections: {walls_after_5} walls ({walls_before - walls_after_5} removed)")
    print(f"With 15 interconnections: {walls_after_15} walls ({walls_before - walls_after_15} removed)")
    print(f"Valid interconnection walls found: {len(valid_walls)}")
    print(f"Stairs remain at dead ends: {stairs_still_dead_ends}")
    
    success = (
        walls_after_5 < walls_before and  # Some walls were removed
        walls_after_15 < walls_after_5 and    # More walls removed with higher setting
        len(valid_walls) > 0 and           # Valid walls were found
        stairs_still_dead_ends              # Stairs still at dead ends
    )
    
    if success:
        print("🎉 SUCCESS: Interconnection feature working correctly!")
    else:
        print("❌ FAILURE: Interconnection feature has issues")
        print(f"  - Walls reduced with 5 openings: {walls_after_5 < walls_before}")
        print(f"  - More walls reduced with 15 openings: {walls_after_15 < walls_after_5}")
        print(f"  - Valid walls found: {len(valid_walls) > 0}")
        print(f"  - Stairs still dead ends: {stairs_still_dead_ends}")
    
    return success


if __name__ == "__main__":
    success = test_maze_interconnections()
    exit(0 if success else 1)
