# Wretched & Alone Game Generator

A static site generator for solo journaling RPGs in the "Wretched & Alone" style.

**Not Complete. Just an experiment**

## What This Is

This tool transforms simple YAML and Markdown files into complete, playable HTML games. Think of it like Hugo for static websites, but for solo RPG games.

**You write:**
- Game rules in `config.yaml`
- Card prompts in `cards.yaml`
- Visual styling in `theme.yaml`
- Story/instructions in `story.md`

See [getting started doc.](GETTING-STARTED.md)


**You get:**
- A single self-contained HTML file
- Professional-looking game
- No coding required
- Works in any browser

## Quick Start

### Installation

1. Install Python 3.9 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Build a Game

```bash
python3 cli/wretched.py build example-game
```

This creates `what-lies-beneath.html` - a complete, playable game!

### Validate Configuration

```bash
python3 cli/wretched.py validate example-game
```

Checks that all config files are correct and complete.

### Show Game Info

```bash
python3 cli/wretched.py info example-game
```

Displays game metadata and mechanics summary.

## Directory Structure

```
wretched-generator/
├── cli/
│   └── wretched.py          # Command-line interface
├── lib/
│   └── builder.py           # Core builder module
├── templates/
│   └── base.html            # HTML template
├── example-game/            # Example game (The Cave)
│   ├── config.yaml
│   ├── cards.yaml
│   ├── theme.yaml
│   ├── story.md
│   └── the-cave.html        # Generated output
├── requirements.txt
└── README.md
```

## Commands

### new

Create a new game project from template.

```bash
python3 cli/wretched.py new <project-name>
```

**Arguments:**
- `project-name`: Name for your new game project

**Example:**
```bash
python3 cli/wretched.py new my-awesome-game
cd my-awesome-game
# Edit the config files...
python3 ../cli/wretched.py build .
```

### build

Build a game from configuration files.

```bash
python3 cli/wretched.py build <game-path> [-o output.html] [-m]
```

**Arguments:**
- `game-path`: Directory containing config files
- `-o, --output`: Optional output path (default: `<game-title>.html`)
- `-m, --minify`: Minify the output HTML (requires htmlmin package)

**Example:**
```bash
python3 cli/wretched.py build example-game
python3 cli/wretched.py build my-game -o dist/my-game.html
python3 cli/wretched.py build my-game --minify
```

### validate

Validate game configuration files.

```bash
python3 cli/wretched.py validate <game-path>
```

**Checks:**
- All required files present
- YAML syntax correct
- All 52 cards defined
- Required config fields present

**Example:**
```bash
python3 cli/wretched.py validate example-game
```

### info

Display game information.

```bash
python3 cli/wretched.py info <game-path>
```

**Shows:**
- Game title, author, version
- Description
- Mechanics used
- Card count

**Example:**
```bash
python3 cli/wretched.py info example-game
```

### Global Options

All commands support these global options:

```bash
--no-color    # Disable colored output
--debug       # Show detailed error messages and stack traces
```

**Example:**
```bash
python3 cli/wretched.py build my-game --no-color
python3 cli/wretched.py validate my-game --debug
```

## Creating Your Own Game

### Step 1: Create New Project

The easiest way to start is using the `new` command:

```bash
python3 cli/wretched.py new my-awesome-game
cd my-awesome-game
```

Or manually copy the example:

```bash
cp -r example-game my-awesome-game
cd my-awesome-game
```

### Step 2: Edit Config Files

**config.yaml** - Define your game mechanics:
```yaml
game:
  title: "My Awesome Game"
  author: "Your Name"
  
mechanics:
  tokens:
    initial: 10
    name: "Hope Points"
  stability:
    initial: 100
    name: "Mental State"
```

**cards.yaml** - Write your 52 card prompts:
```yaml
spades:
  A:
    title: "A New Discovery"
    description: "You find something unexpected..."
    tokens: 2
    blocks: 0
```

**theme.yaml** - Choose your colors and style:
```yaml
theme:
  colors:
    primary: "#1a1a2e"
    accent: "#16213e"
```

**story.md** - Write your introduction:
```markdown
# My Awesome Game

You are a brave explorer...
```

### Step 3: Build and Test

```bash
python3 cli/wretched.py validate my-awesome-game
python3 cli/wretched.py build my-awesome-game
```

Open the generated HTML file in your browser!

## Example Game Included

The `example-game/` directory contains a fully-configured version of "The Cave" - an archaeological mystery game. Study these files to understand the system:

- **config.yaml** (5.3 KB) - Game mechanics and rules
- **cards.yaml** (17 KB) - All 52 card prompts with narrative
- **theme.yaml** (12 KB) - Complete visual styling (dark archaeology theme)
- **story.md** (9 KB) - Game introduction and instructions

