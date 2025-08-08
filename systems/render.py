"""
Rendering system using blessed for terminal output.
Refactored for modularity and scalability.
"""

from ecs.system import System
from game.camera import Camera
from game.message_log import MessageLog
from game.level_world_gen import LevelWorldGenerator
from game.game_state import GameStateManager
from game.glyph_config import GlyphConfig
from game.config import GameConfig
from systems.menu import MenuManager
from ui.text_formatter import TextFormatter
from ui.status_display import StatusDisplay
from rendering.entity_renderer import EntityRenderer
from rendering.unified_tile_renderer import UnifiedTileRenderer
import blessed
from contextlib import ExitStack
import atexit
import sys
import os


class RenderSystem(System):
    """Handles all terminal rendering using blessed with fullscreen mode."""
    
    def __init__(self, world, camera: Camera, message_log: MessageLog, 
                 world_generator: LevelWorldGenerator, game_state: GameStateManager, tile_effects_system=None, glyph_config=None):
        super().__init__(world)
        self.camera = camera
        self.message_log = message_log
        self.world_generator = world_generator
        self.game_state = game_state
        
        # Setup encoding for cross-platform compatibility
        self._setup_encoding()
        
        # Use provided glyph configuration or create default
        self.glyph_config = glyph_config if glyph_config else GlyphConfig()
        self.term = blessed.Terminal()
        
        # Log platform and character set information
        self._log_startup_info()
        
        # Terminal state management
        self._stack = ExitStack()
        self._stack.enter_context(self.term.fullscreen())
        self._stack.enter_context(self.term.cbreak())
        self._stack.enter_context(self.term.hidden_cursor())
        atexit.register(self.cleanup)
        
        # Screen layout constants - use calculated dimensions from config
        self.CHAR_INFO_WIDTH = GameConfig.SIDEBAR_WIDTH
        self.CHAR_INFO_HEIGHT = GameConfig.CHARACTER_INFO_HEIGHT
        self.MESSAGE_WIDTH = GameConfig.SIDEBAR_WIDTH
        self.MESSAGE_HEIGHT = GameConfig.GAME_INFO_HEIGHT
        self.MAP_WIDTH = GameConfig.MAP_WIDTH
        self.MAP_HEIGHT = GameConfig.MAP_HEIGHT
        self.TOTAL_SCREEN_HEIGHT = GameConfig.SCREEN_HEIGHT
        
        # Initialize modular components
        self.text_formatter = TextFormatter(self.term)
        self.menu_manager = MenuManager(world)
        self.status_display = StatusDisplay(world, world_generator, game_state, self.text_formatter)
        self.entity_renderer = EntityRenderer(world)
        self.tile_renderer = UnifiedTileRenderer(world, world_generator, self.glyph_config, game_state)
        
        # Unified FOV/Lighting system will be set later by main.py
        self.unified_fov_lighting = None
    
    def update(self, dt: float = 0.0) -> None:
        """Render the complete game screen."""
        if self.game_state.is_game_over():
            self._render_game_over()
        else:
            self._render_game()
    
    def _render_game(self) -> None:
        """Render the main game screen with new layout."""
        # Build the entire screen as a string buffer
        screen_buffer = []
        
        # Get viewport bounds and message lines
        left, top, right, bottom = self.camera.get_viewport_bounds()
        message_lines = self.message_log.get_recent_lines(self.MESSAGE_HEIGHT)
        
        
        # Build each row of the screen (24 total rows)
        for screen_y in range(self.TOTAL_SCREEN_HEIGHT):
            line = ""
            
            # Left panel: Character info (first 10 rows) or messages (remaining rows)
            if screen_y < self.CHAR_INFO_HEIGHT:
                # Character info section - use the same formatting approach as menus
                char_info = self.status_display.get_character_info_line(screen_y)
                formatted_char_info = self.text_formatter.format_character_info_line(char_info, self.CHAR_INFO_WIDTH)
                line += formatted_char_info
            else:
                # Message section - show inventory/menus or messages
                message_row = screen_y - self.CHAR_INFO_HEIGHT
                
                if self.menu_manager.is_menu_active() or self.menu_manager.is_inventory_shown():
                    # Show menu or inventory
                    player_entity = self.game_state.get_player_entity()
                    if player_entity:
                        menu_line, is_highlighted = self.menu_manager.get_menu_line(message_row, player_entity)
                        formatted_line = self.text_formatter.format_menu_line(menu_line, is_highlighted, self.MESSAGE_WIDTH)
                        line += formatted_line
                    else:
                        line += self.term.ljust('', self.MESSAGE_WIDTH)
                else:
                    # Show regular messages
                    if message_row < len(message_lines):
                        text, color = message_lines[message_row]
                        colored_text = self.text_formatter.apply_color(text, color)
                        # Use blessed's methods for truncation and padding
                        formatted_text = self.term.ljust(self.term.truncate(colored_text, self.MESSAGE_WIDTH), self.MESSAGE_WIDTH)
                        line += formatted_text
                    else:
                        # Empty message line - use blessed's ljust for padding
                        line += self.term.ljust('', self.MESSAGE_WIDTH)
            
            # Add vertical border (if enabled)
            if GameConfig.SHOW_VERTICAL_DIVIDER:
                line += self.text_formatter.apply_color('│', 'white')
            
            # Right panel: Map or status line
            if screen_y < self.MAP_HEIGHT:
                # Map area (rows 0-22)
                world_y = top + screen_y
                for screen_x in range(self.MAP_WIDTH):
                    world_x = left + screen_x
                    char, color = self.tile_renderer.get_tile_display(world_x, world_y)
                    line += self.text_formatter.apply_color(char, color)
            else:
                # Status line (row 23)
                status_line = self.status_display.get_status_line()
                line += status_line
            
            screen_buffer.append(line)
        
        # Render the entire screen at once
        output = self.term.home
        for i, line in enumerate(screen_buffer):
            output += self.term.move_xy(0, i) + line
        
        # Output everything at once and flush
        print(output, end='', flush=True)
    
    def _render_game_over(self) -> None:
        """Render the game over screen."""
        # Move to home and clear screen for game over
        print(self.term.home + self.term.clear, end='')
        
        message = self.game_state.get_game_over_message()
        lines = message.split('\n')
        
        # Center the message on screen using blessed's center method
        screen_height = self.term.height
        start_y = (screen_height - len(lines)) // 2
        
        for i, line in enumerate(lines):
            y = start_y + i
            centered_line = self.term.center(self.term.red + line + self.term.normal)
            print(self.term.move_y(y) + centered_line)
        
        # Show restart instruction
        restart_msg = "Press any key to exit..."
        y = start_y + len(lines) + 2
        centered_restart = self.term.center(restart_msg)
        print(self.term.move_y(y) + centered_restart)
        
        # Flush output
        print('', end='', flush=True)
    
    # Menu management methods - delegate to MenuManager
    def show_equip_menu(self) -> None:
        """Show the equip menu."""
        self.menu_manager.show_menu('equip')
    
    def show_use_menu(self) -> None:
        """Show the use menu."""
        self.menu_manager.show_menu('use')
    
    def show_drop_menu(self) -> None:
        """Show the drop menu."""
        self.menu_manager.show_menu('drop')
    
    def show_throwing_menu(self) -> None:
        """Show the throwing menu."""
        self.menu_manager.show_menu('throwing')
    
    def toggle_inventory_display(self) -> None:
        """Toggle between showing character stats and inventory."""
        if self.menu_manager.is_inventory_shown():
            self.menu_manager.hide_all()
        else:
            self.menu_manager.show_inventory_display()
    
    def hide_all_menus(self) -> None:
        """Hide all menus and return to messages."""
        self.menu_manager.hide_all()
    
    def navigate_menu_up(self) -> None:
        """Navigate up in the current menu."""
        self.menu_manager.navigate_up()
    
    def navigate_menu_down(self) -> None:
        """Navigate down in the current menu."""
        self.menu_manager.navigate_down()
    
    def get_selected_menu_item(self) -> int:
        """Get the currently selected menu item number (1-based) or -1 if none."""
        return self.menu_manager.get_selected_item_number()
    
    # Cache management - delegate to EntityRenderer
    def invalidate_cache(self) -> None:
        """Mark the entity cache as dirty."""
        self.entity_renderer.invalidate_cache()
    
    def set_throwing_system(self, throwing_system) -> None:
        """Set the throwing system reference for rendering throwing cursor and line."""
        self.tile_renderer.throwing_system = throwing_system
    
    def set_examine_system(self, examine_system) -> None:
        """Set the examine system reference for rendering examine cursor."""
        self.tile_renderer.examine_system = examine_system
    
    def set_fov_system(self, fov_system) -> None:
        """Set the unified FOV/Lighting system reference for the tile renderer."""
        self.unified_fov_lighting = fov_system
        self.tile_renderer.set_unified_fov_lighting(fov_system)
        # Keep fov_system for compatibility
        self.fov_system = fov_system
    
    def _setup_encoding(self) -> None:
        """Setup proper encoding for cross-platform compatibility."""
        # Try to ensure UTF-8 encoding on stdout/stderr
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except (AttributeError, OSError):
                # Python < 3.7 or encoding not supported
                pass
        
        # Set environment variables for better Unicode support
        if os.name == 'nt':  # Windows
            # Try to enable UTF-8 mode on Windows
            os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
            # Enable ANSI escape sequences on Windows 10+
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except (ImportError, AttributeError, OSError):
                pass
    
    def _log_startup_info(self) -> None:
        """Log startup information about platform and character set."""
        charset = self.glyph_config.get_character_set()
        
        # Add startup message to game log
        self.message_log.add_system(f"Character set: {charset}")
        
        # Detailed debug info if requested
        if os.environ.get('BLESSED_RL_DEBUG'):
            platform_info = self.glyph_config.platform_detector.get_platform_info()
            self.message_log.add_system(f"Platform: {platform_info['system']}")
            self.message_log.add_system(f"Encoding: {platform_info['encoding']}")
            self.message_log.add_system(f"Unicode support: {platform_info['supports_unicode']}")
            
            # Test character rendering
            test_chars = {
                'unicode': ['·', '▒', '↑', '♣'],
                'ascii': ['.', '#', '^', '&'],
                'cp437': ['·', '▒', '↑', '♣']
            }
            
            if charset in test_chars:
                char_list = ', '.join(test_chars[charset])
                self.message_log.add_system(f"Test chars: {char_list}")
    
    def cleanup(self) -> None:
        """Clean up terminal state."""
        print(self.term.normal + self.term.show_cursor, end='')
        self._stack.close()
