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
        - Dice rolling mechanics
        - Card drawing system
        - Stability/tower mechanics
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
        
        # Build JavaScript
        js = f"""
// Game Configuration
const GAME_CONFIG = {json.dumps(config, indent=2)};
const CARD_DATA = {card_data_js};

// Game State
let gameState = {{
    tokens: {config['mechanics']['tokens']['initial']},
    stability: {config['mechanics']['stability']['initial']},
    deck: [],
    drawnCards: [],
    cardHistory: [],
    pendingCard: null,
    gameEnded: false
}};

// Initialize deck
function initializeDeck() {{
    const suits = ['spades', 'hearts', 'diamonds', 'clubs'];
    const values = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
    gameState.deck = [];
    
    for (let suit of suits) {{
        for (let value of values) {{
            gameState.deck.push({{ suit, value }});
        }}
    }}
    
    shuffleDeck();
    updateDeckDisplay();
}}

function shuffleDeck() {{
    for (let i = gameState.deck.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [gameState.deck[i], gameState.deck[j]] = [gameState.deck[j], gameState.deck[i]];
    }}
}}

// Dice rolling
function rollDice() {{
    const die1 = document.getElementById('die1');
    const die2 = document.getElementById('die2');
    
    die1.classList.add('rolling');
    die2.classList.add('rolling');
    
    setTimeout(() => {{
        const result1 = Math.floor(Math.random() * 6) + 1;
        const result2 = Math.floor(Math.random() * 6) + 1;
        const total = result1 + result2;
        
        die1.firstChild.textContent = result1;
        die2.firstChild.textContent = result2;
        
        document.getElementById('diceResult').textContent = `Total: ${{total}}`;
        
        die1.classList.remove('rolling');
        die2.classList.remove('rolling');
    }}, 600);
}}

// Card drawing
function drawCard() {{
    if (gameState.deck.length === 0) {{
        if (GAME_CONFIG.mechanics.deck.reshuffle) {{
            alert('Deck empty! Reshuffling...');
            initializeDeck();
        }} else {{
            alert('Deck is empty!');
            return;
        }}
    }}

    // Check if there's already a pending card
    if (gameState.pendingCard) {{
        alert('Please apply the current card effects before drawing another card.');
        return;
    }}

    const card = gameState.deck.pop();
    const cardData = CARD_DATA[card.suit][card.value];

    // Store as pending card
    gameState.pendingCard = {{ card, cardData }};

    // Display card for examination
    displayCard(card, cardData);

    // Update displays
    updateDeckDisplay();
    saveGameState();
}}

function applyCurrentCard() {{
    if (!gameState.pendingCard) {{
        alert('No card to apply.');
        return;
    }}

    const {{ card, cardData }} = gameState.pendingCard;

    // Add to history
    gameState.cardHistory.unshift({{ ...card, ...cardData }});
    if (gameState.cardHistory.length > 10) {{
        gameState.cardHistory.pop();
    }}

    // Apply effects
    applyCardEffects(cardData);

    // Clear pending card
    gameState.pendingCard = null;

    // Update displays
    updateHistoryDisplay();

    // Clear the card display
    document.getElementById('cardResult').innerHTML = 'No card drawn yet';

    saveGameState();
}}

function displayCard(card, cardData) {{
    const suitSymbols = {{
        'spades': '♠️',
        'hearts': '♥️',
        'diamonds': '♦️',
        'clubs': '♣️'
    }};

    const display = document.getElementById('cardResult');

    // Build effects preview
    let effectsHTML = '';
    if (cardData.tokens !== 0) {{
        effectsHTML += `<p><strong>Effect: ${{cardData.tokens > 0 ? '+' : ''}}${{cardData.tokens}} Tokens</strong></p>`;
    }}
    if (cardData.blocks > 0) {{
        effectsHTML += `<p><strong>Effect: Pull ${{cardData.blocks}} block(s)</strong></p>`;
    }}

    display.innerHTML = `
        <div style="border: 3px solid var(--color-accent_primary); border-radius: 8px; padding: 15px; background: rgba(42, 31, 20, 0.9);">
            <h3 style="margin-bottom: 10px;">${{suitSymbols[card.suit]}} ${{card.value}} - ${{cardData.title}}</h3>
            <div style="margin: 15px 0; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 4px;">
                <p style="line-height: 1.6; white-space: pre-wrap;">${{cardData.description}}</p>
            </div>
            ${{effectsHTML}}
            <div style="margin-top: 15px; text-align: center;">
                <button
                    onclick="applyCurrentCard()"
                    style="width: 100%; background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%); font-size: 1.1em; padding: 15px;"
                    aria-label="Apply card effects and add to journal">
                    ✓ Apply Card Effects
                </button>
            </div>
            <p style="margin-top: 10px; font-size: 0.9em; font-style: italic; color: var(--color-text_secondary); text-align: center;">
                Read the prompt and write in your journal before applying effects
            </p>
        </div>
    `;
}}

function applyCardEffects(cardData) {{
    // Apply token changes
    if (cardData.tokens) {{
        gameState.tokens += cardData.tokens;
        updateTokenDisplay();
    }}
    
    // Handle block pulls
    if (cardData.blocks > 0) {{
        for (let i = 0; i < cardData.blocks; i++) {{
            pullBlock();
        }}
    }}
    
    // Check win/loss conditions
    checkGameEnd();
}}

// Stability/Tower mechanics
function pullBlock() {{
    if (gameState.stability <= 0) return;
    
    const thresholds = GAME_CONFIG.mechanics.stability.thresholds;
    let failureThreshold = 1;
    
    if (gameState.stability <= thresholds.critical) {{
        failureThreshold = 3;
    }} else if (gameState.stability <= thresholds.danger) {{
        failureThreshold = 2;
    }}
    
    // Roll dice pool
    let lost = 0;
    for (let i = 0; i < gameState.stability; i++) {{
        if (Math.random() * 6 + 1 <= failureThreshold) {{
            lost++;
        }}
    }}
    
    gameState.stability -= lost;
    if (gameState.stability < 0) gameState.stability = 0;
    
    updateStabilityDisplay();
    
    if (gameState.stability === 0) {{
        endGame('stability');
    }}
}}

// Token management
function adjustTokens(amount) {{
    gameState.tokens += amount;
    updateTokenDisplay();
    saveGameState();
}}

// Display updates
function updateTokenDisplay() {{
    const tokenName = GAME_CONFIG.mechanics.tokens.name;
    document.getElementById('tokenValue').textContent = gameState.tokens;
    document.getElementById('tokenName').textContent = tokenName;
}}

function updateStabilityDisplay() {{
    const stabilityName = GAME_CONFIG.mechanics.stability.name;
    const maxStability = GAME_CONFIG.mechanics.stability.initial;
    document.getElementById('stabilityValue').textContent = gameState.stability;
    document.getElementById('stabilityName').textContent = stabilityName;

    const thresholds = GAME_CONFIG.mechanics.stability.thresholds;
    let className = 'stability-safe';
    if (gameState.stability <= thresholds.critical) {{
        className = 'stability-critical';
    }} else if (gameState.stability <= thresholds.danger) {{
        className = 'stability-danger';
    }}

    document.getElementById('stabilityValue').className = className;

    // Update visual bar
    const barElement = document.getElementById('stabilityBar');
    if (barElement) {{
        const percentage = (gameState.stability / maxStability) * 100;
        barElement.style.width = percentage + '%';

        // Update bar color class
        barElement.className = 'stability-fill';
        if (gameState.stability <= thresholds.critical) {{
            barElement.className = 'stability-fill critical';
        }} else if (gameState.stability <= thresholds.danger) {{
            barElement.className = 'stability-fill danger';
        }}
    }}
}}

function updateDeckDisplay() {{
    document.getElementById('deckCount').textContent = gameState.deck.length;
}}

function updateHistoryDisplay() {{
    const history = document.getElementById('cardHistory');
    const suitSymbols = {{
        'spades': '♠️',
        'hearts': '♥️',
        'diamonds': '♦️',
        'clubs': '♣️'
    }};
    
    history.innerHTML = gameState.cardHistory
        .map(card => `<div class="history-item">${{suitSymbols[card.suit]}} ${{card.value}} - ${{card.title}}</div>`)
        .join('');
}}

// Game end conditions
function checkGameEnd() {{
    const conditions = GAME_CONFIG.conditions;
    
    // Check loss conditions
    if (gameState.stability <= 0) {{
        endGame('stability');
        return;
    }}
    
    if (gameState.tokens <= 0) {{
        endGame('tokens');
        return;
    }}
    
    // Check win condition
    if (gameState.deck.length === 0 && gameState.tokens > 0 && gameState.stability > 0) {{
        endGame('win');
    }}
}}

function endGame(reason) {{
    gameState.gameEnded = true;
    
    const conditions = GAME_CONFIG.conditions;
    let message = '';
    
    if (reason === 'win') {{
        const winCondition = conditions.win.find(c => c.type === 'deck_empty');
        message = winCondition.message;
    }} else if (reason === 'stability') {{
        const loseCondition = conditions.lose.find(c => c.type === 'stability_zero');
        message = loseCondition.message || 'Game Over: Stability collapsed';
    }} else if (reason === 'tokens') {{
        const loseCondition = conditions.lose.find(c => c.type === 'tokens_zero');
        message = loseCondition.message || 'Game Over: All resources lost';
    }}
    
    document.getElementById('cardResult').innerHTML = `
        <div class="game-end">
            <h2>Game Over</h2>
            <p>${{message}}</p>
            <button onclick="newGame()">New Game</button>
        </div>
    `;
    
    document.querySelectorAll('button:not([onclick*="newGame"])').forEach(btn => {{
        btn.disabled = true;
    }});
}}

// Save/Load
function saveGameState() {{
    localStorage.setItem('gameState', JSON.stringify(gameState));
    localStorage.setItem('journalContent', document.getElementById('journal').value);
}}

function loadGameState() {{
    const saved = localStorage.getItem('gameState');
    if (saved) {{
        gameState = JSON.parse(saved);
        updateTokenDisplay();
        updateStabilityDisplay();
        updateDeckDisplay();
        updateHistoryDisplay();

        // Restore pending card if exists
        if (gameState.pendingCard) {{
            displayCard(gameState.pendingCard.card, gameState.pendingCard.cardData);
        }}

        if (gameState.gameEnded) {{
            document.querySelectorAll('button:not([onclick*="newGame"])').forEach(btn => {{
                btn.disabled = true;
            }});
        }}
    }}

    const journal = localStorage.getItem('journalContent');
    if (journal) {{
        document.getElementById('journal').value = journal;
    }}
}}

function newGame() {{
    if (confirm('Start a new game? This will erase all progress.')) {{
        localStorage.clear();
        location.reload();
    }}
}}

// Journal auto-save
let saveTimeout;
function autoSaveJournal() {{
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {{
        saveGameState();
    }}, 1000);
}}

function downloadJournal() {{
    const text = document.getElementById('journal').value;
    const blob = new Blob([text], {{ type: 'text/plain' }});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `journal-${{new Date().toISOString().slice(0,10)}}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
}}

// Initialize on load
window.onload = function() {{
    initializeDeck();
    loadGameState();
    updateTokenDisplay();
    updateStabilityDisplay();
    
    document.getElementById('journal').addEventListener('input', autoSaveJournal);
}};
"""
        
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