After building, you get:
- **the-cave.html** (50 KB) - Complete playable game

## Themes

The generator includes **two complete themes** you can use for your games:

### Dark Archaeology Theme (Default)
- **File:** `theme.yaml`
- **Aesthetic:** Cave exploration with warm browns, golds, and scholarly Victorian atmosphere
- **Best for:** Archaeological mysteries, historical exploration, academic pursuits
- **Colors:** Deep browns (#2c2416), gold accents (#d4af37), cream text (#e8dcc4)

### Arctic Theme
- **File:** `theme-arctic.yaml`
- **Aesthetic:** Icy blues, frost effects, and harsh Arctic isolation
- **Best for:** Polar exploration, survival scenarios, frozen wasteland settings
- **Colors:** Steel blues (#5d6d7e, #8a9ba8), ice blues (#c5d8e1), aged paper panels
- **Documentation:** See [ARCTIC-THEME.md](example-game/ARCTIC-THEME.md) for details

### Using a Theme

To use the Arctic theme (or switch between themes):

```bash
# Backup current theme
cp example-game/theme.yaml example-game/theme-backup.yaml

# Switch to Arctic theme
cp example-game/theme-arctic.yaml example-game/theme.yaml

# Build with new theme
python3 cli/wretched.py build example-game
```

### Creating Your Own Theme

Themes are defined in YAML and control:
- Color palettes (20+ customizable colors)
- Typography (fonts, sizes, spacing)
- Layout (grid, panels, breakpoints)
- Components (buttons, dice, cards, journal)
- Background effects (gradients, textures, overlays)
- Animations and transitions
- Narrative tone and messages

See `theme.yaml` or `theme-arctic.yaml` for complete examples.

## Features

### Current Features

**Core Functionality**
- Parse YAML configurations with full error handling
- Generate CSS from theme config
- Generate JavaScript game engine
- Render HTML template
- Single self-contained output
- Comprehensive validation system
- Full command-line interface with colored output

**Game Mechanics**
- Card deck mechanics
- Dice rolling
- Stability/tower system
- Token/resource system
- Auto-save to browser localStorage
- Journal with download
- Win/loss conditions

### Dependencies

- **Python 3.9+**
- **PyYAML** - YAML parsing
- **Jinja2** - Template rendering
- **markdown** - Markdown to HTML conversion

### Output Format

The generated HTML file contains:
- All CSS inlined in `<style>` tags
- All JavaScript inlined in `<script>` tags
- All game data as JSON
- Story content as HTML
- No external dependencies

This means:
- Single file distribution
- Works offline
- No server needed
- Email or upload anywhere

### Browser Compatibility

Generated games work in:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

Uses:
- Vanilla JavaScript (ES6+)
- CSS3 with variables
- LocalStorage API

## How It Works

1. **Load Configurations**
   - Parse YAML files (config, cards, theme)
   - Convert Markdown to HTML (story)

2. **Validate**
   - Check all 52 cards present
   - Verify required fields
   - Validate structure

3. **Generate CSS**
   - Convert theme YAML to CSS
   - Create CSS variables
   - Apply component styles

4. **Generate JavaScript**
   - Create game engine code
   - Embed card data as JSON
   - Add game logic (dice, cards, stability, tokens)
   - Implement save/load system

5. **Render Template**
   - Inject generated CSS
   - Inject generated JavaScript
   - Inject story HTML
   - Apply configuration

6. **Output**
   - Write single HTML file
   - Self-contained and ready to play

## Troubleshooting

### "File not found" error
Make sure you're running from the `wretched-generator` directory and the game path is correct.

### "Missing card" validation error
Each of the 52 cards (A-K-Q-J-10-9-8-7-6-5-4-3-2 in spades, hearts, diamonds, clubs) must be defined in `cards.yaml`.

### "Invalid YAML" error
Check your YAML syntax. Common issues:
- Inconsistent indentation (use 2 spaces)
- Missing colons
- Unquoted strings with special characters

### Generated game doesn't work
1. Validate first: `python3 cli/wretched.py validate <game>`
2. Check browser console for JavaScript errors
3. Make sure localStorage is enabled in browser

## Contributing

This is a minimal viable product (MVP). Contributions welcome!

## License

Open source - use however you want!

## Credits

- **System Design**: Based on "Wretched & Alone" by Chris Bissette
- **Example Game**: "The Cave" by Shawn Graham
- **Generator**: Created as proof of concept for modular game creation

## Resources

- [Wretched & Alone SRD](https://sealedlibrary.itch.io/wretched-alone-srd)
- [Example Game Documentation](example-game/README.md)
- [Strategy Document](../wretched-generator-strategy.md)

---

**Ready to create your own solo journaling RPG?**

```bash
cp -r example-game my-game
# Edit the config files
python3 cli/wretched.py build my-game
```

