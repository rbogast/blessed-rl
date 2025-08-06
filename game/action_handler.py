"""
Player action handling logic.
"""

from components.core import Position, Player
from components.items import Inventory, Item, Equipment, Consumable, EquipmentSlots


class ActionHandler:
    """Handles all player actions and menu interactions."""
    
    def __init__(self, world, game_state, message_log, render_system, movement_system, 
                 combat_system, inventory_system, throwing_system, level_manager, auto_explore_system=None):
        self.world = world
        self.game_state = game_state
        self.message_log = message_log
        self.render_system = render_system
        self.movement_system = movement_system
        self.combat_system = combat_system
        self.inventory_system = inventory_system
        self.throwing_system = throwing_system
        self.level_manager = level_manager
        self.auto_explore_system = auto_explore_system
    
    def handle_player_movement(self, player_entity: int, dx: int, dy: int) -> None:
        """Handle player movement or attack."""
        position = self.world.get_component(player_entity, Position)
        if not position:
            return
        
        target_x = position.x + dx
        target_y = position.y + dy
        
        # Check if there's an attackable entity at the target position
        target_entity = self.combat_system.get_attackable_entity_at(target_x, target_y)
        
        if target_entity and not self.world.has_component(target_entity, Player):
            # Attack the target
            self.combat_system.attack(player_entity, target_entity)
            # Invalidate render cache since entity positions may have changed due to combat/knockback
            self.render_system.invalidate_cache()
        else:
            # Try to move
            success = self.movement_system.try_move_entity(player_entity, dx, dy)
            
            if success:
                # Invalidate render cache since player moved
                self.render_system.invalidate_cache()
                
                # Update camera to follow player
                new_position = self.world.get_component(player_entity, Position)
                if new_position:
                    from game.camera import Camera
                    # Get camera from render system
                    camera = self.render_system.camera
                    camera.follow_entity(new_position.x, new_position.y)
                    
                    # Check for stairs and handle level transitions
                    self.level_manager.check_stairs_interaction(player_entity, new_position.x, new_position.y)
            else:
                # Movement blocked
                from game.level_world_gen import LevelWorldGenerator
                # Get world generator from render system
                world_generator = self.render_system.world_generator
                if world_generator.is_wall_at(target_x, target_y):
                    self.message_log.add_warning("You bump into a wall.")
                else:
                    self.message_log.add_warning("Something blocks your way.")
    
    def handle_pickup(self, player_entity: int) -> None:
        """Handle picking up items at player's position."""
        position = self.world.get_component(player_entity, Position)
        if not position:
            return
        
        # Get items at player's position
        items_at_pos = self.inventory_system.get_items_at_position(position.x, position.y)
        
        if not items_at_pos:
            self.message_log.add_warning("There's nothing here to pick up.")
            return
        
        # Try to pick up all items
        picked_up_count = 0
        current_level = self.game_state.get_current_level()
        
        for item_entity_id in items_at_pos:
            if self.inventory_system.pickup_item(player_entity, item_entity_id):
                picked_up_count += 1
                # Remove item from current level's entity list
                if current_level:
                    current_level.remove_entity(item_entity_id)
                # Invalidate render cache since item was removed from world
                self.render_system.invalidate_cache()
        
        if picked_up_count == 0:
            self.message_log.add_warning("Your inventory is full!")
    
    def handle_item_selection(self, player_entity: int, item_number: int) -> None:
        """Handle item selection from menus."""
        # Check which menu is active using the menu manager
        menu_manager = self.render_system.menu_manager
        
        if menu_manager.active_menu and menu_manager.active_menu.__class__.__name__ == 'EquipMenu':
            self._handle_equip_selection(player_entity, item_number)
        elif menu_manager.active_menu and menu_manager.active_menu.__class__.__name__ == 'UseMenu':
            self._handle_use_selection(player_entity, item_number)
        elif menu_manager.active_menu and menu_manager.active_menu.__class__.__name__ == 'DropMenu':
            self._handle_drop_selection(player_entity, item_number)
        elif menu_manager.active_menu and menu_manager.active_menu.__class__.__name__ == 'ThrowingMenu':
            self._handle_throwing_selection(player_entity, item_number)
        elif menu_manager.is_inventory_shown():
            # Just show item info for now
            inventory = self.world.get_component(player_entity, Inventory)
            if inventory and item_number <= len(inventory.items):
                item_entity_id = inventory.items[item_number - 1]
                item = self.world.get_component(item_entity_id, Item)
                if item:
                    self.message_log.add_info(f"Selected: {item.name}")
    
    def _handle_equip_selection(self, player_entity: int, item_number: int) -> None:
        """Handle equipment selection."""
        # Build the same list as the render system
        inventory = self.world.get_component(player_entity, Inventory)
        equipment_slots = self.world.get_component(player_entity, EquipmentSlots)
        
        if not inventory or not equipment_slots:
            return
        
        # Build equip menu items list - same logic as render system
        equip_items = []
        
        # Add equippable items from inventory
        for item_entity_id in inventory.items:
            equipment = self.world.get_component(item_entity_id, Equipment)
            if equipment:
                equip_items.append(('equip', item_entity_id))
        
        # Add equipped items for unequipping
        equipped_items = equipment_slots.get_equipped_items()
        for slot, item_entity_id in equipped_items.items():
            if item_entity_id:
                equip_items.append(('unequip', item_entity_id, slot))
        
        # Handle selection
        if 1 <= item_number <= len(equip_items):
            item_info = equip_items[item_number - 1]
            
            if item_info[0] == 'equip':
                # Equip item
                _, item_entity_id = item_info
                success = self.inventory_system.equip_item(player_entity, item_entity_id)
                if success:
                    self.render_system.hide_all_menus()
                else:
                    self.message_log.add_warning("Cannot equip that item.")
            elif item_info[0] == 'unequip':
                # Unequip item
                _, item_entity_id, slot = item_info
                success = self.inventory_system.unequip_item(player_entity, slot)
                if success:
                    self.render_system.hide_all_menus()
                else:
                    self.message_log.add_warning("Cannot unequip that item.")
        else:
            self.message_log.add_warning("Invalid selection.")
    
    def _handle_use_selection(self, player_entity: int, item_number: int) -> None:
        """Handle consumable use selection."""
        inventory = self.world.get_component(player_entity, Inventory)
        if not inventory:
            return
        
        # Build list of consumable items
        consumable_items = []
        for item_entity_id in inventory.items:
            consumable = self.world.get_component(item_entity_id, Consumable)
            if consumable:
                consumable_items.append(item_entity_id)
        
        # Handle selection
        if 1 <= item_number <= len(consumable_items):
            item_entity_id = consumable_items[item_number - 1]
            success = self.inventory_system.use_consumable(player_entity, item_entity_id)
            if success:
                self.render_system.hide_all_menus()
        else:
            self.message_log.add_warning("Invalid selection.")
    
    def _handle_drop_selection(self, player_entity: int, item_number: int) -> None:
        """Handle drop item selection."""
        inventory = self.world.get_component(player_entity, Inventory)
        if not inventory:
            return
        
        # Handle selection - all items in inventory can be dropped
        if 1 <= item_number <= len(inventory.items):
            item_entity_id = inventory.items[item_number - 1]
            success = self.inventory_system.drop_item(player_entity, item_entity_id)
            if success:
                # Add dropped item to current level's entity list
                current_level = self.game_state.get_current_level()
                if current_level:
                    current_level.add_entity(item_entity_id)
                # Invalidate render cache since item was added to world
                self.render_system.invalidate_cache()
                self.render_system.hide_all_menus()
        else:
            self.message_log.add_warning("Invalid selection.")
    
    def _handle_throwing_selection(self, player_entity: int, item_number: int) -> None:
        """Handle throwing item selection."""
        from systems.menus.throwing_menu import ThrowingMenu
        
        # Get throwable items using the throwing menu's method
        throwing_menu = self.render_system.menu_manager.menus['throwing']
        throwable_items = throwing_menu.get_throwable_items(player_entity)
        
        # Handle selection
        if 1 <= item_number <= len(throwable_items):
            item_entity_id = throwable_items[item_number - 1]
            
            # Start throwing with the selected item
            success = self.throwing_system.start_throwing(player_entity, item_entity_id)
            if success:
                self.render_system.hide_all_menus()
                # Request render to show the targeting cursor
                self.game_state.request_render()
            else:
                self.message_log.add_warning("Cannot throw that item.")
        else:
            self.message_log.add_warning("Invalid selection.")
    
    def handle_auto_explore_toggle(self, player_entity: int) -> None:
        """Handle toggling auto-exploration on/off."""
        if not self.auto_explore_system:
            self.message_log.add_warning("Auto-explore system not available.")
            return
        
        from components.auto_explore import AutoExplore
        auto_explore = self.world.get_component(player_entity, AutoExplore)
        
        if auto_explore and auto_explore.is_active():
            # Auto-explore is active, so stop it
            self.auto_explore_system.interrupt_auto_explore(player_entity)
        else:
            # Auto-explore is not active, so start it
            self.auto_explore_system.start_auto_explore(player_entity)
    
    def handle_use_stairs_down(self, player_entity: int) -> None:
        """Handle using downward stairs at current position."""
        position = self.world.get_component(player_entity, Position)
        if not position:
            return
        
        # Check if player is on downward stairs
        from game.level_world_gen import LevelWorldGenerator
        world_generator = self.render_system.world_generator
        stairs_type = world_generator.is_stairs_at(position.x, position.y)
        
        if stairs_type == 'down':
            # Player is on downward stairs - use them
            self.level_manager.use_stairs_down(player_entity)
        else:
            self.message_log.add_warning("You're not standing on downward stairs.")
    
    def handle_use_stairs_up(self, player_entity: int) -> None:
        """Handle using upward stairs at current position."""
        position = self.world.get_component(player_entity, Position)
        if not position:
            return
        
        # Check if player is on upward stairs
        from game.level_world_gen import LevelWorldGenerator
        world_generator = self.render_system.world_generator
        stairs_type = world_generator.is_stairs_at(position.x, position.y)
        
        if stairs_type == 'up':
            # Player is on upward stairs - use them
            self.level_manager.use_stairs_up(player_entity)
        else:
            self.message_log.add_warning("You're not standing on upward stairs.")
    
    def handle_travel_to_stairs_down(self, player_entity: int) -> None:
        """Handle traveling to downward stairs."""
        if not self.auto_explore_system:
            self.message_log.add_warning("Auto-explore system not available.")
            return
        
        self.auto_explore_system.travel_to_stairs_down(player_entity)
    
    def handle_travel_to_stairs_up(self, player_entity: int) -> None:
        """Handle traveling to upward stairs."""
        if not self.auto_explore_system:
            self.message_log.add_warning("Auto-explore system not available.")
            return
        
        self.auto_explore_system.travel_to_stairs_up(player_entity)
    
    def handle_show_interactive_inventory(self, player_entity: int) -> None:
        """Handle showing the interactive inventory menu."""
        inventory = self.world.get_component(player_entity, Inventory)
        if not inventory:
            self.message_log.add_warning("You have no inventory.")
            return
        
        if not inventory.items:
            self.message_log.add_warning("Your inventory is empty.")
            return
        
        # Show the interactive inventory menu
        self.render_system.menu_manager.show_interactive_inventory()
        self.game_state.request_render()
    
    def handle_interactive_inventory_selection(self, player_entity: int) -> None:
        """Handle selection from the interactive inventory menu."""
        menu_manager = self.render_system.menu_manager
        
        if not menu_manager.is_interactive_inventory_active():
            return
        
        # Get the selected item
        selected_item_id = menu_manager.get_selected_inventory_item(player_entity)
        if selected_item_id is None:
            self.message_log.add_warning("No item selected.")
            return
        
        # Show the item examination menu
        menu_manager.show_item_examination(selected_item_id, player_entity)
        self.game_state.request_render()
    
    def handle_item_examination_selection(self, player_entity: int) -> None:
        """Handle selection from the item examination menu."""
        menu_manager = self.render_system.menu_manager
        
        if not menu_manager.is_item_examination_active():
            return
        
        examination_menu = menu_manager.menus['item_examination']
        
        # Check if we're showing the description or the actions
        if not examination_menu.show_actions:
            # Currently showing description, switch to actions
            menu_manager.show_examination_actions()
            self.game_state.request_render()
        else:
            # Currently showing actions, execute the selected action
            selected_action = menu_manager.get_selected_examination_action()
            if selected_action:
                self._execute_item_action(player_entity, examination_menu.examined_item_id, selected_action)
    
    def _execute_item_action(self, player_entity: int, item_entity_id: int, action: str) -> None:
        """Execute the selected action on an item."""
        if action == "Drop":
            success = self.inventory_system.drop_item(player_entity, item_entity_id)
            if success:
                # Add dropped item to current level's entity list
                current_level = self.game_state.get_current_level()
                if current_level:
                    current_level.add_entity(item_entity_id)
                # Invalidate render cache since item was added to world
                self.render_system.invalidate_cache()
                self.render_system.hide_all_menus()
        
        elif action == "Equip":
            success = self.inventory_system.equip_item(player_entity, item_entity_id)
            if success:
                self.render_system.hide_all_menus()
            else:
                self.message_log.add_warning("Cannot equip that item.")
        
        elif action == "Unequip":
            # Find which slot this item is equipped in
            from components.items import EquipmentSlots
            equipment_slots = self.world.get_component(player_entity, EquipmentSlots)
            if equipment_slots:
                equipped_items = equipment_slots.get_equipped_items()
                for slot, equipped_item_id in equipped_items.items():
                    if equipped_item_id == item_entity_id:
                        success = self.inventory_system.unequip_item(player_entity, slot)
                        if success:
                            self.render_system.hide_all_menus()
                        else:
                            self.message_log.add_warning("Cannot unequip that item.")
                        return
                self.message_log.add_warning("Item is not equipped.")
        
        elif action == "Use":
            success = self.inventory_system.use_consumable(player_entity, item_entity_id)
            if success:
                self.render_system.hide_all_menus()
        
        elif action == "Light":
            self._handle_light_action(item_entity_id, True)
            self.render_system.hide_all_menus()
        
        elif action == "Extinguish":
            self._handle_light_action(item_entity_id, False)
            self.render_system.hide_all_menus()
        
        elif action == "Throw":
            # Start throwing with the selected item
            success = self.throwing_system.start_throwing(player_entity, item_entity_id)
            if success:
                self.render_system.hide_all_menus()
                # Request render to show the targeting cursor
                self.game_state.request_render()
            else:
                self.message_log.add_warning("Cannot throw that item.")
        
        else:
            self.message_log.add_warning(f"Unknown action: {action}")
    
    def _handle_light_action(self, item_entity_id: int, activate: bool) -> None:
        """Handle lighting or extinguishing a light source."""
        from components.items import LightEmitter, Item
        
        light = self.world.get_component(item_entity_id, LightEmitter)
        item = self.world.get_component(item_entity_id, Item)
        
        if not light or not item:
            return
        
        if activate:
            if light.fuel > 0:
                light.active = True
                self.message_log.add_info(f"You light the {item.name}.")
            else:
                self.message_log.add_warning(f"The {item.name} has no fuel.")
        else:
            light.active = False
            self.message_log.add_info(f"You extinguish the {item.name}.")
