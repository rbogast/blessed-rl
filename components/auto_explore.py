"""
Auto-exploration component for tracking exploration state and behavior.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from enum import Enum


class AutoExploreState(Enum):
    """States for auto-exploration."""
    INACTIVE = "inactive"
    SCANNING = "scanning"
    MOVING = "moving"


class ExploreTargetType(Enum):
    """Types of exploration targets."""
    UNEXPLORED = "unexplored"
    STAIRS_DOWN = "stairs_down"
    STAIRS_UP = "stairs_up"
    ITEM = "item"
    DOOR = "door"


@dataclass
class ExploreTarget:
    """Represents a target for auto-exploration."""
    x: int
    y: int
    target_type: ExploreTargetType
    priority: int = 0  # Higher priority = more important
    entity_id: Optional[int] = None  # For items/doors
    
    def __post_init__(self):
        """Set default priorities based on target type."""
        if self.priority == 0:
            if self.target_type == ExploreTargetType.STAIRS_DOWN:
                self.priority = 100
            elif self.target_type == ExploreTargetType.STAIRS_UP:
                self.priority = 90
            elif self.target_type == ExploreTargetType.ITEM:
                self.priority = 50
            elif self.target_type == ExploreTargetType.DOOR:
                self.priority = 40
            elif self.target_type == ExploreTargetType.UNEXPLORED:
                self.priority = 10


@dataclass
class AutoExplore:
    """Component for auto-exploration behavior."""
    
    # Current state
    state: AutoExploreState = AutoExploreState.INACTIVE
    
    # Current target and path
    current_target: Optional[ExploreTarget] = None
    current_path: List[Tuple[int, int]] = field(default_factory=list)
    path_index: int = 0
    
    # Exploration preferences
    prefer_stairs: bool = True
    prefer_items: bool = True
    max_search_distance: int = 50
    
    # Interrupt conditions
    interrupt_on_enemy: bool = True
    interrupt_on_damage: bool = True
    interrupt_on_new_items: bool = False
    
    # State tracking
    last_scan_turn: int = 0
    scan_frequency: int = 5  # Rescan every N turns
    visited_positions: set = field(default_factory=set)
    
    # Statistics
    tiles_explored: int = 0
    items_found: int = 0
    stairs_found: int = 0
    
    def is_active(self) -> bool:
        """Check if auto-explore is currently active."""
        return self.state != AutoExploreState.INACTIVE
    
    def is_moving(self) -> bool:
        """Check if currently moving along a path."""
        return self.state == AutoExploreState.MOVING
    
    def has_target(self) -> bool:
        """Check if there's a current target."""
        return self.current_target is not None
    
    def has_path(self) -> bool:
        """Check if there's a current path."""
        return len(self.current_path) > 0
    
    def get_next_step(self) -> Optional[Tuple[int, int]]:
        """Get the next step in the current path."""
        if self.has_path() and self.path_index < len(self.current_path):
            return self.current_path[self.path_index]
        return None
    
    def advance_path(self) -> None:
        """Advance to the next step in the path."""
        if self.path_index < len(self.current_path):
            self.path_index += 1
    
    def is_path_complete(self) -> bool:
        """Check if the current path is complete."""
        return self.path_index >= len(self.current_path)
    
    def clear_target(self) -> None:
        """Clear the current target and path."""
        self.current_target = None
        self.current_path.clear()
        self.path_index = 0
    
    def set_target(self, target: ExploreTarget, path: List[Tuple[int, int]]) -> None:
        """Set a new target and path."""
        self.current_target = target
        self.current_path = path.copy()
        self.path_index = 0
        self.state = AutoExploreState.MOVING
    
    def interrupt(self, reason: str = "unknown") -> None:
        """Stop auto-exploration."""
        self.deactivate()
    
    def activate(self) -> None:
        """Activate auto-exploration."""
        if self.state == AutoExploreState.INACTIVE:
            self.state = AutoExploreState.SCANNING
            self.clear_target()
    
    def deactivate(self) -> None:
        """Deactivate auto-exploration."""
        self.state = AutoExploreState.INACTIVE
        self.clear_target()
    
    def mark_position_visited(self, x: int, y: int) -> None:
        """Mark a position as visited."""
        self.visited_positions.add((x, y))
    
    def is_position_visited(self, x: int, y: int) -> bool:
        """Check if a position has been visited."""
        return (x, y) in self.visited_positions
    
    def should_rescan(self, current_turn: int) -> bool:
        """Check if it's time to rescan for new targets."""
        return (current_turn - self.last_scan_turn) >= self.scan_frequency
    
    def mark_scan_complete(self, current_turn: int) -> None:
        """Mark that a scan was completed."""
        self.last_scan_turn = current_turn
    
    def get_status_message(self) -> str:
        """Get a status message for the current auto-explore state."""
        if self.state == AutoExploreState.INACTIVE:
            return "Auto-explore: Off"
        elif self.state == AutoExploreState.SCANNING:
            return "Auto-explore: Scanning for targets..."
        elif self.state == AutoExploreState.MOVING:
            if self.current_target:
                target_desc = {
                    ExploreTargetType.UNEXPLORED: "unexplored area",
                    ExploreTargetType.STAIRS_DOWN: "stairs down",
                    ExploreTargetType.STAIRS_UP: "stairs up",
                    ExploreTargetType.ITEM: "item",
                    ExploreTargetType.DOOR: "door"
                }.get(self.current_target.target_type, "unknown")
                return f"Auto-explore: Moving to {target_desc}"
            else:
                return "Auto-explore: Moving"
        else:
            return "Auto-explore: Unknown state"
