"""
Item factory for creating items from YAML definitions.
"""

import yaml
from typing import Dict, Any, Optional
from components.items import Item, Equipment, Consumable, Pickupable
from components.core import Renderable


class ItemFactory:
    """Factory for creating item entities from YAML definitions."""
    
    def __init__(self, world):
        self.world = world
        self.item_definitions = {}
        self._load_item_definitions()
    
    def _load_item_definitions(self) -> None:
        """Load item definitions from YAML file."""
        try:
            with open('data/items.yaml', 'r') as file:
                data = yaml.safe_load(file)
                self.item_definitions = data.get('items', {})
        except FileNotFoundError:
            print("Warning: data/items.yaml not found. No items will be available.")
            self.item_definitions = {}
        except yaml.YAMLError as e:
            print(f"Error loading items.yaml: {e}")
            self.item_definitions = {}
    
    def create_item(self, item_id: str, x: Optional[int] = None, y: Optional[int] = None) -> Optional[int]:
        """Create an item entity from its definition."""
        if item_id not in self.item_definitions:
            print(f"Warning: Item '{item_id}' not found in definitions")
            return None
        
        definition = self.item_definitions[item_id]
        
        # Create the entity
        entity_id = self.world.create_entity()
        
        # Add base Item component
        item_component = Item(
            name=definition.get('name', item_id),
            description=definition.get('description', ''),
            item_type=definition.get('type', 'misc'),
            value=definition.get('value', 0)
        )
        self.world.add_component(entity_id, item_component)
        
        # Add Renderable component
        char = definition.get('char', '?')
        color = definition.get('color', 'white')
        self.world.add_component(entity_id, Renderable(char, color))
        
        # Add Pickupable component
        self.world.add_component(entity_id, Pickupable())
        
        # Add type-specific components
        item_type = definition.get('type', 'misc')
        
        if item_type in ['weapon', 'armor', 'accessory']:
            # Add Equipment component
            equipment_component = Equipment(
                slot=definition.get('slot', item_type),
                attack_bonus=definition.get('attack_bonus', 0),
                defense_bonus=definition.get('defense_bonus', 0),
                attribute_bonuses=definition.get('attribute_bonuses', {})
            )
            self.world.add_component(entity_id, equipment_component)
            
            # Add WeaponEffects component for weapons with special effects
            if item_type == 'weapon' and 'weapon_effects' in definition:
                from components.effects import WeaponEffects
                weapon_effects = WeaponEffects()
                
                effects_data = definition['weapon_effects']
                
                # Set knockback effects
                if 'knockback_chance' in effects_data and 'knockback_force' in effects_data:
                    weapon_effects.set_knockback(
                        effects_data['knockback_chance'],
                        effects_data['knockback_force']
                    )
                
                # Set slashing effects
                if 'slashing_chance' in effects_data and 'slashing_damage' in effects_data:
                    weapon_effects.set_slashing(
                        effects_data['slashing_chance'],
                        effects_data['slashing_damage']
                    )
                
                self.world.add_component(entity_id, weapon_effects)
        
        elif item_type == 'consumable':
            # Add Consumable component
            consumable_component = Consumable(
                effect_type=definition.get('effect_type', 'heal'),
                effect_value=definition.get('effect_value', 0),
                uses=definition.get('uses', 1)
            )
            self.world.add_component(entity_id, consumable_component)
        
        # Add Position component if coordinates provided
        if x is not None and y is not None:
            from components.core import Position
            self.world.add_component(entity_id, Position(x, y))
        
        return entity_id
    
    def get_item_definition(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get the raw definition for an item."""
        return self.item_definitions.get(item_id)
    
    def get_all_item_ids(self) -> list:
        """Get a list of all available item IDs."""
        return list(self.item_definitions.keys())
    
    def get_items_by_type(self, item_type: str) -> list:
        """Get all item IDs of a specific type."""
        return [
            item_id for item_id, definition in self.item_definitions.items()
            if definition.get('type') == item_type
        ]
