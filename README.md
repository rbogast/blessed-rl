# Blessed Roguelike

A traditional terminal-based roguelike dungeon crawler built with Python and an Entity Component System (ECS) architecture. Descend through procedurally generated dungeon levels, fighting enemies and collecting treasure in classic roguelike style.

## Features

- **Entity Component System Architecture**: Scalable and modular game design
- **Multi-Level Dungeon Crawling**: Descend through connected dungeon levels via stairs
- **Procedural Level Generation**: Each level features unique layouts using cellular automata and maze algorithms
- **Turn-based Combat**: Classic roguelike combat with melee and ranged weapons
- **Field of View System**: Realistic line-of-sight and exploration mechanics
- **Comprehensive Inventory System**: Collect, manage, and equip weapons, armor, and consumables
- **Character Progression**: Skill development and experience system
- **Advanced Throwing Mechanics**: Physics-based projectile combat with trajectory visualization
- **AI Enemies**: Multiple enemy types with different behaviors and stats
- **Auto-Explore**: Automated exploration with intelligent pathfinding
- **Save System**: Continue your dungeon delve across sessions
- **Cross-Platform Terminal UI**: Clean interface using blessed library with automatic character set detection

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
```

**Note for Windows users**: If you see garbled characters, use the `-f` flag to force ASCII mode.

### Controls

- **Numpad Movement**: Use numpad keys for 8-directional movement
  ```
  7 8 9
  4   6
  1 2 3
  ```
- **Space**: Wait/skip turn
- **I**: Toggle inventory display
- **T**: Open throwing menu
- **D**: Drop item menu
- **U**: Use item menu
- **E**: Equip/unequip item menu
- **Period (.)**: Use stairs down
- **Comma (,)**: Use stairs up
- **Shift+Period (>)**: Travel to stairs down
- **Shift+Comma (<)**: Travel to stairs up
- **O**: Auto-explore current level
- **X**: Examine mode
- **Q**: Quit game

### Game Mechanics

- **Objective**: Descend as deep as possible through the dungeon levels
- **Levels**: Each dungeon level is a single screen (45x23 tiles) with unique layout
- **Stairs**: Use stairs to move between levels - downward stairs (>) lead deeper, upward stairs (<) lead back up
- **Combat**: Move into enemies to attack with equipped weapons
- **Inventory**: Collect and manage items found throughout the dungeon
- **Equipment**: Equip weapons and armor to improve combat effectiveness
- **Skills**: Character progression through skill development
- **Auto-Explore**: Press 'O' to automatically explore the current level
- **Field of View**: Areas become visible as you explore them
- **Death**: Game ends when you die (permadeath)

## Architecture

The game uses a clean Entity Component System architecture:

- **Entities**: Game objects (player, enemies, items, stairs)
- **Components**: Data containers (Position, Health, Renderable, AI, Inventory)
- **Systems**: Logic processors (Movement, Combat, Rendering, AI, FOV)

### Key Systems

- **LevelManager**: Handles level transitions and stair interactions
- **DungeonLevel**: Individual level management with entity persistence
- **WorldGenerator**: Procedural dungeon level generation with multiple algorithms
- **SimpleLightingSystem**: Field of view and lighting calculations
- **MovementSystem**: Entity movement and collision detection
- **CombatSystem**: Turn-based combat resolution
- **AISystem**: Enemy behavior and pathfinding
- **RenderSystem**: Terminal-based rendering with blessed
- **InventorySystem**: Item management and equipment
- **ThrowingSystem**: Ranged combat mechanics
- **AutoExploreSystem**: Automated exploration with pathfinding

## Level Generation

Dungeon levels are procedurally generated using various algorithms:

- **Cellular Automata**: Creates organic cave-like structures
- **Maze Generation**: Generates maze-like corridors and rooms
- **Template System**: Supports different biome types (caves, mazes, forests, graveyards)
- **Stair Placement**: Ensures proper connections between levels

## Development

The codebase is organized into clear modules:

- `ecs/`: Core ECS framework
- `components/`: Game component definitions
- `systems/`: Game system implementations and menu interfaces
- `game/`: Game-specific logic (level management, world generation, etc.)
- `effects/`: Effect system for temporary modifications
- `rendering/`: Entity and tile rendering systems
- `ui/`: User interface components
- `utils/`: Utility functions (pathfinding, line drawing, etc.)
- `data/`: Game data files (items, characters, configuration)

## Character Types

Enemy types and NPCs are defined in `data/characters.json` with unique stats, AI behaviors, and special abilities.

## Items & Equipment

The game features a comprehensive item system:

- **Weapons**: Melee and ranged weapons with different damage and accuracy
- **Armor**: Protective gear that reduces incoming damage
- **Consumables**: Potions, food, and other single-use items
- **Throwables**: Items that can be thrown as projectiles

Item definitions are stored in `data/items.yaml` with procedural generation support.
