"""
Game initialization and setup logic.
"""

import random
from components.core import Position, Renderable, Player, Blocking, Visible
from components.combat import Health, Stats
from components.character import CharacterAttributes, Experience
from components.effects import Physics
from components.items import Inventory, EquipmentSlots
from components.corpse import Species
from components.skills import Skills
from game.character_stats import calculate_max_hp


class GameInitializer:
    """Handles game world initialization and player setup."""
    
    def __init__(self, world, world_generator, game_state, message_log, glyph_config, item_factory):
        self.world = world
        self.world_generator = world_generator
        self.game_state = game_state
        self.message_log = message_log
        self.glyph_config = glyph_config
        self.item_factory = item_factory
    
    def initialize_game(self) -> None:
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
        
        # Create player
        self._create_player(player_entity, spawn_x, spawn_y)
        
        # Add player to current level
        level_0.add_entity(player_entity)
        
        # Set player in game state
        self.game_state.set_player_entity(player_entity)
        
        # Give player some starting items
        self._give_starting_items(player_entity)
        
        # Spawn some test items in the world
        self._spawn_test_items(spawn_x, spawn_y, level_0)
        
        self.message_log.add_system(f"Player spawned at X={spawn_x}, Y={spawn_y} on level 0")
        self.message_log.add_info("Use numpad keys to move (7,8,9,4,6,1,2,3)")
        self.message_log.add_info("Press 5 to wait, I for inventory, G to pickup")
        self.message_log.add_info("Press E to equip/unequip, U to use, D to drop")
        self.message_log.add_info("Step on '>' to descend to the next level!")
        
        return player_entity, spawn_x, spawn_y
    
    def _create_player(self, player_entity: int, spawn_x: int, spawn_y: int) -> None:
        """Create the player entity with all necessary components."""
        # Get player glyph from configuration
        player_char, player_color = self.glyph_config.get_entity_glyph('player')
        
        # Create player attributes (boosted for testing)
        player_attributes = CharacterAttributes(
            strength=20, agility=15, constitution=15, 
            intelligence=10, willpower=10, perception=8
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
        
        # Spawn potions and light sources for testing
        test_items = ['health_potion', 'greater_health_potion', 'torch', 'lantern']
        
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
