#!/usr/bin/env python3
"""
Utility script to fix door tiles that weren't properly converted to entities.
This addresses the issue where some door tiles remain as tiles instead of being converted to door entities.
"""

import json
import sys
import os

def fix_door_tiles_in_save(save_path):
    """Fix door tiles in a save file by converting them to entities."""
    
    # Load the save file
    with open(save_path, 'r') as f:
        save_data = json.load(f)
    
    print(f"Fixing door tiles in {save_path}")
    
    # Track changes
    doors_fixed = 0
    
    # Get the next available entity ID
    world_state = save_data['world_state']
    entity_ids = []
    
    # Collect all existing entity IDs
    for component_type, entities in world_state['components'].items():
        entity_ids.extend([int(eid) for eid in entities.keys()])
    
    next_entity_id = max(entity_ids) + 1 if entity_ids else 1
    
    # Process each level
    levels = save_data['levels']
    for level_id, level_data in levels.items():
        print(f"Checking level {level_id}...")
        
        tiles = level_data['tiles']
        level_entities = set(level_data['entities'])
        
        # Scan for door tiles that don't have corresponding entities
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if tile['tile_type'] in ['door_closed', 'door_open']:
                    # Check if there's already an entity at this position
                    entity_at_pos = None
                    
                    # Look through Position components to find entity at this position
                    positions = world_state['components'].get('Position', {})
                    for entity_id, pos_data in positions.items():
                        if (pos_data['x'] == x and pos_data['y'] == y and 
                            int(entity_id) in level_entities):
                            entity_at_pos = int(entity_id)
                            break
                    
                    if entity_at_pos is None:
                        # No entity at this position - create one
                        print(f"  Creating door entity {next_entity_id} at ({x}, {y}) for {tile['tile_type']}")
                        
                        # Determine door state
                        is_open = (tile['tile_type'] == 'door_open')
                        
                        # Add Position component
                        if 'Position' not in world_state['components']:
                            world_state['components']['Position'] = {}
                        world_state['components']['Position'][str(next_entity_id)] = {
                            'x': x,
                            'y': y
                        }
                        
                        # Add Door component
                        if 'Door' not in world_state['components']:
                            world_state['components']['Door'] = {}
                        world_state['components']['Door'][str(next_entity_id)] = {
                            'is_open': is_open
                        }
                        
                        # Add Renderable component
                        if 'Renderable' not in world_state['components']:
                            world_state['components']['Renderable'] = {}
                        door_char = '-' if is_open else '+'
                        world_state['components']['Renderable'][str(next_entity_id)] = {
                            'char': door_char,
                            'color': 'brown'
                        }
                        
                        # Add Visible component
                        if 'Visible' not in world_state['components']:
                            world_state['components']['Visible'] = {}
                        world_state['components']['Visible'][str(next_entity_id)] = {
                            'visible': False
                        }
                        
                        # Add Blocking component if door is closed
                        if not is_open:
                            if 'Blocking' not in world_state['components']:
                                world_state['components']['Blocking'] = {}
                            world_state['components']['Blocking'][str(next_entity_id)] = {}
                        
                        # Add entity to level
                        level_data['entities'].append(next_entity_id)
                        
                        # Convert tile to floor
                        tile['is_wall'] = False
                        tile['tile_type'] = 'floor'
                        if 'door' in tile.get('properties', {}):
                            del tile['properties']['door']
                        
                        doors_fixed += 1
                        next_entity_id += 1
    
    if doors_fixed > 0:
        # Save the fixed file
        backup_path = save_path + '.backup'
        print(f"Creating backup at {backup_path}")
        os.rename(save_path, backup_path)
        
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"Fixed {doors_fixed} door tiles and saved to {save_path}")
        print(f"Original save backed up to {backup_path}")
    else:
        print("No door tiles needed fixing")

def main():
    save_path = 'saves/current_game.json'
    
    if not os.path.exists(save_path):
        print(f"Save file not found: {save_path}")
        return 1
    
    try:
        fix_door_tiles_in_save(save_path)
        return 0
    except Exception as e:
        print(f"Error fixing door tiles: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
