# What Lies Beneath - Example Game Configuration

This directory contains a complete example of how a game would be configured in the Wretched & Alone Game Generator system. These files demonstrate the separation of concerns between content, mechanics, and presentation.

## Files in This Example

### `config.yaml` - Game Configuration
**What it does:** Defines the core mechanics and rules of your game
- Metadata (title, author, description)
- Which mechanics systems to use (dice, cards, tokens, stability)
- Starting values and thresholds
- Win/loss conditions
- UI layout preferences
- Special game-specific mechanics

**Key insight:** An author can completely change how the game plays by editing this file—without touching any code.

### `cards.yaml` - Card Definitions
**What it does:** Defines all 52 playing cards and their effects
- Card titles and descriptions (the narrative content)
- Mechanical effects (Evidence gained/lost, block pulls required)
- Special card behaviors (like Ace of Hearts requiring a roll)
- Organized by suit with thematic consistency

**Key insight:** This is where 90% of your creative writing happens. The generator handles turning this YAML into interactive card displays.

### `theme.yaml` - Visual Theme
**What it does:** Controls every aspect of how the game looks
- Color palette (backgrounds, text, accents, UI elements)
- Typography (fonts, sizes, weights)
- Layout (grid structure, spacing, borders)
- Component styling (dice, buttons, panels, cards)
- Background effects and overlays
- Animation settings
- Narrative tone for flavor text

**Key insight:** You can completely reskin the game without changing any content—just by editing colors and styles.

### `story.md` - Narrative Content
**What it does:** Contains all the non-interactive text content
- Character introduction and setup
- How to play instructions
- Game rules explanation
- Historical context and flavor text
- Tips and suggestions
- About section

**Key insight:** Written in simple Markdown, familiar to most content creators. No HTML knowledge required.

## How These Files Work Together

When you run the generator:

```bash
wretched build example-game
```

The system:

1. **Loads all configuration files**
   - Validates that everything is correctly formatted
   - Checks that all 52 cards are defined
   - Ensures mechanics are consistent

2. **Processes the theme**
   - Converts theme.yaml into CSS stylesheets
   - Generates color variables and component styles
   - Creates responsive layouts

3. **Compiles card data**
   - Transforms cards.yaml into JavaScript data structures
   - Handles special card behaviors
   - Organizes by suit and value

4. **Generates the game engine**
   - Creates JavaScript code for dice rolling, card drawing, stability mechanics
   - Implements win/loss conditions from config
   - Adds auto-save functionality

5. **Renders the template**
   - Combines story.md content with UI components
   - Applies theme styling
   - Injects game data and engine code

6. **Outputs a single HTML file**
   - Everything inlined (CSS, JavaScript, fonts)
   - No external dependencies
   - Self-contained and portable

The result: `the-cave.html` - a complete, playable game.

## Customization Examples

### Easy: Change the Theme Colors

In `theme.yaml`, modify the color palette:

```yaml
colors:
  primary: "#1a2332"        # Change to dark blue
  accent_primary: "#ff6b6b"  # Change gold to red
```

Result: The entire game UI updates to use your new colors.

### Medium: Adjust Mechanics

In `config.yaml`, make the game harder:

```yaml
mechanics:
  stability:
    initial: 75              # Start with less Credibility
  tokens:
    initial: 5               # Start with less Evidence
```

Result: A more challenging version of the same game.

### Advanced: Create New Card Content

In `cards.yaml`, replace cards with your own story:

```yaml
spades:
  A:
    title: "Your Discovery"
    description: "Your unique narrative here..."
    tokens: 2
    blocks: 1
```

Result: The same game system tells your story.

### Expert: Add Custom Mechanics

In `config.yaml`, define special rules:

```yaml
special:
  queen_tracker:
    enabled: true
    threshold: 3
    effect: "Drawing 3 Queens triggers a special ending"
```

Result: The generator creates code for your custom mechanic.

## File Structure Benefits

### For Authors

