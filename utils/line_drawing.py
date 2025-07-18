"""
Line drawing utilities using Bresenham's algorithm.
"""

from typing import List, Tuple


def draw_line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """
    Draw a line from (x0, y0) to (x1, y1) using Bresenham's algorithm.
    Returns a list of (x, y) coordinates along the line, including start and end points.
    """
    points = []
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    
    # Determine direction of line
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    
    err = dx - dy
    x, y = x0, y0
    
    while True:
        points.append((x, y))
        
        # Check if we've reached the end point
        if x == x1 and y == y1:
            break
        
        e2 = 2 * err
        
        if e2 > -dy:
            err -= dy
            x += sx
        
        if e2 < dx:
            err += dx
            y += sy
    
    return points


def get_line_to_target(start_x: int, start_y: int, target_x: int, target_y: int, 
                      max_distance: int = None) -> List[Tuple[int, int]]:
    """
    Get line from start to target, optionally limited by max distance.
    Returns list of (x, y) coordinates.
    """
    line = draw_line(start_x, start_y, target_x, target_y)
    
    if max_distance is not None and len(line) > max_distance + 1:
        # Limit line to max distance (+ 1 because start point is included)
        line = line[:max_distance + 1]
    
    return line


def calculate_distance(x0: int, y0: int, x1: int, y1: int) -> int:
    """Calculate Chebyshev distance (8-directional movement)."""
    return max(abs(x1 - x0), abs(y1 - y0))


def calculate_euclidean_distance(x0: int, y0: int, x1: int, y1: int) -> float:
    """Calculate Euclidean distance."""
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
