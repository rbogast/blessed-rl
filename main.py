"""
Main entry point for the ECS Roguelike game.
"""

import random
from ecs import World
from components.core import Position, Renderable, Player, Blocking, Visible
from components.combat import Health, Stats
from components.character import CharacterAttributes, Experience
from components.effects import Physics
from components.items import Inventory, EquipmentSlots
from components.corpse import Race
from components.skills import Skills
from game.world_gen import WorldGenerator
from game.character_stats import calculate_max_hp
from game.camera import Camera
from game.message_log import MessageLog
from game.game_state import GameStateManager
from game.glyph_config import GlyphConfig
from game.config import GameConfig
from systems.input import InputSystem
from systems.movement import MovementSystem
from systems.combat import CombatSystem
from systems.inventory import InventorySystem
from systems.ai import AISystem
from systems.fov import FOVSystem
from systems.render import RenderSystem
from systems.skills import SkillsSystem
from systems.throwing import ThrowingSystem
from game.prefabs import PrefabManager
from game.item_factory import ItemFactory
from effects.core import EffectsManager
from effects.physics import PhysicsSystem, KnockbackEffect, ShockwaveEffect
from effects.status_effects import StatusEffectsSystem, BleedingEffect
from effects.tile_effects import TileEffectsSystem, BloodSplatterEffect


