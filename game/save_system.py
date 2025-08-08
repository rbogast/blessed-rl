"""
Save/Load system for traditional roguelike gameplay.
Auto-saves at the beginning of each turn, single save file per game.
"""

import json
import os
import random
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
from enum import Enum
from pathlib import Path


class SaveGameEncoder(json.JSONEncoder):
    """Custom JSON encoder for game objects."""
    
    def default(self, obj):
        if isinstance(obj, Enum):
            return {'__enum__': obj.__class__.__name__, 'value': obj.value}
        elif isinstance(obj, set):
            return {'__set__': list(obj)}
        elif isinstance(obj, tuple):
            return {'__tuple__': list(obj)}
        elif hasattr(obj, '__dict__'):
            # Handle component objects
            return {'__class__': obj.__class__.__name__, '__dict__': obj.__dict__}
        return super().default(obj)


def save_game_decoder(dct):
    """Custom JSON decoder for game objects."""
    if '__enum__' in dct:
        # Import enum classes as needed
        enum_name = dct['__enum__']
        if enum_name == 'GameState':
            from game.game_state import GameState
            return GameState(dct['value'])
        elif enum_name == 'AutoExploreState':
            from components.auto_explore import AutoExploreState
            return AutoExploreState(dct['value'])
        elif enum_name == 'ExploreTargetType':
            from components.auto_explore import ExploreTargetType
            return ExploreTargetType(dct['value'])
        elif enum_name == 'AIType':
            from components.ai import AIType
            return AIType(dct['value'])
        elif enum_name == 'DispositionType':
            from components.corpse import DispositionType
            return DispositionType(dct['value'])
        # Add other enums as needed
        return dct['value']  # Fallback
    elif '__set__' in dct:
        return set(dct['__set__'])
    elif '__tuple__' in dct:
        return tuple(dct['__tuple__'])
    return dct


