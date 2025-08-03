"""
A* pathfinding algorithm for auto-exploration.
"""

import heapq
from typing import List, Tuple, Optional, Set, Callable
from dataclasses import dataclass


@dataclass
class PathNode:
    """A node in the pathfinding graph."""
    x: int
    y: int
    g_cost: float = 0.0  # Cost from start
    h_cost: float = 0.0  # Heuristic cost to goal
    f_cost: float = 0.0  # Total cost (g + h)
    parent: Optional['PathNode'] = None
    
    def __post_init__(self):
        self.f_cost = self.g_cost + self.h_cost
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))


class Pathfinder:
    """A* pathfinding implementation."""
    
    def __init__(self, is_walkable_func: Callable[[int, int], bool]):
        """
        Initialize pathfinder.
        
        Args:
            is_walkable_func: Function that returns True if a position is walkable
        """
        self.is_walkable = is_walkable_func
        self.path_cache = {}  # Cache for frequently requested paths
        self.max_cache_size = 100
    
    def find_path(self, start_x: int, start_y: int, goal_x: int, goal_y: int, 
                  max_distance: int = 100) -> Optional[List[Tuple[int, int]]]:
        """
        Find a path from start to goal using A* algorithm.
        
        Args:
            start_x, start_y: Starting position
            goal_x, goal_y: Goal position
            max_distance: Maximum search distance to prevent infinite loops
            
        Returns:
            List of (x, y) coordinates representing the path, or None if no path found
        """
        # Check cache first
        cache_key = (start_x, start_y, goal_x, goal_y)
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
        
        # Check if start and goal are walkable
        if not self.is_walkable(start_x, start_y) or not self.is_walkable(goal_x, goal_y):
            return None
        
        # If start is goal, return empty path
        if start_x == goal_x and start_y == goal_y:
            return []
        
        open_set = []
        closed_set: Set[Tuple[int, int]] = set()
        
        # Create start node
        start_node = PathNode(start_x, start_y)
        start_node.h_cost = self._heuristic(start_x, start_y, goal_x, goal_y)
        start_node.f_cost = start_node.h_cost
        
        heapq.heappush(open_set, start_node)
        open_dict = {(start_x, start_y): start_node}
        
        while open_set:
            current = heapq.heappop(open_set)
            current_pos = (current.x, current.y)
            
            # Remove from open dict
            if current_pos in open_dict:
                del open_dict[current_pos]
            
            # Add to closed set
            closed_set.add(current_pos)
            
            # Check if we reached the goal
            if current.x == goal_x and current.y == goal_y:
                path = self._reconstruct_path(current)
                self._cache_path(cache_key, path)
                return path
            
            # Check max distance
            if current.g_cost > max_distance:
                continue
            
            # Check all neighbors
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                neighbor_x = current.x + dx
                neighbor_y = current.y + dy
                neighbor_pos = (neighbor_x, neighbor_y)
                
                # Skip if already processed
                if neighbor_pos in closed_set:
                    continue
                
                # Skip if not walkable
                if not self.is_walkable(neighbor_x, neighbor_y):
                    continue
                
                # Calculate movement cost (diagonal moves cost more)
                move_cost = 1.4 if abs(dx) + abs(dy) == 2 else 1.0
                tentative_g = current.g_cost + move_cost
                
                # Check if this is a better path to the neighbor
                if neighbor_pos in open_dict:
                    neighbor = open_dict[neighbor_pos]
                    if tentative_g < neighbor.g_cost:
                        neighbor.g_cost = tentative_g
                        neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
                        neighbor.parent = current
                        heapq.heapify(open_set)  # Re-heapify since we changed a value
                else:
                    # Create new neighbor node
                    neighbor = PathNode(neighbor_x, neighbor_y)
                    neighbor.g_cost = tentative_g
                    neighbor.h_cost = self._heuristic(neighbor_x, neighbor_y, goal_x, goal_y)
                    neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
                    neighbor.parent = current
                    
                    heapq.heappush(open_set, neighbor)
                    open_dict[neighbor_pos] = neighbor
        
        # No path found
        self._cache_path(cache_key, None)
        return None
    
    def find_nearest_reachable(self, start_x: int, start_y: int, 
                              targets: List[Tuple[int, int]], 
                              max_distance: int = 50) -> Optional[Tuple[int, int, List[Tuple[int, int]]]]:
        """
        Find the nearest reachable target from a list of targets.
        
        Args:
            start_x, start_y: Starting position
            targets: List of (x, y) target positions
            max_distance: Maximum search distance
            
        Returns:
            Tuple of (target_x, target_y, path) for the nearest reachable target, or None
        """
        if not targets:
            return None
        
        best_target = None
        best_path = None
        best_distance = float('inf')
        
        for target_x, target_y in targets:
            # Quick distance check
            heuristic_dist = self._heuristic(start_x, start_y, target_x, target_y)
            if heuristic_dist > max_distance:
                continue
            
            path = self.find_path(start_x, start_y, target_x, target_y, max_distance)
            if path is not None:
                path_length = len(path)
                if path_length < best_distance:
                    best_distance = path_length
                    best_target = (target_x, target_y)
                    best_path = path
        
        if best_target:
            return (best_target[0], best_target[1], best_path)
        return None
    
    def _heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculate heuristic distance (Chebyshev distance for 8-directional movement)."""
        return max(abs(x2 - x1), abs(y2 - y1))
    
    def _reconstruct_path(self, node: PathNode) -> List[Tuple[int, int]]:
        """Reconstruct path from goal node back to start."""
        path = []
        current = node
        
        while current.parent is not None:
            path.append((current.x, current.y))
            current = current.parent
        
        path.reverse()
        return path
    
    def _cache_path(self, cache_key: Tuple[int, int, int, int], path: Optional[List[Tuple[int, int]]]):
        """Cache a path result."""
        if len(self.path_cache) >= self.max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.path_cache))
            del self.path_cache[oldest_key]
        
        self.path_cache[cache_key] = path
    
    def clear_cache(self):
        """Clear the path cache."""
        self.path_cache.clear()
    
    def is_reachable(self, start_x: int, start_y: int, goal_x: int, goal_y: int, 
                     max_distance: int = 50) -> bool:
        """
        Check if a goal is reachable from start position.
        
        Args:
            start_x, start_y: Starting position
            goal_x, goal_y: Goal position
            max_distance: Maximum search distance
            
        Returns:
            True if goal is reachable, False otherwise
        """
        path = self.find_path(start_x, start_y, goal_x, goal_y, max_distance)
        return path is not None
