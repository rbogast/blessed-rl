"""
Map Preview Tool for roguelike development.
Schedule editor for testing and configuring map generation parameters.
"""

import random
import yaml
from ecs import World
from components.core import Position, Renderable, Player, Blocking, Visible
from game.level_world_gen import LevelWorldGenerator
from game.camera import Camera
from game.message_log import MessageLog
from game.game_state import GameStateManager, GameState
from game.glyph_config import GlyphConfig
from game.config import GameConfig
from systems.input import InputSystem
from systems.fov import FOVSystem
from systems.render import RenderSystem


class MapPreviewTool:
    """Map preview tool for testing map generation and editing schedule.yaml."""
    
    def __init__(self, charset_override=None):
        # Store charset override for use in initialization
        self.charset_override = charset_override
        
        # Initialize core ECS
        self.world = World()
        
        # Initialize game components for preview mode
        self.game_state = GameStateManager()
        self.game_state.set_state(GameState.MAP_PREVIEW)
        
        self.message_log = MessageLog(width=GameConfig.SIDEBAR_WIDTH, height=GameConfig.GAME_INFO_HEIGHT, game_state=self.game_state)
        self.camera = Camera(viewport_width=GameConfig.MAP_WIDTH, viewport_height=GameConfig.MAP_HEIGHT)
        
        # Use LevelWorldGenerator - same as main game
        self.world_generator = LevelWorldGenerator(self.world, seed=random.randint(0, 1000000))
        
        # Schedule editing state
        self.current_editing_level = 0
        self.schedule_data = self._load_schedule()
        self.current_level = None
        
        # Temporary overrides for preview (not saved until 'S' is pressed)
        self.temp_overrides = {}
        
        # Generation counter for terrain variation (simulates turn_count)
        self.generation_counter = 0
        
        # Parameter editing system
        self.selected_parameter = 0
        self.editing_parameter = False
        self.edit_buffer = ""
        self.template_menu_active = False
        
        # Get available templates dynamically from the registry
        from game.worldgen.templates import list_templates
        available_templates = list_templates()
        
        # Create template selection menu
        from systems.menus.template_menu import TemplateSelectionMenu
        self.template_menu = TemplateSelectionMenu(self.world, available_templates)
        
        # Base parameter definitions
        self.parameter_definitions = {
            'seed': {'type': int, 'min': 0, 'max': 1000000},
            'generation': {'type': int, 'min': 0, 'max': 1000},
            'level': {'type': int, 'min': 0, 'max': 100},
            'template': {'type': str, 'options': available_templates},
            'wall_probability': {'type': float, 'min': 0.0, 'max': 1.0},
            'ca_iterations': {'type': int, 'min': 0, 'max': 10},
            'tree_density': {'type': float, 'min': 0.0, 'max': 1.0},
            'tree_count': {'type': int, 'min': 0, 'max': 50},
            'enemy_density': {'type': float, 'min': 0.0, 'max': 2.0},
            'maze_openings': {'type': int, 'min': 0, 'max': 50}
        }
        
        # Add template-specific parameters dynamically
        self._load_template_parameters()
        # Dynamic parameter order will be updated based on current template
        self.parameter_order = ['level', 'seed', 'generation', 'template']
        self._update_parameter_order()
    
    def _load_template_parameters(self) -> None:
        """Load parameter definitions from all available templates."""
        try:
            from game.worldgen.templates import list_templates, get_template
            
            for template_name in list_templates():
                try:
                    template = get_template(template_name)
                    if template:
                        template_params = template.get_parameters()
                        
                        # Add each template parameter to our definitions
                        for param_name, param_def in template_params.items():
                            if param_name not in self.parameter_definitions:
                                # Convert ParameterDef to our format
                                self.parameter_definitions[param_name] = {
                                    'type': param_def.param_type,
                                    'min': param_def.min_value,
                                    'max': param_def.max_value
                                }
                except Exception as e:
                    # Skip templates that fail to load
                    continue
        except Exception as e:
            # Fallback if template system fails
            pass
        
        # Initialize systems for preview mode
        self.render_system = RenderSystem(self.world, self.camera, self.message_log, 
                                        self.world_generator, self.game_state)
        
        # Replace the status display with our map generation version after render system is created
        from ui.status_display import MapGenStatusDisplay
        from ui.text_formatter import TextFormatter
        text_formatter = TextFormatter(self.render_system.term)
        self.render_system.status_display = MapGenStatusDisplay(self.world, self, text_formatter)
        
        # Override the menu manager's get_menu_line method to handle our template menu
        original_get_menu_line = self.render_system.menu_manager.get_menu_line
        def custom_get_menu_line(line_num, player_entity):
            if self.template_menu_active:
                return self.template_menu.get_menu_line(line_num, player_entity)
            return original_get_menu_line(line_num, player_entity)
        
        self.render_system.menu_manager.get_menu_line = custom_get_menu_line
        
        # Override the menu manager's is_menu_active method to include our template menu
        original_is_menu_active = self.render_system.menu_manager.is_menu_active
        def custom_is_menu_active():
            return self.template_menu_active or original_is_menu_active()
        
        self.render_system.menu_manager.is_menu_active = custom_is_menu_active
        self.input_system = InputSystem(self.world, self.game_state, self.message_log, self.render_system)
        self.fov_system = FOVSystem(self.world, self.world_generator, message_log=self.message_log)
        
        # Enable preview mode in FOV system
        self.fov_system.set_preview_mode(True)
        
        # Add systems to world
        self.world.systems.add_system(self.input_system)
        self.world.systems.add_system(self.fov_system)
        self.world.systems.add_system(self.render_system)
        
        # Initialize the preview
        self._initialize_preview()
    
    def _load_schedule(self) -> list:
        """Load the current schedule.yaml file."""
        try:
            with open('data/schedule.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.message_log.add_warning("schedule.yaml not found, using defaults")
            return []
        except Exception as e:
            self.message_log.add_error(f"Error loading schedule: {e}")
            return []
    
    def _save_schedule(self) -> None:
        """Save the current schedule data to schedule.yaml with proper formatting."""
        try:
            # Apply temporary overrides to the actual schedule before saving
            self._apply_temp_overrides_to_schedule()
            
            with open('data/schedule.yaml', 'w') as f:
                # Write header comment
                f.write("# Dungeon level progression schedule for the ECS Roguelike Engine\n")
                f.write("# This file defines biome segments and their parameters by level\n\n")
                
                # Write each entry with proper spacing
                for i, entry in enumerate(self.schedule_data):
                    if i > 0:
                        f.write("\n")  # Add blank line between entries
                    
                    # Write the entry
                    yaml.dump([entry], f, default_flow_style=False, sort_keys=False)
            
            # Clear temporary overrides since they're now saved
            self.temp_overrides.clear()
            
            # Reload the scheduler to pick up the saved changes
            self.world_generator.scheduler.reload_schedule()
            
            self.message_log.add_system("Schedule saved to data/schedule.yaml")
        except Exception as e:
            self.message_log.add_error(f"Error saving schedule: {e}")
    
    def _apply_temp_overrides_to_schedule(self) -> None:
        """Apply temporary overrides to the actual schedule data."""
        for level_id, overrides in self.temp_overrides.items():
            # Find or create schedule entry for this level
            existing_entry = None
            for entry in self.schedule_data:
                if entry['from'] <= level_id <= entry['to']:
                    existing_entry = entry
                    break
            
            if existing_entry:
                # Update existing entry
                if 'biome' in overrides:
                    existing_entry['biome'] = overrides['biome']
                
                if 'overrides' in overrides:
                    if 'overrides' not in existing_entry:
                        existing_entry['overrides'] = {}
                    existing_entry['overrides'].update(overrides['overrides'])
            else:
                # Create new entry for this level
                new_entry = {
                    'from': level_id,
                    'to': level_id,
                    'biome': overrides.get('biome', 'default'),
                    'overrides': overrides.get('overrides', {})
                }
                self.schedule_data.append(new_entry)
    
    def _get_schedule_entry_for_level(self, level_id: int) -> dict:
        """Get the schedule entry that applies to the given level."""
        for entry in self.schedule_data:
            if entry['from'] <= level_id <= entry['to']:
                return entry
        
        # Return default entry if no match found
        return {
            'from': level_id,
            'to': level_id,
            'biome': 'default',
            'overrides': {}
        }
    
    def _initialize_preview(self) -> None:
        """Initialize the map preview."""
        self.message_log.add_system("Map Schedule Editor Initialized")
        self.message_log.add_system(f"World seed: {self.world_generator.seed}")
        
        # Generate initial level using current editing level
        self._generate_current_level()
        
        # Create a dummy player entity for camera positioning
        player_entity = self.world.create_entity()
        
        # Position player at center of map
        center_x = self.current_level.width // 2
        center_y = self.current_level.height // 2
        
        # Get player glyph from configuration
        glyph_config = GlyphConfig(charset_override=self.charset_override)
        player_char, player_color = glyph_config.get_entity_glyph('player')
        
        # Add player components with all required components for status display
        from components.combat import Health
        from components.character import CharacterAttributes, Experience
        from components.items import EquipmentSlots
        
        self.world.add_component(player_entity, Position(center_x, center_y))
        self.world.add_component(player_entity, Renderable(player_char, player_color))
        self.world.add_component(player_entity, Player())
        self.world.add_component(player_entity, Blocking())
        self.world.add_component(player_entity, Visible())
        
        # Add components needed for status display
        self.world.add_component(player_entity, Health(100))
        self.world.add_component(player_entity, CharacterAttributes(10, 10, 10, 10, 10, 10))
        self.world.add_component(player_entity, Experience(1, 0))
        self.world.add_component(player_entity, EquipmentSlots())
        
        # Add player to current level
        self.current_level.add_entity(player_entity)
        
        # Set player in game state
        self.game_state.set_player_entity(player_entity)
        
        # Update camera to follow player and set level bounds
        self.camera.set_level_bounds(self.current_level.width, self.current_level.height)
        self.camera.follow_entity(center_x, center_y)
        
        # Calculate initial FOV (preview mode)
        self.fov_system.update()
        
        # Show current level info
        self._show_level_info()
        
        # Show controls
        self.message_log.add_info("Controls:")
        self.message_log.add_info("< > - Change level")
        self.message_log.add_info("G - Generate new seed")
        self.message_log.add_info("S - Save schedule")
        self.message_log.add_info("8/2 - Navigate parameters")
        self.message_log.add_info("Enter - Edit parameter")
        self.message_log.add_info("Q - Quit")
    
    def _generate_current_level(self) -> None:
        """Generate the current editing level."""
        # Apply temporary overrides to the scheduler before generation
        self._apply_temp_overrides_to_scheduler()
        
        # Generate level using the world generator with generation counter as turn_count
        # This ensures terrain variation when pressing 'G' to generate new layouts
        level = self.world_generator.generate_level(self.current_editing_level, None, self.generation_counter)
        
        # Set as current level in world generator and game state
        self.world_generator.set_current_level(level)
        self.game_state.reset()
        self.game_state.set_state(GameState.MAP_PREVIEW)
        self.game_state.add_level(level)
        self.game_state.change_level(self.current_editing_level)
        self.current_level = level
    
    def _show_level_info(self) -> None:
        """Show minimal information about the current level."""
        # Just show a simple message - all the important info is now in the sidebar
        pass
    
    def run(self) -> None:
        """Main preview loop."""
        try:
            # The render system handles terminal setup
            while True:
                # Render only when needed
                if self.game_state.should_render():
                    self.render_system.update()
                    self.game_state.render_complete()
                
                # Check for quit
                if self.game_state.is_game_over():
                    break
                
                # Get input (blocking - no timeout)
                key = self.render_system.term.inkey()
                if key:
                    # Handle input
                    action_taken = self._handle_preview_input(key)
                    
                    if action_taken:
                        # Request a render after changes
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
                print("Exited map schedule editor.")
    
    def _handle_preview_input(self, key) -> bool:
        """Handle input specific to preview mode."""
        key_str = str(key)
        key_name = key.name if hasattr(key, 'name') else key_str
        
        if key == 'q':
            self._quit_preview()
            return True
        elif key.lower() == 'g' and not self.editing_parameter:
            self._generate_new_seed()
            return True
        elif key.lower() == 's' and not self.editing_parameter:
            self._save_schedule()
            return True
        elif self.editing_parameter:
            # Handle parameter editing input
            return self._handle_parameter_edit_input(key)
        elif self.template_menu_active:
            # Handle biome menu input
            return self._handle_biome_menu_input(key)
        elif key_str == '8':  # Up arrow - navigate up through parameters
            self._navigate_parameter(-1)
            return True
        elif key_str == '2':  # Down arrow - navigate down through parameters
            self._navigate_parameter(1)
            return True
        elif key_name == 'KEY_ENTER':  # Enter - start editing selected parameter
            self._start_parameter_edit()
            return True
        elif key == '+' or key == '=':  # Plus - increment parameter
            self._increment_parameter(1)
            return True
        elif key == '-' or key == '_':  # Minus - decrement parameter
            self._increment_parameter(-1)
            return True
        elif key == 'KEY_ESCAPE' or key == '\x1b':  # Escape - cancel any editing
            if self.editing_parameter:
                self._cancel_parameter_edit()
                return True
            elif self.template_menu_active:
                self._cancel_biome_menu()
                return True
        
        return False
    
    def _change_level(self, direction: int) -> None:
        """Change the current editing level."""
        new_level = max(0, self.current_editing_level + direction)
        if new_level != self.current_editing_level:
            self.current_editing_level = new_level
            
            # Clear entities and regenerate
            self._clear_entities()
            self._generate_current_level()
            self._recreate_player()
            
            # Force FOV system to recalculate by clearing its cache
            self.fov_system.last_player_pos = None
            self.fov_system.previously_visible_tiles.clear()
            
            # Update FOV after regenerating the level
            self.fov_system.update()
            
            # Show new level info
            self.message_log.clear()
            self._show_level_info()
            
            # Invalidate render cache
            self.render_system.invalidate_cache()
    
    def _generate_new_seed(self) -> None:
        """Generate a new terrain layout by incrementing the generation counter."""
        # Increment generation counter to get terrain variation
        self.generation_counter += 1
        
        # Clear entities and regenerate with new generation counter
        self._clear_entities()
        self._generate_current_level()
        self._recreate_player()
        
        # Force FOV system to recalculate by clearing its cache
        self.fov_system.last_player_pos = None
        self.fov_system.previously_visible_tiles.clear()
        
        # Update FOV after regenerating the level
        self.fov_system.update()
        
        self.message_log.add_system(f"Generated layout #{self.generation_counter}")
        
        # Invalidate render cache
        self.render_system.invalidate_cache()
    
    def _clear_entities(self) -> None:
        """Clear all entities from the world."""
        entities_to_destroy = list(self.world.entities.get_alive_entities())
        for entity_id in entities_to_destroy:
            self.world.destroy_entity(entity_id)
    
    def _recreate_player(self) -> None:
        """Recreate the player entity for camera positioning."""
        player_entity = self.world.create_entity()
        
        # Position player at center of map
        center_x = self.current_level.width // 2
        center_y = self.current_level.height // 2
        
        # Get player glyph from configuration
        glyph_config = GlyphConfig(charset_override=self.charset_override)
        player_char, player_color = glyph_config.get_entity_glyph('player')
        
        # Add player components
        from components.combat import Health
        from components.character import CharacterAttributes, Experience
        from components.items import EquipmentSlots
        
        self.world.add_component(player_entity, Position(center_x, center_y))
        self.world.add_component(player_entity, Renderable(player_char, player_color))
        self.world.add_component(player_entity, Player())
        self.world.add_component(player_entity, Blocking())
        self.world.add_component(player_entity, Visible())
        self.world.add_component(player_entity, Health(100))
        self.world.add_component(player_entity, CharacterAttributes(10, 10, 10, 10, 10, 10))
        self.world.add_component(player_entity, Experience(1, 0))
        self.world.add_component(player_entity, EquipmentSlots())
        
        # Add player to current level
        self.current_level.add_entity(player_entity)
        
        # Set player in game state
        self.game_state.set_player_entity(player_entity)
        
        # Update camera
        self.camera.set_level_bounds(self.current_level.width, self.current_level.height)
        self.camera.follow_entity(center_x, center_y)
        
        # Update FOV
        self.fov_system.update()
    
    def _navigate_parameter(self, direction: int) -> None:
        """Navigate through parameters (direction: -1 for up, 1 for down)."""
        if not self.editing_parameter:
            self.selected_parameter = (self.selected_parameter + direction) % len(self.parameter_order)
    
    def _increment_parameter(self, direction: int) -> None:
        """Increment/decrement the selected parameter (direction: 1 for +, -1 for -)."""
        if self.editing_parameter or self.template_menu_active:
            return
        
        param_name = self.parameter_order[self.selected_parameter]
        
        # Skip template parameter (use Enter to select)
        if param_name == 'template':
            return
        
        current_value = self._get_current_parameter_value(param_name)
        param_def = self.parameter_definitions[param_name]
        
        # Calculate increment amount based on parameter type
        if param_def['type'] == int:
            increment = direction * 1  # Increment by 1 for integers
        elif param_def['type'] == float:
            increment = direction * 0.01  # Increment by 0.01 for floats
        else:
            return  # Skip string parameters
        
        # Calculate new value and clamp to bounds
        new_value = current_value + increment
        new_value = max(param_def['min'], min(param_def['max'], new_value))
        
        # Round float values to avoid floating point precision issues
        if param_def['type'] == float:
            new_value = round(new_value, 2)
        
        # Apply the change
        try:
            if param_name == 'level':
                # Change the current editing level
                old_level = self.current_editing_level
                self.current_editing_level = int(new_value)
                # Clear entities and regenerate the new level
                self._clear_entities()
                self._generate_current_level()
                self._recreate_player()
                
                # Update parameter order for the new level's template
                self._update_parameter_order()
                
                # Force FOV system to recalculate
                self.fov_system.last_player_pos = None
                self.fov_system.previously_visible_tiles.clear()
                self.fov_system.update()
                
                # Invalidate render cache
                self.render_system.invalidate_cache()
                self.message_log.add_info(f"Set level to {int(new_value)}")
            elif param_name == 'seed':
                # Change the world generator seed by recreating the level generator
                self._change_seed(int(new_value))
                self.message_log.add_info(f"Set seed to {int(new_value)}")
            elif param_name == 'generation':
                # Change generation counter and regenerate
                self.generation_counter = int(new_value)
                self._regenerate_with_new_parameters()
                self.message_log.add_info(f"Set generation to {int(new_value)}")
            else:
                # Update schedule parameter
                self._update_schedule_parameter(param_name, new_value)
                self._regenerate_with_new_parameters()
                self.message_log.add_info(f"Set {param_name} to {new_value}")
        except Exception as e:
            self.message_log.add_error(f"Error updating {param_name}: {e}")
    
    def _change_seed(self, new_seed: int) -> None:
        """Change the world generator seed by updating the level generator's seed."""
        # Update the level generator's seed directly
        self.world_generator.level_generator.seed = new_seed
        
        # Update the level generator's config seed
        self.world_generator.level_generator.config.seed = new_seed
        
        # Update the base generator's config seed
        self.world_generator.level_generator.base_generator.config.seed = new_seed
        
        # Update the world generator's internal seed
        self.world_generator._seed = new_seed
        
        # Regenerate the level with the new seed
        self._regenerate_with_new_parameters()
    
    def _regenerate_with_new_parameters(self) -> None:
        """Regenerate the level with new parameters."""
        # Clear entities and regenerate
        self._clear_entities()
        self._generate_current_level()
        self._recreate_player()
        
        # Force FOV system to recalculate
        self.fov_system.last_player_pos = None
        self.fov_system.previously_visible_tiles.clear()
        self.fov_system.update()
        
        # Invalidate render cache
        self.render_system.invalidate_cache()
    
    def _start_parameter_edit(self) -> None:
        """Start editing the selected parameter."""
        if not self.editing_parameter and not self.template_menu_active:
            param_name = self.parameter_order[self.selected_parameter]
            
            if param_name == 'template':
                # Show template selection menu
                self.template_menu_active = True
                self.template_menu.reset()
                self.message_log.clear()
                self.message_log.add_info("Select a template:")
            else:
                # Regular text editing for other parameters
                current_value = self._get_current_parameter_value(param_name)
                self.edit_buffer = str(current_value)
                self.editing_parameter = True
                self.message_log.add_info(f"Editing {param_name}: {current_value}")
    
    def _cancel_parameter_edit(self) -> None:
        """Cancel parameter editing."""
        if self.editing_parameter:
            self.editing_parameter = False
            self.edit_buffer = ""
            self.message_log.add_info("Edit cancelled")
    
    def _handle_biome_menu_input(self, key) -> bool:
        """Handle input while biome menu is active."""
        key_str = str(key)
        key_name = key.name if hasattr(key, 'name') else key_str
        
        if key_name == 'KEY_ENTER':
            # Select the current biome
            selected_template = self.template_menu.get_selected_template()
            if selected_template:
                self._apply_biome_selection(selected_template)
            return True
        elif key == 'KEY_ESCAPE' or key == '\x1b':
            # Cancel biome selection
            self._cancel_biome_menu()
            return True
        elif key_str == '8':  # Up arrow
            self.template_menu.navigate_up()
            return True
        elif key_str == '2':  # Down arrow
            self.template_menu.navigate_down()
            return True
        
        return False
    
    def _cancel_biome_menu(self) -> None:
        """Cancel biome menu selection."""
        self.template_menu_active = False
        self.message_log.clear()
        self._show_level_info()
        self.message_log.add_info("Biome selection cancelled")
    
    def _apply_biome_selection(self, template_name: str) -> None:
        """Apply the selected template temporarily for preview."""
        try:
            # Store temporary override (still using 'biome' in schedule for compatibility)
            self._set_temp_override('biome', template_name)
            
            # Update parameter order for the new template
            self._update_parameter_order()
            
            # Regenerate level with new template immediately
            self._clear_entities()
            self._generate_current_level()
            self._recreate_player()
            
            # Force FOV system to recalculate immediately
            self.fov_system.last_player_pos = None
            self.fov_system.previously_visible_tiles.clear()
            self.fov_system.update()
            
            self.render_system.invalidate_cache()
            
            # Exit template menu
            self.template_menu_active = False
            self.message_log.clear()
            self._show_level_info()
            self.message_log.add_info(f"Set template to {template_name} (preview)")
            
        except Exception as e:
            self.message_log.add_error(f"Error applying template: {e}")
            self._cancel_biome_menu()
    
    def _handle_parameter_edit_input(self, key) -> bool:
        """Handle input while editing a parameter."""
        key_str = str(key)
        key_name = key.name if hasattr(key, 'name') else key_str
        
        if key_name == 'KEY_ENTER':
            # Apply the parameter change
            self._apply_parameter_change()
            return True
        elif key == 'KEY_ESCAPE' or key == '\x1b':
            # Cancel editing
            self._cancel_parameter_edit()
            return True
        elif key_name == 'KEY_BACKSPACE' or key == '\x7f':
            # Remove last character
            if self.edit_buffer:
                self.edit_buffer = self.edit_buffer[:-1]
            return True
        elif len(key_str) == 1 and (key_str.isalnum() or key_str in '.-_'):
            # Add character to buffer
            self.edit_buffer += key_str
            return True
        
        return False
    
    def _apply_parameter_change(self) -> None:
        """Apply the parameter change and update the schedule."""
        param_name = self.parameter_order[self.selected_parameter]
        param_def = self.parameter_definitions[param_name]
        
        try:
            # Parse and validate the new value
            if param_def['type'] == int:
                new_value = int(self.edit_buffer)
                if new_value < param_def['min'] or new_value > param_def['max']:
                    raise ValueError(f"Value must be between {param_def['min']} and {param_def['max']}")
            elif param_def['type'] == float:
                new_value = float(self.edit_buffer)
                if new_value < param_def['min'] or new_value > param_def['max']:
                    raise ValueError(f"Value must be between {param_def['min']} and {param_def['max']}")
            elif param_def['type'] == str:
                new_value = self.edit_buffer.lower()
                if new_value not in param_def['options']:
                    raise ValueError(f"Value must be one of: {', '.join(param_def['options'])}")
            else:
                raise ValueError("Unknown parameter type")
            
            # Apply the parameter to schedule
            if param_name == 'level':
                # Change editing level
                self.current_editing_level = new_value
                self._change_level(0)  # Regenerate current level
            elif param_name == 'seed':
                # Change the world generator seed
                self._change_seed(new_value)
            elif param_name == 'generation':
                # Change generation counter and regenerate
                self.generation_counter = new_value
                self._regenerate_with_new_parameters()
            else:
                # Update schedule entry
                self._update_schedule_parameter(param_name, new_value)
                
                # Reload the scheduler to pick up the new schedule
                self.world_generator.scheduler.reload_schedule()
                
                # Regenerate level with new parameters
                self._clear_entities()
                self._generate_current_level()
                self._recreate_player()
                self.render_system.invalidate_cache()
            
            # Success message
            self.message_log.add_info(f"Set {param_name} to {new_value}")
            
        except ValueError as e:
            self.message_log.add_warning(f"Invalid value: {e}")
        
        # Exit edit mode
        self.editing_parameter = False
        self.edit_buffer = ""
    
    def _update_schedule_parameter(self, param_name: str, value) -> None:
        """Update a parameter in the schedule for the current level."""
        entry = self._get_schedule_entry_for_level(self.current_editing_level)
        
        # Find existing entry in schedule_data or create new one
        existing_entry = None
        for i, schedule_entry in enumerate(self.schedule_data):
            if (schedule_entry['from'] <= self.current_editing_level <= schedule_entry['to']):
                existing_entry = schedule_entry
                break
        
        if existing_entry:
            # Update existing entry
            if param_name == 'biome':
                existing_entry['biome'] = value
            else:
                if 'overrides' not in existing_entry:
                    existing_entry['overrides'] = {}
                existing_entry['overrides'][param_name] = value
        else:
            # Create new entry for this level
            new_entry = {
                'from': self.current_editing_level,
                'to': self.current_editing_level,
                'biome': 'default',
                'overrides': {}
            }
            
            if param_name == 'biome':
                new_entry['biome'] = value
            else:
                new_entry['overrides'][param_name] = value
            
            self.schedule_data.append(new_entry)
    
    def _get_current_parameter_value(self, param_name: str):
        """Get the current value of a parameter."""
        if param_name == 'seed':
            return self.world_generator.seed
        elif param_name == 'generation':
            return self.generation_counter
        elif param_name == 'level':
            return self.current_editing_level
        
        # Use effective entry that includes temporary overrides
        entry = self._get_effective_schedule_entry(self.current_editing_level)
        
        if param_name == 'biome':
            return entry.get('biome', 'default')
        elif param_name == 'template':
            return entry.get('biome', 'forest')  # Map biome to template for now
        
        # Check overrides first, then defaults
        overrides = entry.get('overrides', {})
        if param_name in overrides:
            return overrides[param_name]
        
        # Fallback defaults
        defaults = {
            'wall_probability': 0.45,
            'ca_iterations': 3,
            'tree_density': 0.3,
            'tree_count': 10,
            'enemy_density': 0.8,
            'maze_openings': 5
        }
        return defaults.get(param_name, 0)
    
    def _update_parameter_order(self) -> None:
        """Update parameter order based on current template."""
        # Start with basic parameters in the desired order
        self.parameter_order = ['level', 'seed', 'generation', 'template']
        
        # Get current template name
        current_template_name = self._get_current_parameter_value('template')
        
        # Get template and its parameters
        try:
            from game.worldgen.templates import get_template
            template = get_template(current_template_name)
            if template:
                template_params = template.get_parameters()
                # Add template-specific parameters to the order
                for param_name in template_params.keys():
                    if param_name not in self.parameter_order:
                        self.parameter_order.append(param_name)
        except:
            # Fallback to default parameters if template system fails
            pass
        
        # Ensure selected parameter is still valid
        if self.selected_parameter >= len(self.parameter_order):
            self.selected_parameter = 0
    
    def _quit_preview(self) -> None:
        """Quit the preview tool."""
        self.game_state.game_over("Player quit", 0)
    
    # Interface methods expected by systems
    def get_current_level(self):
        """Get the current level (interface compatibility)."""
        return self.current_level
    
    def set_current_level(self, level):
        """Set the current level (interface compatibility)."""
        self.current_level = level
    
    def get_biome_for_current_level(self):
        """Get biome for current level (interface compatibility)."""
        return self.world_generator.get_biome_for_current_level()
    
    def is_wall_at(self, x, y):
        """Check if there's a wall at the given coordinates (interface compatibility)."""
        return self.world_generator.is_wall_at(x, y)
    
    def get_tile_at(self, x, y):
        """Get the tile at the given coordinates (interface compatibility)."""
        return self.world_generator.get_tile_at(x, y)
    
    def get_blood_tiles(self):
        """Get blood tiles for the current level (interface compatibility)."""
        return self.world_generator.get_blood_tiles()
    
    def _set_temp_override(self, param_name: str, value) -> None:
        """Set a temporary override for preview purposes."""
        if self.current_editing_level not in self.temp_overrides:
            self.temp_overrides[self.current_editing_level] = {}
        
        if param_name == 'biome':
            self.temp_overrides[self.current_editing_level]['biome'] = value
        else:
            if 'overrides' not in self.temp_overrides[self.current_editing_level]:
                self.temp_overrides[self.current_editing_level]['overrides'] = {}
            self.temp_overrides[self.current_editing_level]['overrides'][param_name] = value
    
    def _get_effective_schedule_entry(self, level_id: int) -> dict:
        """Get the effective schedule entry including temporary overrides."""
        # Start with the base schedule entry
        entry = self._get_schedule_entry_for_level(level_id).copy()
        
        # Apply temporary overrides if they exist
        if level_id in self.temp_overrides:
            temp_entry = self.temp_overrides[level_id]
            
            # Override biome if specified
            if 'biome' in temp_entry:
                entry['biome'] = temp_entry['biome']
            
            # Override parameters if specified
            if 'overrides' in temp_entry:
                if 'overrides' not in entry:
                    entry['overrides'] = {}
                entry['overrides'].update(temp_entry['overrides'])
        
        return entry
    
    def _apply_temp_overrides_to_scheduler(self) -> None:
        """Temporarily modify the scheduler to use our overrides."""
        # Store original method
        if not hasattr(self, '_original_segment_at'):
            self._original_segment_at = self.world_generator.scheduler.segment_at
        
        # Create a custom segment_at method that uses our overrides
        def custom_segment_at(level_id):
            # Get the effective entry with temp overrides
            effective_entry = self._get_effective_schedule_entry(level_id)
            
            # Create a temporary segment with the effective values
            from game.worldgen.scheduler import Segment
            segment = Segment(
                x0=effective_entry['from'],
                x1=effective_entry['to'],
                biome=effective_entry['biome'],
                overrides={}
            )
            
            # Convert override values to curves
            if 'overrides' in effective_entry:
                for key, value in effective_entry['overrides'].items():
                    from game.worldgen.scheduler import ConstantCurve
                    segment.overrides[key] = ConstantCurve(value)
            
            return segment
        
        # Replace the method temporarily
        self.world_generator.scheduler.segment_at = custom_segment_at


def main():
    """Entry point for the map preview tool."""
    tool = MapPreviewTool()
    tool.run()


if __name__ == "__main__":
    main()
