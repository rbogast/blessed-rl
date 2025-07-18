"""
Skills components for tracking character abilities.
"""

from ecs.component import Component
from typing import Dict


class Skills(Component):
    """Component for tracking character skills."""
    
    def __init__(self):
        self.skills: Dict[str, int] = {
            'throwing': 1,  # Start with basic throwing skill
        }
    
    def get_skill(self, skill_name: str) -> int:
        """Get skill level for a specific skill."""
        return self.skills.get(skill_name, 0)
    
    def set_skill(self, skill_name: str, level: int) -> None:
        """Set skill level for a specific skill."""
        self.skills[skill_name] = max(0, level)
    
    def increase_skill(self, skill_name: str, amount: int = 1) -> int:
        """Increase skill level and return new level."""
        current = self.get_skill(skill_name)
        new_level = current + amount
        self.set_skill(skill_name, new_level)
        return new_level
    
    def has_skill(self, skill_name: str) -> bool:
        """Check if character has any level in a skill."""
        return self.get_skill(skill_name) > 0