- **No coding required** - Edit YAML and Markdown files
- **Clear separation** - Content, mechanics, and style are independent
- **Easy iteration** - Change one aspect without affecting others
- **Reusable components** - Same theme with different content, or vice versa

### For Players

- **Single file download** - the-cave.html contains everything
- **No installation** - Open in any web browser
- **Works offline** - No internet connection needed
- **Auto-saves** - Progress stored in browser

### For the Community

- **Shareable themes** - "Use my cave theme for your game!"
- **Template libraries** - Start with a working config, customize it
- **Mix and match** - Arctic theme + cave cards = new game
- **Version control friendly** - YAML files work great with Git

## Validation

The generator validates your configs:

```bash
wretched validate example-game
```

This checks:
- All required config fields are present
- All 52 cards are defined
- Token/stability values make sense
- Color codes are valid
- Font families are available
- No contradictory settings

Example validation output:
```
✓ config.yaml: Valid
✓ cards.yaml: All 52 cards defined
✓ theme.yaml: Valid color palette
✓ story.md: Present
✓ Ready to build!
```

## Testing Your Game

```bash
wretched serve example-game
```

This starts a local server at `http://localhost:8000` where you can:
- Play the game
- See changes in real-time (hot reload)
- Test on different devices
- Check responsive layout

## Building for Distribution

```bash
wretched build example-game --minify
```

Creates: `dist/the-cave.html`

This file is:
- Fully self-contained
- Optimized for size
- Ready to upload to itch.io, your website, or share directly
- Can be opened directly from the file system

## Comparison: Before and After

### Before (Monolithic HTML)

The original `the-cave.html` file you examined has:
- 2,212 lines of mixed HTML, CSS, and JavaScript
- Hard to modify without breaking something
- All content, style, and logic intertwined
- Difficult to reuse or adapt
- Requires HTML/CSS/JS knowledge

### After (Modular Config System)

The new system has:
- 4 separate, focused files
- Easy to modify one aspect
- Content, style, and mechanics separated
- Easy to create variations
- No code knowledge required

## Creating Your Own Game

To create a new game based on this example:

1. **Copy this directory**
   ```bash
   cp -r example-game my-new-game
   cd my-new-game
   ```

2. **Edit config.yaml**
   - Change title, author, description
   - Adjust starting values
   - Modify mechanics if needed

3. **Write your cards in cards.yaml**
   - Replace card titles and descriptions
   - Adjust token/block values
   - Keep the same YAML structure

4. **Customize theme.yaml**
   - Choose your color palette
   - Select fonts
   - Adjust styling to match your theme

5. **Write your story in story.md**
   - Introduce your character
   - Explain your setting
   - Provide instructions

6. **Build and test**
   ```bash
   wretched build my-new-game
   wretched serve my-new-game
   ```

## Advanced: Template Inheritance

You can extend existing themes:

```yaml
# In theme.yaml
theme:
  name: "My Custom Theme"
  base: "cave_archaeology"    # Inherit from the cave theme
  
  # Only specify what you want to change
  colors:
    accent_primary: "#ff0000"  # Change gold to red
```

This inherits all the cave theme's styling but overrides the accent color.

## Tips for Success

1. **Start with a template** - Don't create from scratch
2. **Validate often** - Run `wretched validate` after changes
3. **Test as you go** - Use `wretched serve` during development
4. **Keep backups** - Version control is your friend
5. **Focus on content first** - Get cards written before perfecting the theme
6. **Iterate on mechanics** - Playtest and adjust difficulty
7. **Share early** - Get feedback from players

## What's Next?

With this example, you can:
- Create your own "Wretched & Alone" game
- Modify the Cave for your setting
- Mix and match components
- Share your creations with others

The power of the modular system is that you can focus on what matters—telling a great story—while the generator handles the technical details.

---

**Ready to create your own archaeological mystery, arctic expedition, haunted house, or space station crisis?**

Start with these files, make them your own, and build something amazing.
