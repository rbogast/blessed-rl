"""
Game state management.
"""

from enum import Enum
from typing import Optional


class GameState(Enum):
    """Possible game states."""
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    MENU = "menu"


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
        self.blood_tiles = set()  # Simple set of (x, y) coordinates for bloody tiles
    
    def set_state(self, new_state: GameState) -> None:
        """Change the game state."""
        self.current_state = new_state
    
    def is_playing(self) -> bool:
        """Check if the game is in playing state."""
        return self.current_state == GameState.PLAYING
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.current_state == GameState.GAME_OVER
    
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
        self.blood_tiles = set()  # Clear blood tiles on reset
