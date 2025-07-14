"""Status display components for character info and game status."""

from typing import Tuple
from components.core import Position
from components.combat import Health
from components.character import CharacterAttributes, Experience
from components.items import EquipmentSlots, Item, Pickupable
from game.config import GameConfig


class StatusDisplay:
    """Handles display of character information and status lines."""
    
    def __init__(self, world, world_generator, game_state, text_formatter):
        self.world = world
        self.world_generator = world_generator
        self.game_state = game_state
        self.formatter = text_formatter
        self.CHAR_INFO_WIDTH = GameConfig.SIDEBAR_WIDTH
    
    def get_character_info_line(self, line_num: int) -> str:
        """Get a line of character information."""
        player_entity = self.game_state.get_player_entity()
        
        if not player_entity:
            return ""
        
        return self._get_stats_line(line_num, player_entity)
    
    def _get_stats_line(self, line_num: int, player_entity: int) -> str:
        """Get a line of character stats."""
        # Get player components
        health = self.world.get_component(player_entity, Health)
        experience = self.world.get_component(player_entity, Experience)
        attributes = self.world.get_component(player_entity, CharacterAttributes)
        
        if line_num == 0:
            # Level line
            if experience:
                return self.formatter.apply_color("LVL ", "bright_black") + self.formatter.apply_color(str(experience.level), "white")
            else:
                return self.formatter.apply_color("LVL ", "bright_black") + self.formatter.apply_color("1", "white")
        elif line_num == 1:
            # XP line
            if experience:
                current_in_level, needed_for_next = experience.get_xp_progress()
                return self.formatter.apply_color("XP ", "bright_black") + self.formatter.apply_color(f"{current_in_level}/{needed_for_next}", "white")
            else:
                return self.formatter.apply_color("XP ", "bright_black") + self.formatter.apply_color("0/100", "white")
        elif line_num == 2:
            # First attribute line: STR AGI CON - now with proper gray/white colors
            if attributes:
                str_text = self.formatter.apply_color("STR ", "bright_black") + self.formatter.apply_color(f"{attributes.strength:2d}", "white")
                agi_text = self.formatter.apply_color(" AGI ", "bright_black") + self.formatter.apply_color(f"{attributes.agility:2d}", "white")
                con_text = self.formatter.apply_color(" CON ", "bright_black") + self.formatter.apply_color(f"{attributes.constitution:2d}", "white")
                return str_text + agi_text + con_text
            else:
                str_text = self.formatter.apply_color("STR ", "bright_black") + self.formatter.apply_color("10", "white")
                agi_text = self.formatter.apply_color(" AGI ", "bright_black") + self.formatter.apply_color("10", "white")
                con_text = self.formatter.apply_color(" CON ", "bright_black") + self.formatter.apply_color("10", "white")
                return str_text + agi_text + con_text
        elif line_num == 3:
            # Second attribute line: INT WIL AUR - now with proper gray/white colors
            if attributes:
                int_text = self.formatter.apply_color("INT ", "bright_black") + self.formatter.apply_color(f"{attributes.intelligence:2d}", "white")
                wil_text = self.formatter.apply_color(" WIL ", "bright_black") + self.formatter.apply_color(f"{attributes.willpower:2d}", "white")
                aur_text = self.formatter.apply_color(" AUR ", "bright_black") + self.formatter.apply_color(f"{attributes.aura:2d}", "white")
                return int_text + wil_text + aur_text
            else:
                int_text = self.formatter.apply_color("INT ", "bright_black") + self.formatter.apply_color("10", "white")
                wil_text = self.formatter.apply_color(" WIL ", "bright_black") + self.formatter.apply_color("10", "white")
                aur_text = self.formatter.apply_color(" AUR ", "bright_black") + self.formatter.apply_color("10", "white")
                return int_text + wil_text + aur_text
        elif line_num == 4:
            # HP line
            if health:
                return self.formatter.apply_color("HP: ", "bright_black") + self.formatter.apply_color(f"{health.current_health}/{health.max_health}", "white")
            else:
                return self.formatter.apply_color("HP: ", "bright_black") + self.formatter.apply_color("--/--", "white")
        elif line_num == 5:
            # Status effects header and display
            from components.effects import StatusEffect
            status_effect = self.world.get_component(player_entity, StatusEffect)
            
            status_text = self.formatter.apply_color("Status: ", "bright_black")
            
            if status_effect and status_effect.effects:
                # Show status effects with colored indicators
                status_indicators = []
                if status_effect.has_effect("bleeding"):
                    # Red "B" for bleeding
                    status_indicators.append(self.formatter.apply_color("B", "red"))
                # Future status effects can be added here
                # if status_effect.has_effect("poison"):
                #     status_indicators.append(self.formatter.apply_color("P", "green"))
                
                if status_indicators:
                    status_text += "".join(status_indicators)
                else:
                    status_text += self.formatter.apply_color("None", "bright_black")
            else:
                status_text += self.formatter.apply_color("None", "bright_black")
            
            return status_text
        elif line_num == 6:
            # Weapon equipment line
            return self._get_equipment_line(player_entity, "weapon", "Weapon")
        elif line_num == 7:
            # Armor equipment line
            return self._get_equipment_line(player_entity, "armor", "Armor")
        elif line_num == 8:
            # Ring equipment line (accessory slot)
            return self._get_equipment_line(player_entity, "accessory", "Ring")
        elif line_num == 9:
            # Ground items display
            return self._get_ground_items_display(player_entity)
        else:
            # Empty lines
            return ""
    
    def _get_equipment_line(self, player_entity: int, slot: str, display_name: str) -> str:
        """Get an equipment line showing what's equipped in the specified slot."""
        equipment_slots = self.world.get_component(player_entity, EquipmentSlots)
        
        # Start with the slot name and colon in bright_black (gray)
        label_text = self.formatter.apply_color(f"{display_name}: ", "bright_black")
        
        if equipment_slots:
            # Get the equipped item entity ID
            equipped_item_id = None
            if slot == "weapon":
                equipped_item_id = equipment_slots.weapon
            elif slot == "armor":
                equipped_item_id = equipment_slots.armor
            elif slot == "accessory":
                equipped_item_id = equipment_slots.accessory
            
            if equipped_item_id:
                # Get the item's name
                item = self.world.get_component(equipped_item_id, Item)
                if item:
                    # Item name in white
                    item_text = self.formatter.apply_color(item.name, "white")
                else:
                    # Unknown in white
                    item_text = self.formatter.apply_color("unknown", "white")
            else:
                # "none" in bright_black (gray)
                item_text = self.formatter.apply_color("none", "bright_black")
        else:
            # "none" in bright_black (gray)
            item_text = self.formatter.apply_color("none", "bright_black")
        
        # Return the line without padding - let the render system handle it
        return label_text + item_text
    
    def _get_ground_items_display(self, player_entity: int) -> str:
        """Get the ground items display line showing item names for single items or glyphs for multiple items."""
        # Get player position
        position = self.world.get_component(player_entity, Position)
        if not position:
            # No position - show "Ground: empty" in bright_black (gray)
            return self.formatter.apply_color("Ground: ", "bright_black") + self.formatter.apply_color("empty", "bright_black")
        
        # Get all items at player's position
        items_at_pos = []
        entities = self.world.get_entities_with_components(Position, Pickupable)
        
        for entity_id in entities:
            entity_pos = self.world.get_component(entity_id, Position)
            if entity_pos and entity_pos.x == position.x and entity_pos.y == position.y:
                from components.core import Renderable
                renderable = self.world.get_component(entity_id, Renderable)
                item = self.world.get_component(entity_id, Item)
                if renderable and item:
                    items_at_pos.append((entity_id, renderable.char, renderable.color, item.name))
        
        # Build the display string
        if not items_at_pos:
            # No items - show "Ground: empty" in bright_black (gray)
            return self.formatter.apply_color("Ground: ", "bright_black") + self.formatter.apply_color("empty", "bright_black")
        
        # Start with "Ground: " in bright_black (gray)
        label_text = self.formatter.apply_color("Ground: ", "bright_black")
        
        if len(items_at_pos) == 1:
            # Single item: show the item name in white
            item_name = items_at_pos[0][3]  # Get the item name
            display_text = self.formatter.apply_color(item_name, "white")
        else:
            # Multiple items: show colored glyphs
            colored_glyphs = ""
            for _, char, color, _ in items_at_pos:
                colored_glyphs += self.formatter.apply_color(char, color)
            display_text = colored_glyphs
        
        # Return the line without padding - let the render system handle it
        return label_text + display_text
    
    def get_status_line(self) -> str:
        """Get the status line showing biome, chunk, position, and turn."""
        player_entity = self.game_state.get_player_entity()
        if not player_entity:
            return "Biome: unknown | Chunk: -- | X: -- | Turn: --"
        
        position = self.world.get_component(player_entity, Position)
        if not position:
            return "Biome: unknown | Chunk: -- | X: -- | Turn: --"
        
        # Get current biome from scheduler
        segment = self.world_generator._generator.scheduler.segment_at(position.x)
        biome_name = segment.biome
        
        # Calculate chunk
        chunk_id = position.x // 40
        
        # Build status line
        status = f"Biome: {biome_name} | Chunk: {chunk_id} | X: {position.x} | Turn: {self.game_state.turn_count}"
        
        # Pad or truncate to map width only
        map_width = GameConfig.MAP_WIDTH
        if len(status) > map_width:
            status = status[:map_width]
        else:
            status += ' ' * (map_width - len(status))
        
        return status
