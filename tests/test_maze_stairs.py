#!/usr/bin/env python3
"""
Test script to verify that maze stairs are placed at dead ends.
"""

import random
from game.worldgen.maze_generator import MazeBiome
from game.worldgen.core import WorldConfig, GenContext, Tile


def count_walkable_neighbors(tiles, x, y):
    """Count walkable neighbors for a given position."""
    height = len(tiles)
    width = len(tiles[0]) if height > 0 else 0
    
    count = 0
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if (0 <= nx < width and 0 <= ny < height and 
            not tiles[ny][nx].is_wall):
            count += 1
    
    return count


def is_dead_end(tiles, x, y):
    """Check if a position is a dead end (exactly one walkable neighbor)."""
    if tiles[y][x].is_wall:
        return False
    return count_walkable_neighbors(tiles, x, y) == 1


def print_maze_with_stairs(tiles, upstairs_pos, downstairs_pos):
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


def test_maze_stairs():
    """Test that maze stairs are placed at dead ends."""
    print("Testing Maze Stair Placement at Dead Ends")
    print("=" * 50)
    
    # Test parameters
    width, height = 21, 15  # Odd dimensions work best for mazes
    seed = 12345
    
    # Create tiles grid
    tiles = [[Tile(x, y) for x in range(width)] for y in range(height)]
    
    # Create generation context
    config = WorldConfig(chunk_width=width, chunk_height=height, halo_size=0, seed=seed)
    rng = random.Random(seed)
    ctx = GenContext(
        chunk_id=0,
        seed=seed,
        rng=rng,
        config=config,
        parameters={}
    )
    
    # Test 1: Generate maze without upstairs (level 0)
    print("\nTest 1: Level 0 (no upstairs)")
    print("-" * 30)
    
    maze_biome = MazeBiome()
    downstairs_pos = maze_biome.generate_with_stairs(tiles, ctx, None)
    
    print(f"Downstairs placed at: {downstairs_pos}")
    if downstairs_pos:
        x, y = downstairs_pos
        is_down_dead_end = is_dead_end(tiles, x, y)
        walkable_neighbors = count_walkable_neighbors(tiles, x, y)
        print(f"Downstairs is dead end: {is_down_dead_end}")
        print(f"Downstairs walkable neighbors: {walkable_neighbors}")
    
    print_maze_with_stairs(tiles, None, downstairs_pos)
    
    # Test 2: Generate maze with upstairs (level 1+)
    print("\nTest 2: Level 1+ (with upstairs)")
    print("-" * 30)
    
    # Reset tiles
    tiles = [[Tile(x, y) for x in range(width)] for y in range(height)]
    
    # Use the previous downstairs as upstairs for next level
    upstairs_pos = downstairs_pos
    
    maze_biome = MazeBiome()
    downstairs_pos = maze_biome.generate_with_stairs(tiles, ctx, upstairs_pos)
    
    print(f"Upstairs placed at: {upstairs_pos}")
    print(f"Downstairs placed at: {downstairs_pos}")
    
    # Check if both stairs are at dead ends
    if upstairs_pos:
        x, y = upstairs_pos
        is_up_dead_end = is_dead_end(tiles, x, y)
        up_walkable_neighbors = count_walkable_neighbors(tiles, x, y)
        print(f"Upstairs is dead end: {is_up_dead_end}")
        print(f"Upstairs walkable neighbors: {up_walkable_neighbors}")
    
    if downstairs_pos:
        x, y = downstairs_pos
        is_down_dead_end = is_dead_end(tiles, x, y)
        down_walkable_neighbors = count_walkable_neighbors(tiles, x, y)
        print(f"Downstairs is dead end: {is_down_dead_end}")
        print(f"Downstairs walkable neighbors: {down_walkable_neighbors}")
    
    print_maze_with_stairs(tiles, upstairs_pos, downstairs_pos)
    
    # Test 3: Find all dead ends in the maze
    print("\nTest 3: All Dead Ends Analysis")
    print("-" * 30)
    
    dead_ends = []
    for y in range(height):
        for x in range(width):
            if is_dead_end(tiles, x, y):
                dead_ends.append((x, y))
    
    print(f"Total dead ends found: {len(dead_ends)}")
    print(f"Dead end positions: {dead_ends}")
    
    # Verify stairs are among the dead ends
    stairs_at_dead_ends = 0
    if upstairs_pos and upstairs_pos in dead_ends:
        stairs_at_dead_ends += 1
        print(f"✓ Upstairs {upstairs_pos} is at a dead end")
    elif upstairs_pos:
        print(f"✗ Upstairs {upstairs_pos} is NOT at a dead end")
    
    if downstairs_pos and downstairs_pos in dead_ends:
        stairs_at_dead_ends += 1
        print(f"✓ Downstairs {downstairs_pos} is at a dead end")
    elif downstairs_pos:
        print(f"✗ Downstairs {downstairs_pos} is NOT at a dead end")
    
    total_stairs = (1 if upstairs_pos else 0) + (1 if downstairs_pos else 0)
    print(f"\nResult: {stairs_at_dead_ends}/{total_stairs} stairs are at dead ends")
    
    if stairs_at_dead_ends == total_stairs:
        print("🎉 SUCCESS: All stairs are placed at dead ends!")
    else:
        print("❌ FAILURE: Some stairs are not at dead ends")
    
    return stairs_at_dead_ends == total_stairs


if __name__ == "__main__":
    success = test_maze_stairs()
    exit(0 if success else 1)
