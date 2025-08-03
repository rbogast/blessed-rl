#!/usr/bin/env python3
"""
Test script for cross-platform character set functionality.
Run this to test Unicode character display on your system.
"""

import os
import sys
from utils.platform_detection import PlatformDetector
from game.glyph_config import GlyphConfig


def test_character_sets():
    """Test all character sets and display results."""
    print("=== Blessed RL Character Set Test ===\n")
    
    # Initialize platform detector
    detector = PlatformDetector()
    platform_info = detector.get_platform_info()
    
    # Display platform information
    print("Platform Information:")
    print(f"  System: {platform_info['system']}")
    print(f"  Platform: {platform_info['platform']}")
    print(f"  Encoding: {platform_info['encoding']}")
    print(f"  Stdout encoding: {platform_info['stdout_encoding']}")
    print(f"  Locale encoding: {platform_info['locale_encoding']}")
    print(f"  Unicode support: {platform_info['supports_unicode']}")
    print(f"  CP437 support: {platform_info['supports_cp437']}")
    print(f"  Recommended charset: {platform_info['recommended_charset']}")
    print()
    
    # Display environment variables
    print("Environment Variables:")
    for key, value in platform_info['environment'].items():
        print(f"  {key}: {value}")
    print()
    
    # Test each character set
    character_sets = ['unicode', 'ascii', 'cp437']
    
    for charset in character_sets:
        print(f"=== Testing {charset.upper()} Character Set ===")
        
        try:
            # Initialize glyph config with specific character set
            glyph_config = GlyphConfig(character_set=charset)
            
            # Test terrain characters
            print("Terrain characters:")
            terrain_types = ['floor', 'wall', 'pine_tree', 'oak_tree']
            for terrain_type in terrain_types:
                char, color = glyph_config.get_terrain_glyph(terrain_type)
                print(f"  {terrain_type}: '{char}' ({color})")
            
            # Test entity characters
            print("Entity characters:")
            entity_types = ['player', 'stone_wall']
            for entity_type in entity_types:
                char, color = glyph_config.get_entity_glyph(entity_type)
                print(f"  {entity_type}: '{char}' ({color})")
            
            # Test character encoding
            print("Character encoding test:")
            test_chars = {
                'unicode': ['·', '▒', '↑', '♣'],
                'ascii': ['.', '#', '^', '&'],
                'cp437': ['·', '▒', '↑', '♣']
            }
            
            if charset in test_chars:
                chars = test_chars[charset]
                print(f"  Characters: {' '.join(chars)}")
                
                # Try to encode each character
                for i, char in enumerate(chars):
                    try:
                        encoded = char.encode(platform_info['encoding'])
                        print(f"    '{char}' -> {encoded} (OK)")
                    except UnicodeEncodeError as e:
                        print(f"    '{char}' -> ENCODING ERROR: {e}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        print()
    
    # Test manual override
    print("=== Testing Manual Override ===")
    print("Set BLESSED_RL_CHARSET environment variable to override:")
    print("  export BLESSED_RL_CHARSET=unicode")
    print("  export BLESSED_RL_CHARSET=ascii")
    print("  export BLESSED_RL_CHARSET=cp437")
    print()
    
    # Test debug mode
    print("=== Testing Debug Mode ===")
    print("Set BLESSED_RL_DEBUG=1 to enable debug output in the game:")
    print("  export BLESSED_RL_DEBUG=1")
    print()


def test_visual_display():
    """Test visual display of characters."""
    print("=== Visual Character Display Test ===\n")
    
    detector = PlatformDetector()
    recommended = detector.get_recommended_character_set()
    
    print(f"Recommended character set: {recommended}")
    print()
    
    # Create a simple map display
    glyph_config = GlyphConfig()
    
    print("Sample map display:")
    print("Legend:")
    floor_char, _ = glyph_config.get_terrain_glyph('floor')
    wall_char, _ = glyph_config.get_terrain_glyph('wall')
    tree_char, _ = glyph_config.get_terrain_glyph('pine_tree')
    player_char, _ = glyph_config.get_entity_glyph('player')
    
    print(f"  {floor_char} = floor")
    print(f"  {wall_char} = wall")
    print(f"  {tree_char} = tree")
    print(f"  {player_char} = player")
    print()
    
    # Create a small sample map
    map_lines = [
        f"{wall_char}{wall_char}{wall_char}{wall_char}{wall_char}{wall_char}{wall_char}",
        f"{wall_char}{floor_char}{floor_char}{tree_char}{floor_char}{floor_char}{wall_char}",
        f"{wall_char}{floor_char}{player_char}{floor_char}{floor_char}{tree_char}{wall_char}",
        f"{wall_char}{floor_char}{floor_char}{floor_char}{floor_char}{floor_char}{wall_char}",
        f"{wall_char}{wall_char}{wall_char}{wall_char}{wall_char}{wall_char}{wall_char}",
    ]
    
    print("Sample map:")
    for line in map_lines:
        print(f"  {line}")
    print()


if __name__ == "__main__":
    try:
        test_character_sets()
        test_visual_display()
        
        print("=== Test Complete ===")
        print("If characters display incorrectly, try:")
        print("1. Use a different terminal (Windows Terminal, iTerm2, etc.)")
        print("2. Set BLESSED_RL_CHARSET=ascii for maximum compatibility")
        print("3. Set BLESSED_RL_DEBUG=1 to see detailed platform info in game")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)
