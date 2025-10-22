"""
Wretched & Alone Game Generator
Core builder module
"""

import yaml
import json
import markdown
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import re

class GameBuilder:
    """Main game builder class"""
    
    def __init__(self, game_path: str):
        self.game_path = Path(game_path)
        self.config = None
        self.cards = None
        self.theme = None
        self.story = None
        
    def load_config(self):
        """Load and parse config.yaml"""
        config_file = self.game_path / "config.yaml"
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        return self.config
    
    def load_cards(self):
        """Load and parse cards.yaml"""
        cards_file = self.game_path / "cards.yaml"
        with open(cards_file, 'r', encoding='utf-8') as f:
            self.cards = yaml.safe_load(f)
        return self.cards
    
    def load_theme(self):
        """Load and parse theme.yaml"""
        theme_file = self.game_path / "theme.yaml"
        with open(theme_file, 'r', encoding='utf-8') as f:
            self.theme = yaml.safe_load(f)
        return self.theme
    
    def load_story(self):
        """Load and parse story.md"""
        story_file = self.game_path / "story.md"
        with open(story_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
            # Convert markdown to HTML
            self.story = markdown.markdown(md_content, extensions=['extra', 'nl2br'])
        return self.story
    
    def validate(self):
        """Validate all loaded configurations"""
        errors = []
        
        # Check that all configs are loaded
        if not self.config:
            errors.append("Config file not loaded")
        if not self.cards:
            errors.append("Cards file not loaded")
        if not self.theme:
            errors.append("Theme file not loaded")
        
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
        
        # Validate config required fields
        if self.config:
            required = ['game', 'mechanics', 'conditions', 'ui']
            for field in required:
                if field not in self.config:
                    errors.append(f"Missing required config field: {field}")
        
        return errors
    
    def generate_css(self):
        """Generate CSS from theme configuration"""
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
""")
        
        # Custom CSS from theme
        custom_css = theme.get('custom_css', '')
        if custom_css:
            css.append("\n/* Custom CSS */\n")
            css.append(custom_css)
        
        return '\n'.join(css)
    
    def generate_javascript(self):
        """Generate JavaScript game engine"""
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
    
    const card = gameState.deck.pop();
    const cardData = CARD_DATA[card.suit][card.value];
    
    // Add to history
    gameState.cardHistory.unshift({{ ...card, ...cardData }});
    if (gameState.cardHistory.length > 10) {{
        gameState.cardHistory.pop();
    }}
    
    // Display card
    displayCard(card, cardData);
    
    // Apply effects
    applyCardEffects(cardData);
    
    // Update displays
    updateDeckDisplay();
    updateHistoryDisplay();
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
    display.innerHTML = `
        <h3>${{suitSymbols[card.suit]}} ${{card.value}} - ${{cardData.title}}</h3>
        <p>${{cardData.description}}</p>
        ${{cardData.tokens !== 0 ? `<p><strong>Tokens: ${{cardData.tokens > 0 ? '+' : ''}}${{cardData.tokens}}</strong></p>` : ''}}
        ${{cardData.blocks > 0 ? `<p><strong>Pull ${{cardData.blocks}} block(s)</strong></p>` : ''}}
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
    
    def build(self, output_path: str = None):
        """Build the complete game HTML file"""
        # Load all configs
        self.load_config()
        self.load_cards()
        self.load_theme()
        self.load_story()
        
        # Validate
        errors = self.validate()
        if errors:
            raise ValueError(f"Validation errors:\\n" + "\\n".join(errors))
        
        # Generate CSS and JS
        css = self.generate_css()
        js = self.generate_javascript()
        
        # Load template
        template_dir = Path(__file__).parent.parent / 'templates'
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template('base.html')
        
        # Render template
        html = template.render(
            config=self.config,
            story=self.story,
            css=css,
            js=js
        )
        
        # Determine output path
        if not output_path:
            game_title = self.config['game']['title'].lower().replace(' ', '-')
            output_path = self.game_path / f"{game_title}.html"
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
