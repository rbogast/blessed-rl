# Cross-Platform Character Support

This document explains how the game handles Unicode characters across different operating systems and terminals.

## The Problem

The original game used Unicode characters like `·` (middle dot), `▒` (shaded block), `↑` (up arrow), and `♣` (club suit) for terrain and entities. While these display beautifully on Linux and macOS, they often appear as garbled text on Windows terminals (e.g., "â-'", "Â·", "â✝'").

## The Solution

The game now includes an automatic character set detection and fallback system that:

1. **Detects your platform and terminal capabilities**
2. **Automatically chooses the best character set**
3. **Provides ASCII fallbacks for maximum compatibility**
4. **Allows manual override for user preference**

## Character Sets

### Unicode (UTF-8)
- **Best visual experience** with special symbols
- **Recommended for**: Linux, macOS, Windows Terminal, modern terminals
- **Characters**: `·` (floor), `▒` (wall), `↑` (tree), `♣` (tree), `@` (player)

### ASCII Compatible
- **Maximum compatibility** across all systems
- **Recommended for**: Older Windows terminals, compatibility issues
- **Characters**: `.` (floor), `#` (wall), `^` (tree), `&` (tree), `@` (player)

### Code Page 437 (CP437)
- **Windows extended ASCII** with some special characters
- **Recommended for**: Traditional Windows cmd.exe, PowerShell
- **Characters**: `·` (floor), `▒` (wall), `↑` (tree), `♣` (tree), `@` (player)

## Automatic Detection

The game automatically detects:

- **Operating system** (Windows, Linux, macOS)
- **Terminal type** (Windows Terminal, cmd.exe, PowerShell, etc.)
- **Encoding support** (UTF-8, CP437, ASCII)
- **Unicode capabilities** of your terminal

Based on this detection, it chooses the most appropriate character set.

## Manual Override

You can manually override the character set using environment variables:

### Windows (Command Prompt)
```cmd
set BLESSED_RL_CHARSET=ascii
python main.py
```

### Windows (PowerShell)
```powershell
$env:BLESSED_RL_CHARSET="ascii"
python main.py
```

### Linux/macOS (Bash)
```bash
export BLESSED_RL_CHARSET=ascii
python main.py
```

### Available Options
- `unicode` - Full Unicode character set
- `ascii` - ASCII-compatible characters
- `cp437` - Code Page 437 (Windows extended ASCII)

## Testing Your System

Run the character set test to see what works on your system:

```bash
python test_charset.py
```

This will:
- Show your platform information
- Test all character sets
- Display a sample map
- Provide recommendations

## Debug Mode

Enable debug mode to see detailed platform information in the game:

```bash
export BLESSED_RL_DEBUG=1
python main.py
```

This will show:
- Detected platform and encoding
- Selected character set
- Unicode support status
- Test characters in the message log

## Troubleshooting

### Characters Still Look Wrong?

1. **Try a different terminal**:
   - Windows: Use Windows Terminal instead of cmd.exe
   - macOS: Use iTerm2 or Terminal.app
   - Linux: Use a modern terminal emulator

2. **Force ASCII mode**:
   ```bash
   export BLESSED_RL_CHARSET=ascii
   ```

3. **Check your terminal encoding**:
   - Ensure your terminal is set to UTF-8
   - On Windows, try `chcp 65001` to set UTF-8

4. **Update your terminal**:
   - Windows Terminal supports Unicode well
   - Older terminals may have limited support

### Windows-Specific Issues

- **cmd.exe**: Limited Unicode support, ASCII mode recommended
- **PowerShell**: Better Unicode support, CP437 or Unicode may work
- **Windows Terminal**: Excellent Unicode support, Unicode mode recommended
- **VSCode Terminal**: Usually supports Unicode well

### Font Issues

Some fonts don't include all Unicode characters. Try:
- **Windows**: Consolas, Cascadia Code, DejaVu Sans Mono
- **macOS**: SF Mono, Menlo, Monaco
- **Linux**: DejaVu Sans Mono, Liberation Mono, Source Code Pro

## Technical Details

### Platform Detection Logic

1. Check for `BLESSED_RL_CHARSET` environment variable override
2. Detect operating system (Windows, Linux, macOS)
3. Detect terminal type (Windows Terminal, cmd.exe, etc.)
4. Test Unicode encoding capabilities
5. Choose appropriate character set based on capabilities

### Fallback Hierarchy

When a character set is not available:
1. Try requested character set
2. Fall back to Unicode
3. Fall back to ASCII
4. Fall back to CP437
5. Use fallback character (`?`)

### File Structure

- `data/glyphs.yaml` - Character definitions for all sets
- `utils/platform_detection.py` - Platform detection logic
- `game/glyph_config.py` - Character set management
- `systems/render.py` - Encoding setup and rendering
- `test_charset.py` - Testing utility

## Contributing

When adding new characters:

1. Add all three character set variants to `data/glyphs.yaml`:
   ```yaml
   new_terrain:
     unicode: "★"
     ascii: "*"
     cp437: "★"
     visible_color: "yellow"
     explored_color: "blue"
   ```

2. Test on multiple platforms
3. Ensure ASCII fallback is readable
4. Update this documentation if needed

## Future Improvements

Potential enhancements:
- Terminal capability detection
- User preference storage
- Additional character sets (e.g., box drawing)
- Runtime character set switching
- Custom character mappings
