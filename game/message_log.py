"""
Message log system with word wrapping.
"""

from typing import List, Tuple
from collections import deque


class Message:
    """Represents a single message with color."""
    
    def __init__(self, text: str, color: str = 'white'):
        self.text = text
        self.color = color


class MessageLog:
    """Manages game messages with word wrapping and scrolling."""
    
    def __init__(self, width: int = 40, height: int = 19, max_messages: int = 1000, game_state=None):
        self.width = width
        self.height = height
        self.max_messages = max_messages
        self.messages: deque = deque(maxlen=max_messages)
        self.wrapped_lines: List[Tuple[str, str]] = []  # (text, color) pairs
        self.game_state = game_state
    
    def add_message(self, text: str, color: str = 'white') -> None:
        """Add a new message to the log."""
        message = Message(text, color)
        self.messages.append(message)
        self._rewrap_messages()
        # Request a render when a new message is added
        if self.game_state:
            self.game_state.request_render()
    
    def add_debug(self, text: str) -> None:
        """Add a debug message."""
        self.add_message(f"DEBUG: {text}", 'cyan')
    
    def add_info(self, text: str) -> None:
        """Add an info message."""
        self.add_message(text, 'white')
    
    def add_warning(self, text: str) -> None:
        """Add a warning message."""
        self.add_message(text, 'yellow')
    
    def add_error(self, text: str) -> None:
        """Add an error message."""
        self.add_message(text, 'red')
    
    def add_combat(self, text: str) -> None:
        """Add a combat message."""
        self.add_message(text, 'red')
    
    def add_system(self, text: str) -> None:
        """Add a system message."""
        self.add_message(text, 'green')
    
    def _rewrap_messages(self) -> None:
        """Rewrap all messages to fit the display width."""
        self.wrapped_lines.clear()
        
        for message in self.messages:
            wrapped = self._wrap_text(message.text, self.width)
            for line in wrapped:
                self.wrapped_lines.append((line, message.color))
    
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to fit within the specified width."""
        if not text:
            return ['']
        
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            # Check if adding this word would exceed the width
            word_length = len(word)
            space_length = 1 if current_line else 0
            
            if current_length + space_length + word_length <= width:
                current_line.append(word)
                current_length += space_length + word_length
            else:
                # Start a new line
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Handle words longer than the width
                if word_length > width:
                    # Split long words
                    while word_length > width:
                        lines.append(word[:width])
                        word = word[width:]
                        word_length = len(word)
                
                current_line = [word] if word else []
                current_length = len(word) if word else 0
        
        # Add the last line if it has content
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else ['']
    
    def get_recent_lines(self, count: int = None) -> List[Tuple[str, str]]:
        """Get the most recent lines for display."""
        if count is None:
            count = self.height
        
        # Return the last 'count' lines
        return self.wrapped_lines[-count:] if self.wrapped_lines else []
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        self.wrapped_lines.clear()
    
    def get_line_count(self) -> int:
        """Get the total number of wrapped lines."""
        return len(self.wrapped_lines)
