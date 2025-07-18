"""Text formatting utilities for terminal output."""

import blessed


class TextFormatter:
    """Handles text formatting, coloring, and highlighting for terminal output."""
    
    def __init__(self, terminal: blessed.Terminal):
        self.term = terminal
    
    def apply_color(self, text: str, color: str) -> str:
        """Apply terminal color to text."""
        if color == 'white':
            return self.term.white + text + self.term.normal
        elif color == 'yellow':
            return self.term.yellow + text + self.term.normal
        elif color == 'red':
            return self.term.red + text + self.term.normal
        elif color == 'green':
            return self.term.green + text + self.term.normal
        elif color == 'bright_black':
            return self.term.bright_black + text + self.term.normal
        elif color == 'cyan':
            return self.term.cyan + text + self.term.normal
        elif color == 'magenta':
            return self.term.magenta + text + self.term.normal
        elif color == 'black_on_magenta':
            return self.term.black_on_magenta + text + self.term.normal
        elif color == 'blue':
            return self.term.blue + text + self.term.normal
        elif color == 'black':
            return self.term.black + text + self.term.normal
        elif color == 'dark_red':
            return self.term.color(88) + text + self.term.normal  # Dark red color
        else:
            return text
    
    def apply_highlight(self, text: str) -> str:
        """Apply highlighting (reverse colors) to text."""
        return self.term.reverse + text + self.term.normal
    
    def calculate_visual_length(self, text: str) -> int:
        """Calculate the visual length of text, excluding ANSI escape codes."""
        return self.term.length(text)
    
    def truncate_to_visual_length(self, text: str, max_length: int) -> str:
        """Truncate text to a specific visual length, preserving ANSI codes."""
        return self.term.truncate(text, max_length)
    
    def format_menu_line(self, text: str, is_highlighted: bool, max_width: int) -> str:
        """Format a menu line with proper highlighting and padding."""
        # Truncate if too long using blessed's method
        text = self.term.truncate(text, max_width)
        
        # Apply highlighting if needed
        if is_highlighted:
            text = self.apply_highlight(text)
        
        # Use blessed's ljust for padding
        return self.term.ljust(text, max_width)
    
    def format_character_info_line(self, text: str, max_width: int) -> str:
        """Format a character info line with proper padding using blessed's methods."""
        # Truncate if too long and pad to width using blessed's methods
        text = self.term.truncate(text, max_width)
        return self.term.ljust(text, max_width)
