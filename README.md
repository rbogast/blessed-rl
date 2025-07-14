# ECS Roguelike

A traditional terminal-based roguelike game built with Python and an Entity Component System (ECS) architecture. Journey eastward through procedurally generated caves, fighting enemies and exploring an infinite horizontal world.

## Features

- **Entity Component System Architecture**: Scalable and modular game design
- **Seamless Horizontal Scrolling**: Travel east through an infinite world
- **Cellular Automata Map Generation**: Procedurally generated cave systems
- **Recursive Shadowcasting FOV**: Realistic field of view and exploration
- **Turn-based Combat**: Classic roguelike combat mechanics
- **AI Enemies**: Multiple enemy types with different behaviors
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

### Controls

- **Numpad Movement**: Use numpad keys for 8-directional movement
  ```
  7 8 9
  4   6
  1 2 3
  ```
- **Space**: Wait/skip turn
- **Q**: Quit game

### Game Mechanics

- **Objective**: Journey eastward as far as possible
- **Combat**: Move into enemies to attack them
- **Exploration**: Areas become visible as you explore them
- **Progress**: Your X position shows how far east you've traveled
- **Death**: Game ends when you die, showing your final position

### Screen Layout

```
┌─────────────────────────────────────────┬──────────────────────────────────────┐
│ Map Viewport (19x40)                    │ Message Log (19x40)                  │
│                                         │ > Game messages appear here          │
│ @...........                            │ > Combat results                     │
│ .###........                            │ > System notifications               │
│ .#.#........                            │                                      │
│ ............                            │                                      │
├─────────────────────────────────────────┴──────────────────────────────────────┤
│ Stats Panel (5x80)                                                            │
│ HP: 50/50    X: 25    STR: 10  DEF: 5  SPD: 100                              │
└────────────────────────────────────────────────────────────────────────────────┘
```

## Architecture

The game uses a clean Entity Component System architecture:

- **Entities**: Game objects (player, enemies, walls)
- **Components**: Data containers (Position, Health, Renderable, AI)
- **Systems**: Logic processors (Movement, Combat, Rendering, AI)

### Key Systems

- **WorldGenerator**: Procedural map generation using cellular automata
- **FOVSystem**: Recursive shadowcasting for field of view
- **MovementSystem**: Handles entity movement and collision
- **CombatSystem**: Turn-based combat resolution
- **AISystem**: Enemy behavior and pathfinding
- **RenderSystem**: Terminal-based rendering with blessed
- **EffectSystem**: Applies effects to entities and tiles

## Development

The codebase is organized into clear modules:

- `ecs/`: Core ECS framework
- `components/`: Game component definitions
- `systems/`: Game system implementations
- `game/`: Game-specific logic (world generation, camera, etc.)
- `effects/`: Effect definitions and implementations
- `data/`: Game data files (enemy definitions)

## Enemy Types

- **Goblin**: Aggressive, attacks on sight
- **Orc**: Patrols area, attacks when close
- **Skeleton**: Fast and aggressive
- **Troll**: Guards territory, high health

Each enemy has unique stats and AI behavior patterns defined in `data/enemies.json`.

## Effects

Effects are temporary modifications to entities or tiles, managed by the ECS. They can alter stats, apply status conditions, or trigger visual changes.

- **Core Effects**: Basic effect definitions and application logic in `effects/core.py`
- **Physics Effects**: Effects related to movement and spatial interactions in `effects/physics.py`
- **Status Effects**: Temporary conditions like poison or stun in `effects/status_effects.py`
- **Tile Effects**: Changes to map tiles, such as creating blood splatters in `effects/tile_effects.py`
- **Implementations**: Specific effect behaviors in `effects/implementations/`

## World Generation

The world is procedurally generated using cellular automata and biome plugins. The `game/worldgen/` module contains the map generator, biome definitions, and scheduler functions.

- **Map Generator**: Generates the cave system using cellular automata in `game/worldgen/core.py`
- **Biome Plugins**: Define terrain features, enemy spawns, and item placement in `game/worldgen/biomes.py`
- **Scheduler**: Manages the order of world generation steps in `game/worldgen/scheduler.py`
