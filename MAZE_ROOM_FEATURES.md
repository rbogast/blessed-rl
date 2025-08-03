# Maze Room Features

The maze generator now supports adding rooms to mazes. This feature allows for more interesting and varied maze layouts while maintaining the mathematical properties of the recursive backtracking algorithm.

## New Parameters

The maze template now includes three new parameters for room generation:

### `num_rooms`
- **Type**: Integer
- **Range**: 0 to 10
- **Default**: 0
- **Description**: Number of rooms to generate in the maze. Set to 0 to disable room generation (maintains backward compatibility).

### `min_room_size`
- **Type**: Integer  
- **Range**: 3 to 15
- **Default**: 5
- **Description**: Minimum size for room dimensions. Must be an odd number. The system will automatically adjust even numbers to the next odd number.

### `max_room_size`
- **Type**: Integer
- **Range**: 5 to 15  
- **Default**: 9
- **Description**: Maximum size for room dimensions. Must be an odd number. The system will automatically adjust even numbers to the next odd number.

## Room Constraints

Rooms in the maze follow strict mathematical constraints to ensure proper integration with the maze algorithm:

1. **Odd Dimensions Only**: Room width and height must be odd numbers (3, 5, 7, 9, etc.)
2. **Odd Position Coordinates**: Rooms can only start at odd coordinate positions (1, 3, 5, 7, etc.)
3. **Minimum Spacing**: Rooms maintain at least 2 tiles of spacing between each other to allow for maze corridors
4. **Border Respect**: Rooms respect the 1-tile border requirement around the entire maze

## How It Works

The room generation process follows this sequence:

1. **Room Layer**: Pre-places rooms as floor areas following all constraints
2. **Maze Layer**: Generates maze corridors around and between rooms using recursive backtracking
3. **Interconnection Layer**: Adds tactical openings while avoiding room areas
4. **Border Layer**: Ensures border integrity

## Integration with Maze Algorithm

Rooms integrate seamlessly with the maze generation:

- **Natural Connections**: The recursive backtracking algorithm naturally connects to room edges, creating doorway-like entrances
- **Preserved Properties**: The maze maintains its mathematical properties (exactly one path between any two points in the maze portion)
- **Room Accessibility**: All rooms are guaranteed to be accessible from the maze corridors

## Example Usage

```python
# Generate a maze with 3 rooms of varying sizes
parameters = {
    'num_rooms': 3,
    'min_room_size': 5,
    'max_room_size': 9,
    'maze_openings': 2
}
```

## Backward Compatibility

Setting `num_rooms` to 0 completely disables room generation, producing the same mazes as before this feature was added.
