"""
Character-related components for attributes and experience.
"""

from ecs.component import Component


class CharacterAttributes(Component):
    """Character attributes that affect various game mechanics."""
    
    def __init__(self, strength=10, agility=10, constitution=10, 
                 intelligence=10, willpower=10, perception=10):
        self.strength = strength          # Affects damage and contributes to HP
        self.agility = agility            # Affects speed and dodge
        self.constitution = constitution  # Affects HP and vulnerability to physical debuffs
        self.intelligence = intelligence  # Affects aptitude for magic
        self.willpower = willpower        # Affects resistance to charm, intimidate
        self.perception = perception      # Awareness and ability to notice details, traps, and hidden things
    
    def get_total_attributes(self) -> int:
        """Get sum of all attributes for display purposes."""
        return (self.strength + self.agility + self.constitution + 
                self.intelligence + self.willpower + self.perception)


class Experience(Component):
    """Experience points and level tracking."""
    
    def __init__(self, current_xp=0, level=1):
        self.current_xp = current_xp
        self.level = level
    
    def xp_for_next_level(self) -> int:
        """Calculate XP required for next level using 1.5x curve starting at 100."""
        if self.level == 1:
            return 100
        
        # Calculate cumulative XP needed for current level
        total_xp_needed = 0
        xp_for_level = 100
        
        for level in range(2, self.level + 2):  # +2 because we want next level
            total_xp_needed += xp_for_level
            if level < self.level + 1:  # Don't multiply for the target level calculation
                xp_for_level = int(xp_for_level * 1.5)
        
        return total_xp_needed
    
    def xp_for_current_level(self) -> int:
        """Calculate XP that was required to reach current level."""
        if self.level == 1:
            return 0
        
        total_xp_needed = 0
        xp_for_level = 100
        
        for level in range(2, self.level + 1):
            total_xp_needed += xp_for_level
            xp_for_level = int(xp_for_level * 1.5)
        
        return total_xp_needed
    
    def add_xp(self, amount: int) -> bool:
        """Add XP and return True if leveled up."""
        self.current_xp += amount
        
        # Check for level up
        while self.current_xp >= self.xp_for_next_level():
            self.level += 1
            return True
        
        return False
    
    def get_xp_progress(self) -> tuple:
        """Get current XP progress as (current_in_level, needed_for_next)."""
        current_level_base = self.xp_for_current_level()
        next_level_total = self.xp_for_next_level()
        
        current_in_level = self.current_xp - current_level_base
        needed_for_next = next_level_total - current_level_base
        
        return current_in_level, needed_for_next


class XPValue(Component):
    """XP value that an entity gives when killed."""
    
    def __init__(self, xp_value: int):
        self.xp_value = xp_value
