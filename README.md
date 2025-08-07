# ECS Roguelike

A traditional terminal-based roguelike game built with Python and an Entity Component System (ECS) architecture. Journey eastward through procedurally generated caves, fighting enemies and exploring an infinite horizontal world.

## Features

- **Entity Component System Architecture**: Scalable and modular game design
- **Seamless Horizontal Scrolling**: Travel east through an infinite world
- **Cellular Automata Map Generation**: Procedurally generated cave systems
- **Recursive Shadowcasting FOV**: Realistic field of view and exploration
- **Turn-based Combat**: Classic roguelike combat mechanics with melee and ranged options
- **Comprehensive Inventory System**: Item collection, management, and equipment
- **Character Skills**: Progression system with skill development
- **Advanced Throwing Mechanics**: Physics-based projectile combat with trajectory visualization
- **AI Enemies**: Multiple enemy types with different behaviors
- **Rich Item System**: Weapons, armor, consumables, and throwable items
- **Interactive Menus**: Dedicated interfaces for inventory, throwing, and item management
- **Terminal-based UI**: Clean 80x24 terminal interface using blessed

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Play

Run the game:
```bash
python3 main.py
```

### Command-Line Options

The game supports several command-line options for customization:

```bash
# Run with default settings (auto-detected character set)
python3 main.py

# Force ASCII fallback character set (recommended for Windows)
python3 main.py -f
python3 main.py --fallback

# Specify exact character set
python3 main.py --charset unicode    # Full Unicode characters (Linux/macOS)
python3 main.py --charset ascii      # Basic ASCII characters (universal)
python3 main.py --charset cp437      # Extended ASCII (Windows terminals)

# Debug mode with character set information
python3 main.py -d
python3 main.py --debug

# List available character sets
python3 main.py --list-charsets

# Combine options (debug mode with ASCII charset)
python3 main.py -d -f
```

#### Character Sets

The game automatically detects the best character set for your system, but you can override this:

- **unicode**: Full Unicode characters with the best visual quality
  - Uses: `█▓▒░` for walls, `·` for floor, `♠♣♥♦` for suits
  - Default on Linux and macOS
  - May not display correctly on some Windows terminals

- **ascii**: Basic ASCII characters that work everywhere
  - Uses: `#` for walls, `.` for floor, basic letters/symbols
  - Guaranteed compatibility with all terminals and systems
  - Recommended fallback for display issues

- **cp437**: Extended ASCII (Code Page 437)
  - Uses: `██▓▒░` for walls, `·` for floor, extended symbols
  - Good compatibility with Windows Command Prompt and PowerShell

**Note for Windows users**: If you see garbled characters like `â-'` or `Â·`, use the `-f` flag to force ASCII mode:
```bash
python3 main.py -f
```

### Controls

- **Numpad Movement**: Use numpad keys for 8-directional movement
  ```
  7 8 9
  4   6
  1 2 3
  ```
- **Space**: Wait/skip turn
- **I**: Open inventory menu
- **T**: Open throwing menu
- **D**: Drop item
- **U**: Use item
- **E**: Equip/unequip item
- **Q**: Quit game

### Game Mechanics

- **Objective**: Journey eastward as far as possible
- **Combat**: Move into enemies to attack them with melee or ranged weapons
- **Inventory**: Collect, manage, and use items found throughout the world
- **Skills**: Character progression through skill development
- **Throwing**: Ranged combat using throwable weapons and items
- **Equipment**: Equip weapons and armor to improve combat effectiveness
- **Exploration**: Areas become visible as you explore them
- **Progress**: Your X position shows how far east you've traveled
- **Death**: Game ends when you die, showing your final position

## Architecture

The game uses a clean Entity Component System architecture:

- **Entities**: Game objects (player, enemies, walls)
- **Components**: Data containers (Position, Health, Renderable, AI)
- **Systems**: Logic processors (Movement, Combat, Rendering, AI)

### Key Systems

- **LevelGenerator**: Procedural dungeon level generation
- **FOVSystem**: Recursive shadowcasting for field of view
- **MovementSystem**: Handles entity movement and collision
- **CombatSystem**: Turn-based combat resolution
- **AISystem**: Enemy behavior and pathfinding
- **RenderSystem**: Terminal-based rendering with blessed
- **EffectSystem**: Applies effects to entities and tiles
- **InventorySystem**: Item collection, storage, and management
- **SkillSystem**: Character progression and skill development
- **ThrowingSystem**: Ranged combat mechanics and projectile physics

## Development

The codebase is organized into clear modules:

- `ecs/`: Core ECS framework
- `components/`: Game component definitions
- `systems/`: Game system implementations and menu interfaces
- `game/`: Game-specific logic (world generation, camera, item factory, etc.)
- `effects/`: Effect definitions and implementations
- `rendering/`: Entity and tile rendering systems
- `ui/`: User interface components and text formatting
- `utils/`: Utility functions (line drawing, etc.)
- `data/`: Game data files (items, enemies, schedules, prefabs)

## Character Types

Each character type (enemies, NPCs) has unique stats, species, disposition, and AI behavior patterns defined in `data/characters.json`.

## Effects

Effects are temporary modifications to entities or tiles, managed by the ECS. They can alter stats, apply status conditions, or trigger visual changes.

- **Core Effects**: Basic effect definitions and application logic in `effects/core.py`
- **Physics Effects**: Effects related to movement and spatial interactions in `effects/physics.py`
- **Status Effects**: Temporary conditions like poison or stun in `effects/status_effects.py`
- **Tile Effects**: Changes to map tiles, such as creating blood splatters in `effects/tile_effects.py`
- **Implementations**: Specific effect behaviors in `effects/implementations/`

## Inventory & Items

The game features a comprehensive item system with various types of equipment and consumables:

- **Item Factory**: Procedural item generation and configuration in `game/item_factory.py`
- **Item Data**: Item definitions and properties stored in `data/items.yaml`
- **Inventory Management**: Full inventory system with pickup, drop, use, and equip functionality
- **Equipment System**: Weapons, armor, and accessories that modify character stats
- **Menu System**: Dedicated menus for inventory, equipment, dropping, and using items

### Item Types

Items are categorized by type and rarity, with various effects and properties:
- **Weapons**: Melee and ranged weapons with different damage and accuracy stats
- **Armor**: Protective gear that reduces incoming damage
- **Consumables**: Potions, food, and other single-use items
- **Throwables**: Items that can be thrown as projectiles for ranged combat

## Skills System

Character progression through skill development:

- **Skill Components**: Character skills and progression tracking in `components/skills.py`
- **Skill System**: Skill advancement and effect application in `systems/skills.py`
- **Skill-based Combat**: Skills affect combat effectiveness, accuracy, and damage

## Throwing System

Advanced ranged combat mechanics:

- **Throwing Components**: Projectile properties and throwing mechanics in `components/throwing.py`
- **Throwing System**: Physics-based projectile movement and collision in `systems/throwing.py`
- **Throwing Menu**: Dedicated interface for selecting and aiming throwable items
- **Line Drawing**: Trajectory visualization and targeting assistance in `utils/line_drawing.py`

## World Generation

The world is procedurally generated using cellular automata and biome plugins. The `game/worldgen/` module contains the map generator, biome definitions, and scheduler functions.

- **Map Generator**: Generates the cave system using cellular automata in `game/worldgen/core.py`
- **Biome Plugins**: Define terrain features, enemy spawns, and item placement in `game/worldgen/biomes.py`
- **Scheduler**: Manages the order of world generation steps in `game/worldgen/scheduler.py`