class SaveSystem:
    """Manages saving and loading game state for traditional roguelike gameplay."""
    
    SAVE_DIR = "saves"
    SAVE_FILE = "current_game.json"
    
    def __init__(self):
        self.save_path = Path(self.SAVE_DIR)
        self.save_path.mkdir(exist_ok=True)
        self.save_file_path = self.save_path / self.SAVE_FILE
    
    def has_save_file(self) -> bool:
        """Check if a save file exists."""
        return self.save_file_path.exists()
    
    def delete_save_file(self) -> None:
        """Delete the save file (called on permadeath)."""
        if self.save_file_path.exists():
            self.save_file_path.unlink()
    
    def save_game(self, world, game_state, message_log, camera, world_generator) -> bool:
        """Save the current game state. Returns True if successful."""
        try:
            save_data = self._create_save_data(world, game_state, message_log, camera, world_generator)
            
            # Write to temporary file first, then rename (atomic operation)
            temp_file = self.save_file_path.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(save_data, f, cls=SaveGameEncoder, indent=2)
            
            # Atomic rename
            temp_file.rename(self.save_file_path)
            return True
            
        except Exception as e:
            print(f"Error saving game: {e}")
            # Clean up temp file if it exists
            temp_file = self.save_file_path.with_suffix('.tmp')
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    def load_game(self) -> Optional[Dict[str, Any]]:
        """Load the saved game state. Returns None if loading fails."""
        print(f"DEBUG: Checking for save file at: {self.save_file_path}")
        if not self.has_save_file():
            print("DEBUG: No save file found")
            return None
        
        print("DEBUG: Save file exists, attempting to load...")
        try:
            with open(self.save_file_path, 'r') as f:
                save_data = json.load(f, object_hook=save_game_decoder)
            print("DEBUG: Save data loaded successfully")
            return save_data
            
        except Exception as e:
            print(f"Error loading game: {e}")
            return None
    
    def _create_save_data(self, world, game_state, message_log, camera, world_generator) -> Dict[str, Any]:
        """Create the complete save data structure."""
        save_data = {
            'version': '1.0',
            'game_state': self._save_game_state(game_state),
            'world_state': self._save_world_state(world),
            'levels': self._save_levels(game_state),
            'message_log': self._save_message_log(message_log),
            'camera': self._save_camera(camera),
            'world_generator': self._save_world_generator(world_generator),
            'rng_state': random.getstate()
        }
        return save_data
    
    def _save_game_state(self, game_state) -> Dict[str, Any]:
        """Save GameStateManager data."""
        return {
            'current_state': game_state.current_state,
            'player_entity': game_state.player_entity,
            'turn_count': game_state.turn_count,
            'player_acted': game_state.player_acted,
            'game_over_reason': game_state.game_over_reason,
            'final_position': game_state.final_position,
            'needs_render': game_state.needs_render,
            'is_in_automated_action': game_state.is_in_automated_action,
            'current_level_id': game_state.get_current_level_id()
        }
    
    def _save_world_state(self, world) -> Dict[str, Any]:
        """Save ECS World state."""
        # Save entity manager state
        entity_state = {
            'next_id': world.entities._next_id,
            'alive_entities': list(world.entities._alive_entities),
            'dead_entities': list(world.entities._dead_entities)
        }
        
        # Save all components for all entities
        components_data = {}
        for component_type, entity_dict in world.components._components.items():
            component_name = component_type.__name__
            components_data[component_name] = {}
            
            for entity_id, component in entity_dict.items():
                components_data[component_name][str(entity_id)] = component.__dict__.copy()
        
        return {
            'entities': entity_state,
            'components': components_data
        }
    
    def _save_levels(self, game_state) -> Dict[str, Any]:
        """Save all dungeon levels."""
        levels_data = {}
        
        for level_id, level in game_state.dungeon_manager.levels.items():
            # Convert tiles to serializable format
            tiles_data = []
            for row in level.tiles:
                row_data = []
                for tile in row:
                    tile_data = {
                        'x': tile.x,
                        'y': tile.y,
                        'is_wall': tile.is_wall,
                        'tile_type': tile.tile_type,
                        'properties': tile.properties.copy(),
                        'visible': tile.visible,
                        'explored': tile.explored,
                        'interesting': tile.interesting
                    }
                    row_data.append(tile_data)
                tiles_data.append(row_data)
            
            level_data = {
                'level_id': level.level_id,
                'width': level.width,
                'height': level.height,
                'tiles': tiles_data,
                'entities': level.entities.copy(),
                'blood_tiles': list(level.blood_tiles),
                'stairs_down': level.stairs_down,
                'stairs_up': level.stairs_up
            }
            levels_data[str(level_id)] = level_data
        
        return levels_data
    
    def _save_message_log(self, message_log) -> Dict[str, Any]:
        """Save message log state."""
        # Convert deque to list for JSON serialization
        messages_list = []
        for message in message_log.messages:
            messages_list.append({
                'text': message.text,
                'color': message.color
            })
        
        return {
            'messages': messages_list,
            'width': message_log.width,
            'height': message_log.height
        }
    
    def _save_camera(self, camera) -> Dict[str, Any]:
        """Save camera state."""
        return {
            'x': camera.x,
            'y': camera.y,
            'viewport_width': camera.viewport_width,
            'viewport_height': camera.viewport_height,
            'level_width': camera.level_width,
            'level_height': camera.level_height
        }
    
    def _save_world_generator(self, world_generator) -> Dict[str, Any]:
        """Save world generator state."""
        return {
            'seed': world_generator.seed,
            'current_level_id': world_generator._current_level_id
        }
    
    def restore_game(self, save_data: Dict[str, Any], world, game_state, message_log, camera, world_generator) -> bool:
        """Restore game state from save data. Returns True if successful."""
        try:
            print("DEBUG: Starting game restoration...")
            
            # Restore RNG state first
            if 'rng_state' in save_data:
                try:
                    # Convert list back to tuple if needed
                    rng_state = save_data['rng_state']
                    if isinstance(rng_state, list):
                        rng_state = tuple(rng_state)
                    elif isinstance(rng_state, dict) and 'state' in rng_state:
                        # Handle the case where it's been serialized as a dict
                        state_data = rng_state['state']
                        if isinstance(state_data, list):
                            state_data = tuple(state_data)
                        rng_state = (rng_state['version'], state_data, rng_state.get('gauss_next'))
                    random.setstate(rng_state)
                    print("DEBUG: RNG state restored")
                except Exception as e:
                    print(f"Warning: Could not restore RNG state: {e}")
                    # Continue without restoring RNG state
            
            # Clear existing world state
            print("DEBUG: Clearing world...")
            self._clear_world(world)
            
            # Restore world state
            if 'world_state' in save_data:
                print("DEBUG: Restoring world state...")
                self._restore_world_state(save_data['world_state'], world)
            
            # Restore levels
            if 'levels' in save_data:
                print("DEBUG: Restoring levels...")
                self._restore_levels(save_data['levels'], game_state)
            
            # Restore game state
            if 'game_state' in save_data:
                print("DEBUG: Restoring game state...")
                self._restore_game_state(save_data['game_state'], game_state)
                print(f"DEBUG: Game state restored - turn: {game_state.turn_count}, player: {game_state.player_entity}")
            
            # Restore world generator AFTER levels and game state are restored
            if 'world_generator' in save_data:
                print("DEBUG: Restoring world generator...")
                self._restore_world_generator(save_data['world_generator'], world_generator)
            
            # Set the current level in the world generator
            current_level = game_state.get_current_level()
            if current_level:
                print("DEBUG: Setting current level in world generator...")
                world_generator.set_current_level(current_level)
                print(f"DEBUG: World generator current level set to: {current_level.level_id}")
            else:
                print("DEBUG: WARNING - No current level found to set in world generator")
            
            # Restore message log
            if 'message_log' in save_data:
                print("DEBUG: Restoring message log...")
                self._restore_message_log(save_data['message_log'], message_log)
            
            # Restore camera
            if 'camera' in save_data:
                print("DEBUG: Restoring camera...")
                self._restore_camera(save_data['camera'], camera)
            
            print("DEBUG: Game restoration completed successfully")
            return True
            
        except Exception as e:
            print(f"Error restoring game: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _clear_world(self, world) -> None:
        """Clear all entities and components from the world."""
        # Get all alive entities and destroy them
        entities_to_destroy = list(world.entities.get_alive_entities())
        for entity_id in entities_to_destroy:
            world.destroy_entity(entity_id)
        
        # Clear any remaining state
        world.entities._next_id = 0
        world.entities._alive_entities.clear()
        world.entities._dead_entities.clear()
        world.components._components.clear()
        world.components._entity_components.clear()
    
    def _restore_world_state(self, world_data: Dict[str, Any], world) -> None:
        """Restore ECS World state."""
        # Restore entity manager state
        entity_data = world_data['entities']
        world.entities._next_id = entity_data['next_id']
        world.entities._alive_entities = set(entity_data['alive_entities'])
        world.entities._dead_entities = set(entity_data['dead_entities'])
        
        # Import component classes
        component_classes = self._get_component_classes()
        
        # Restore components
        components_data = world_data['components']
        for component_name, entity_dict in components_data.items():
            if component_name in component_classes:
                component_class = component_classes[component_name]
                
                for entity_id_str, component_data in entity_dict.items():
                    entity_id = int(entity_id_str)
                    
                    # Create component instance and restore its data
                    component = component_class.__new__(component_class)
                    component.__dict__.update(component_data)
                    
                    # Add component to world
                    world.components.add_component(entity_id, component)
    
    def _restore_levels(self, levels_data: Dict[str, Any], game_state) -> None:
        """Restore all dungeon levels."""
        from game.dungeon_level import DungeonLevel
        from game.worldgen.core import Tile
        
        game_state.dungeon_manager.levels.clear()
        
        for level_id_str, level_data in levels_data.items():
            level_id = int(level_id_str)
            
            # Restore tiles
            tiles = []
            for row_data in level_data['tiles']:
                row = []
                for tile_data in row_data:
                    tile = Tile(
                        tile_data['x'],
                        tile_data['y'],
                        tile_data['is_wall']
                    )
                    tile.tile_type = tile_data['tile_type']
                    tile.properties = tile_data['properties']
                    # Restore FOV state
                    tile.visible = tile_data.get('visible', False)
                    tile.explored = tile_data.get('explored', False)
                    tile.interesting = tile_data.get('interesting', False)
                    row.append(tile)
                tiles.append(row)
            
            # Create level
            level = DungeonLevel(
                level_id=level_id,
                width=level_data['width'],
                height=level_data['height'],
                tiles=tiles,
                entities=level_data['entities'].copy(),
                blood_tiles=set(),  # Start with empty set, will be populated if needed
                stairs_down=tuple(level_data['stairs_down']) if level_data['stairs_down'] else None,
                stairs_up=tuple(level_data['stairs_up']) if level_data['stairs_up'] else None
            )
            
            # Handle blood_tiles separately to avoid unhashable type errors
            if level_data['blood_tiles']:
                for pos in level_data['blood_tiles']:
                    if isinstance(pos, list):
                        level.blood_tiles.add(tuple(pos))
                    else:
                        level.blood_tiles.add(pos)
            
            game_state.dungeon_manager.levels[level_id] = level
    
    def _restore_game_state(self, game_data: Dict[str, Any], game_state) -> None:
        """Restore GameStateManager state."""
        from game.game_state import GameState
        
        # Restore most state, but reset game over conditions
        game_state.current_state = GameState.PLAYING  # Always start in playing state
        game_state.player_entity = game_data['player_entity']
        game_state.turn_count = game_data['turn_count']
        game_state.player_acted = game_data['player_acted']
        # Don't restore game_over_reason - start fresh
        game_state.game_over_reason = None
        game_state.final_position = None  # Don't restore final position either
        game_state.needs_render = True  # Always need render after load
        # Restore automation state (with fallback for older saves)
        game_state.is_in_automated_action = game_data.get('is_in_automated_action', False)
        game_state.dungeon_manager.current_level_id = game_data['current_level_id']
        
        print(f"DEBUG: Restored game state - level: {game_data['current_level_id']}, turn: {game_data['turn_count']}")
    
    def _restore_message_log(self, log_data: Dict[str, Any], message_log) -> None:
        """Restore message log state."""
        from collections import deque
        from game.message_log import Message
        
        # Clear existing messages
        message_log.messages.clear()
        
        # Restore messages as Message objects in deque
        for msg_data in log_data['messages']:
            message = Message(msg_data['text'], msg_data['color'])
            message_log.messages.append(message)
        
        message_log.width = log_data['width']
        message_log.height = log_data['height']
        
        # Rewrap messages to update display
        message_log._rewrap_messages()
    
    def _restore_camera(self, camera_data: Dict[str, Any], camera) -> None:
        """Restore camera state."""
        camera.x = camera_data['x']
        camera.y = camera_data['y']
        camera.viewport_width = camera_data['viewport_width']
        camera.viewport_height = camera_data['viewport_height']
        camera.level_width = camera_data['level_width']
        camera.level_height = camera_data['level_height']
    
    def _restore_world_generator(self, gen_data: Dict[str, Any], world_generator) -> None:
        """Restore world generator state."""
        world_generator._seed = gen_data['seed']
        world_generator._current_level_id = gen_data['current_level_id']
        print(f"DEBUG: World generator restored - seed: {world_generator._seed}, level_id: {world_generator._current_level_id}")
    
    def _get_component_classes(self) -> Dict[str, type]:
        """Get mapping of component names to classes."""
        from components.core import Position, Renderable, Player, Blocking, Visible, Door, Prefab
        from components.combat import Health, Stats
        from components.character import CharacterAttributes, Experience, XPValue
        from components.effects import Physics, StatusEffect, TileModification, WeaponEffects
        from components.items import Inventory, EquipmentSlots, Item, Equipment, Consumable, Pickupable, Throwable, LightEmitter
        from components.corpse import Species, Corpse, Disposition
        from components.skills import Skills
        from components.ai import AI
        from components.throwing import ThrowingCursor, ThrownObject
        from components.auto_explore import AutoExplore
        from components.dead import Dead
        
        return {
            'Position': Position,
            'Renderable': Renderable,
            'Player': Player,
            'Blocking': Blocking,
            'Visible': Visible,
            'Door': Door,
            'Prefab': Prefab,
            'Health': Health,
            'Stats': Stats,
            'CharacterAttributes': CharacterAttributes,
            'Experience': Experience,
            'XPValue': XPValue,
            'Physics': Physics,
            'StatusEffect': StatusEffect,
            'TileModification': TileModification,
            'WeaponEffects': WeaponEffects,
            'Inventory': Inventory,
            'EquipmentSlots': EquipmentSlots,
            'Item': Item,
            'Equipment': Equipment,
            'Consumable': Consumable,
            'Pickupable': Pickupable,
            'Throwable': Throwable,
            'LightEmitter': LightEmitter,
            'Species': Species,
            'Corpse': Corpse,
            'Disposition': Disposition,
            'Skills': Skills,
            'AI': AI,
            'ThrowingCursor': ThrowingCursor,
            'ThrownObject': ThrownObject,
            'AutoExplore': AutoExplore,
            'Dead': Dead,
        }
