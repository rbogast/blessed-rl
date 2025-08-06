"""
Lighting system for managing light sources and fuel depletion.
"""

from ecs.system import System
from components.items import LightEmitter, EquipmentSlots
from components.core import Player


class LightingSystem(System):
    """Manages light sources, fuel depletion, and light activation/deactivation."""
    
    def __init__(self, world, message_log=None):
        super().__init__(world)
        self.message_log = message_log
    
    def update(self, dt: float = 0.0) -> None:
        """Update lighting system - deplete fuel for active lights."""
        # Get all entities with light emitters
        light_entities = self.world.get_entities_with_components(LightEmitter)
        
        for entity_id in light_entities:
            light = self.world.get_component(entity_id, LightEmitter)
            if not light:
                continue
            
            # Only deplete fuel if the light is active and has fuel
            if light.active and light.fuel > 0:
                light.fuel -= 1
                
                # Check if fuel ran out
                if light.fuel <= 0:
                    light.active = False
                    self._notify_fuel_depleted(entity_id)
    
    def activate_light(self, light_entity_id: int) -> bool:
        """Activate a light source if it has fuel."""
        light = self.world.get_component(light_entity_id, LightEmitter)
        if not light:
            return False
        
        if light.fuel > 0:
            light.active = True
            return True
        else:
            light.active = False
            return False
    
    def deactivate_light(self, light_entity_id: int) -> None:
        """Deactivate a light source."""
        light = self.world.get_component(light_entity_id, LightEmitter)
        if light:
            light.active = False
    
    def get_player_equipped_light_radius(self, player_entity_id: int) -> int:
        """Get the light radius for a player based only on equipped light sources."""
        equipment_slots = self.world.get_component(player_entity_id, EquipmentSlots)
        if not equipment_slots:
            return 0
        
        total_brightness = 0
        
        # Check accessory slot for light sources
        if equipment_slots.accessory:
            light = self.world.get_component(equipment_slots.accessory, LightEmitter)
            if light and light.active:
                total_brightness += light.brightness
        
        return total_brightness
    
    def get_player_light_radius(self, player_entity_id: int) -> int:
        """Get the total light radius for a player based on equipped light sources and nearby world light sources."""
        from components.core import Position
        
        player_pos = self.world.get_component(player_entity_id, Position)
        if not player_pos:
            return 0
        
        total_brightness = 0
        
        # Check equipped light sources
        equipment_slots = self.world.get_component(player_entity_id, EquipmentSlots)
        if equipment_slots and equipment_slots.accessory:
            light = self.world.get_component(equipment_slots.accessory, LightEmitter)
            if light and light.active:
                total_brightness += light.brightness
        
        # Check for active light sources in the world near the player
        light_entities = self.world.get_entities_with_components(LightEmitter, Position)
        for entity_id in light_entities:
            # Skip if this is the equipped light source (already counted)
            if equipment_slots and entity_id == equipment_slots.accessory:
                continue
            
            light = self.world.get_component(entity_id, LightEmitter)
            position = self.world.get_component(entity_id, Position)
            
            if light and position and light.active:
                # Calculate distance from player
                dx = position.x - player_pos.x
                dy = position.y - player_pos.y
                distance_squared = dx * dx + dy * dy
                
                # Light sources affect the player if they're within their brightness radius
                if distance_squared <= light.brightness * light.brightness:
                    # Add the light's contribution (could be reduced by distance, but for simplicity we'll use full brightness)
                    total_brightness += light.brightness
        
        return total_brightness
    
    def get_all_world_light_sources(self) -> list:
        """Get all active light sources in the world with their positions."""
        from components.core import Position
        
        world_lights = []
        light_entities = self.world.get_entities_with_components(LightEmitter, Position)
        
        for entity_id in light_entities:
            light = self.world.get_component(entity_id, LightEmitter)
            position = self.world.get_component(entity_id, Position)
            
            if light and position and light.active:
                world_lights.append({
                    'entity_id': entity_id,
                    'x': position.x,
                    'y': position.y,
                    'brightness': light.brightness
                })
        
        return world_lights
    
    def get_player_sight_radius(self, player_entity_id: int) -> int:
        """Get the sight radius for a player (2x light brightness)."""
        light_radius = self.get_player_light_radius(player_entity_id)
        return light_radius * 2
    
    def _notify_fuel_depleted(self, light_entity_id: int) -> None:
        """Notify when a light source runs out of fuel."""
        if not self.message_log:
            return
        
        # Check if this light is equipped by a player
        player_entities = self.world.get_entities_with_components(Player, EquipmentSlots)
        
        for player_entity in player_entities:
            equipment_slots = self.world.get_component(player_entity, EquipmentSlots)
            if equipment_slots and equipment_slots.accessory == light_entity_id:
                # Get the item name for the message
                from components.items import Item
                item = self.world.get_component(light_entity_id, Item)
                item_name = item.name if item else "light source"
                
                self.message_log.add_warning(f"Your {item_name} has run out of fuel and goes dark!")
                break
