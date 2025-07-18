# Details

Date : 2025-07-17 20:11:55

Directory /home/jesse/code/blessed-rl/blessed-rl

Total : 77 files,  5140 codes, 1410 comments, 1724 blanks, all 8274 lines

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)

## Files
| filename | language | code | comment | blank | total |
| :--- | :--- | ---: | ---: | ---: | ---: |
| [README.md](/README.md) | Markdown | 119 | 0 | 40 | 159 |
| [components/\_\_init\_\_.py](/components/__init__.py) | Python | 22 | 3 | 3 | 28 |
| [components/ai.py](/components/ai.py) | Python | 15 | 5 | 7 | 27 |
| [components/character.py](/components/character.py) | Python | 51 | 13 | 26 | 90 |
| [components/combat.py](/components/combat.py) | Python | 26 | 11 | 14 | 51 |
| [components/core.py](/components/core.py) | Python | 23 | 10 | 21 | 54 |
| [components/corpse.py](/components/corpse.py) | Python | 7 | 5 | 8 | 20 |
| [components/dead.py](/components/dead.py) | Python | 4 | 4 | 5 | 13 |
| [components/effects.py](/components/effects.py) | Python | 61 | 20 | 27 | 108 |
| [components/items.py](/components/items.py) | Python | 79 | 17 | 33 | 129 |
| [components/skills.py](/components/skills.py) | Python | 18 | 8 | 9 | 35 |
| [components/throwing.py](/components/throwing.py) | Python | 22 | 7 | 10 | 39 |
| [data/corpses.json](/data/corpses.json) | JSON | 10 | 0 | 1 | 11 |
| [data/enemies.json](/data/enemies.json) | JSON | 62 | 0 | 1 | 63 |
| [data/glyphs.json](/data/glyphs.json) | JSON | 28 | 0 | 1 | 29 |
| [data/items.yaml](/data/items.yaml) | YAML | 144 | 7 | 13 | 164 |
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
| [game/config.py](/game/config.py) | Python | 31 | 15 | 14 | 60 |
| [game/game\_state.py](/game/game_state.py) | Python | 56 | 19 | 21 | 96 |
| [game/glyph\_config.py](/game/glyph_config.py) | Python | 65 | 30 | 19 | 114 |
| [game/item\_factory.py](/game/item_factory.py) | Python | 96 | 22 | 27 | 145 |
| [game/message\_log.py](/game/message_log.py) | Python | 73 | 24 | 29 | 126 |
| [game/prefabs/\_\_init\_\_.py](/game/prefabs/__init__.py) | Python | 4 | 3 | 3 | 10 |
| [game/prefabs/loader.py](/game/prefabs/loader.py) | Python | 74 | 14 | 23 | 111 |
| [game/prefabs/manager.py](/game/prefabs/manager.py) | Python | 50 | 17 | 19 | 86 |
| [game/prefabs/spawner.py](/game/prefabs/spawner.py) | Python | 125 | 37 | 47 | 209 |
| [game/world\_gen.py](/game/world_gen.py) | Python | 29 | 16 | 16 | 61 |
| [game/worldgen/\_\_init\_\_.py](/game/worldgen/__init__.py) | Python | 4 | 9 | 3 | 16 |
| [game/worldgen/biomes.py](/game/worldgen/biomes.py) | Python | 173 | 45 | 76 | 294 |
| [game/worldgen/core.py](/game/worldgen/core.py) | Python | 213 | 50 | 62 | 325 |
| [game/worldgen/scheduler.py](/game/worldgen/scheduler.py) | Python | 169 | 30 | 49 | 248 |
| [main.py](/main.py) | Python | 392 | 111 | 115 | 618 |
| [rendering/\_\_init\_\_.py](/rendering/__init__.py) | Python | 0 | 1 | 1 | 2 |
| [rendering/entity\_renderer.py](/rendering/entity_renderer.py) | Python | 62 | 22 | 17 | 101 |
| [rendering/tile\_renderer.py](/rendering/tile_renderer.py) | Python | 89 | 37 | 24 | 150 |
| [requirements.txt](/requirements.txt) | pip requirements | 2 | 0 | 1 | 3 |
| [systems/\_\_init\_\_.py](/systems/__init__.py) | Python | 10 | 3 | 3 | 16 |
| [systems/ai.py](/systems/ai.py) | Python | 139 | 39 | 37 | 215 |
| [systems/combat.py](/systems/combat.py) | Python | 172 | 51 | 67 | 290 |
| [systems/combat\_helpers.py](/systems/combat_helpers.py) | Python | 174 | 37 | 58 | 269 |
| [systems/fov.py](/systems/fov.py) | Python | 134 | 35 | 36 | 205 |
| [systems/input.py](/systems/input.py) | Python | 207 | 45 | 41 | 293 |
| [systems/inventory.py](/systems/inventory.py) | Python | 189 | 46 | 66 | 301 |
| [systems/menu.py](/systems/menu.py) | Python | 111 | 30 | 37 | 178 |
| [systems/menus/\_\_init\_\_.py](/systems/menus/__init__.py) | Python | 0 | 1 | 1 | 2 |
| [systems/menus/drop\_menu.py](/systems/menus/drop_menu.py) | Python | 27 | 7 | 11 | 45 |
| [systems/menus/equip\_menu.py](/systems/menus/equip_menu.py) | Python | 29 | 5 | 12 | 46 |
| [systems/menus/inventory\_menu.py](/systems/menus/inventory_menu.py) | Python | 41 | 10 | 16 | 67 |
| [systems/menus/throwing\_menu.py](/systems/menus/throwing_menu.py) | Python | 52 | 9 | 19 | 80 |
| [systems/menus/use\_menu.py](/systems/menus/use_menu.py) | Python | 22 | 4 | 11 | 37 |
| [systems/movement.py](/systems/movement.py) | Python | 114 | 29 | 46 | 189 |
| [systems/render.py](/systems/render.py) | Python | 141 | 48 | 40 | 229 |
| [systems/skills.py](/systems/skills.py) | Python | 52 | 29 | 26 | 107 |
| [systems/throwing.py](/systems/throwing.py) | Python | 206 | 48 | 70 | 324 |
| [ui/\_\_init\_\_.py](/ui/__init__.py) | Python | 0 | 1 | 1 | 2 |
| [ui/status\_display.py](/ui/status_display.py) | Python | 156 | 47 | 34 | 237 |
| [ui/text\_formatter.py](/ui/text_formatter.py) | Python | 64 | 18 | 18 | 100 |
| [utils/\_\_init\_\_.py](/utils/__init__.py) | Python | 0 | 3 | 1 | 4 |
| [utils/line\_drawing.py](/utils/line_drawing.py) | Python | 31 | 16 | 21 | 68 |

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)