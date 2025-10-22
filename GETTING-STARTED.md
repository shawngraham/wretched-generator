# Getting Started with Wretched Generator

## Installation (30 seconds)

```bash
# 1. Make sure you have Python 3.9+ installed
python3 --version

# 2. Navigate to the generator directory
cd wretched-generator

# 3. Install dependencies
pip install -r requirements.txt
```

## Your First Build (1 minute)

```bash
# Build the included example game
python3 cli/wretched.py build example-game

# Or use the wrapper script
./wretched build example-game
```

You'll see:
```
Building game from: example-game
Loading configurations...
Validating...
Generating CSS...
Generating JavaScript...
Rendering template...
✓ Successfully built: example-game/what-lies-beneath.html
  File size: 49.6 KB
```

## Play the Game

Open `example-game/what-lies-beneath.html` in your web browser. You now have a fully functional solo journaling RPG!

## Create Your Own Game (5 minutes)

### Step 1: Copy the template
```bash
cp -r example-game my-first-game
cd my-first-game
```

### Step 2: Edit config.yaml
Change the basic info:
```yaml
game:
  title: "My First Game"
  author: "Your Name"
  description: "My awesome solo RPG"
```

### Step 3: Customize a few cards
Open `cards.yaml` and edit some cards:
```yaml
spades:
  A:
    title: "Your Opening Scene"
    description: |
      Write your own prompt here.
      What happens? How do you feel?
    tokens: 2
    blocks: 0
```

### Step 4: Build it!
```bash
cd ..
python3 cli/wretched.py build my-first-game
```

Open `my-first-game/my-first-game.html` and play!

## What You Can Customize

### Easy Changes (No learning curve)
- Game title and author
- Token and stability names
- Starting values
- Card prompts (your story!)
- Basic colors

### Medium Changes (Some YAML knowledge)
- Win/loss conditions
- Mechanical thresholds
- UI layout preferences
- Complete color schemes
- Font choices

### Advanced Changes (For power users)
- Custom CSS in theme.yaml
- Custom JavaScript mechanics
- Special card behaviors
- Complex conditions

## Commands Cheat Sheet

```bash
# Validate your game
./wretched validate my-game

# Show game info
./wretched info my-game

# Build game
./wretched build my-game

# Build with custom output path
./wretched build my-game -o dist/game.html

# Get help
./wretched --help
```

## Common First Steps

### Change the Theme Colors
Edit `theme.yaml`:
```yaml
colors:
  primary: "#1a1a2e"       # Your dark background
  accent_primary: "#e63946" # Your highlight color
  text_primary: "#f1faee"  # Your text color
```

### Write Your Own Cards
Edit `cards.yaml` - focus on making interesting prompts:
- Ask questions
- Create tension
- Develop character
- Tell a story

### Adjust Difficulty
Edit `config.yaml`:
```yaml
mechanics:
  tokens:
    initial: 5    # Fewer = harder
  stability:
    initial: 75   # Lower = harder
```

## Tips for Success

1. **Start Small** - Edit just a few cards first
2. **Validate Often** - Run validate after changes
3. **Study the Example** - What Lies Beneath shows all features
4. **Iterate Quickly** - Build, play, adjust, rebuild
5. **One Change at a Time** - Easier to debug

## File Structure Quick Reference

```
your-game/
├── config.yaml    ← Game mechanics (tokens, stability, etc.)
├── cards.yaml     ← Your 52 card prompts
├── theme.yaml     ← Colors, fonts, styling
└── story.md       ← Instructions and introduction
```

## Troubleshooting

**"Command not found"**
- Use `python3 cli/wretched.py` instead of `./wretched`

**"Module not found"**
- Run `pip install -r requirements.txt`

**"Validation failed"**
- Check that all 52 cards are defined
- Verify YAML indentation (2 spaces)

**"Game doesn't work in browser"**
- Check browser console for errors
- Validate your config files first
- Try with the example game to verify setup

