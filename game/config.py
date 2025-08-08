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
    
    # Dungeon level configuration
    LEVEL_WIDTH = MAP_WIDTH     # Width of each dungeon level - match viewport width
    LEVEL_HEIGHT = MAP_HEIGHT   # Height of each dungeon level - match viewport height
    PERSISTENT_LEVELS = False    # If True, keep levels in memory; if False, delete levels unless they have persistence artifacts
    
    # Camera configuration
    CAMERA_VIEWPORT_WIDTH = VIEWPORT_WIDTH
    CAMERA_VIEWPORT_HEIGHT = VIEWPORT_HEIGHT
    
    
    # Field of View
    PLAYER_SIGHT_RADIUS = 45
    
    # Rendering colors
    EXPLORED_TILE_COLOR = 'blue'  # Color for explored but not visible tiles
    PENUMBRA_COLOR = 'blue'      # Color for tiles in penumbra (dim lighting)
    UNLIT_COLOR = 'blue'         # Color for tiles in FOV but outside light radius
    
    @classmethod
    def get_map_bounds(cls):
        """Get map bounds as (min_x, min_y, max_x, max_y)."""
        return (0, 0, cls.LEVEL_WIDTH - 1, cls.LEVEL_HEIGHT - 1)
    
    @classmethod
    def is_valid_y(cls, y: int) -> bool:
        """Check if Y coordinate is within valid map bounds."""
        return 0 <= y < cls.LEVEL_HEIGHT
    
    @classmethod
    def is_valid_x(cls, x: int) -> bool:
        """Check if X coordinate is within valid map bounds."""
        return 0 <= x < cls.LEVEL_WIDTH
    
    @classmethod
    def is_valid_position(cls, x: int, y: int) -> bool:
        """Check if position is within valid map bounds."""
        return cls.is_valid_x(x) and cls.is_valid_y(y)
