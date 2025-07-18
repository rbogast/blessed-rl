"""
Inventory management system for handling items, equipment, and consumables.
"""

from ecs.system import System
from components.core import Position, Player
from components.items import Item, Equipment, Consumable, Inventory, EquipmentSlots, Pickupable
from components.combat import Health
from components.character import CharacterAttributes
from typing import Optional, List, Tuple


class InventorySystem(System):
    """Handles inventory management, item usage, and equipment."""
    
    def __init__(self, world, message_log):
        super().__init__(world)
        self.message_log = message_log
        self.render_system = None  # Will be set by the main game
    
    def set_render_system(self, render_system):
        """Set the render system reference for menu invalidation."""
        self.render_system = render_system
    
    def _invalidate_inventory_menu(self):
        """Invalidate the inventory menu cache to force refresh."""
        if self.render_system and hasattr(self.render_system, 'menu_manager'):
            self.render_system.menu_manager.menus['inventory'].invalidate()
    
    def update(self, dt: float = 0.0) -> None:
        """Inventory system doesn't auto-update - it responds to player actions."""
        pass
    
    def pickup_item(self, entity_id: int, item_entity_id: int) -> bool:
        """Try to pick up an item and add it to inventory."""
        inventory = self.world.get_component(entity_id, Inventory)
        if not inventory:
            return False
        
        # Check if inventory is full
        if inventory.is_full():
            if self.world.has_component(entity_id, Player):
                self.message_log.add_warning("Your inventory is full!")
            return False
        
        # Add item to inventory
        if inventory.add_item(item_entity_id):
            # Remove item from world position (make it non-renderable)
            if self.world.has_component(item_entity_id, Position):
                self.world.remove_component(item_entity_id, Position)
            
            # Get item name for message
            item = self.world.get_component(item_entity_id, Item)
            if item:
                item_name = item.name
            else:
                # Check if it's a corpse
                from components.corpse import Corpse
                corpse = self.world.get_component(item_entity_id, Corpse)
                if corpse:
                    item_name = f"{corpse.original_entity_type} corpse"
                else:
                    item_name = "item"
            
            if self.world.has_component(entity_id, Player):
                self.message_log.add_info(f"You pick up the {item_name}.")
                # Invalidate inventory menu to refresh display
                self._invalidate_inventory_menu()
            
            return True
        
        return False
    
    def drop_item(self, entity_id: int, item_entity_id: int) -> bool:
        """Drop an item from inventory to the ground."""
        inventory = self.world.get_component(entity_id, Inventory)
        position = self.world.get_component(entity_id, Position)
        
        if not inventory or not position:
            return False
        
        # Remove from inventory
        if inventory.remove_item(item_entity_id):
            # Place item at entity's position
            self.world.add_component(item_entity_id, Position(position.x, position.y))
            
            # Get item name for message
            item = self.world.get_component(item_entity_id, Item)
            if item:
                item_name = item.name
            else:
                # Check if it's a corpse
                from components.corpse import Corpse
                corpse = self.world.get_component(item_entity_id, Corpse)
                if corpse:
                    item_name = f"{corpse.original_entity_type} corpse"
                else:
                    item_name = "item"
            
            if self.world.has_component(entity_id, Player):
                self.message_log.add_info(f"You drop the {item_name}.")
                # Invalidate inventory menu to refresh display
                self._invalidate_inventory_menu()
            
            return True
        
        return False
    
    def equip_item(self, entity_id: int, item_entity_id: int) -> bool:
        """Equip an item from inventory."""
        inventory = self.world.get_component(entity_id, Inventory)
        equipment_slots = self.world.get_component(entity_id, EquipmentSlots)
        equipment = self.world.get_component(item_entity_id, Equipment)
        
        if not inventory or not equipment_slots or not equipment:
            return False
        
        # Check if item is in inventory
        if item_entity_id not in inventory.items:
            return False
        
        # Equip the item (this may return a previously equipped item)
        previous_item = equipment_slots.equip_item(item_entity_id, equipment.slot)
        
        # Remove the equipped item from inventory
        inventory.remove_item(item_entity_id)
        
        # If there was a previously equipped item, put it back in inventory
        if previous_item:
            inventory.add_item(previous_item)
        
        # Get item name for message
        item = self.world.get_component(item_entity_id, Item)
        item_name = item.name if item else "item"
        
        if self.world.has_component(entity_id, Player):
            self.message_log.add_info(f"You equip the {item_name}.")
            # Invalidate inventory menu to refresh display
            self._invalidate_inventory_menu()
        
        return True
    
    def unequip_item(self, entity_id: int, slot: str) -> bool:
        """Unequip an item from a slot."""
        equipment_slots = self.world.get_component(entity_id, EquipmentSlots)
        inventory = self.world.get_component(entity_id, Inventory)
        
        if not equipment_slots or not inventory:
            return False
        
        # Check if inventory has space
        if inventory.is_full():
            if self.world.has_component(entity_id, Player):
                self.message_log.add_warning("Your inventory is full! Cannot unequip item.")
            return False
        
        # Unequip the item
        unequipped_item = equipment_slots.unequip_item(slot)
        
        if unequipped_item:
            # Add the unequipped item back to inventory
            inventory.add_item(unequipped_item)
            
            # Get item name for message
            item = self.world.get_component(unequipped_item, Item)
            item_name = item.name if item else "item"
            
            if self.world.has_component(entity_id, Player):
                self.message_log.add_info(f"You unequip the {item_name}.")
                # Invalidate inventory menu to refresh display
                self._invalidate_inventory_menu()
            
            return True
        
        return False
    
    def use_consumable(self, entity_id: int, item_entity_id: int) -> bool:
        """Use a consumable item."""
        inventory = self.world.get_component(entity_id, Inventory)
        consumable = self.world.get_component(item_entity_id, Consumable)
        
        if not inventory or not consumable:
            return False
        
        # Check if item is in inventory
        if item_entity_id not in inventory.items:
            return False
        
        # Apply the consumable effect
        success = self._apply_consumable_effect(entity_id, consumable)
        
        if success:
            # Reduce uses
            consumable.uses -= 1
            
            # Get item name for message
            item = self.world.get_component(item_entity_id, Item)
            item_name = item.name if item else "item"
            
            if self.world.has_component(entity_id, Player):
                self.message_log.add_info(f"You use the {item_name}.")
            
            # Remove item if no uses left
            if consumable.uses <= 0:
                inventory.remove_item(item_entity_id)
                self.world.destroy_entity(item_entity_id)
            
            return True
        
        return False
    
    def _apply_consumable_effect(self, entity_id: int, consumable: Consumable) -> bool:
        """Apply the effect of a consumable item."""
        if consumable.effect_type == 'heal':
            health = self.world.get_component(entity_id, Health)
            if health:
                healed = health.heal(consumable.effect_value)
                if healed > 0:
                    if self.world.has_component(entity_id, Player):
                        self.message_log.add_info(f"You heal {healed} HP!")
                    return True
                else:
                    if self.world.has_component(entity_id, Player):
                        self.message_log.add_warning("You are already at full health.")
                    return False
        
        # Add more effect types here as needed
        return False
    
    def get_items_at_position(self, x: int, y: int) -> List[int]:
        """Get all pickupable items at a position."""
        items = []
        entities = self.world.get_entities_with_components(Position, Pickupable)
        
        for entity_id in entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                items.append(entity_id)
        
        return items
    
    def get_inventory_items(self, entity_id: int) -> List[Tuple[int, str, str]]:
        """Get a list of items in inventory as (entity_id, name, type) tuples."""
        inventory = self.world.get_component(entity_id, Inventory)
        if not inventory:
            return []
        
        items = []
        for item_entity_id in inventory.items:
            item = self.world.get_component(item_entity_id, Item)
            if item:
                items.append((item_entity_id, item.name, item.item_type))
        
        return items
    
    def get_equipped_items(self, entity_id: int) -> dict:
        """Get equipped items with their details."""
        equipment_slots = self.world.get_component(entity_id, EquipmentSlots)
        if not equipment_slots:
            return {}
        
        equipped = {}
        for slot, item_entity_id in equipment_slots.get_equipped_items().items():
            if item_entity_id:
                item = self.world.get_component(item_entity_id, Item)
                if item:
                    equipped[slot] = item.name
                else:
                    equipped[slot] = "Unknown"
            else:
                equipped[slot] = None
        
        return equipped
    
    def get_total_equipment_bonuses(self, entity_id: int) -> dict:
        """Calculate total bonuses from all equipped items."""
        equipment_slots = self.world.get_component(entity_id, EquipmentSlots)
        if not equipment_slots:
            return {'attack': 0, 'defense': 0, 'attributes': {}}
        
        total_attack = 0
        total_defense = 0
        total_attributes = {}
        
        for slot, item_entity_id in equipment_slots.get_equipped_items().items():
            if item_entity_id:
                equipment = self.world.get_component(item_entity_id, Equipment)
                if equipment:
                    total_attack += equipment.attack_bonus
                    total_defense += equipment.defense_bonus
                    
                    # Add attribute bonuses
                    for attr, bonus in equipment.attribute_bonuses.items():
                        total_attributes[attr] = total_attributes.get(attr, 0) + bonus
        
        return {
            'attack': total_attack,
            'defense': total_defense,
            'attributes': total_attributes
        }
