#!/usr/bin/env python3
"""
Test script to verify that maze interconnections work correctly.
"""

import random
from game.worldgen.maze_generator import MazeBiome
from game.worldgen.core import WorldConfig, GenContext, Tile


def print_maze_with_openings(tiles, upstairs_pos, downstairs_pos, openings):
    """Print the maze with stairs and openings marked."""
    height = len(tiles)
    width = len(tiles[0]) if height > 0 else 0
    
    print("\nGenerated Maze (U=upstairs, D=downstairs, O=opening, #=wall, .=floor):")
    print("=" * (width + 2))
    
    for y in range(height):
        row = ""
        for x in range(width):
            if upstairs_pos and (x, y) == upstairs_pos:
                row += "U"
            elif downstairs_pos and (x, y) == downstairs_pos:
                row += "D"
            elif (x, y) in openings:
                row += "O"
            elif tiles[y][x].is_wall:
                row += "#"
            else:
                row += "."
        print(f"|{row}|")
    
    print("=" * (width + 2))


def count_paths_between_points(tiles, start, end):
    """Count the number of different paths between two points using BFS."""
    from collections import deque
    
    height = len(tiles)
    width = len(tiles[0]) if height > 0 else 0
    
    # Simple path existence check
    queue = deque([start])
    visited = {start}
    
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    
    while queue:
        x, y = queue.popleft()
        
        if (x, y) == end:
            return True
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            if (0 <= nx < width and 0 <= ny < height and 
                (nx, ny) not in visited and not tiles[ny][nx].is_wall):
                visited.add((nx, ny))
                queue.append((nx, ny))
    
    return False


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
    config = WorldConfig(chunk_width=width, chunk_height=height, halo_size=0, seed=seed)
    rng = random.Random(seed)
    ctx = GenContext(
        chunk_id=0,
        seed=seed,
        rng=rng,
        config=config,
        parameters={}  # No maze_openings parameter
    )
    
    maze_biome = MazeBiome()
    downstairs_pos = maze_biome.generate_with_stairs(tiles, ctx, None)
    
    # Count walls on odd coordinates (potential interconnection points)
    odd_walls_before = 0
    for y in range(1, height - 1, 2):
        for x in range(1, width - 1, 2):
            if tiles[y][x].is_wall:
                odd_walls_before += 1
    
    print(f"Walls on odd coordinates: {odd_walls_before}")
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
    
    maze_biome = MazeBiome()
    downstairs_pos = maze_biome.generate_with_stairs(tiles, ctx, None)
    
    # Count walls on odd coordinates after interconnections
    odd_walls_after = 0
    openings = []
    for y in range(1, height - 1, 2):
        for x in range(1, width - 1, 2):
            if tiles[y][x].is_wall:
                odd_walls_after += 1
            else:
                # This was potentially an opening (if it's not part of original maze)
                openings.append((x, y))
    
    print(f"Walls on odd coordinates: {odd_walls_after}")
    print(f"Reduction in walls: {odd_walls_before - odd_walls_after}")
    print(f"Downstairs at: {downstairs_pos}")
    
    print_maze_with_openings(tiles, None, downstairs_pos, [])
    
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
    
    maze_biome = MazeBiome()
    downstairs_pos = maze_biome.generate_with_stairs(tiles, ctx, None)
    
    # Count walls on odd coordinates after many interconnections
    odd_walls_many = 0
    for y in range(1, height - 1, 2):
        for x in range(1, width - 1, 2):
            if tiles[y][x].is_wall:
                odd_walls_many += 1
    
    print(f"Walls on odd coordinates: {odd_walls_many}")
    print(f"Reduction in walls: {odd_walls_before - odd_walls_many}")
    print(f"Downstairs at: {downstairs_pos}")
    
    print_maze_with_openings(tiles, None, downstairs_pos, [])
    
    # Test 4: Verify stairs still at dead ends
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
    maze_biome = MazeBiome()
    downstairs_pos = maze_biome.generate_with_stairs(tiles, ctx, upstairs_pos)
    
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
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Original maze walls on odd coordinates: {odd_walls_before}")
    print(f"With 5 interconnections: {odd_walls_after} walls ({odd_walls_before - odd_walls_after} removed)")
    print(f"With 15 interconnections: {odd_walls_many} walls ({odd_walls_before - odd_walls_many} removed)")
    print(f"Stairs remain at dead ends: {stairs_still_dead_ends}")
    
    success = (
        odd_walls_after < odd_walls_before and  # Some walls were removed
        odd_walls_many < odd_walls_after and    # More walls removed with higher setting
        stairs_still_dead_ends                  # Stairs still at dead ends
    )
    
    if success:
        print("🎉 SUCCESS: Interconnection feature working correctly!")
    else:
        print("❌ FAILURE: Interconnection feature has issues")
    
    return success


if __name__ == "__main__":
    success = test_maze_interconnections()
    exit(0 if success else 1)
