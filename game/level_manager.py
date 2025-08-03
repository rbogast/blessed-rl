"""
Level management and transition logic.
"""

from components.core import Position
from components.items import Inventory, EquipmentSlots


class LevelManager:
    """Handles level transitions and stair interactions."""
    
    def __init__(self, world, world_generator, game_state, message_log, camera, fov_system, render_system):
        self.world = world
        self.world_generator = world_generator
        self.game_state = game_state
        self.message_log = message_log
        self.camera = camera
        self.fov_system = fov_system
        self.render_system = render_system
    
    def check_stairs_interaction(self, player_entity: int, x: int, y: int) -> None:
        """Check if player is on stairs and show information."""
        stairs_type = self.world_generator.is_stairs_at(x, y)
        
        if stairs_type == 'down':
            # Player stepped on downward stairs - just show info
            self.message_log.add_info("You see stairs leading down. Press '.' to descend.")
            
        elif stairs_type == 'up':
            # Player stepped on upward stairs - just show info
            self.message_log.add_info("You see stairs leading up. Press ',' to ascend.")
    
    def use_stairs_down(self, player_entity: int) -> None:
        """Use downward stairs to go to the next level."""
        current_level_id = self.game_state.get_current_level_id()
        next_level_id = current_level_id + 1
        
        self.message_log.add_info(f"You descend to level {next_level_id}...")
        self._change_to_level(player_entity, next_level_id, 'down')
    
    def use_stairs_up(self, player_entity: int) -> None:
        """Use upward stairs to go to the previous level."""
        current_level_id = self.game_state.get_current_level_id()
        if current_level_id > 0:
            prev_level_id = current_level_id - 1
            self.message_log.add_info(f"You ascend to level {prev_level_id}...")
            self._change_to_level(player_entity, prev_level_id, 'up')
        else:
            self.message_log.add_warning("You can't go up from here.")
    
    def _change_to_level(self, player_entity: int, target_level_id: int, stairs_type: str) -> None:
        """Change to a different dungeon level."""
        current_level_id = self.game_state.get_current_level_id()
        current_level = self.game_state.get_current_level()
        
        # Save current level's entity data (excluding player and their inventory items)
        if current_level:
            # Get player's inventory items to exclude them from level saving
            player_inventory_items = set()
            
            inventory = self.world.get_component(player_entity, Inventory)
            if inventory:
                player_inventory_items.update(inventory.items)
            
            equipment_slots = self.world.get_component(player_entity, EquipmentSlots)
            if equipment_slots:
                equipped_items = equipment_slots.get_equipped_items()
                for slot, item_id in equipped_items.items():
                    if item_id:
                        player_inventory_items.add(item_id)
            
            # Create a list of entities to save (exclude player and their items)
            entities_to_save = []
            for eid in current_level.entities:
                if eid != player_entity and eid not in player_inventory_items:
                    entities_to_save.append(eid)
            
            if entities_to_save:
                # Save entity data for level entities only (not player items)
                saved_entities = []
                for entity_id in entities_to_save:
                    if self.world.entities.is_alive(entity_id):
                        # Get all components for this entity
                        components = {}
                        for component_type, component_dict in self.world.components._components.items():
                            if entity_id in component_dict:
                                component = component_dict[entity_id]
                                # Store component data as a dictionary
                                components[component_type.__name__] = component.__dict__.copy()
                        
                        if components:  # Only save if entity has components
                            saved_entities.append(components)
                
                current_level.entity_data = saved_entities
            else:
                # No entities to save
                current_level.entity_data = []
            
            # Remove entities from the ECS world (exclude player and their inventory items)
            entities_to_remove = []
            for entity_id in self.world.entities.get_alive_entities():
                if entity_id != player_entity and entity_id not in player_inventory_items:
                    entities_to_remove.append(entity_id)
            
            for entity_id in entities_to_remove:
                self.world.destroy_entity(entity_id)
            
            # Clear the level's entity list completely
            current_level.entities.clear()
        
        # Check if target level exists, if not generate it
        if not self.game_state.has_level(target_level_id):
            # Determine stairs position for new level
            stairs_up_pos = None
            if stairs_type == 'down':
                # Going down - place upward stairs at same position as current downward stairs
                stairs_down_pos = self.world_generator.get_stairs_down_pos()
                if stairs_down_pos:
                    stairs_up_pos = stairs_down_pos
                    self.message_log.add_system(f"Enforcing stair connection: down stairs at {stairs_down_pos} -> up stairs at {stairs_up_pos}")
            
            # Generate new level
            new_level = self.world_generator.generate_level(target_level_id, stairs_up_pos, self.game_state.turn_count)
            self.game_state.add_level(new_level)
            
            # Validate the stair connection was enforced correctly
            if stairs_type == 'down' and current_level and stairs_up_pos:
                if new_level.validate_stair_connection(current_level, 'up'):
                    self.message_log.add_system(f"✓ Stair connection validated: Level {current_level_id} ↔ Level {target_level_id}")
                else:
                    self.message_log.add_warning(f"✗ Stair connection failed: Level {current_level_id} ↔ Level {target_level_id}")
                    self.message_log.add_warning(f"  Current level down: {current_level.get_stairs_down_pos()}")
                    self.message_log.add_warning(f"  New level up: {new_level.get_stairs_up_pos()}")
        
        # Change to target level with proper cleanup
        self.game_state.change_level(target_level_id, self.world)
        target_level = self.game_state.get_current_level()
        self.world_generator.set_current_level(target_level)
        
        # Restore entities for the target level
        if target_level.entity_data:
            target_level.restore_entity_data(self.world, target_level.entity_data)
            # Don't clear entity_data - we need it for future level transitions
        
        # Position player on appropriate stairs
        if stairs_type == 'down':
            # Coming from above - place on upward stairs
            stairs_pos = target_level.get_stairs_up_pos()
        else:
            # Coming from below - place on downward stairs
            stairs_pos = target_level.get_stairs_down_pos()
        
        if stairs_pos:
            position = self.world.get_component(player_entity, Position)
            if position:
                position.x, position.y = stairs_pos
        
        # Add player to new level
        target_level.add_entity(player_entity)
        
        # Update camera bounds and position
        self.camera.set_level_bounds(target_level.width, target_level.height)
        player_pos = self.world.get_component(player_entity, Position)
        if player_pos:
            self.camera.follow_entity(player_pos.x, player_pos.y)
        
        # Force FOV recalculation for new level (reset cached position)
        self.fov_system.force_recalculation()
        
        # Update FOV for new level
        self.fov_system.update()
        
        # Invalidate render cache
        self.render_system.invalidate_cache()
        
        # Request render
        self.game_state.request_render()
