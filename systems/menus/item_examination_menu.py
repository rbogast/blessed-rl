"""Item examination menu for detailed item view and action selection."""

from typing import List
from systems.menu import BaseMenu


class ItemExaminationMenu(BaseMenu):
    """Menu for examining items and selecting actions."""
    
    def __init__(self, world):
        super().__init__(world)
        self.examined_item_id = None
        self.show_actions = False
        self.item_description_lines = []
        self.available_actions = []
    
    def set_examined_item(self, item_entity_id: int, player_entity: int):
        """Set the item to examine and build description."""
        self.examined_item_id = item_entity_id
        self.show_actions = False
        self.selected_index = -1
        self._build_item_description(player_entity)
        self._build_available_actions(player_entity)
        self.invalidate()
    
    def show_action_menu(self):
        """Switch to showing the action selection menu."""
        self.show_actions = True
        self.selected_index = 0
        self.invalidate()
    
    def get_title(self) -> str:
        if self.show_actions:
            return "--- Select Action ---"
        else:
            return "--- Item Details ---"
    
    def get_subtitle(self) -> str:
        if self.show_actions:
            return "Choose what to do:"
        else:
            return "Press Enter to see actions"
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build menu items based on current mode."""
        if self.show_actions:
            return self.available_actions
        else:
            return self.item_description_lines
    
    def _build_item_description(self, player_entity: int):
        """Build the detailed item description."""
        from components.items import Item, Equipment, Consumable, LightEmitter
        from components.corpse import Corpse
        
        self.item_description_lines = []
        
        if not self.examined_item_id:
            self.item_description_lines = ["No item to examine"]
            return
        
        # Get item glyph and name
        item = self.world.get_component(self.examined_item_id, Item)
        if item:
            # Add item name with glyph (we'll get glyph from item factory data)
            glyph_info = self._get_item_glyph(self.examined_item_id)
            if glyph_info:
                self.item_description_lines.append(f"{glyph_info} {item.name}")
            else:
                self.item_description_lines.append(item.name)
            
            self.item_description_lines.append("")  # Empty line
            
            # Add description
            if item.description:
                # Split long descriptions into multiple lines
                desc_words = item.description.split()
                current_line = ""
                for word in desc_words:
                    if len(current_line + " " + word) <= 40:  # Fit in sidebar
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                    else:
                        if current_line:
                            self.item_description_lines.append(current_line)
                        current_line = word
                if current_line:
                    self.item_description_lines.append(current_line)
            
            self.item_description_lines.append("")  # Empty line
            
            # Add stats based on item type
            equipment = self.world.get_component(self.examined_item_id, Equipment)
            if equipment:
                self.item_description_lines.append("Equipment Stats:")
                if equipment.attack_bonus > 0:
                    self.item_description_lines.append(f"  Attack: +{equipment.attack_bonus}")
                if equipment.defense_bonus > 0:
                    self.item_description_lines.append(f"  Defense: +{equipment.defense_bonus}")
                if equipment.attribute_bonuses:
                    for attr, bonus in equipment.attribute_bonuses.items():
                        self.item_description_lines.append(f"  {attr.title()}: +{bonus}")
                self.item_description_lines.append("")
            
            consumable = self.world.get_component(self.examined_item_id, Consumable)
            if consumable:
                self.item_description_lines.append("Consumable:")
                self.item_description_lines.append(f"  Effect: {consumable.effect_type}")
                self.item_description_lines.append(f"  Value: {consumable.effect_value}")
                self.item_description_lines.append(f"  Uses: {consumable.uses}")
                self.item_description_lines.append("")
            
            light = self.world.get_component(self.examined_item_id, LightEmitter)
            if light:
                self.item_description_lines.append("Light Source:")
                self.item_description_lines.append(f"  Brightness: {light.brightness}")
                self.item_description_lines.append(f"  Fuel: {light.fuel}/{light.max_fuel}")
                status = "On" if light.active else "Off"
                self.item_description_lines.append(f"  Status: {status}")
                self.item_description_lines.append("")
        
        else:
            # Check if it's a corpse
            corpse = self.world.get_component(self.examined_item_id, Corpse)
            if corpse:
                self.item_description_lines.append(f"% {corpse.original_entity_type} corpse")
                self.item_description_lines.append("")
                self.item_description_lines.append("The remains of a fallen creature.")
            else:
                self.item_description_lines.append("Unknown item")
    
    def _get_item_glyph(self, item_entity_id: int) -> str:
        """Get the visual glyph for an item."""
        from components.core import Renderable
        
        # Try to get the renderable component which has the visual glyph
        renderable = self.world.get_component(item_entity_id, Renderable)
        if renderable:
            return renderable.char
        
        # Fallback to placeholder if no renderable component
        return "?"
    
    def _build_available_actions(self, player_entity: int):
        """Build list of available actions for the current item."""
        from components.items import Equipment, Consumable, LightEmitter, Throwable, EquipmentSlots
        
        self.available_actions = []
        
        if not self.examined_item_id:
            return
        
        # Check for equipment
        if self.world.has_component(self.examined_item_id, Equipment):
            equipment_slots = self.world.get_component(player_entity, EquipmentSlots)
            equipment = self.world.get_component(self.examined_item_id, Equipment)
            
            if equipment_slots and equipment:
                # Check if already equipped
                equipped_items = equipment_slots.get_equipped_items()
                if self.examined_item_id in equipped_items.values():
                    self.available_actions.append("Unequip")
                else:
                    self.available_actions.append("Equip")
        
        # Check for consumable
        if self.world.has_component(self.examined_item_id, Consumable):
            self.available_actions.append("Use")
        
        # Check for light emitter
        if self.world.has_component(self.examined_item_id, LightEmitter):
            light = self.world.get_component(self.examined_item_id, LightEmitter)
            if light.fuel > 0:
                if light.active:
                    self.available_actions.append("Extinguish")
                else:
                    self.available_actions.append("Light")
        
        # Check for throwable
        if self.world.has_component(self.examined_item_id, Throwable):
            self.available_actions.append("Throw")
        
        # Always available
        self.available_actions.append("Drop")
    
    def get_selected_action(self) -> str:
        """Get the currently selected action."""
        if (self.show_actions and self.selected_index >= 0 and 
            self.selected_index < len(self.available_actions)):
            return self.available_actions[self.selected_index]
        return None
    
    def reset(self):
        """Reset the menu state."""
        super().reset()
        self.examined_item_id = None
        self.show_actions = False
        self.item_description_lines = []
        self.available_actions = []
    
    def get_menu_line(self, line_num: int, player_entity: int) -> tuple:
        """Override to provide custom display for item examination."""
        if line_num == 0:
            return self.get_title(), False
        elif line_num == 1:
            return self.get_subtitle(), False
        
        # Build menu items if needed
        if self._items_dirty:
            self._menu_items = self.build_menu_items(player_entity)
            self._items_dirty = False
        
        item_line = line_num - 2
        if item_line >= 0 and item_line < len(self._menu_items):
            item_text = self._menu_items[item_line]
            
            if self.show_actions:
                # Show numbered actions with highlighting
                is_highlighted = item_line == self.selected_index
                prefix = "> " if is_highlighted else "  "
                return f"{prefix}{item_line + 1}. {item_text}", is_highlighted
            else:
                # Show description lines without highlighting
                return item_text, False
        
        return "", False
