# Wretched & Alone Game Generator - Modular System Strategy

## Executive Summary

This document outlines a strategy for creating a Hugo-like static site generator for solo journaling RPGs following the "Wretched & Alone" system. The generator will allow authors to create fully-functional HTML games from configuration files without writing code.

## System Architecture

### Core Philosophy
- **Single Source of Truth**: All game content lives in easily-editable config files
- **Zero Code Required**: Authors work only with YAML/JSON configs and markdown
- **Single HTML Output**: Generate one self-contained HTML file per game
- **Template-Based**: Use a robust templating system (like Hugo's Go templates or Jinja2)

### Directory Structure

```
wretched-generator/
├── generator/              # The build tool
│   ├── templates/         # HTML/CSS/JS templates
│   │   ├── base.html     # Base game template
│   │   ├── themes/       # Theme templates
│   │   └── components/   # Reusable UI components
│   ├── builder.py        # Main build script
│   └── validators.py     # Config validation
├── themes/                # Pre-made themes
│   ├── cave/
│   ├── arctic/
│   ├── default/
│   └── minimal/
└── games/                 # Author's game projects
    └── my-game/
        ├── config.yaml   # Main game configuration
        ├── cards.yaml    # Card definitions
        ├── theme.yaml    # Visual customization
        ├── story.md      # Story/rules content
        └── assets/       # Images, fonts, etc.
```

## Configuration System

### 1. Main Game Config (`config.yaml`)

```yaml
# Game Metadata
game:
  title: "The Cave"
  subtitle: "An Archaeological Mystery"
  author: "Jane Smith"
  version: "1.0.0"
  description: "Excavate an ancient cave and uncover its secrets"

# Mechanics Configuration
mechanics:
  # Core systems to include
  systems:
    - dice        # 2d6 rolling
    - cards       # Standard 52-card deck
    - stability   # Jenga tower simulation
    - tokens      # Counter mechanic
  
  # Stability/Tower Settings
  stability:
    initial: 100
    name: "Mental State"           # Display name
    narrative_flavor: "academic"   # Affects flavor text
    thresholds:
      critical: 20
      danger: 50
    risk_scaling: true
    
  # Token Settings
  tokens:
    initial: 10
    name: "Evidence Fragments"
    count_up: false          # Direction of token change
    display_type: "numeric"  # numeric, hearts, custom_icon
    
  # Deck Settings
  deck:
    type: "standard_52"
    reshuffle: true
    track_history: true
    
  # Dice Settings
  dice:
    types:
      - name: "fate"
        count: 2
        sides: 6
      - name: "salvation"
        count: 1
        sides: 6
        
# Win/Loss Conditions
conditions:
  win:
    - type: "deck_empty_and_tokens_positive"
    - type: "custom"
      trigger: "four_kings_drawn"
  lose:
    - type: "stability_zero"
    - type: "tokens_zero"
    
# UI Configuration
ui:
  layout: "two_column"    # two_column, tabbed, single
  panels:
    left_width: "400px"
    show_instructions: true
    show_card_reference: true
  journal:
    placeholder: "Record your excavation notes..."
    autosave: true
    
# Special Mechanics (game-specific)
special:
  queen_tracker:
    enabled: true
    trigger_on: 4
    effect: "alternate_ending"
```

### 2. Card Definitions (`cards.yaml`)

```yaml
# Cards are organized by suit and value
# Each card has: title, description, tokens (±), blocks (pulls), special_effects

spades:
  A:
    title: "The First Chamber"
    description: "You discover a vast underground chamber. The walls shimmer with ancient paintings."
    tokens: 2
    blocks: 0
    special: null
    
  K:
    title: "Cave-In Warning"
    description: "The ceiling groans ominously. Should you continue?"
    tokens: 0
    blocks: 1
    special: null
    
  Q:
    title: "The Artefact"
    description: "You find a golden idol, but removing it might destabilize the cave."
    tokens: 3
    blocks: 2
    special: "queen_counter"
    
  # ... continue for all values
  
hearts:
  A:
    title: "Letter from the Society"
    description: "Your peers express doubt about your methods. Roll a die."
    tokens: 0
    blocks: 0
    special: "ace_of_hearts_roll"
    
  # ... etc

diamonds:
  # ... etc
  
clubs:
  # ... etc
  
# Special card groups
special_cards:
  queens:
    track_count: true
    threshold: 4
    threshold_effect: "trigger_alternate_ending"
    
  aces:
    hearts:
      requires_roll: true
      roll_success_on: [6]
      success_effect: "adjust_tokens"
```

### 3. Theme Configuration (`theme.yaml`)

```yaml
# Visual Theme Configuration
theme:
  name: "Cave Explorer"
  base: "dark_archaeology"  # Extends a base theme
  
  # Color Palette
  colors:
    primary: "#2c2416"
    secondary: "#1a1410"
    accent: "#d4af37"
    text_primary: "#e8dcc4"
    text_secondary: "#b8936f"
    borders: "#8b6f47"
    
    # Suit-specific colors
    suits:
      spades: "#4a4a4a"
      hearts: "#c41e3a"
      diamonds: "#0066cc"
      clubs: "#006400"
  
  # Typography
  fonts:
    title: "'IM Fell English', serif"
    body: "'Crimson Text', serif"
    ui: "'Crimson Text', serif"
    google_fonts:
      - "Crimson+Text:ital,wght@0,400;0,600;1,400"
      - "IM+Fell+English:ital@0;1"
  
  # Layout
  layout:
    container_max_width: "1600px"
    grid_columns: "400px 1fr"
    grid_gap: "30px"
    panel_border_radius: "12px"
    
  # Background Effects
  background:
    type: "gradient"
    gradient:
      angle: 135
      stops:
        - color: "#2c2416"
          position: 0
        - color: "#1a1410"
          position: 100
    overlay:
      type: "radial_pattern"
      pattern: "cave_texture"
      
  # Component Styling
  components:
    dice:
      size: "80px"
      colors:
        face: "#f5e6d3"
        border: "#8b6f47"
        text: "#2a1f14"
      animation: "roll"
      
    buttons:
      style: "gradient"
      hover_effect: "lift"
      
    panels:
      style: "bordered_gradient"
      shadow: "dramatic"
      
  # Card Display
  cards:
    display_style: "detailed"  # detailed, compact, minimal
    show_suit_symbols: true
    show_effects: true
    
  # Narrative Flavor
  narrative:
    tone: "scholarly"  # scholarly, gritty, whimsical, horror
    stability_messages:
      safe:
        - "Your mind remains steady and focused."
        - "The work proceeds methodically."
      danger:
        - "Doubt creeps into your thoughts."
        - "The pressure mounts."
      critical:
        - "Your composure cracks."
        - "Madness beckons."
```

### 4. Story Content (`story.md`)

```markdown
# Introduction

You are Dr. Elisabeth Blackwood, an archaeologist who has discovered a hidden cave system...

## Your Character

**Name:** Dr. Elisabeth Blackwood
**Occupation:** Independent Archaeologist
**Date:** June 15th, 1924

## How to Play

### Setup
- Begin with 10 Evidence Fragments
- Your Mental State starts at 100 (stable)
- You have a standard deck of 52 cards

### Each Turn
1. Roll 2d6 to determine how many cards to draw
2. Draw the indicated cards
3. Follow the prompts on each card
4. Write your response in your journal

### Winning
You win if you complete the excavation with evidence intact...

### Losing
You lose if your mental state collapses or you destroy all evidence...

## Card Suits

### ♠️ The Cave's Secrets
These cards represent discoveries within the cave...

### ♥️ Academic Relations
These cards deal with your peers and reputation...

### ♦️ Resources and Methodology
These cards affect your tools and approach...

### ♣️ Mental Strain
These cards test your psychological fortitude...
```

## Template System Architecture

### Base Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ game.title }}</title>
    <style>
        /* Inject compiled theme CSS */
        {{ theme.css | safe }}
    </style>
</head>
<body>
    <!-- Inject layout template based on config -->
    {% if ui.layout == "two_column" %}
        {% include "layouts/two-column.html" %}
    {% elif ui.layout == "tabbed" %}
        {% include "layouts/tabbed.html" %}
    {% endif %}
    
    <script>
        /* Inject game data */
        const GAME_CONFIG = {{ config | tojson }};
        const CARD_DATA = {{ cards | tojson }};
        
        /* Inject core game engine */
        {{ engine.js | safe }}
        
        /* Inject theme-specific customizations */
        {{ theme.js | safe }}
    </script>
</body>
</html>
```

### Component Templates

#### Two-Column Layout
```html
<div class="container">
    <div class="controls-panel">
        {% include "components/dice.html" %}
        {% include "components/card-draw.html" %}
        {% include "components/stability.html" %}
        {% include "components/tokens.html" %}
    </div>
    
    <div class="journal-panel">
        {% if story %}
            {% include "components/story-intro.html" %}
        {% endif %}
        {% include "components/journal.html" %}
        {% include "components/controls.html" %}
    </div>
</div>
```

## Build Process

### Generator Script Flow

```python
# builder.py pseudo-code

def build_game(game_path):
    """Main build function"""
    
    # 1. Load and validate configurations
    config = load_yaml(f"{game_path}/config.yaml")
    cards = load_yaml(f"{game_path}/cards.yaml")
    theme = load_yaml(f"{game_path}/theme.yaml")
    story = load_markdown(f"{game_path}/story.md")
    
    validate_config(config)
    validate_cards(cards)
    validate_theme(theme)
    
    # 2. Process theme
    css = compile_theme_to_css(theme)
    js_customizations = generate_theme_js(theme)
    
    # 3. Process cards
    card_data = compile_card_data(cards, config)
    
    # 4. Generate JavaScript game engine
    engine = generate_game_engine(config, cards)
    
    # 5. Render HTML template
    template = load_template(config.ui.layout)
    html = template.render(
        game=config.game,
        config=config,
        cards=card_data,
        story=story,
        theme={
            'css': css,
            'js': js_customizations
        },
        engine={'js': engine}
    )
    
    # 6. Inline assets (images, fonts)
    html = inline_assets(html, f"{game_path}/assets")
    
    # 7. Minify (optional)
    if config.build.minify:
        html = minify_html(html)
    
    # 8. Write output
    output_path = f"{game_path}/dist/{config.game.title.lower().replace(' ', '-')}.html"
    write_file(output_path, html)
    
    return output_path
```

### Validation System

```python
# validators.py

def validate_config(config):
    """Ensure config has required fields and valid values"""
    required = ['game', 'mechanics', 'conditions', 'ui']
    validate_required_keys(config, required)
    
    # Check mechanics
    if 'cards' in config.mechanics.systems:
        assert 'deck' in config.mechanics
    
    # Validate thresholds
    if config.mechanics.stability.thresholds:
        assert config.mechanics.stability.thresholds.critical < \
               config.mechanics.stability.thresholds.danger
    
    # etc.

def validate_cards(cards):
    """Ensure all 52 cards are defined"""
    suits = ['spades', 'hearts', 'diamonds', 'clubs']
    values = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
    
    for suit in suits:
        for value in values:
            assert value in cards[suit], f"Missing {value} of {suit}"
            validate_card_structure(cards[suit][value])
```

## Preset Themes

### Default Theme Library

```yaml
# themes/default/theme.yaml
theme:
  name: "Classic Wretched"
  colors:
    primary: "#1a1a1a"
    accent: "#e74c3c"
  # ... minimal styling
  
# themes/cave/theme.yaml (used by The Cave example)
# themes/arctic/theme.yaml (used by Whoever Finds This Paper)
# themes/horror/theme.yaml
# themes/cyberpunk/theme.yaml
# themes/fantasy/theme.yaml
```

## Advanced Features

### 1. Custom Mechanics System

Allow authors to define custom mechanics via JavaScript snippets:

```yaml
# In config.yaml
custom_mechanics:
  - name: "queen_tracker"
    trigger: "on_card_draw"
    code: |
      if (card.value === 'Q') {
        queensDrawn.push(card);
        if (queensDrawn.length === 4) {
          triggerAlternateEnding();
        }
      }
```

### 2. Conditional Card Effects

```yaml
# In cards.yaml
spades:
  K:
    title: "The Collapse"
    description: "Part of the cave collapses"
    effects:
      - condition: "tokens < 5"
        tokens: -2
        blocks: 2
      - condition: "tokens >= 5"
        tokens: -1
        blocks: 1
```

### 3. Multi-language Support

```yaml
# config.yaml
game:
  title: "The Cave"
  languages:
    - en
    - es
    - fr
    
# cards.en.yaml, cards.es.yaml, etc.
```

### 4. Accessibility Options

```yaml
# theme.yaml
accessibility:
  high_contrast_mode: true
  screen_reader_labels: true
  keyboard_navigation: true
  font_size_control: true
  dyslexia_friendly_font: optional
```

## CLI Tool

### Command-Line Interface

```bash
# Install
pip install wretched-generator

# Create new game project
wretched new my-awesome-game --template cave

# Build game
wretched build games/my-awesome-game

# Serve for testing
wretched serve games/my-awesome-game

# Validate configuration
wretched validate games/my-awesome-game

# List available themes
wretched themes list

# Install community theme
wretched themes install dark-forest
```

## Example Workflow

### Author's Journey

1. **Initialize Project**
```bash
wretched new "The Sunken Temple" --template fantasy
cd the-sunken-temple
```

2. **Edit Config** (`config.yaml`)
   - Set game title, author, description
   - Choose mechanics (cards, dice, stability, tokens)
   - Set initial values and thresholds

3. **Define Cards** (`cards.yaml`)
   - Write 52 card prompts (can use template as starting point)
   - Set token changes, block pulls, special effects

4. **Customize Theme** (`theme.yaml`)
   - Choose color palette
   - Select fonts
   - Adjust layout

5. **Write Story** (`story.md`)
   - Write introduction
   - Explain rules
   - Provide context

6. **Build & Test**
```bash
wretched serve
# Opens browser at localhost:8000
# Hot reload on save
```

7. **Publish**
```bash
wretched build --minify
# Output: dist/the-sunken-temple.html
# Upload to itch.io or personal website
```

## Technical Stack Recommendations

### Generator
- **Language**: Python 3.9+
- **Templating**: Jinja2
- **YAML Parsing**: PyYAML
- **Markdown**: python-markdown with extensions
- **CSS Generation**: SCSS compiler or CSS-in-Python
- **Minification**: htmlmin, csscompressor, jsmin
- **CLI**: Click or Typer

### Output HTML
- **Core JS**: Vanilla JavaScript (ES6+)
- **No External Dependencies**: Everything inlined
- **Storage**: localStorage API
- **Styling**: CSS3 with CSS variables for theming

## Distribution

### Package Distribution
- PyPI package for generator tool
- GitHub repository with examples
- Documentation site (generated with MkDocs)
- itch.io page with sample games

### Community Features
- Theme marketplace
- Card prompt library
- Template gallery
- Discord/forum for creators

## Migration Path

### For Existing Games

Provide conversion scripts:

```bash
# Convert existing HTML to config
wretched extract the-cave.html --output games/the-cave

# This would parse the HTML and generate:
# - config.yaml (detected mechanics)
# - cards.yaml (extracted from cardData)
# - theme.yaml (extracted from CSS)
# - story.md (extracted from HTML content)
```

## Future Enhancements

1. **Visual Config Editor**: Web-based GUI for non-technical creators
2. **Card Prompt Generator**: AI-assisted card writing
3. **Playtesting Mode**: Analytics and balance suggestions
4. **Print-Friendly Export**: PDF generation for physical play
5. **Mobile App**: Native iOS/Android wrapper
6. **Multiplayer Variant**: Optional synchronous/asynchronous multiplayer
7. **Asset Library**: Royalty-free images, fonts, sound effects
8. **Localization Tools**: Translation management system

## Summary

This modular system provides:

 **Separation of Concerns**: Content, mechanics, and presentation are independent
 **Ease of Use**: Authors work with familiar formats (YAML, Markdown)
 **Flexibility**: Supports multiple layouts, themes, and mechanics
 **Portability**: Generates single HTML file, no server required
 **Extensibility**: Custom mechanics and themes possible
 **Maintainability**: Templates can be updated without affecting games
 **Community**: Shareable themes and templates

The system empowers creators to focus on storytelling and game design while handling the technical complexity of building a polished, functional web application.
