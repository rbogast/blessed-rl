"""
Main entry point for the ECS Roguelike game launcher.
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
from systems.lighting import LightingSystem
from systems.render import RenderSystem
from systems.skills import SkillsSystem
from systems.throwing import ThrowingSystem
from systems.auto_explore import AutoExploreSystem
from systems.examine import ExamineSystem
from game.prefabs import PrefabManager
from game.item_factory import ItemFactory
from effects.core import EffectsManager
from effects.physics import PhysicsSystem, KnockbackEffect, ShockwaveEffect
from effects.status_effects import StatusEffectsSystem, BleedingEffect
from effects.tile_effects import TileEffectsSystem, BloodSplatterEffect
from game.game_initializer import GameInitializer
from game.level_manager import LevelManager
from game.action_handler import ActionHandler
from game.save_system import SaveSystem


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
        self.lighting_system = LightingSystem(self.world, self.message_log)
        self.fov_system = FOVSystem(self.world, self.world_generator, message_log=self.message_log, lighting_system=self.lighting_system)
        self.throwing_system = ThrowingSystem(self.world, self.movement_system, self.fov_system, 
                                            self.physics_system, self.skills_system, self.message_log)
        
        # Initialize auto-explore system
        self.auto_explore_system = AutoExploreSystem(self.world, self.movement_system, self.fov_system,
                                                    self.world_generator, self.message_log)
        
        # Initialize examine system
        self.examine_system = ExamineSystem(self.world, self.fov_system, self.message_log, self.world_generator)
        
        # Set throwing system reference in render system for cursor visualization
        self.render_system.set_throwing_system(self.throwing_system)
        
        # Set examine system reference in render system for cursor visualization
        self.render_system.set_examine_system(self.examine_system)
        
        # Initialize helper classes
        self.level_manager = LevelManager(self.world, self.world_generator, self.game_state, 
                                        self.message_log, self.camera, self.fov_system, self.render_system)
        self.action_handler = ActionHandler(self.world, self.game_state, self.message_log, 
                                          self.render_system, self.movement_system, self.combat_system,
                                          self.inventory_system, self.throwing_system, self.level_manager,
                                          self.auto_explore_system)
        self.game_initializer = GameInitializer(self.world, self.world_generator, self.game_state,
                                              self.message_log, self.glyph_config, self.item_factory)
        
        # Initialize save system
        self.save_system = SaveSystem()
        
        # Add systems to world
        self.world.systems.add_system(self.input_system)
        self.world.systems.add_system(self.movement_system)
        self.world.systems.add_system(self.combat_system)
        self.world.systems.add_system(self.ai_system)
        self.world.systems.add_system(self.fov_system)
        self.world.systems.add_system(self.render_system)
        self.world.systems.add_system(self.throwing_system)
        self.world.systems.add_system(self.auto_explore_system)
        
        # Note: Game initialization is now handled explicitly by caller
        # Don't automatically initialize here to avoid conflicts with loading
    
    def _initialize_game(self) -> None:
        """Initialize the game world and player."""
        player_entity, spawn_x, spawn_y = self.game_initializer.initialize_game()
        
        # Update camera to follow player and set level bounds
        level_0 = self.game_state.get_current_level()
        self.camera.set_level_bounds(level_0.width, level_0.height)
        self.camera.follow_entity(spawn_x, spawn_y)
        
        # Calculate initial FOV
        self.fov_system.update()
    
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
        import time
        
        try:
            # The render system now handles terminal setup
            while True:
                # Render only when needed
                if self.game_state.should_render():
                    self.render_system.update()
                    self.game_state.render_complete()
                
                # Check for game over (only quit if explicitly requested)
                if self.game_state.is_game_over():
                    # Handle permadeath - delete save file if player died
                    if self.game_state.game_over_reason == "You died!":
                        self.handle_player_death()
                    break
                
                # Check if auto-explore is active
                player_entity = self.game_state.get_player_entity()
                is_auto_exploring = self._is_auto_exploring(player_entity)
                
                if is_auto_exploring:
                    # Auto-explore mode: non-blocking input with timing
                    key = self.render_system.term.inkey(timeout=0.025)  # 25ms = 40 FPS
                    
                    if key:
                        # Any key interrupts auto-explore
                        self._interrupt_auto_explore(player_entity)
                        # Process the interrupting key
                        action_taken = self.input_system.handle_input(key)
                        if action_taken:
                            self._process_player_action()
                            self.game_state.player_turn_taken()
                            self._update_world()
                            self.game_state.reset_turn_flag()
                            self.game_state.request_render()
                    else:
                        # Continue auto-explore
                        self._process_auto_explore_step(player_entity)
                else:
                    # Normal mode: blocking input
                    key = self.render_system.term.inkey()
                    if key:
                        # Handle input
                        action_taken = self.input_system.handle_input(key)
                        
                        if action_taken:
                            # Auto-save at the beginning of the turn (traditional roguelike style)
                            self._auto_save()
                            
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
            self.action_handler.handle_player_movement(player_entity, dx, dy)
        elif action[0] == 'wait':
            # Player waits - no additional processing needed
            pass
        elif action[0] == 'restart':
            self._restart_game()
        elif action[0] == 'toggle_inventory':
            self.render_system.toggle_inventory_display()
        elif action[0] == 'pickup':
            self.action_handler.handle_pickup(player_entity)
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
            self.action_handler.handle_item_selection(player_entity, item_number)
        elif action[0] == 'move_throwing_cursor':
            _, dx, dy = action
            self.throwing_system.move_cursor(player_entity, dx, dy)
        elif action[0] == 'execute_throw':
            self.throwing_system.execute_throw(player_entity)
        elif action[0] == 'cancel_throw':
            self.throwing_system.cancel_throwing(player_entity)
        elif action[0] == 'toggle_auto_explore':
            self.action_handler.handle_auto_explore_toggle(player_entity)
        elif action[0] == 'use_stairs_down':
            self.action_handler.handle_use_stairs_down(player_entity)
        elif action[0] == 'use_stairs_up':
            self.action_handler.handle_use_stairs_up(player_entity)
        elif action[0] == 'travel_to_stairs_down':
            self.action_handler.handle_travel_to_stairs_down(player_entity)
        elif action[0] == 'travel_to_stairs_up':
            self.action_handler.handle_travel_to_stairs_up(player_entity)
        elif action[0] == 'enter_examine_mode':
            self._handle_enter_examine_mode(player_entity)
        elif action[0] == 'move_examine_cursor':
            _, dx, dy = action
            self._handle_move_examine_cursor(player_entity, dx, dy)
        elif action[0] == 'examine_select':
            self._handle_examine_select(player_entity)
        elif action[0] == 'exit_examine_mode':
            self._handle_exit_examine_mode(player_entity)
        elif action[0] == 'close_menus':
            self.render_system.hide_all_menus()
    
    
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
    
    
    
    def _update_world(self) -> None:
        """Update all world systems after player action."""
        # Update lighting system first (fuel depletion)
        self.lighting_system.update()
        
        # Update FOV (which now uses lighting for sight radius)
        self.fov_system.update()
        
        # Update auto-explore system (before AI so it can move the player)
        self.auto_explore_system.update()
        
        # Update effects systems
        self.effects_manager.update()  # Process pending effects first
        self.render_system.invalidate_cache()  # Invalidate cache after effects (knockback, etc.)
        self.status_effects_system.update()
        self.physics_system.update()
        
        # Update AI
        self.ai_system.update()
    
    def _is_auto_exploring(self, player_entity: int) -> bool:
        """Check if the player is currently auto-exploring."""
        if not player_entity:
            return False
        
        from components.auto_explore import AutoExplore
        auto_explore = self.world.get_component(player_entity, AutoExplore)
        return auto_explore and auto_explore.is_active()
    
    def _interrupt_auto_explore(self, player_entity: int) -> None:
        """Interrupt auto-exploration."""
        if player_entity:
            self.auto_explore_system.interrupt_auto_explore(player_entity)
    
    def _process_auto_explore_step(self, player_entity: int) -> None:
        """Process one step of auto-exploration."""
        if not player_entity:
            return
        
        # Store previous position to check if movement occurred
        position = self.world.get_component(player_entity, Position)
        prev_x, prev_y = (position.x, position.y) if position else (0, 0)
        
        # Update auto-explore system
        self.auto_explore_system.update()
        
        # Check if player actually moved
        position = self.world.get_component(player_entity, Position)
        if position and (position.x != prev_x or position.y != prev_y):
            # Update FOV after movement
            self.fov_system.update()
            
            # Update camera to follow player
            self.camera.follow_entity(position.x, position.y)
            
            # Invalidate entity cache since player moved
            self.render_system.invalidate_cache()
            
            # Force immediate render to show movement
            self.render_system.update()
            self.game_state.render_complete()
        else:
            # No movement occurred, just request render for any state changes
            self.game_state.request_render()
    
    def _auto_save(self) -> None:
        """Auto-save the game state at the beginning of each turn."""
        try:
            success = self.save_system.save_game(
                self.world, 
                self.game_state, 
                self.message_log, 
                self.camera, 
                self.world_generator
            )
            if not success:
                # Save failed, but don't interrupt gameplay
                # Could add a subtle indicator or log message here
                pass
        except Exception as e:
            # Save failed, but don't crash the game
            print(f"Auto-save failed: {e}")
    
    def load_saved_game(self) -> bool:
        """Load a saved game. Returns True if successful."""
        save_data = self.save_system.load_game()
        if not save_data:
            return False
        
        try:
            # Clear current game state
            self._clear_current_game()
            
            # Restore the saved game
            success = self.save_system.restore_game(
                save_data,
                self.world,
                self.game_state,
                self.message_log,
                self.camera,
                self.world_generator
            )
            
            if success:
                # Update systems that need to know about the restored state
                self._post_load_setup()
                return True
            else:
                # Restore failed, reinitialize fresh game
                self._initialize_game()
                return False
                
        except Exception as e:
            print(f"Error loading saved game: {e}")
            # Restore failed, reinitialize fresh game
            self._initialize_game()
            return False
    
    def _clear_current_game(self) -> None:
        """Clear the current game state before loading."""
        # Clear all entities from the world
        entities_to_destroy = list(self.world.entities.get_alive_entities())
        for entity_id in entities_to_destroy:
            self.world.destroy_entity(entity_id)
        
        # Reset game state
        self.game_state.reset()
        
        # Clear message log
        self.message_log.clear()
    
    def _post_load_setup(self) -> None:
        """Setup systems after loading a saved game."""
        # Update camera bounds based on current level
        current_level = self.game_state.get_current_level()
        if current_level:
            self.camera.set_level_bounds(current_level.width, current_level.height)
        
        # Update systems that reference the world generator
        self.movement_system.world_generator = self.world_generator
        self.fov_system.world_generator = self.world_generator
        self.render_system.world_generator = self.world_generator
        
        # Calculate FOV for current player position
        self.fov_system.update()
        
        # Invalidate render cache
        self.render_system.invalidate_cache()
        
        # Request a render
        self.game_state.request_render()
    
    def handle_player_death(self) -> None:
        """Handle player death - delete save file for permadeath."""
        self.save_system.delete_save_file()
    
    def _handle_enter_examine_mode(self, player_entity: int) -> None:
        """Handle entering examine mode."""
        if self.examine_system.start_examine_mode(player_entity):
            # Set up examine menu
            from systems.menus.examine_menu import ExamineMenu
            examine_menu = ExamineMenu(self.world, self.examine_system)
            self.render_system.menu_manager.set_examine_menu(examine_menu)
            self.render_system.menu_manager.show_examine_menu()
    
    def _handle_move_examine_cursor(self, player_entity: int, dx: int, dy: int) -> None:
        """Handle moving the examine cursor."""
        self.examine_system.move_cursor(player_entity, dx, dy)
        # Update examine menu content
        if self.render_system.menu_manager.is_examine_active():
            self.render_system.menu_manager.examine_menu.invalidate()
    
    def _handle_examine_select(self, player_entity: int) -> None:
        """Handle selecting from examine list."""
        examine_menu = self.render_system.menu_manager.examine_menu
        if examine_menu and examine_menu.can_select_items():
            selected_index = examine_menu.selected_index
            if selected_index >= 0:
                examine_menu.select_entity(selected_index)
        elif examine_menu and examine_menu.is_showing_detail():
            # Return to list view
            examine_menu.return_to_list()
    
    def _handle_exit_examine_mode(self, player_entity: int) -> None:
        """Handle exiting examine mode."""
        self.examine_system.exit_examine_mode(player_entity)
        self.render_system.hide_all_menus()


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


def show_launcher_menu():
    """Show the game launcher menu and return user choice."""
    # Check if a save file exists
    save_system = SaveSystem()
    has_save = save_system.has_save_file()
    
    print("=" * 50)
    print("    BLESSED ROGUELIKE LAUNCHER")
    print("=" * 50)
    print()
    
    if has_save:
        print("1. New Game")
        print("2. Continue Game")
        print("3. Dungeon Editor")
        print("4. Exit")
        print()
        valid_choices = ['1', '2', '3', '4']
        max_choice = 4
    else:
        print("1. New Game")
        print("2. Dungeon Editor")
        print("3. Exit")
        print()
        valid_choices = ['1', '2', '3']
        max_choice = 3
    
    while True:
        try:
            choice = input(f"Select an option (1-{max_choice}): ").strip()
            if choice in valid_choices:
                return int(choice), has_save
            else:
                print(f"Invalid choice. Please enter 1-{max_choice}.")
        except (EOFError, KeyboardInterrupt):
            return max_choice, has_save  # Exit on Ctrl+C or EOF


def main():
    """Entry point for the game launcher."""
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
        print("Debug: Starting launcher...")
        print()
    
    # Show launcher menu
    choice, has_save = show_launcher_menu()
    
    if choice == 1:
        # New Game
        try:
            game = RoguelikeGame(charset_override=charset_override)
            game._initialize_game()  # Explicitly initialize for new games
            game.run()
        except Exception as e:
            print(f"Error starting game: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    elif choice == 2:
        if has_save:
            # Continue Game
            try:
                print("DEBUG: Creating RoguelikeGame instance...")
                game = RoguelikeGame(charset_override=charset_override)
                print("DEBUG: Attempting to load saved game...")
                success = game.load_saved_game()
                print(f"DEBUG: Load result: {success}")
                if success:
                    print("DEBUG: Load successful, starting game...")
                    game.run()
                else:
                    print("Failed to load saved game. Starting new game instead.")
                    game._initialize_game()  # Initialize new game if loading failed
                    game.run()
            except Exception as e:
                print(f"Error loading saved game: {e}")
                if args.debug:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
        else:
            # Dungeon Editor (when no save exists)
            try:
                from maps import MapPreviewTool
                editor = MapPreviewTool(charset_override=charset_override)
                editor.run()
            except Exception as e:
                print(f"Error starting dungeon editor: {e}")
                if args.debug:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
    
    elif choice == 3:
        if has_save:
            # Dungeon Editor (when save exists)
            try:
                from maps import MapPreviewTool
                editor = MapPreviewTool(charset_override=charset_override)
                editor.run()
            except Exception as e:
                print(f"Error starting dungeon editor: {e}")
                if args.debug:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
        else:
            # Exit (when no save exists)
            print("Goodbye!")
            return
    
    elif choice == 4:
        # Exit (when save exists)
        print("Goodbye!")
        return


if __name__ == "__main__":
    main()
