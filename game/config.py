"""
Centralized game configuration.
"""


class GameConfig:
    """Central configuration for game dimensions and constants."""
    
    # Base layout dimensions - change these to experiment with different layouts
    SCREEN_WIDTH = 80           # Total screen width
    SCREEN_HEIGHT = 24          # Total screen height
    SIDEBAR_WIDTH = 35          # Width of left sidebar panel
    CHARACTER_INFO_HEIGHT = 11  # Height of character info panel
    
    # UI display options
    SHOW_VERTICAL_DIVIDER = False  # Controls whether vertical divider bar is shown
    
    # Calculated layout dimensions - automatically derived from base dimensions
    BORDER_WIDTH = 1 if SHOW_VERTICAL_DIVIDER else 0   # Vertical border between panels
    MAP_WIDTH = SCREEN_WIDTH - SIDEBAR_WIDTH - BORDER_WIDTH  # Map panel width (51 or 52)
    MAP_HEIGHT = SCREEN_HEIGHT - 1                     # Map viewport height (23, -1 for status bar)
    GAME_INFO_HEIGHT = SCREEN_HEIGHT - CHARACTER_INFO_HEIGHT  # Message/menu panel height (13)
    
    # Legacy aliases for backward compatibility
    VIEWPORT_WIDTH = MAP_WIDTH
    VIEWPORT_HEIGHT = MAP_HEIGHT
    TOTAL_SCREEN_HEIGHT = SCREEN_HEIGHT
    MESSAGE_LOG_WIDTH = SIDEBAR_WIDTH
    MESSAGE_LOG_HEIGHT = GAME_INFO_HEIGHT
    
    # Chunk configuration
    CHUNK_WIDTH = 40
    CHUNK_HEIGHT = MAP_HEIGHT  # Chunks are full height
    
    # Camera configuration
    CAMERA_VIEWPORT_WIDTH = VIEWPORT_WIDTH
    CAMERA_VIEWPORT_HEIGHT = VIEWPORT_HEIGHT
    
    # World generation
    HALO_SIZE = 10
    LEGACY_HALO_SIZE = 5  # For compatibility layer
    
    # Field of View
    PLAYER_SIGHT_RADIUS = 8
    
    # Rendering colors
    EXPLORED_TILE_COLOR = 'blue'  # Color for explored but not visible tiles
    
    @classmethod
    def get_map_bounds(cls):
        """Get map bounds as (min_x, min_y, max_x, max_y)."""
        return (0, 0, float('inf'), cls.MAP_HEIGHT - 1)
    
    @classmethod
    def is_valid_y(cls, y: int) -> bool:
        """Check if Y coordinate is within valid map bounds."""
        return 0 <= y < cls.MAP_HEIGHT
    
    @classmethod
    def is_valid_position(cls, x: int, y: int) -> bool:
        """Check if position is within valid map bounds."""
        return x >= 0 and cls.is_valid_y(y)
