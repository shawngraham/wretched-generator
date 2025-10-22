"""
Wretched & Alone Game Generator
Core builder module

This module provides the GameBuilder class which handles:
- Loading game configuration files (YAML and Markdown)
- Validating game data (cards, config, theme)
- Generating CSS from theme configuration
- Generating JavaScript game engine
- Rendering HTML templates
- Building self-contained HTML game files
"""

import yaml
import json
import markdown
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, List, Optional, Any, Tuple
import re


class ValidationError(Exception):
    """Raised when game configuration validation fails"""
    pass


class BuildError(Exception):
    """Raised when game building fails"""
    pass


class GameBuilder:
    """
    Main game builder class for Wretched & Alone style games.

    This class handles the complete build pipeline from loading configuration
    files to generating a single self-contained HTML game file.

    Attributes:
        game_path (Path): Path to the game directory containing config files
        config (dict): Loaded game configuration from config.yaml
        cards (dict): Loaded card definitions from cards.yaml
        theme (dict): Loaded theme configuration from theme.yaml
        story (str): Loaded and converted story content from story.md

    Example:
        >>> builder = GameBuilder('example-game')
        >>> builder.load_all()
        >>> output = builder.build()
    """

    def __init__(self, game_path: str):
        """
        Initialize the GameBuilder.

        Args:
            game_path: Path to the game directory (string or Path object)
        """
        self.game_path = Path(game_path)
        self.config: Optional[Dict[str, Any]] = None
        self.cards: Optional[Dict[str, Any]] = None
        self.theme: Optional[Dict[str, Any]] = None
        self.story: Optional[str] = None
        
    def load_config(self) -> Dict[str, Any]:
        """
        Load and parse config.yaml.

        Returns:
            dict: Parsed configuration data

        Raises:
            FileNotFoundError: If config.yaml doesn't exist
            yaml.YAMLError: If config.yaml has invalid syntax
        """
        config_file = self.game_path / "config.yaml"
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            return self.config
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Config file not found: {config_file}\n"
                f"Make sure config.yaml exists in {self.game_path}"
            )
        except yaml.YAMLError as e:
            raise BuildError(f"Invalid YAML in config.yaml: {e}")

    def load_cards(self) -> Dict[str, Any]:
        """
        Load and parse cards.yaml.

        Returns:
            dict: Parsed card definitions (suits -> values -> card data)

        Raises:
            FileNotFoundError: If cards.yaml doesn't exist
            yaml.YAMLError: If cards.yaml has invalid syntax
        """
        cards_file = self.game_path / "cards.yaml"
        try:
            with open(cards_file, 'r', encoding='utf-8') as f:
                self.cards = yaml.safe_load(f)
            return self.cards
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Cards file not found: {cards_file}\n"
                f"Make sure cards.yaml exists in {self.game_path}"
            )
        except yaml.YAMLError as e:
            raise BuildError(f"Invalid YAML in cards.yaml: {e}")

    def load_theme(self) -> Dict[str, Any]:
        """
        Load and parse theme.yaml.

        Returns:
            dict: Parsed theme configuration

        Raises:
            FileNotFoundError: If theme.yaml doesn't exist
            yaml.YAMLError: If theme.yaml has invalid syntax
        """
        theme_file = self.game_path / "theme.yaml"
        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                self.theme = yaml.safe_load(f)
            return self.theme
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Theme file not found: {theme_file}\n"
                f"Make sure theme.yaml exists in {self.game_path}"
            )
        except yaml.YAMLError as e:
            raise BuildError(f"Invalid YAML in theme.yaml: {e}")

    def load_story(self) -> str:
        """
        Load and parse story.md, converting markdown to HTML.

        Returns:
            str: HTML-formatted story content

        Raises:
            FileNotFoundError: If story.md doesn't exist
        """
        story_file = self.game_path / "story.md"
        try:
            with open(story_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
                # Convert markdown to HTML with extensions for tables, code blocks, etc.
                self.story = markdown.markdown(
                    md_content,
                    extensions=['extra', 'nl2br', 'sane_lists']
                )
            return self.story
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Story file not found: {story_file}\n"
                f"Make sure story.md exists in {self.game_path}"
            )

    def load_all(self) -> None:
        """
        Load all configuration files in one call.

        This is a convenience method that loads config, cards, theme, and story
        in the correct order.

        Raises:
            FileNotFoundError: If any required file is missing
            BuildError: If any file has invalid syntax
        """
        self.load_config()
        self.load_cards()
        self.load_theme()
        self.load_story()
    
    def validate(self) -> List[str]:
        """
        Validate all loaded configurations.

        Checks:
        - All config files are loaded
        - All 52 cards are defined
        - Required config fields are present
        - Card data has required fields

        Returns:
            list: List of error messages (empty if validation passes)
        """
        errors = []

        # Check that all configs are loaded
        if not self.config:
            errors.append("Config file not loaded - call load_config() first")
        if not self.cards:
            errors.append("Cards file not loaded - call load_cards() first")
        if not self.theme:
            errors.append("Theme file not loaded - call load_theme() first")

        # Validate cards (all 52 should be present)
        if self.cards:
            suits = ['spades', 'hearts', 'diamonds', 'clubs']
            values = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']

            for suit in suits:
                if suit not in self.cards:
                    errors.append(f"Missing suit: {suit}")
                    continue
                for value in values:
                    if value not in self.cards[suit]:
                        errors.append(f"Missing card: {value} of {suit}")
                    else:
                        # Validate card structure
                        card = self.cards[suit][value]
                        if not isinstance(card, dict):
                            errors.append(f"Invalid card data for {value} of {suit}")
                            continue
                        # Check required card fields
                        required_card_fields = ['title', 'description']
                        for field in required_card_fields:
                            if field not in card:
                                errors.append(
                                    f"Card {value} of {suit} missing required field: {field}"
                                )

        # Validate config required fields
        if self.config:
            required = ['game', 'mechanics', 'conditions', 'ui']
            for field in required:
                if field not in self.config:
                    errors.append(f"Missing required config field: {field}")

            # Validate game metadata
            if 'game' in self.config:
                game_required = ['title', 'author']
                for field in game_required:
                    if field not in self.config['game']:
                        errors.append(f"Missing required game field: {field}")

        return errors
    
    def generate_css(self) -> str:
        """
        Generate CSS from theme configuration.

        Converts theme.yaml settings into CSS including:
        - Google Fonts imports
        - CSS custom properties (variables)
        - Base styles
        - Component styles
        - Custom CSS from theme

        Returns:
            str: Complete CSS stylesheet as a string
        """
        theme = self.theme.get('theme', {})
        colors = theme.get('colors', {})
        fonts = theme.get('fonts', {})
        layout = theme.get('layout', {})
        components = theme.get('components', {})
        
        # Build CSS
        css = []
        
        # Import Google Fonts
        google_fonts = fonts.get('google_fonts', [])
        if google_fonts:
            font_imports = []
            for font in google_fonts:
                if isinstance(font, dict):
                    family = font.get('family', '')
                    weights = font.get('weights', [400])
                    styles = font.get('styles', ['normal'])
                    # Build font URL
                    weight_str = ','.join(str(w) for w in weights)
                    style_str = '1' if 'italic' in styles else '0'
                    font_imports.append(f"{family}:wght@{weight_str}")
                else:
                    font_imports.append(font)
            
            if font_imports:
                css.append(f"@import url('https://fonts.googleapis.com/css2?{'&'.join(f'family={f}' for f in font_imports)}&display=swap');")
        
        # CSS Variables
        css.append("\n:root {")
        
        # Color variables
        for key, value in colors.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    css.append(f"  --color-{key}-{subkey}: {subvalue};")
            else:
                css.append(f"  --color-{key}: {value};")
        
        # Font variables
        for key, value in fonts.items():
            if key not in ['google_fonts', 'sizes', 'line_heights', 'letter_spacing']:
                css.append(f"  --font-{key}: {value};")
        
        css.append("}\n")
        
        # Base styles
        css.append("""
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: var(--font-body);
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
    color: var(--color-text_primary);
    min-height: 100vh;
    padding: 20px;
    position: relative;
    overflow-x: hidden;
}

h1, h2, h3 {
    font-family: var(--font-title);
    color: var(--color-accent_primary);
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}

h1 { font-size: 3em; text-align: center; margin-bottom: 10px; letter-spacing: 2px; }
h2 { font-size: 2em; margin-bottom: 15px; }
h3 { font-size: 1.5em; margin-bottom: 12px; }

.container {
    max-width: """ + layout.get('container_max_width', '1600px') + """;
    margin: 0 auto;
    display: grid;
    grid-template-columns: """ + layout.get('grid_columns', '400px 1fr') + """;
    gap: """ + layout.get('grid_gap', '30px') + """;
    position: relative;
    z-index: 1;
}

.panel {
    background: linear-gradient(135deg, var(--color-tertiary) 0%, var(--color-secondary) 100%);
    border: 3px solid var(--color-borders);
    border-radius: 12px;
    padding: 25px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}

.section {
    background: rgba(42, 31, 20, 0.6);
    border: 1px solid var(--color-borders);
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
}

button {
    background: linear-gradient(135deg, var(--color-borders) 0%, var(--color-secondary) 100%);
    color: var(--color-text_primary);
    border: 2px solid var(--color-accent_primary);
    padding: 12px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-family: var(--font-ui);
    font-size: 1em;
    font-weight: 600;
    transition: all 0.3s ease;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.4);
}

button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

textarea {
    width: 100%;
    min-height: 400px;
    background: rgba(42, 31, 20, 0.4);
    color: var(--color-text_primary);
    border: 2px solid var(--color-borders);
    border-radius: 8px;
    padding: 20px;
    font-family: var(--font-body);
    font-size: 1.1em;
    line-height: 1.8;
    resize: vertical;
}

.die {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #f5e6d3 0%, #e8dcc4 100%);
    border: 3px solid var(--color-borders);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
    font-weight: bold;
    color: #2a1f14;
    box-shadow: 0 4px 8px rgba(0,0,0,0.4);
    transition: transform 0.6s ease;
}

.die.rolling {
    animation: diceRoll 0.6s ease-in-out;
}

@keyframes diceRoll {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(90deg) scale(1.1); }
    50% { transform: rotate(180deg) scale(1.05); }
    75% { transform: rotate(270deg) scale(1.1); }
}

.dice-container {
    display: flex;
    gap: 15px;
    justify-content: center;
    margin: 15px 0;
}

.card-display {
    background: rgba(42, 31, 20, 0.8);
    border: 2px solid var(--color-accent_primary);
    border-radius: 8px;
    padding: 20px;
    margin: 15px 0;
    min-height: 100px;
}

.modal-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(4px);
    z-index: 1000;
    padding: 20px;
    overflow-y: auto;
}

.modal-overlay.active {
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-content {
    background: linear-gradient(135deg, var(--color-tertiary) 0%, var(--color-secondary) 100%);
    border: 3px solid var(--color-borders);
    border-radius: 12px;
    padding: 40px;
    max-width: 800px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.8);
    position: relative;
}

.modal-close {
    position: absolute;
    top: 10px;
    right: 10px;
    background: transparent;
    border: none;
    font-size: 30px;
    color: var(--color-accent_primary);
    cursor: pointer;
    padding: 5px 10px;
}

/* Card Examination Enhancements */
.card-pending {
    animation: cardGlow 2s ease-in-out infinite;
}

@keyframes cardGlow {
    0%, 100% { box-shadow: 0 0 10px rgba(212, 175, 55, 0.3); }
    50% { box-shadow: 0 0 20px rgba(212, 175, 55, 0.6); }
}

/* Tension/Stability Visual Bar */
.stability-bar {
    width: 100%;
    height: 20px;
    background: rgba(0, 0, 0, 0.4);
    border-radius: 10px;
    overflow: hidden;
    margin: 10px 0;
    border: 2px solid var(--color-borders);
}

.stability-fill {
    height: 100%;
    transition: width 0.5s ease, background-color 0.5s ease;
    background: linear-gradient(90deg, #4caf50 0%, #8bc34a 100%);
}

.stability-fill.danger {
    background: linear-gradient(90deg, #ff9800 0%, #ffb74d 100%);
}

.stability-fill.critical {
    background: linear-gradient(90deg, #f44336 0%, #e57373 100%);
    animation: pulse 1.5s ease-in-out infinite;
}

/* Apply Card Button Enhancement */
button[onclick*="applyCurrentCard"] {
    background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%) !important;
    border-color: #4CAF50 !important;
    font-weight: bold;
}

button[onclick*="applyCurrentCard"]:hover {
    background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%) !important;
}

/* Visual Card Display Styles */
.cards-drawn-area {
    background: linear-gradient(135deg, #2a1f14 0%, #1a0f0a 100%);
    border: 3px solid var(--color-borders);
    border-radius: 12px;
    padding: 20px;
    min-height: 150px;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    align-items: flex-start;
    justify-content: center;
}

.cards-drawn-area.empty {
    justify-content: center;
    align-items: center;
}

.drawn-card {
    width: 100px;
    height: 140px;
    background: linear-gradient(135deg, #f5f5dc 0%, #e8dcc4 100%);
    border: 3px solid var(--color-borders);
    border-radius: 10px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    box-shadow: 0 4px 8px rgba(0,0,0,0.4);
    position: relative;
}

.drawn-card:hover:not(.resolved) {
    transform: translateY(-10px) scale(1.05);
    box-shadow: 0 8px 16px rgba(212, 175, 55, 0.5);
    border-color: var(--color-accent_primary);
}

.drawn-card.resolved {
    opacity: 0.4;
    cursor: default;
    border-color: #5a4a3a;
}

.drawn-card.active {
    border: 4px solid var(--color-accent_primary);
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.8);
}

.drawn-card-value {
    font-size: 2em;
    font-weight: bold;
    margin-bottom: 5px;
}

.drawn-card-suit {
    font-size: 1.5em;
}

.drawn-card.red-card .drawn-card-value,
.drawn-card.red-card .drawn-card-suit {
    color: #d32f2f;
}

.drawn-card.black-card .drawn-card-value,
.drawn-card.black-card .drawn-card-suit {
    color: #2a1f14;
}

.drawn-card-resolved-badge {
    position: absolute;
    top: 5px;
    right: 5px;
    background: #4a7c59;
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8em;
    font-weight: bold;
}

.empty-cards-message {
    color: var(--color-text_secondary);
    font-style: italic;
    text-align: center;
    font-size: 1.1em;
}

/* Card count result display */
#cardCountResult {
    background: rgba(212, 175, 55, 0.2);
    border: 2px solid var(--color-accent_primary);
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    font-size: 1.3em;
    font-weight: bold;
    color: var(--color-accent_primary);
    margin-top: 10px;
}

/* Deck status */
.deck-status {
    text-align: center;
    color: var(--color-text_secondary);
    margin-top: 10px;
    font-style: italic;
}

/* Card prompt panel enhancements */
#promptPanel {
    background: linear-gradient(135deg, #3a2818 0%, #2a1810 100%);
    border: 2px solid var(--color-borders);
    border-radius: 8px;
    padding: 20px;
    margin-top: 15px;
}

#promptPanel h3 {
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--color-borders);
}

/* Dice container enhancements */
.die-label {
    position: absolute;
    bottom: 5px;
    font-size: 12px;
    color: #6b5437;
    font-weight: normal;
}

.result {
    background: rgba(212, 175, 55, 0.15);
    border: 1px solid var(--color-borders);
    padding: 12px;
    border-radius: 6px;
    margin-top: 10px;
    text-align: center;
    font-weight: 600;
    min-height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
}

""")

        # Custom CSS from theme
        custom_css = theme.get('custom_css', '')
        if custom_css:
            css.append("\n/* Custom CSS */\n")
            css.append(custom_css)

        return '\n'.join(css)
    
    def generate_javascript(self) -> str:
        """
        Generate JavaScript game engine.

        Creates a complete game engine including:
        - Game configuration and card data (as JSON)
        - Game state management
        - Deck initialization and shuffling
        - Dice rolling mechanics (turn dice + effect dice)
        - Card drawing system with visual display
        - Multi-card turn system
        - Stability/tower mechanics with escalating risk
        - Token management
        - Save/load system (localStorage)
        - Journal auto-save
        - Win/loss condition checking

        Returns:
            str: Complete JavaScript code as a string
        """
        config = self.config
        cards = self.cards

        # Convert cards to JavaScript format
        card_data_js = json.dumps(cards, indent=2)

        # Load the enhanced JavaScript template
        template_path = Path(__file__).parent.parent / 'new_js_template.txt'
        with open(template_path, 'r', encoding='utf-8') as f:
            js_template = f.read()

        # Replace placeholders with actual values
        js = js_template.replace('CONFIG_PLACEHOLDER', json.dumps(config, indent=2))
        js = js.replace('CARDS_PLACEHOLDER', card_data_js)
        js = js.replace('TOKENS_INIT', str(config['mechanics']['tokens']['initial']))
        js = js.replace('STABILITY_INIT', str(config['mechanics']['stability']['initial']))

        return js
    
    def build(self, output_path: Optional[str] = None, minify: bool = False) -> Path:
        """
        Build the complete game HTML file.

        This is the main build method that orchestrates the entire build process:
        1. Load all configuration files
        2. Validate all data
        3. Generate CSS and JavaScript
        4. Render HTML template
        5. Write output file

        Args:
            output_path: Optional custom output path. If not provided, uses
                        game title to generate filename in game directory
            minify: If True, minify the output HTML (requires htmlmin package)

        Returns:
            Path: Path to the generated HTML file

        Raises:
            ValidationError: If configuration validation fails
            BuildError: If build process encounters an error
        """
        try:
            # Load all configs
            self.load_all()

            # Validate
            errors = self.validate()
            if errors:
                raise ValidationError(
                    f"Validation failed with {len(errors)} error(s):\n" +
                    "\n".join(f"  - {error}" for error in errors)
                )

            # Generate CSS and JS
            css = self.generate_css()
            js = self.generate_javascript()

            # Load template
            template_dir = Path(__file__).parent.parent / 'templates'
            if not template_dir.exists():
                raise BuildError(f"Templates directory not found: {template_dir}")

            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('base.html')

            # Render template
            html = template.render(
                config=self.config,
                story=self.story,
                css=css,
                js=js
            )

            # Minify if requested
            if minify:
                try:
                    import htmlmin
                    html = htmlmin.minify(html, remove_comments=True, remove_empty_space=True)
                except ImportError:
                    print("Warning: htmlmin not installed, skipping minification")
                    print("Install with: pip install htmlmin")

            # Determine output path
            if not output_path:
                game_title = self.config['game']['title'].lower().replace(' ', '-')
                # Remove any characters that aren't alphanumeric or hyphens
                game_title = re.sub(r'[^a-z0-9-]', '', game_title)
                output_path = self.game_path / f"{game_title}.html"
            else:
                output_path = Path(output_path)

            # Write output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            return Path(output_path)

        except (FileNotFoundError, ValidationError, BuildError):
            raise
        except Exception as e:
            raise BuildError(f"Build failed: {e}")
