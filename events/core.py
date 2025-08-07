"""
Core event system classes.
"""

from typing import Dict, List, Callable, Any
from abc import ABC, abstractmethod


class Event(ABC):
    """Base class for all events."""
    pass


class EventManager:
    """Manages event subscriptions and publishing."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Subscribe a callback to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Unsubscribe a callback from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass  # Callback wasn't subscribed
    
    def emit(self, event_type: str, event: Event) -> None:
        """Emit an event to all subscribers."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    # Log error but don't crash the game
                    print(f"Error in event callback for {event_type}: {e}")
    
    def clear_subscribers(self, event_type: str = None) -> None:
        """Clear all subscribers for an event type, or all subscribers if no type specified."""
        if event_type is None:
            self._subscribers.clear()
        elif event_type in self._subscribers:
            self._subscribers[event_type].clear()
