# Arctic Theme

The **Arctic** theme provides an icy, frost-covered aesthetic inspired by polar exploration games like "Whoever Finds This Paper" (the Franklin Expedition game).

## Visual Style

The Arctic theme features:
- **Icy blue gradients** - Cool blues, grays, and whites (#c5d8e1, #8a9ba8, #5d6d7e)
- **Frost overlay effects** - Radial gradients simulating ice crystals and frost
- **Aged paper panels** - Warm cream/beige (#f5f5dc, #e8dcc4) contrasting with the cold background
- **Steel blue borders** - #5d6d7e for a cold, metallic feel
- **Paper texture** - Subtle line grids on panels to simulate written documents

## Color Palette

### Background
- Primary: `#8a9ba8` (Steel blue-gray)
- Secondary: `#5d6d7e` (Darker slate)
- Tertiary: `#c5d8e1` (Light ice blue)

### Panels & Content
- Background: Linear gradient `#f5f5dc` to `#e8dcc4` (Aged paper)
- Borders: `#8b7355` (Brown) and `#5d6d7e` (Steel blue)
- Text: `#2c3e50` (Dark blue-gray)

### Interactive Elements
- Buttons: Steel blue gradients `#5d6d7e` to `#4a5a6e`
- Hover: Lighter blues `#6d7d8e` to `#5a6a7e`
- Active cards: Bright blue `#2980b9`

## Typography

Same fonts as the original theme:
- **Title font**: 'IM Fell English', serif (3em)
- **Body font**: 'Crimson Text', serif (1.1em)
- **UI font**: 'Libre Baskerville', serif

## Special Effects

### Frost Overlay
The arctic theme includes a unique frost/ice texture overlay created with CSS radial gradients:
```css
body::before {
  background-image:
    radial-gradient(circle at 20% 30%, rgba(255,255,255,0.3) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(200,220,240,0.2) 0%, transparent 40%),
    radial-gradient(circle at 40% 80%, rgba(255,255,255,0.15) 0%, transparent 30%);
}
```

### Paper Texture
Panels and headers get a subtle line grid texture:
```css
.panel::before {
  background:
    repeating-linear-gradient(90deg, transparent 0px, rgba(0,0,0,0.03) 1px, ...),
    repeating-linear-gradient(0deg, transparent 0px, rgba(0,0,0,0.03) 1px, ...);
}
```

## How to Use

### Option 1: Swap Theme Files
The easiest way to use the Arctic theme:

```bash
cd example-game

# Backup the original theme
mv theme.yaml theme-dark-archaeology.yaml

# Use the arctic theme
cp theme-arctic.yaml theme.yaml

# Build the game
python3 ../cli/wretched.py build .
```

### Option 2: Create a New Game with Arctic Theme
```bash
# Create a new game project
python3 cli/wretched.py new my-arctic-game

cd my-arctic-game

# Replace the default theme with arctic
cp ../example-game/theme-arctic.yaml theme.yaml

# Edit your game content
# ... edit config.yaml, cards.yaml, story.md ...

# Build
python3 ../cli/wretched.py build .
```

### Option 3: Modify Existing Game
If you have an existing game and want to apply the Arctic theme:

```bash
# Copy the arctic theme to your game directory
cp example-game/theme-arctic.yaml my-game/theme.yaml

# Rebuild your game
python3 cli/wretched.py build my-game
```

## Customization

The arctic theme is fully customizable through `theme-arctic.yaml`. Common customizations:

### Change the Ice Colors
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

### Modify Frost Effect Intensity
Adjust the frost overlay in `custom_css`:
```yaml
custom_css: |
  body::before {
    background-image:
      radial-gradient(circle at 20% 30%, rgba(255,255,255,0.5) 0%, transparent 40%),
      /* More intense: increase rgba alpha values */
  }
```

### Change Border Colors
Switch from steel blue to another color:
```yaml
colors:
  borders: "#5d6d7e"    # Try "#4a5a6e" for darker, "#8a9ba8" for lighter
```

## Narrative Tone

The Arctic theme includes gritty survival messages for the stability meter:

**Safe:**
- "The crew maintains discipline despite the cold."
- "Morale remains steady in the face of adversity."

**Danger:**
- "Fear begins to take hold among the men."
- "The cold gnaws at everyone's resolve."

**Critical:**
- "Madness lurks at the edges of consciousness."
- "Desperation drives men to dark thoughts."

## Compatibility

The Arctic theme works with:
- Standard Wretched & Alone mechanics
- Card deck system
- Dice rolling (1d6, 2d6)
- Stability/tower system
- Token/resource management
- All standard game endings

## Examples

### Games That Pair Well with Arctic Theme
- Polar exploration narratives
- Arctic survival scenarios
- Frozen wasteland settings
- Isolation and cold-themed stories
- Historical expeditions (Franklin, Shackleton, etc.)
- Sci-fi frozen planet missions

### Recommended Narrative Elements
- Cold weather events (blizzards, frostbite)
- Resource scarcity (food, fuel, warmth)
- Psychological isolation
- Environmental hazards
- Crew morale challenges
- Encounters with indigenous peoples or wildlife

## Technical Details

### File Structure
```
theme-arctic.yaml
├── theme
│   ├── colors (20+ color definitions)
│   ├── fonts (4 font families + Google Fonts)
│   ├── layout (grid, spacing, breakpoints)
│   ├── background (gradient + frost overlay)
│   ├── components (10+ component styles)
│   ├── modals (dialog styling)
│   ├── animations (timing and effects)
│   ├── accessibility (focus indicators, etc.)
│   └── narrative (tone and messages)
├── custom_css (frost effects, paper texture)
└── custom_js (future enhancements)
```

### CSS Variables Generated
The theme generates CSS variables for:
- All colors (`--color-primary`, etc.)
- Font families and sizes
- Spacing and layout dimensions
- Border radii and widths
- Shadow definitions
- Animation timings

## Troubleshooting

### Theme Not Applying
1. Make sure the file is named `theme.yaml` (not `theme-arctic.yaml`)
2. Check for YAML syntax errors: `python3 cli/wretched.py validate .`
3. Rebuild the game: `python3 cli/wretched.py build .`

### Colors Look Wrong
- Check your monitor color calibration
- Try adjusting the gradient stops in the theme file
- Verify you're using a modern browser (Chrome, Firefox, Safari latest)

### Frost Effect Not Visible
The frost overlay is subtle by design. To make it more prominent:
1. Edit `custom_css` in `theme-arctic.yaml`
2. Increase the rgba alpha values (e.g., 0.3 → 0.5)
3. Rebuild the game

## Credits

**Design Inspiration:**
- "Whoever Finds This Paper" by Shawn Graham
- Franklin Expedition historical aesthetic
- Arctic exploration narratives

**Theme Created:**
- By Claude (AI Assistant) for Wretched & Alone Generator
- Based on the Wretched & Alone SRD system by Chris Bissette

## License

This theme configuration is provided as part of the Wretched & Alone Game Generator and can be freely used and modified for your own games.

---

**Questions or feedback?** Open an issue on the project repository or modify the theme to suit your needs!
