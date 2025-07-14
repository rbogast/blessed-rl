# Details

Date : 2025-07-13 16:54:26

Directory /home/jesse/code/ecs-rl/ecs

Total : 68 files,  4291 codes, 1178 comments, 1468 blanks, all 6937 lines

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)

## Files
| filename | language | code | comment | blank | total |
| :--- | :--- | ---: | ---: | ---: | ---: |
| [README.md](/README.md) | Markdown | 75 | 0 | 25 | 100 |
| [components/\_\_init\_\_.py](/components/__init__.py) | Python | 10 | 3 | 3 | 16 |
| [components/ai.py](/components/ai.py) | Python | 15 | 5 | 7 | 27 |
| [components/character.py](/components/character.py) | Python | 51 | 13 | 26 | 90 |
| [components/combat.py](/components/combat.py) | Python | 26 | 11 | 14 | 51 |
| [components/core.py](/components/core.py) | Python | 23 | 10 | 21 | 54 |
| [components/effects.py](/components/effects.py) | Python | 61 | 20 | 27 | 108 |
| [components/items.py](/components/items.py) | Python | 75 | 16 | 30 | 121 |
| [data/enemies.json](/data/enemies.json) | JSON | 62 | 0 | 1 | 63 |
| [data/glyphs.json](/data/glyphs.json) | JSON | 28 | 0 | 1 | 29 |
| [data/items.yaml](/data/items.yaml) | YAML | 134 | 7 | 13 | 154 |
| [data/prefabs.yaml](/data/prefabs.yaml) | YAML | 38 | 13 | 4 | 55 |
| [data/schedule.yaml](/data/schedule.yaml) | YAML | 33 | 2 | 6 | 41 |
| [ecs/\_\_init\_\_.py](/ecs/__init__.py) | Python | 5 | 3 | 3 | 11 |
| [ecs/component.py](/ecs/component.py) | Python | 37 | 17 | 19 | 73 |
| [ecs/entity.py](/ecs/entity.py) | Python | 24 | 11 | 11 | 46 |
| [ecs/system.py](/ecs/system.py) | Python | 28 | 11 | 15 | 54 |
| [ecs/world.py](/ecs/world.py) | Python | 33 | 14 | 16 | 63 |
| [effects/\_\_init\_\_.py](/effects/__init__.py) | Python | 14 | 8 | 3 | 25 |
| [effects/core.py](/effects/core.py) | Python | 29 | 10 | 15 | 54 |
| [effects/implementations/\_\_init\_\_.py](/effects/implementations/__init__.py) | Python | 8 | 3 | 3 | 14 |
| [effects/implementations/blood\_splatter.py](/effects/implementations/blood_splatter.py) | Python | 14 | 24 | 7 | 45 |
| [effects/implementations/knockback.py](/effects/implementations/knockback.py) | Python | 3 | 4 | 3 | 10 |
| [effects/implementations/shockwave.py](/effects/implementations/shockwave.py) | Python | 3 | 4 | 3 | 10 |
| [effects/physics.py](/effects/physics.py) | Python | 140 | 41 | 50 | 231 |
| [effects/status\_effects.py](/effects/status_effects.py) | Python | 82 | 19 | 31 | 132 |
| [effects/tile\_effects.py](/effects/tile_effects.py) | Python | 73 | 18 | 26 | 117 |
| [game/\_\_init\_\_.py](/game/__init__.py) | Python | 4 | 3 | 3 | 10 |
| [game/camera.py](/game/camera.py) | Python | 33 | 12 | 14 | 59 |
| [game/character\_stats.py](/game/character_stats.py) | Python | 70 | 20 | 35 | 125 |
| [game/config.py](/game/config.py) | Python | 30 | 14 | 13 | 57 |
| [game/game\_state.py](/game/game_state.py) | Python | 56 | 19 | 21 | 96 |
| [game/glyph\_config.py](/game/glyph_config.py) | Python | 65 | 30 | 19 | 114 |
| [game/item\_factory.py](/game/item_factory.py) | Python | 81 | 20 | 25 | 126 |
| [game/message\_log.py](/game/message_log.py) | Python | 73 | 24 | 29 | 126 |
| [game/prefabs/\_\_init\_\_.py](/game/prefabs/__init__.py) | Python | 4 | 3 | 3 | 10 |
| [game/prefabs/loader.py](/game/prefabs/loader.py) | Python | 74 | 14 | 23 | 111 |
| [game/prefabs/manager.py](/game/prefabs/manager.py) | Python | 50 | 17 | 19 | 86 |
| [game/prefabs/spawner.py](/game/prefabs/spawner.py) | Python | 125 | 37 | 47 | 209 |
| [game/world\_gen.py](/game/world_gen.py) | Python | 29 | 16 | 16 | 61 |
| [game/worldgen/\_\_init\_\_.py](/game/worldgen/__init__.py) | Python | 4 | 9 | 3 | 16 |
| [game/worldgen/biomes.py](/game/worldgen/biomes.py) | Python | 173 | 45 | 76 | 294 |
| [game/worldgen/core.py](/game/worldgen/core.py) | Python | 210 | 49 | 61 | 320 |
| [game/worldgen/scheduler.py](/game/worldgen/scheduler.py) | Python | 168 | 30 | 49 | 247 |
| [main.py](/main.py) | Python | 354 | 104 | 109 | 567 |
| [rendering/\_\_init\_\_.py](/rendering/__init__.py) | Python | 0 | 1 | 1 | 2 |
| [rendering/entity\_renderer.py](/rendering/entity_renderer.py) | Python | 53 | 19 | 16 | 88 |
| [rendering/tile\_renderer.py](/rendering/tile_renderer.py) | Python | 35 | 15 | 11 | 61 |
| [requirements.txt](/requirements.txt) | pip requirements | 2 | 0 | 1 | 3 |
| [systems/\_\_init\_\_.py](/systems/__init__.py) | Python | 10 | 3 | 3 | 16 |
| [systems/ai.py](/systems/ai.py) | Python | 115 | 31 | 35 | 181 |
| [systems/combat.py](/systems/combat.py) | Python | 119 | 33 | 51 | 203 |
| [systems/combat\_helpers.py](/systems/combat_helpers.py) | Python | 127 | 28 | 47 | 202 |
| [systems/fov.py](/systems/fov.py) | Python | 125 | 34 | 35 | 194 |
| [systems/input.py](/systems/input.py) | Python | 146 | 34 | 34 | 214 |
| [systems/inventory.py](/systems/inventory.py) | Python | 156 | 37 | 61 | 254 |
| [systems/menu.py](/systems/menu.py) | Python | 109 | 30 | 37 | 176 |
| [systems/menus/\_\_init\_\_.py](/systems/menus/__init__.py) | Python | 0 | 1 | 1 | 2 |
| [systems/menus/drop\_menu.py](/systems/menus/drop_menu.py) | Python | 19 | 4 | 11 | 34 |
| [systems/menus/equip\_menu.py](/systems/menus/equip_menu.py) | Python | 29 | 5 | 12 | 46 |
| [systems/menus/inventory\_menu.py](/systems/menus/inventory_menu.py) | Python | 33 | 7 | 16 | 56 |
| [systems/menus/use\_menu.py](/systems/menus/use_menu.py) | Python | 22 | 4 | 11 | 37 |
| [systems/movement.py](/systems/movement.py) | Python | 114 | 29 | 46 | 189 |
| [systems/render.py](/systems/render.py) | Python | 136 | 46 | 38 | 220 |
| [ui/\_\_init\_\_.py](/ui/__init__.py) | Python | 0 | 1 | 1 | 2 |
| [ui/status\_display.py](/ui/status_display.py) | Python | 150 | 45 | 33 | 228 |
| [ui/text\_formatter.py](/ui/text_formatter.py) | Python | 58 | 18 | 18 | 94 |
| [world\_gen.log](/world_gen.log) | Log | 6 | 0 | 1 | 7 |

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)