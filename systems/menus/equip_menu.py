"""Equipment menu implementation."""

from typing import List
from systems.menu import BaseMenu


class EquipMenu(BaseMenu):
    """Menu for equipping and unequipping items."""
    
    def get_title(self) -> str:
        return "--- Equip/Unequip ---"
    
    def get_subtitle(self) -> str:
        return "Select item number:"
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build list of equippable items and equipped items."""
        from components.items import Inventory, Item, Equipment, EquipmentSlots
        
        items = []
        inventory = self.world.get_component(player_entity, Inventory)
        equipment_slots = self.world.get_component(player_entity, EquipmentSlots)
        
        if not inventory or not equipment_slots:
            return items
        
        # Add equippable items from inventory
        for item_entity_id in inventory.items:
            equipment = self.world.get_component(item_entity_id, Equipment)
            if equipment:
                item = self.world.get_component(item_entity_id, Item)
                if item:
                    name = item.name[:16]
                    items.append(f"{name} (equip)")
        
        # Add equipped items for unequipping
        equipped_items = equipment_slots.get_equipped_items()
        for slot, item_entity_id in equipped_items.items():
            if item_entity_id:
                item = self.world.get_component(item_entity_id, Item)
                if item:
                    name = item.name[:14]
                    items.append(f"{name} (unequip)")
        
        return items
