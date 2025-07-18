"""Text formatting utilities for terminal output."""

import re
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
        elif color == 'dark_red':
            return self.term.color(88) + text + self.term.normal  # Dark red color
        else:
            return text
    
    def apply_highlight(self, text: str) -> str:
        """Apply highlighting (reverse colors) to text."""
        return self.term.reverse + text + self.term.normal
    
    def calculate_visual_length(self, text: str) -> int:
        """Calculate the visual length of text, excluding ANSI escape codes."""
        # Remove ANSI escape sequences to get visual length
        # This regex handles both standard ANSI codes and blessed terminal codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\([AB])')
        clean_text = ansi_escape.sub('', text)
        return len(clean_text)
    
    def truncate_to_visual_length(self, text: str, max_length: int) -> str:
        """Truncate text to a specific visual length, preserving ANSI codes."""
        # If no ANSI codes, simple truncation
        if '\x1b' not in text and '\x1B' not in text:
            return text[:max_length]
        
        # Complex case: preserve ANSI codes while truncating visual content
        # Use the same improved regex pattern as calculate_visual_length
        ansi_escape = re.compile(r'(\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\([AB]))')
        parts = ansi_escape.split(text)
        
        result = ""
        visual_count = 0
        
        for part in parts:
            if ansi_escape.match(part):
                # This is an ANSI escape code, add it without counting
                result += part
            else:
                # This is regular text, count and potentially truncate
                remaining = max_length - visual_count
                if remaining <= 0:
                    break
                if len(part) <= remaining:
                    result += part
                    visual_count += len(part)
                else:
                    result += part[:remaining]
                    visual_count += remaining
                    break
        
        return result
    
    def format_menu_line(self, text: str, is_highlighted: bool, max_width: int) -> str:
        """Format a menu line with proper highlighting and padding."""
        # Calculate visual length of the original text
        visual_length = self.calculate_visual_length(text)
        
        # Truncate if too long
        if visual_length > max_width:
            text = self.truncate_to_visual_length(text, max_width)
            visual_length = max_width
        
        # Apply highlighting if needed
        if is_highlighted:
            text = self.apply_highlight(text)
        
        # Add padding to reach exact width
        padding_needed = max_width - visual_length
        text += ' ' * max(0, padding_needed)
        
        return text
