"""
Game state management.
"""

from enum import Enum
from typing import Optional
from game.dungeon_level import DungeonManager
from game.config import GameConfig


class GameState(Enum):
    """Possible game states."""
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    MENU = "menu"
    MAP_PREVIEW = "map_preview"


class GameStateManager:
    """Manages the current game state and transitions."""
    
    def __init__(self):
        self.current_state = GameState.PLAYING
        self.player_entity: Optional[int] = None
        self.turn_count = 0
        self.player_acted = False  # Flag for turn-based logic
        self.game_over_reason = ""
        self.final_position = 0
        self.needs_render = True  # Flag to control when screen should be redrawn
        
        # Dungeon management
        self.dungeon_manager = DungeonManager(persistent_levels=GameConfig.PERSISTENT_LEVELS)
    
    def set_state(self, new_state: GameState) -> None:
        """Change the game state."""
        self.current_state = new_state
    
    def is_playing(self) -> bool:
        """Check if the game is in playing state."""
        return self.current_state == GameState.PLAYING
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.current_state == GameState.GAME_OVER
    
    def is_map_preview(self) -> bool:
        """Check if the game is in map preview mode."""
        return self.current_state == GameState.MAP_PREVIEW
    
    def set_player_entity(self, entity_id: int) -> None:
        """Set the player entity ID."""
        self.player_entity = entity_id
    
    def get_player_entity(self) -> Optional[int]:
        """Get the player entity ID."""
        return self.player_entity
    
    def player_turn_taken(self) -> None:
        """Mark that the player has taken their turn."""
        self.player_acted = True
        self.turn_count += 1
    
    def reset_turn_flag(self) -> None:
        """Reset the player action flag for the next turn."""
        self.player_acted = False
    
    def has_player_acted(self) -> bool:
        """Check if the player has acted this turn."""
        return self.player_acted
    
    def game_over(self, reason: str, final_x: int) -> None:
        """End the game with a reason and final position."""
        self.current_state = GameState.GAME_OVER
        self.game_over_reason = reason
        self.final_position = final_x
        self.request_render()  # Request render for game over screen
    
    def get_game_over_message(self) -> str:
        """Get the game over message with final position."""
        return f"GAME OVER: {self.game_over_reason}\nYou reached position X={self.final_position} in {self.turn_count} turns."
    
    def request_render(self) -> None:
        """Request that the screen be redrawn."""
        self.needs_render = True
    
    def should_render(self) -> bool:
        """Check if the screen needs to be redrawn."""
        return self.needs_render
    
    def render_complete(self) -> None:
        """Mark that the screen has been redrawn."""
        self.needs_render = False
    
    def reset(self) -> None:
        """Reset the game state to initial values."""
        self.current_state = GameState.PLAYING
        self.player_entity = None
        self.turn_count = 0
        self.player_acted = False
        self.game_over_reason = ""
        self.final_position = 0
        self.needs_render = True
        self.dungeon_manager.clear_all_levels()  # Clear all dungeon levels
    
    # Dungeon level management methods
    def get_current_level_id(self) -> int:
        """Get the current dungeon level ID."""
        return self.dungeon_manager.current_level_id
    
    def get_current_level(self):
        """Get the current dungeon level."""
        return self.dungeon_manager.get_current_level()
    
    def change_level(self, new_level_id: int) -> None:
        """Change to a new dungeon level."""
        old_level_id = self.dungeon_manager.current_level_id
        self.dungeon_manager.change_level(new_level_id, old_level_id)
    
    def has_level(self, level_id: int) -> bool:
        """Check if a level exists in memory."""
        return self.dungeon_manager.has_level(level_id)
    
    def add_level(self, level) -> None:
        """Add a level to the dungeon manager."""
        self.dungeon_manager.add_level(level)
    
    def get_level(self, level_id: int):
        """Get a specific level by ID."""
        return self.dungeon_manager.get_level(level_id)
