"""
Skills system for managing character abilities and progression.
"""

from ecs.system import System
from components.skills import Skills
from components.character import Experience
import random


class SkillsSystem(System):
    """Manages skill progression and calculations."""
    
    def __init__(self, world, message_log):
        super().__init__(world)
        self.message_log = message_log
    
    def update(self, dt: float = 0.0) -> None:
        """Skills system doesn't auto-update."""
        pass
    
    def get_skill_level(self, entity_id: int, skill_name: str) -> int:
        """Get skill level for an entity."""
        skills = self.world.get_component(entity_id, Skills)
        if skills:
            return skills.get_skill(skill_name)
        return 0
    
    def increase_skill(self, entity_id: int, skill_name: str, amount: int = 1) -> bool:
        """Increase a skill and return True if it increased."""
        skills = self.world.get_component(entity_id, Skills)
        if not skills:
            # Add skills component if entity doesn't have one
            skills = Skills()
            self.world.add_component(entity_id, skills)
        
        old_level = skills.get_skill(skill_name)
        new_level = skills.increase_skill(skill_name, amount)
        
        if new_level > old_level:
            self.message_log.add_info(f"Your {skill_name} skill increased to {new_level}!")
            return True
        
        return False
    
    def try_skill_gain(self, entity_id: int, skill_name: str, difficulty: int = 50) -> bool:
        """
        Try to gain skill based on usage.
        Higher difficulty actions have better chance to increase skill.
        """
        current_level = self.get_skill_level(entity_id, skill_name)
        
        # Calculate chance based on difficulty and current level
        # Higher difficulty = better chance, higher level = lower chance
        base_chance = min(difficulty, 90)  # Cap at 90%
        level_penalty = current_level * 2  # 2% penalty per level
        final_chance = max(5, base_chance - level_penalty)  # Minimum 5% chance
        
        if random.randint(1, 100) <= final_chance:
            return self.increase_skill(entity_id, skill_name, 1)
        
        return False
    
    def calculate_throwing_accuracy(self, throwing_skill: int, distance: int, 
                                  agility: int = 10) -> float:
        """
        Calculate throwing accuracy as a percentage (0.0 to 1.0).
        Perfect accuracy (1.0) means item lands exactly on target.
        """
        # Base accuracy from skill
        base_accuracy = min(0.9, throwing_skill * 0.05)  # 5% per skill level, max 90%
        
        # Distance penalty
        distance_penalty = distance * 0.02  # 2% penalty per tile
        
        # Agility bonus
        agility_bonus = (agility - 10) * 0.01  # 1% per point above 10
        
        final_accuracy = base_accuracy - distance_penalty + agility_bonus
        return max(0.1, min(0.95, final_accuracy))  # Clamp between 10% and 95%
    
    def calculate_throwing_distance(self, strength: int, item_weight: float) -> int:
        """Calculate maximum throwing distance based on strength and item weight."""
        # Base distance from strength
        base_distance = strength * 2
        
        # Weight penalty
        weight_penalty = item_weight * 2
        
        # Calculate final distance
        max_distance = max(1, int(base_distance - weight_penalty))
        return min(max_distance, 15)  # Cap at 15 tiles as specified
    
    def calculate_throwing_damage(self, item_weight: float, distance_thrown: int, 
                                strength: int, damage_modifier: float = 1.0) -> int:
        """Calculate damage dealt by a thrown object."""
        # Base damage from weight and distance
        base_damage = int(item_weight * distance_thrown * 0.5)
        
        # Strength bonus
        strength_bonus = max(0, strength - 10)
        
        # Apply damage modifier
        total_damage = int((base_damage + strength_bonus) * damage_modifier)
        
        return max(1, total_damage)  # Minimum 1 damage
