"""
Auto-exploration system for automated dungeon exploration.
"""

from ecs.system import System
from components.core import Position, Player, Visible, Door
from components.items import Item, Pickupable
from components.combat import Health
from components.ai import AI
from components.auto_explore import AutoExplore, AutoExploreState, ExploreTarget, ExploreTargetType
from systems.movement import MovementSystem
from systems.simple_lighting_system import SimpleLightingSystem
from utils.pathfinding import Pathfinder
from typing import List, Tuple, Optional, Set
from game.config import GameConfig


class AutoExploreSystem(System):
    """Handles automated exploration behavior."""
    
    def __init__(self, world, movement_system: MovementSystem, fov_system: SimpleLightingSystem, 
                 world_generator, message_log):
        super().__init__(world)
        self.movement_system = movement_system
        self.fov_system = fov_system
        self.world_generator = world_generator
        self.message_log = message_log
        
        # Create pathfinder with walkability function
        self.pathfinder = Pathfinder(self._is_walkable_for_pathfinding)
        
        # Cache for performance
        self._enemy_cache = set()
        self._last_enemy_scan = 0
        
        # Reference to game state for automation tracking
        self.game_state = None
    
    def set_game_state(self, game_state) -> None:
        """Set the game state reference for automation tracking."""
        self.game_state = game_state
        
    def update(self, dt: float = 0.0) -> None:
        """Update auto-exploration for all entities with AutoExplore component."""
        auto_explore_entities = self.world.get_entities_with_components(AutoExplore, Position, Player)
        
        for entity_id in auto_explore_entities:
            self._update_auto_explore_entity(entity_id)
    
    def _update_auto_explore_entity(self, entity_id: int) -> None:
        """Update auto-exploration for a single entity."""
        auto_explore = self.world.get_component(entity_id, AutoExplore)
        position = self.world.get_component(entity_id, Position)
        
        if not auto_explore or not position:
            return
        
        
        if not auto_explore.is_active():
            return
        
        # Only check for interrupts if not already interrupted
        if self._should_interrupt(entity_id, auto_explore):
            # Get more specific interrupt reason
            if self._has_visible_enemies(entity_id):
                auto_explore.interrupt("Enemy detected nearby")
                self.message_log.add_warning("Auto-explore interrupted - enemy nearby!")
            else:
                auto_explore.interrupt("Unknown interrupt condition")
                self.message_log.add_warning("Auto-explore interrupted - unknown reason!")
            return
        
        # Handle different states
        if auto_explore.state == AutoExploreState.SCANNING:
            self._handle_scanning(entity_id, auto_explore, position)
        elif auto_explore.state == AutoExploreState.MOVING:
            self._handle_movement(entity_id, auto_explore, position)
    
    def _handle_scanning(self, entity_id: int, auto_explore: AutoExplore, position: Position) -> None:
        """Handle the scanning state - look for new targets."""
        # Use a simple counter instead of relying on game state turn count
        # For auto-explore, we just need to know when to rescan
        current_turn = auto_explore.last_scan_turn + 1
        
        # Check if we need to rescan (always scan if last_scan_turn is 0, which means first scan)
        # Also force scan if we don't have a target
        if auto_explore.last_scan_turn != 0 and not auto_explore.should_rescan(current_turn) and auto_explore.has_target():
            return
        
        # Find all potential targets
        targets = self._find_exploration_targets(position.x, position.y, auto_explore.max_search_distance)
        
        if not targets:
            # No targets found - auto-explore complete
            auto_explore.deactivate()
            # Clear automation flag when auto-explore ends
            if self.game_state:
                self.game_state.end_automated_action()
            self.message_log.add_info("Auto-explore complete - no more targets found.")
            return
        
        # Sort targets by priority and distance
        targets.sort(key=lambda t: (-t.priority, self._calculate_distance(position.x, position.y, t.x, t.y)))
        
        # Try to find a path to the best target
        for target in targets:
            path = self.pathfinder.find_path(position.x, position.y, target.x, target.y, 
                                           auto_explore.max_search_distance)
            if path:
                auto_explore.set_target(target, path)
                break
        
        if not auto_explore.has_target():
            # No reachable targets
            auto_explore.deactivate()
            # Clear automation flag when auto-explore ends
            if self.game_state:
                self.game_state.end_automated_action()
            self.message_log.add_warning("No reachable targets found for auto-explore.")
        
        auto_explore.mark_scan_complete(current_turn)
    
    def _handle_movement(self, entity_id: int, auto_explore: AutoExplore, position: Position) -> None:
        """Handle the movement state - move along the current path."""
        if not auto_explore.has_path():
            # No path, switch to scanning
            self.message_log.add_info("Auto-explore: No path, switching to scanning")
            auto_explore.state = AutoExploreState.SCANNING
            return
        
        # Get next step
        next_step = auto_explore.get_next_step()
        if not next_step:
            # Path complete, check if we reached the target
            if auto_explore.has_target():
                target = auto_explore.current_target
                if position.x == target.x and position.y == target.y:
                    # Reached target
                    self._handle_target_reached(entity_id, auto_explore, target)
                else:
                    # Didn't reach target, rescan
                    auto_explore.clear_target()
                    auto_explore.state = AutoExploreState.SCANNING
            else:
                auto_explore.state = AutoExploreState.SCANNING
            return
        
        # Try to move to next step
        next_x, next_y = next_step
        dx = next_x - position.x
        dy = next_y - position.y
        
        # Attempt movement
        if self.movement_system.try_move_entity(entity_id, dx, dy):
            # Movement successful
            auto_explore.advance_path()
            auto_explore.mark_position_visited(next_x, next_y)
            
            # Check if we stepped on an interesting tile
            tile = self.world_generator.get_tile_at(next_x, next_y)
            if tile and tile.interesting:
                # Remove interesting status when stepped on
                tile.interesting = False
                # Interrupt auto-explore when stepping on interesting tiles
                auto_explore.interrupt("Stepped on interesting tile")
                self.message_log.add_info("Auto-explore interrupted - stepped on interesting tile.")
                return
            
        else:
            # Movement blocked, recalculate path or find new target
            if auto_explore.has_target():
                target = auto_explore.current_target
                new_path = self.pathfinder.find_path(position.x, position.y, target.x, target.y,
                                                   auto_explore.max_search_distance)
                if new_path:
                    auto_explore.set_target(target, new_path)
                else:
                    # Target unreachable, find new target
                    auto_explore.clear_target()
                    auto_explore.state = AutoExploreState.SCANNING
            else:
                auto_explore.state = AutoExploreState.SCANNING
    
    def _should_interrupt(self, entity_id: int, auto_explore: AutoExplore) -> bool:
        """Check if auto-exploration should be interrupted."""
        if not auto_explore.interrupt_on_enemy:
            return False
        
        # Check for visible enemies
        return self._has_visible_enemies(entity_id)
    
    def _has_visible_enemies(self, player_entity: int) -> bool:
        """Check if there are any visible hostile entities that pose an immediate threat."""
        # Get player position for distance calculations
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return False
        
        # Get all AI entities (potential enemies)
        ai_entities = self.world.get_entities_with_components(AI, Position, Visible, Health)
        
        for entity_id in ai_entities:
            if entity_id == player_entity:
                continue
            
            visible = self.world.get_component(entity_id, Visible)
            health = self.world.get_component(entity_id, Health)
            ai = self.world.get_component(entity_id, AI)
            position = self.world.get_component(entity_id, Position)
            
            # Check if entity is visible and alive
            if visible and visible.visible and health and health.is_alive() and ai and position:
                # Only consider it an enemy if it's targeting the player AND is close enough to be a threat
                if ai.target_entity == player_entity:
                    # Calculate distance to determine if it's an immediate threat
                    distance = self._calculate_distance(player_pos.x, player_pos.y, position.x, position.y)
                    # Only interrupt if enemy is within 5 tiles (immediate threat range)
                    if distance <= 5:
                        return True
        
        return False
    
    def _find_exploration_targets(self, start_x: int, start_y: int, max_distance: int) -> List[ExploreTarget]:
        """Find all potential exploration targets within range."""
        targets = []
        
        # Get current level for bounds checking
        current_level = self.world_generator.get_current_level()
        if not current_level:
            return targets
        
        # Search area around player
        search_radius = min(max_distance, 30)  # Limit search for performance
        
        unexplored_count = 0
        interesting_count = 0
        total_tiles_checked = 0
        
        for y in range(max(0, start_y - search_radius), 
                      min(current_level.height, start_y + search_radius + 1)):
            for x in range(max(0, start_x - search_radius), 
                          min(current_level.width, start_x + search_radius + 1)):
                
                # Skip if too far
                if self._calculate_distance(start_x, start_y, x, y) > max_distance:
                    continue
                
                total_tiles_checked += 1
                
                tile = self.world_generator.get_tile_at(x, y)
                if not tile or tile.is_wall:
                    continue
                
                # Check for interesting tiles first (highest priority)
                if tile.interesting:
                    # Determine what type of interesting target this is
                    stairs_type = self.world_generator.is_stairs_at(x, y)
                    items_at_pos = self._get_items_at_position(x, y)
                    door_entity = self._get_door_at_position(x, y)
                    
                    if stairs_type == 'down':
                        targets.append(ExploreTarget(x, y, ExploreTargetType.STAIRS_DOWN))
                        interesting_count += 1
                    elif stairs_type == 'up':
                        targets.append(ExploreTarget(x, y, ExploreTargetType.STAIRS_UP))
                        interesting_count += 1
                    elif items_at_pos:
                        # Use the first item entity for the target
                        targets.append(ExploreTarget(x, y, ExploreTargetType.ITEM, entity_id=items_at_pos[0]))
                        interesting_count += 1
                    elif door_entity is not None:
                        door = self.world.get_component(door_entity, Door)
                        if door and not door.is_open:
                            targets.append(ExploreTarget(x, y, ExploreTargetType.DOOR, entity_id=door_entity))
                            interesting_count += 1
                
                # Check for unexplored tiles (lower priority)
                elif not tile.explored:
                    targets.append(ExploreTarget(x, y, ExploreTargetType.UNEXPLORED))
                    unexplored_count += 1
        
        # Debug information
        if len(targets) == 0:
            self.message_log.add_info(f"Auto-explore: No targets found. Checked {total_tiles_checked} tiles.")
        else:
            self.message_log.add_info(f"Auto-explore: Found {len(targets)} targets ({interesting_count} interesting, {unexplored_count} unexplored).")
        
        return targets
    
    def _get_items_at_position(self, x: int, y: int) -> List[int]:
        """Get all item entities at a specific position."""
        items = []
        item_entities = self.world.get_entities_with_components(Position, Item, Pickupable)
        
        for entity_id in item_entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                items.append(entity_id)
        
        return items
    
    def _get_door_at_position(self, x: int, y: int) -> Optional[int]:
        """Get door entity at a specific position."""
        door_entities = self.world.get_entities_with_components(Position, Door)
        
        for entity_id in door_entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                return entity_id
        
        return None
    
    def _handle_target_reached(self, entity_id: int, auto_explore: AutoExplore, target: ExploreTarget) -> None:
        """Handle reaching a target."""
        should_stop = False
        
        if target.target_type == ExploreTargetType.ITEM:
            auto_explore.items_found += 1
            self.message_log.add_info("Auto-explore: Found item!")
            should_stop = True  # Stop at items
        elif target.target_type in [ExploreTargetType.STAIRS_DOWN, ExploreTargetType.STAIRS_UP]:
            auto_explore.stairs_found += 1
            self.message_log.add_info(f"Auto-explore: Found {target.target_type.value}!")
            should_stop = True  # Stop at stairs
        elif target.target_type == ExploreTargetType.DOOR:
            self.message_log.add_info("Auto-explore: Found door!")
            should_stop = True  # Stop at doors
        elif target.target_type == ExploreTargetType.UNEXPLORED:
            auto_explore.tiles_explored += 1
            # Don't stop for unexplored tiles - continue exploring
        
        # Clear target
        auto_explore.clear_target()
        
        if should_stop:
            # Stop auto-explore when reaching interesting targets
            auto_explore.deactivate()
            self.message_log.add_info("Auto-explore stopped.")
        else:
            # Continue scanning for more targets
            auto_explore.state = AutoExploreState.SCANNING
    
    
    def _is_walkable_for_pathfinding(self, x: int, y: int) -> bool:
        """Check if a position is walkable for pathfinding purposes."""
        # Check bounds
        current_level = self.world_generator.get_current_level()
        if not current_level:
            return False
        
        if not (0 <= x < current_level.width and 0 <= y < current_level.height):
            return False
        
        # Check for walls
        if self.world_generator.is_wall_at(x, y):
            return False
        
        # For pathfinding, we should be more permissive
        # Allow movement through most tiles, only block on actual blocking entities
        blocking_entities = self.world.get_entities_with_components(Position, Visible)
        for entity_id in blocking_entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                # Allow movement through doors, items, and corpses
                if (self.world.has_component(entity_id, Door) or 
                    self.world.has_component(entity_id, Item)):
                    continue
                # Check if it's a corpse (allow movement through corpses)
                from components.corpse import Corpse
                if self.world.has_component(entity_id, Corpse):
                    continue
                # Check if it's the player (don't block on player)
                if self.world.has_component(entity_id, Player):
                    continue
                # Block movement through living enemies only
                from components.combat import Health
                health = self.world.get_component(entity_id, Health)
                if health and health.is_alive():
                    return False
        
        return True
    
    def _calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """Calculate Chebyshev distance between two points."""
        return max(abs(x2 - x1), abs(y2 - y1))
    
    def _get_target_description(self, target: ExploreTarget) -> str:
        """Get a human-readable description of a target."""
        descriptions = {
            ExploreTargetType.UNEXPLORED: "unexplored area",
            ExploreTargetType.STAIRS_DOWN: "stairs down",
            ExploreTargetType.STAIRS_UP: "stairs up",
            ExploreTargetType.ITEM: "item",
            ExploreTargetType.DOOR: "door"
        }
        return descriptions.get(target.target_type, "unknown target")
    
    def start_auto_explore(self, entity_id: int) -> None:
        """Start auto-exploration for an entity."""
        auto_explore = self.world.get_component(entity_id, AutoExplore)
        if not auto_explore:
            # Add AutoExplore component if it doesn't exist
            auto_explore = AutoExplore()
            self.world.add_component(entity_id, auto_explore)
        
        if auto_explore.is_active():
            self.message_log.add_info("Auto-explore already active.")
            return
        
        # Reset the component state for a fresh start
        auto_explore.clear_target()
        auto_explore.visited_positions.clear()
        auto_explore.last_scan_turn = 0  # Force immediate scan
        
        auto_explore.activate()
        # Set automation flag when auto-explore starts
        if self.game_state:
            self.game_state.start_automated_action()
        self.message_log.add_info("Auto-explore started.")
        # Clear pathfinding cache when starting new exploration
        self.pathfinder.clear_cache()
    
    def interrupt_auto_explore(self, entity_id: int) -> None:
        """Interrupt auto-exploration for an entity."""
        auto_explore = self.world.get_component(entity_id, AutoExplore)
        if auto_explore and auto_explore.is_active():
            auto_explore.interrupt("Manual interrupt")
            # Clear automation flag when auto-explore is interrupted
            if self.game_state:
                self.game_state.end_automated_action()
            self.message_log.add_warning("Auto-explore interrupted.")
    
    
    def travel_to_stairs_down(self, entity_id: int) -> None:
        """Travel to downward stairs on the current level."""
        position = self.world.get_component(entity_id, Position)
        if not position:
            return
        
        # Find downward stairs on current level
        current_level = self.world_generator.get_current_level()
        if not current_level:
            self.message_log.add_warning("No current level found.")
            return
        
        stairs_pos = current_level.get_stairs_down_pos()
        if not stairs_pos:
            self.message_log.add_warning("No downward stairs found on this level.")
            return
        
        # Check if already at stairs
        if position.x == stairs_pos[0] and position.y == stairs_pos[1]:
            self.message_log.add_info("You're already at the downward stairs.")
            return
        
        # Find path to stairs
        path = self.pathfinder.find_path(position.x, position.y, stairs_pos[0], stairs_pos[1], 100)
        if not path:
            self.message_log.add_warning("Cannot find a path to the downward stairs.")
            return
        
        # Set up auto-explore component
        auto_explore = self.world.get_component(entity_id, AutoExplore)
        if not auto_explore:
            auto_explore = AutoExplore()
            self.world.add_component(entity_id, auto_explore)
        
        # Create target and start movement
        target = ExploreTarget(stairs_pos[0], stairs_pos[1], ExploreTargetType.STAIRS_DOWN)
        auto_explore.set_target(target, path)
        
        self.message_log.add_info("Traveling to downward stairs...")
        # Clear pathfinding cache for fresh start
        self.pathfinder.clear_cache()
    
    def travel_to_stairs_up(self, entity_id: int) -> None:
        """Travel to upward stairs on the current level."""
        position = self.world.get_component(entity_id, Position)
        if not position:
            return
        
        # Find upward stairs on current level
        current_level = self.world_generator.get_current_level()
        if not current_level:
            self.message_log.add_warning("No current level found.")
            return
        
        stairs_pos = current_level.get_stairs_up_pos()
        if not stairs_pos:
            self.message_log.add_warning("No upward stairs found on this level.")
            return
        
        # Check if already at stairs
        if position.x == stairs_pos[0] and position.y == stairs_pos[1]:
            self.message_log.add_info("You're already at the upward stairs.")
            return
        
        # Find path to stairs
        path = self.pathfinder.find_path(position.x, position.y, stairs_pos[0], stairs_pos[1], 100)
        if not path:
            self.message_log.add_warning("Cannot find a path to the upward stairs.")
            return
        
        # Set up auto-explore component
        auto_explore = self.world.get_component(entity_id, AutoExplore)
        if not auto_explore:
            auto_explore = AutoExplore()
            self.world.add_component(entity_id, auto_explore)
        
        # Create target and start movement
        target = ExploreTarget(stairs_pos[0], stairs_pos[1], ExploreTargetType.STAIRS_UP)
        auto_explore.set_target(target, path)
        
        self.message_log.add_info("Traveling to upward stairs...")
        # Clear pathfinding cache for fresh start
        self.pathfinder.clear_cache()
