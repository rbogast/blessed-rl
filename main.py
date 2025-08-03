"""
Main entry point for the ECS Roguelike game.
"""

import argparse
import random
import sys
from ecs import World
from components.core import Position, Renderable, Player, Blocking, Visible
from components.combat import Health, Stats
from components.character import CharacterAttributes, Experience
from components.effects import Physics
from components.items import Inventory, EquipmentSlots
from components.corpse import Species
from components.skills import Skills
from game.level_world_gen import LevelWorldGenerator
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
    
    def __init__(self, charset_override=None):
        # Store charset override for use in initialization
        self.charset_override = charset_override
        
        # Initialize core ECS
        self.world = World()
        
        # Initialize game components
        self.game_state = GameStateManager()
        self.message_log = MessageLog(width=GameConfig.SIDEBAR_WIDTH, height=GameConfig.GAME_INFO_HEIGHT, game_state=self.game_state)
        self.camera = Camera(viewport_width=GameConfig.MAP_WIDTH, viewport_height=GameConfig.MAP_HEIGHT)
        self.world_generator = LevelWorldGenerator(self.world, seed=random.randint(0, 1000000))
        
        # Initialize prefab system
        self.prefab_manager = PrefabManager(self.world, self.world_generator, self.message_log)
        
        # Initialize item factory
        self.item_factory = ItemFactory(self.world)
        
        # Initialize glyph configuration early so it can be used by render system
        self.glyph_config = GlyphConfig(charset_override=self.charset_override)
        
        # Initialize effects systems
        self.effects_manager = EffectsManager(self.world)
        self.tile_effects_system = TileEffectsSystem(self.world, self.message_log)
        self.status_effects_system = StatusEffectsSystem(self.world, self.effects_manager, self.message_log, self.game_state, self.world_generator)
        
        # Initialize systems (render system first, then input system with render system reference)
        self.render_system = RenderSystem(self.world, self.camera, self.message_log, 
                                        self.world_generator, self.game_state, self.tile_effects_system, self.glyph_config)
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
        self.message_log.add_system("Initializing Dungeon Diving Roguelike...")
        self.message_log.add_system(f"World seed: {self.world_generator.seed}")
        
        # Generate initial level (level 0)
        level_0 = self.world_generator.generate_level(0, None, self.game_state.turn_count)
        self.game_state.add_level(level_0)
        self.game_state.change_level(0)
        self.world_generator.set_current_level(level_0)
        self.message_log.add_system("Generated starting level")
        
        # Create player entity
        player_entity = self.world.create_entity()
        
        # Find a safe spawn position on level 0
        spawn_x, spawn_y = self._find_spawn_position(level_0)
        
        # Get player glyph from configuration
        player_char, player_color = self.glyph_config.get_entity_glyph('player')
        
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
        self.world.add_component(player_entity, Species('human'))  # Player is human
        
        # Add player to current level
        level_0.add_entity(player_entity)
        
        # Set player in game state
        self.game_state.set_player_entity(player_entity)
        
        # Update camera to follow player and set level bounds
        self.camera.set_level_bounds(level_0.width, level_0.height)
        self.camera.follow_entity(spawn_x, spawn_y)
        
        # Calculate initial FOV
        self.fov_system.update()
        
        # Give player some starting items
        self._give_starting_items(player_entity)
        
        # Spawn some test items in the world
        self._spawn_test_items(spawn_x, spawn_y, level_0)
        
        self.message_log.add_system(f"Player spawned at X={spawn_x}, Y={spawn_y} on level 0")
        self.message_log.add_info("Use numpad keys to move (7,8,9,4,6,1,2,3)")
        self.message_log.add_info("Press 5 to wait, I for inventory, G to pickup")
        self.message_log.add_info("Press E to equip/unequip, U to use, D to drop")
        self.message_log.add_info("Step on '>' to descend to the next level!")
    
    def _find_spawn_position(self, level) -> tuple:
        """Find a safe spawn position in the level."""
        # Try to find an open position near the center
        center_x = level.width // 2
        center_y = level.height // 2
        
        # Search in expanding rings from center
        for radius in range(1, min(level.width, level.height) // 2):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Only check perimeter
                        x = center_x + dx
                        y = center_y + dy
                        if (0 <= x < level.width and 0 <= y < level.height and 
                            not level.is_wall(x, y)):
                            return x, y
        
        # Fallback: find any open position
        for y in range(level.height):
            for x in range(level.width):
                if not level.is_wall(x, y):
                    return x, y
        
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
                    
                    # Check for stairs and handle level transitions
                    self._check_stairs_interaction(player_entity, new_position.x, new_position.y)
            else:
                # Movement blocked
                if self.world_generator.is_wall_at(target_x, target_y):
                    self.message_log.add_warning("You bump into a wall.")
                else:
                    self.message_log.add_warning("Something blocks your way.")
    
    def _check_stairs_interaction(self, player_entity: int, x: int, y: int) -> None:
        """Check if player is on stairs and handle level transitions."""
        stairs_type = self.world_generator.is_stairs_at(x, y)
        
        if stairs_type == 'down':
            # Player stepped on downward stairs
            current_level_id = self.game_state.get_current_level_id()
            next_level_id = current_level_id + 1
            
            self.message_log.add_info(f"You descend to level {next_level_id}...")
            self._change_to_level(player_entity, next_level_id, stairs_type)
            
        elif stairs_type == 'up':
            # Player stepped on upward stairs
            current_level_id = self.game_state.get_current_level_id()
            if current_level_id > 0:
                prev_level_id = current_level_id - 1
                self.message_log.add_info(f"You ascend to level {prev_level_id}...")
                self._change_to_level(player_entity, prev_level_id, stairs_type)
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
            from components.items import Inventory, EquipmentSlots
            
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
        
        # Update FOV for new level
        self.fov_system.update()
        
        # Invalidate render cache
        self.render_system.invalidate_cache()
        
        # Request render
        self.game_state.request_render()
    
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
        self.world_generator = LevelWorldGenerator(self.world, seed=random.randint(0, 1000000))
        
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
    
    def _spawn_test_items(self, spawn_x: int, spawn_y: int, level) -> None:
        """Spawn some test items near the player for testing."""
        # Spawn persistence artifact on level 0 only
        if level.level_id == 0:
            # Find a position for the persistence artifact (away from player)
            artifact_placed = False
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    if artifact_placed:
                        break
                    
                    # Skip positions too close to player
                    if abs(dx) < 2 and abs(dy) < 2:
                        continue
                    
                    test_x = spawn_x + dx
                    test_y = spawn_y + dy
                    
                    # Check if position is valid and not a wall
                    if (0 <= test_x < level.width and 0 <= test_y < level.height and 
                        not level.is_wall(test_x, test_y)):
                        
                        # Create and place persistence artifact
                        artifact_entity = self.item_factory.create_item('persistence_artifact', test_x, test_y)
                        if artifact_entity:
                            level.add_entity(artifact_entity)
                            artifact_placed = True
                            self.message_log.add_info("A mysterious glowing orb lies nearby...")
                            break
                
                if artifact_placed:
                    break
        
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
                if (0 <= test_x < level.width and 0 <= test_y < level.height and 
                    not level.is_wall(test_x, test_y)):
                    
                    # Create and place item
                    item_id = test_items[placed_items]
                    item_entity = self.item_factory.create_item(item_id, test_x, test_y)
                    if item_entity:
                        level.add_entity(item_entity)
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


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Blessed Roguelike - A terminal-based dungeon crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py                    # Run with auto-detected charset
  python3 main.py -f                 # Force ASCII fallback charset
  python3 main.py --charset unicode  # Force Unicode charset
  python3 main.py --charset ascii    # Force ASCII charset
  python3 main.py --list-charsets    # List available character sets
  python3 main.py -d -f              # Debug mode with ASCII charset
        """
    )
    
    parser.add_argument(
        '-f', '--fallback',
        action='store_true',
        help='Force ASCII fallback character set (same as --charset ascii)'
    )
    
    parser.add_argument(
        '-c', '--charset',
        choices=['unicode', 'ascii', 'cp437'],
        help='Specify character set to use (overrides auto-detection)'
    )
    
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug mode with charset information'
    )
    
    parser.add_argument(
        '--list-charsets',
        action='store_true',
        help='List available character sets and exit'
    )
    
    return parser.parse_args()


def list_available_charsets():
    """List available character sets and their descriptions."""
    print("Available Character Sets:")
    print("=" * 50)
    print("unicode  - Full Unicode characters (default on Linux/macOS)")
    print("         - Uses: █▓▒░ for walls, · for floor, ♠♣♥♦ for suits")
    print("         - Best visual quality but may not work on all terminals")
    print()
    print("ascii    - Basic ASCII characters (fallback)")
    print("         - Uses: # for walls, . for floor, basic letters/symbols")
    print("         - Works on all terminals and systems")
    print()
    print("cp437    - Extended ASCII (Code Page 437)")
    print("         - Uses: ██▓▒░ for walls, · for floor, extended symbols")
    print("         - Good compatibility with Windows terminals")
    print()
    print("The game will auto-detect the best charset for your system,")
    print("but you can override this with the --charset option.")


def main():
    """Entry point for the game."""
    args = parse_arguments()
    
    # Handle special commands
    if args.list_charsets:
        list_available_charsets()
        return
    
    # Determine charset override
    charset_override = None
    if args.fallback:
        charset_override = 'ascii'
    elif args.charset:
        charset_override = args.charset
    
    # Show charset information in debug mode
    if args.debug:
        if charset_override:
            print(f"Debug: Using charset override: {charset_override}")
        else:
            print("Debug: Using auto-detected charset")
        print("Debug: Starting game...")
        print()
    
    # Create and run the game
    try:
        game = RoguelikeGame(charset_override=charset_override)
        game.run()
    except Exception as e:
        print(f"Error starting game: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