class RoguelikeGame:
    """Main game class that coordinates all systems."""
    
    def __init__(self):
        # Initialize core ECS
        self.world = World()
        
        # Initialize game components
        self.game_state = GameStateManager()
        self.message_log = MessageLog(width=GameConfig.SIDEBAR_WIDTH, height=GameConfig.GAME_INFO_HEIGHT, game_state=self.game_state)
        self.camera = Camera(viewport_width=GameConfig.MAP_WIDTH, viewport_height=GameConfig.MAP_HEIGHT)
        self.world_generator = WorldGenerator(self.world, seed=random.randint(0, 1000000))
        
        # Initialize prefab system
        self.prefab_manager = PrefabManager(self.world, self.world_generator, self.message_log)
        
        # Initialize item factory
        self.item_factory = ItemFactory(self.world)
        
        # Initialize effects systems
        self.effects_manager = EffectsManager(self.world)
        self.tile_effects_system = TileEffectsSystem(self.world, self.message_log)
        self.status_effects_system = StatusEffectsSystem(self.world, self.effects_manager, self.message_log, self.game_state, self.world_generator)
        
        # Initialize systems (render system first, then input system with render system reference)
        self.render_system = RenderSystem(self.world, self.camera, self.message_log, 
                                        self.world_generator, self.game_state, self.tile_effects_system)
        self.input_system = InputSystem(self.world, self.game_state, self.message_log, self.render_system)
        self.movement_system = MovementSystem(self.world, self.world_generator, self.message_log)
        
        # Initialize physics system after movement and render systems are created
        self.physics_system = PhysicsSystem(self.world, self.movement_system, self.message_log, 
                                          self.render_system, self.camera)
        
        # Register effects with the manager (after all systems are created)
        self.effects_manager.register_effect(KnockbackEffect(self.physics_system))
        self.effects_manager.register_effect(ShockwaveEffect(self.physics_system, self.movement_system))
        self.effects_manager.register_effect(BleedingEffect(self.status_effects_system))
        self.effects_manager.register_effect(BloodSplatterEffect(self.tile_effects_system))
        self.combat_system = CombatSystem(self.world, self.game_state, self.message_log, self.effects_manager, self.world_generator)
        self.inventory_system = InventorySystem(self.world, self.message_log)
        # Set render system reference for inventory menu invalidation
        self.inventory_system.set_render_system(self.render_system)
        self.skills_system = SkillsSystem(self.world, self.message_log)
        self.ai_system = AISystem(self.world, self.movement_system, self.combat_system, self.message_log)
        self.fov_system = FOVSystem(self.world, self.world_generator)
        self.throwing_system = ThrowingSystem(self.world, self.movement_system, self.fov_system, 
                                            self.physics_system, self.skills_system, self.message_log)
        
        # Set throwing system reference in render system for cursor visualization
        self.render_system.set_throwing_system(self.throwing_system)
        
        # Add systems to world
        self.world.systems.add_system(self.input_system)
        self.world.systems.add_system(self.movement_system)
        self.world.systems.add_system(self.combat_system)
        self.world.systems.add_system(self.ai_system)
        self.world.systems.add_system(self.fov_system)
        self.world.systems.add_system(self.render_system)
        self.world.systems.add_system(self.throwing_system)
        
        # Game initialization
        self._initialize_game()
    
    def _initialize_game(self) -> None:
        """Initialize the game world and player."""
        self.message_log.add_system("Initializing ECS Roguelike...")
        self.message_log.add_system(f"World seed: {self.world_generator.seed}")
        
        # Generate initial chunk
        chunk = self.world_generator.generate_chunk(0)
        self.message_log.add_system("Generated starting area")
        
        # Create player entity
        player_entity = self.world.create_entity()
        
        # Find a safe spawn position in the first chunk
        spawn_x, spawn_y = self._find_spawn_position(chunk)
        
        # Get player glyph from configuration
        glyph_config = GlyphConfig()
        player_char, player_color = glyph_config.get_entity_glyph('player')
        
        # Create player attributes (boosted for testing)
        player_attributes = CharacterAttributes(
            strength=20, agility=15, constitution=15, 
            intelligence=10, willpower=10, aura=8
        )
        player_experience = Experience(current_xp=0, level=1)
        
        # Calculate initial HP based on attributes
        initial_hp = calculate_max_hp(player_attributes, player_experience.level)
        
        # Add player components
        self.world.add_component(player_entity, Position(spawn_x, spawn_y))
        self.world.add_component(player_entity, Renderable(player_char, player_color))
        self.world.add_component(player_entity, Player())
        self.world.add_component(player_entity, Health(initial_hp))
        self.world.add_component(player_entity, player_attributes)
        self.world.add_component(player_entity, player_experience)
        self.world.add_component(player_entity, Physics(mass=150.0))  # Average human weight
        self.world.add_component(player_entity, Blocking())
        self.world.add_component(player_entity, Visible())
        self.world.add_component(player_entity, Inventory(capacity=20))
        self.world.add_component(player_entity, EquipmentSlots())
        self.world.add_component(player_entity, Skills())  # Add skills component
        self.world.add_component(player_entity, Race('human'))  # Player is human
        
        # Set player in game state
        self.game_state.set_player_entity(player_entity)
        
        # TEST: Add a small amount of blood tiles for testing
        self.game_state.blood_tiles.add((spawn_x + 1, spawn_y))
        self.game_state.blood_tiles.add((spawn_x - 1, spawn_y))
        self.message_log.add_info("TEST: Added some blood tiles for testing!")
        
        # Update camera to follow player
        self.camera.follow_entity(spawn_x, spawn_y)
        
        # Calculate initial FOV
        self.fov_system.update()
        
        # Give player some starting items
        self._give_starting_items(player_entity)
        
        # Spawn some test items in the world
        self._spawn_test_items(spawn_x, spawn_y)
        
        self.message_log.add_system(f"Player spawned at X={spawn_x}, Y={spawn_y}")
        self.message_log.add_info("Use numpad keys to move (7,8,9,4,6,1,2,3)")
        self.message_log.add_info("Press 5 to wait, I for inventory, G to pickup")
        self.message_log.add_info("Press E to equip/unequip, U to use, D to drop")
        self.message_log.add_info("Journey east to progress!")
    
    def _find_spawn_position(self, chunk) -> tuple:
        """Find a safe spawn position in the chunk."""
        # Try to find an open position near the west edge
        for x in range(5):  # Check first 5 columns
            for y in range(chunk.height):
                if not chunk.is_wall(x, y):
                    global_x = chunk.chunk_id * chunk.width + x
                    return global_x, y
        
        # Fallback: find any open position
        for y in range(chunk.height):
            for x in range(chunk.width):
                if not chunk.is_wall(x, y):
                    global_x = chunk.chunk_id * chunk.width + x
                    return global_x, y
        
        # Last resort: force a position
        return 5, 10
    
    def run(self) -> None:
        """Main game loop."""
        try:
            # The render system now handles terminal setup
            while True:
                # Render only when needed
                if self.game_state.should_render():
                    self.render_system.update()
                    self.game_state.render_complete()
                
                # Check for game over (only quit if explicitly requested)
                if self.game_state.is_game_over():
                    break
                
                # Get input (blocking - no timeout)
                key = self.render_system.term.inkey()
                if key:
                    # Handle input
                    action_taken = self.input_system.handle_input(key)
                    
                    if action_taken:
                        # Process the player's action
                        self._process_player_action()
                        
                        # Mark that player has acted
                        self.game_state.player_turn_taken()
                        
                        # Update world (AI, etc.)
                        self._update_world()
                        
                        # Reset turn flag for next turn
                        self.game_state.reset_turn_flag()
                        
                        # Request a render after all changes
                        self.game_state.request_render()
        
        except KeyboardInterrupt:
            pass
        finally:
            # Store quit status before cleanup
            was_quit_normally = (self.game_state.is_game_over() and 
                               self.game_state.game_over_reason == "Player quit")
            
            # Clean up the terminal first
            self.render_system.cleanup()
            
            # Now print the message to the restored terminal
            if was_quit_normally:
                print("Exited the game cleanly.")
    
    def _process_player_action(self) -> None:
        """Process the player's pending action."""
        action = self.input_system.get_pending_action()
        if not action:
            return
        
        player_entity = self.game_state.get_player_entity()
        if not player_entity:
            return
        
        if action[0] == 'move':
            _, dx, dy = action
            self._handle_player_movement(player_entity, dx, dy)
        elif action[0] == 'wait':
            # Player waits - no additional processing needed
            pass
        elif action[0] == 'restart':
            self._restart_game()
        elif action[0] == 'toggle_inventory':
            self.render_system.toggle_inventory_display()
        elif action[0] == 'pickup':
            self._handle_pickup(player_entity)
        elif action[0] == 'equip_menu':
            self.render_system.show_equip_menu()
        elif action[0] == 'use_menu':
            self.render_system.show_use_menu()
        elif action[0] == 'drop_menu':
            self.render_system.show_drop_menu()
        elif action[0] == 'throwing_menu':
            self.render_system.show_throwing_menu()
        elif action[0] == 'select_item':
            _, item_number = action
            self._handle_item_selection(player_entity, item_number)
        elif action[0] == 'move_throwing_cursor':
            _, dx, dy = action
            self.throwing_system.move_cursor(player_entity, dx, dy)
        elif action[0] == 'execute_throw':
            self.throwing_system.execute_throw(player_entity)
        elif action[0] == 'cancel_throw':
            self.throwing_system.cancel_throwing(player_entity)
        elif action[0] == 'close_menus':
            self.render_system.hide_all_menus()
    
    def _handle_player_movement(self, player_entity: int, dx: int, dy: int) -> None:
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
                    self.camera.follow_entity(new_position.x, new_position.y)
                    
                    # Generate new chunks if needed
                    self._ensure_chunks_loaded(new_position.x)
            else:
                # Movement blocked
                if self.world_generator.is_wall_at(target_x, target_y):
                    self.message_log.add_warning("You bump into a wall.")
                else:
                    self.message_log.add_warning("Something blocks your way.")
    
    def _ensure_chunks_loaded(self, player_x: int) -> None:
        """Ensure necessary chunks are loaded around the player."""
        current_chunk = player_x // 40
        
        # Load current chunk and next chunk
        for chunk_id in range(max(0, current_chunk - 1), current_chunk + 3):
            if chunk_id not in self.world_generator.chunks:
                chunk = self.world_generator.generate_chunk(chunk_id)
                self.message_log.add_debug(f"Generated chunk {chunk_id}")
                
                # Trigger prefab spawning for the previous chunk
                self.prefab_manager.update_for_chunk_generation(chunk_id)
    
    def _restart_game(self) -> None:
        """Restart the game with a new world."""
        # Clear all entities from the world
        entities_to_destroy = list(self.world.entities.get_alive_entities())
        for entity_id in entities_to_destroy:
            self.world.destroy_entity(entity_id)
        
        # Reset game state
        self.game_state.reset()
        
        # Clear message log
        self.message_log.clear()
        
        # Generate new seed and reinitialize world generator
        self.world_generator = WorldGenerator(self.world, seed=random.randint(0, 1000000))
        
        # Reset prefab manager
        self.prefab_manager = PrefabManager(self.world, self.world_generator, self.message_log)
        
        # Update systems that reference the world generator
        self.movement_system.world_generator = self.world_generator
        self.fov_system.world_generator = self.world_generator
        self.render_system.world_generator = self.world_generator
        
        # Reinitialize the game
        self._initialize_game()
        
        # Invalidate render cache
        self.render_system.invalidate_cache()
        
        # Request a render
        self.game_state.request_render()
    
    def _give_starting_items(self, player_entity: int) -> None:
        """Give the player some starting items."""
        inventory = self.world.get_component(player_entity, Inventory)
        equipment_slots = self.world.get_component(player_entity, EquipmentSlots)
        
        if not inventory or not equipment_slots:
            return
        
        # Create starting equipment - war maul and chain mail
        war_maul = self.item_factory.create_item('war_maul')
        chain_mail = self.item_factory.create_item('chain_mail')
        
        # Equip items directly (without adding to inventory first)
        if war_maul:
            equipment_slots.equip_item(war_maul, 'weapon')
            self.message_log.add_info("You equip the War Maul.")
        
        if chain_mail:
            equipment_slots.equip_item(chain_mail, 'armor')
            self.message_log.add_info("You equip the Chain Mail.")
        
        self.message_log.add_info("You start equipped with a war maul and chain mail.")
    
    def _spawn_test_items(self, spawn_x: int, spawn_y: int) -> None:
        """Spawn some test items near the player for testing."""
        chunk = self.world_generator.chunks.get(0)
        if not chunk:
            return
        
        # Only spawn potions - no extra equipment
        test_items = ['health_potion', 'greater_health_potion']
        
        placed_items = 0
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if placed_items >= len(test_items):
                    break
                    
                test_x = spawn_x + dx
                test_y = spawn_y + dy
                
                # Skip player position
                if dx == 0 and dy == 0:
                    continue
                
                # Check if position is valid and not a wall
                if (test_y >= 0 and test_y < chunk.height and 
                    test_x >= 0 and test_x < chunk.width * 40 and
                    not self.world_generator.is_wall_at(test_x, test_y)):
                    
                    # Create and place item
                    item_id = test_items[placed_items]
                    item_entity = self.item_factory.create_item(item_id, test_x, test_y)
                    if item_entity:
                        placed_items += 1
            
            if placed_items >= len(test_items):
                break
        
        if placed_items > 0:
            self.message_log.add_info(f"Placed {placed_items} potions nearby.")
    
    def _handle_pickup(self, player_entity: int) -> None:
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
        for item_entity_id in items_at_pos:
            if self.inventory_system.pickup_item(player_entity, item_entity_id):
                picked_up_count += 1
                # Invalidate render cache since item was removed from world
                self.render_system.invalidate_cache()
        
        if picked_up_count == 0:
            self.message_log.add_warning("Your inventory is full!")
    
    def _handle_item_selection(self, player_entity: int, item_number: int) -> None:
        """Handle item selection from menus."""
        from components.items import Inventory, Item, Equipment, Consumable, EquipmentSlots
        
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
        from components.items import Inventory, Item, Equipment, EquipmentSlots
        
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
        from components.items import Inventory, Item, Consumable
        
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
        from components.items import Inventory, Item
        
        inventory = self.world.get_component(player_entity, Inventory)
        if not inventory:
            return
        
        # Handle selection - all items in inventory can be dropped
        if 1 <= item_number <= len(inventory.items):
            item_entity_id = inventory.items[item_number - 1]
            success = self.inventory_system.drop_item(player_entity, item_entity_id)
            if success:
                # Invalidate render cache since item was added to world
                self.render_system.invalidate_cache()
                self.render_system.hide_all_menus()
        else:
            self.message_log.add_warning("Invalid selection.")
    
    def _handle_throwing_selection(self, player_entity: int, item_number: int) -> None:
        """Handle throwing item selection."""
        from components.items import Inventory
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
    
    def _update_world(self) -> None:
        """Update all world systems after player action."""
        # Update FOV first
        self.fov_system.update()
        
        # Update effects systems
        self.effects_manager.update()  # Process pending effects first
        self.render_system.invalidate_cache()  # Invalidate cache after effects (knockback, etc.)
        self.status_effects_system.update()
        self.physics_system.update()
        
        # Update AI
        self.ai_system.update()


def main():
    """Entry point for the game."""
    game = RoguelikeGame()
    game.run()


if __name__ == "__main__":
    main()
