# Dark Archaeology Theme

The **Dark Archaeology** theme provides a Victorian, eldritch theme like that used in "The Cave"


## How to Use

### Option 1: Swap Theme Files
The easiest way to use the Darck Archaeology theme:

```bash
cd example-game

# Use the arctic theme
cp theme-dark-archaeology.yaml theme.yaml

# Build the game
python3 ../cli/wretched.py build .
```

### Option 2: Create a New Game with Arctic Theme
```bash
# Create a new game project
python3 cli/wretched.py new my-dark-archaeology-game

cd my-dark-archaeology-game

# Replace the default theme with arctic
cp ../example-game/theme-dark-archaeology.yaml theme.yaml

# Edit your game content
# ... edit config.yaml, cards.yaml, story.md ...

# Build
python3 ../cli/wretched.py build .
```

### Option 3: Modify Existing Game
If you have an existing game and want to apply the Arctic theme:

```bash
# Copy the dark-archaeology theme to your game directory
cp example-game/theme-dark-archaeology.yaml my-game/theme.yaml

# Rebuild your game
python3 cli/wretched.py build my-game
```

## Customization

The theme is fully customizable through `theme-dark-archaeology.yaml`. Common customizations:

### Change the Colors
Edit the `colors.primary`, `colors.secondary`, and `colors.tertiary` values:
```yaml
colors:
  primary: "#8a9ba8"    # Change to darker/lighter blue
  secondary: "#5d6d7e"  # Adjust slate tone
  tertiary: "#c5d8e1"   # Modify ice blue tint
```

### Adjust Panel Background
Make panels warmer or cooler:
```yaml
components:
  panels:
    colors:
      background: "linear-gradient(135deg, #f5f5dc 0%, #e8dcc4 100%)"
```

### Change Border Colors
Switch to another color:
```yaml
colors:
  borders: "#5d6d7e"    # Try "#4a5a6e" for darker, "#8a9ba8" for lighter
```



## Troubleshooting

### Theme Not Applying
1. Make sure the file is named `theme.yaml` (not `theme-dark-archaeology.yaml`)
2. Check for YAML syntax errors: `python3 cli/wretched.py validate .`
3. Rebuild the game: `python3 cli/wretched.py build .`

### Colors Look Wrong
- Check your monitor color calibration
- Try adjusting the gradient stops in the theme file
- Verify you're using a modern browser (Chrome, Firefox, Safari latest)

## Credits

**Design Inspiration:**
- "The Cave" by Shawn Graham
- Victorian historical aesthetic
- Lovecraft narratives


## License

This theme configuration is provided as part of the Wretched & Alone Game Generator and can be freely used and modified for your own games.

