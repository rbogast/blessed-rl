"""
Item-related components for the inventory and equipment system.
"""

from ecs.component import Component
from typing import Dict, Optional


class Item(Component):
    """Base component for all items."""
    
    def __init__(self, name: str, description: str, item_type: str, value: int = 0, special: str = None):
        self.name = name
        self.description = description
        self.item_type = item_type  # weapon, armor, consumable, misc
        self.value = value
        self.special = special  # Special property for unique items like persistence artifacts


class Equipment(Component):
    """Component for equippable items."""
    
    def __init__(self, slot: str, attack_bonus: int = 0, defense_bonus: int = 0, 
                 attribute_bonuses: Optional[Dict[str, int]] = None):
        self.slot = slot  # weapon, armor, accessory
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.attribute_bonuses = attribute_bonuses or {}


class Consumable(Component):
    """Component for consumable items."""
    
    def __init__(self, effect_type: str, effect_value: int, uses: int = 1):
        self.effect_type = effect_type  # heal, mana, buff, etc.
        self.effect_value = effect_value
        self.uses = uses


class Inventory(Component):
    """Component for entities that can carry items."""
    
    def __init__(self, capacity: int = 20):
        self.items = []  # List of entity IDs
        self.capacity = capacity
    
    def add_item(self, item_entity_id: int) -> bool:
        """Add an item to the inventory. Returns True if successful."""
        if len(self.items) < self.capacity:
            self.items.append(item_entity_id)
            return True
        return False
    
    def remove_item(self, item_entity_id: int) -> bool:
        """Remove an item from the inventory. Returns True if successful."""
        if item_entity_id in self.items:
            self.items.remove(item_entity_id)
            return True
        return False
    
    def is_full(self) -> bool:
        """Check if inventory is full."""
        return len(self.items) >= self.capacity
    
    def get_item_count(self) -> int:
        """Get the number of items in inventory."""
        return len(self.items)


class EquipmentSlots(Component):
    """Component for tracking equipped items."""
    
    def __init__(self):
        self.weapon = None      # Entity ID of equipped weapon
        self.armor = None       # Entity ID of equipped armor
        self.accessory = None   # Entity ID of equipped accessory
    
    def equip_item(self, item_entity_id: int, slot: str) -> Optional[int]:
        """Equip an item in the specified slot. Returns previously equipped item ID if any."""
        previous_item = None
        
        if slot == 'weapon':
            previous_item = self.weapon
            self.weapon = item_entity_id
        elif slot == 'armor':
            previous_item = self.armor
            self.armor = item_entity_id
        elif slot == 'accessory':
            previous_item = self.accessory
            self.accessory = item_entity_id
        
        return previous_item
    
    def unequip_item(self, slot: str) -> Optional[int]:
        """Unequip an item from the specified slot. Returns the unequipped item ID if any."""
        unequipped_item = None
        
        if slot == 'weapon':
            unequipped_item = self.weapon
            self.weapon = None
        elif slot == 'armor':
            unequipped_item = self.armor
            self.armor = None
        elif slot == 'accessory':
            unequipped_item = self.accessory
            self.accessory = None
        
        return unequipped_item
    
    def get_equipped_items(self) -> Dict[str, Optional[int]]:
        """Get all equipped items as a dictionary."""
        return {
            'weapon': self.weapon,
            'armor': self.armor,
            'accessory': self.accessory
        }


class Pickupable(Component):
    """Marker component for items that can be picked up from the ground."""
    pass


class Throwable(Component):
    """Component for items that can be thrown."""
    
    def __init__(self, weight: float = 1.0, damage_modifier: float = 1.0):
        self.weight = weight  # Weight affects throwing distance and damage
        self.damage_modifier = damage_modifier  # Multiplier for physics damage


class LightEmitter(Component):
    """Component for items that emit light."""
    
    def __init__(self, brightness: int, fuel: int, active: bool = True):
        self.brightness = brightness  # Light radius/intensity
        self.fuel = fuel             # Fuel remaining
        self.active = active         # Whether light is currently on
        self.max_fuel = fuel         # Store original fuel amount for reference
