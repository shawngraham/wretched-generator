'use strict';
/*
 * Wretched & Alone game engine.
 * Everything game-specific comes from config.yaml / cards.yaml (injected below).
 * Placeholders in the next four lines are replaced by the builder.
 */
const GAME_CONFIG = __WRETCHED_CONFIG__;
const CARD_DATA = __WRETCHED_CARDS__;
const SPECIAL_CARDS = __WRETCHED_SPECIAL_CARDS__;
const GAME_META = __WRETCHED_META__;

// ---------------------------------------------------------------------------
// Configuration (with defaults for anything the config omits)
// ---------------------------------------------------------------------------
const SUITS = ['spades', 'hearts', 'diamonds', 'clubs'];
const VALUES = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
const SUIT_SYMBOLS = { spades: '♠', hearts: '♥', diamonds: '♦', clubs: '♣' };
const RANK_NAMES = {
    A: 'ace', K: 'king', Q: 'queen', J: 'jack', '10': 'ten', '9': 'nine', '8': 'eight',
    '7': 'seven', '6': 'six', '5': 'five', '4': 'four', '3': 'three', '2': 'two'
};

const MECH = GAME_CONFIG.mechanics || {};
const COND = GAME_CONFIG.conditions || {};
const UI = GAME_CONFIG.ui || {};
const SPECIAL = GAME_CONFIG.special || {};
const LABELS = UI.labels || {};
const SYSTEMS = MECH.systems || [];

const TOK = SYSTEMS.includes('tokens') ? (MECH.tokens || null) : null;
const STAB = SYSTEMS.includes('stability') ? (MECH.stability || null) : null;
const TOKEN_NAME = TOK ? (TOK.name || 'tokens') : 'tokens';
const STAB_NAME = STAB ? (STAB.name || 'stability') : 'stability';

const TURN_DICE = Object.assign({ count: 1, sides: 6 }, (MECH.dice && MECH.dice.main) || {});
const TURN_SEQ = SPECIAL.turn_sequence || {};
const MIN_CARDS = Number.isFinite(TURN_SEQ.min_cards) ? TURN_SEQ.min_cards : TURN_DICE.count;
const MAX_CARDS = Number.isFinite(TURN_SEQ.max_cards) ? TURN_SEQ.max_cards : TURN_DICE.count * TURN_DICE.sides;

const BINARY = Object.assign({ split: 3, negative: 'Negative Outcome', positive: 'Positive Outcome' },
    (MECH.dice && MECH.dice.binary) || {});
const INTERPRET = (MECH.dice && Array.isArray(MECH.dice.interpret) && MECH.dice.interpret.length)
    ? MECH.dice.interpret
    : [{ max: 5, label: 'Low' }, { max: 8, label: 'Middle' }, { max: 12, label: 'High' }];

const THRESHOLDS = Object.assign({ critical: 20, danger: 50 }, (STAB && STAB.thresholds) || {});
const FAILURE = Object.assign({ safe: 1, danger: 2, critical: 3 }, (STAB && STAB.failure_thresholds) || {});

const WIN = (COND.win || []).find(c => c.type === 'deck_empty') || null;
const LOSE = COND.lose || null;           // null => defaults (both losses active)
const loseCond = type => (LOSE ? LOSE.find(c => c.type === type) : undefined);
const TOKENS_END_GAME = !!TOK && (!LOSE || !!loseCond('tokens_zero'));

const QUEEN = SPECIAL.queen_tracker && SPECIAL.queen_tracker.enabled ? SPECIAL.queen_tracker : null;

const STORAGE_KEY = GAME_META.storageKey;
const JOURNAL_KEY = STORAGE_KEY + ':journal';
const STATE_VERSION = 2;

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------
function esc(s) {
    return String(s === undefined || s === null ? '' : s).replace(/[&<>"']/g, c =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function el(id) { return document.getElementById(id); }
function rollDie(sides) { return Math.floor(Math.random() * sides) + 1; }
function pick(arr) { return arr && arr.length ? arr[Math.floor(Math.random() * arr.length)] : null; }
function plural(n, one, many) { return n === 1 ? one : many; }
function signed(n) { return (n > 0 ? '+' : '') + n; }

const store = {
    get(key) { try { return localStorage.getItem(key); } catch (e) { return null; } },
    set(key, val) { try { localStorage.setItem(key, val); return true; } catch (e) { return false; } },
    remove(key) { try { localStorage.removeItem(key); } catch (e) { /* ignore */ }
    }
};

function parseDice(spec) {
    const m = /^(\d+)d(\d+)$/i.exec(String(spec || '1d6').trim());
    return m ? { count: parseInt(m[1], 10), sides: parseInt(m[2], 10) } : { count: 1, sides: 6 };
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
function freshState() {
    return {
        v: STATE_VERSION,
        tokens: TOK ? TOK.initial : 0,
        stability: STAB ? STAB.initial : 0,
        deck: [],
        cardHistory: [],
        gameEnded: false,
        endInfo: null,
        cardsToDraw: 0,
        cardsDrawnThisTurn: 0,
        drawnCards: [],      // { card, resolved, applied, special, log[] }
        activeCardIndex: null,
        queens: 0,
        turn: 0,
        stabilityNote: ''
    };
}
let gameState = freshState();

function isValidCard(c) {
    return !!c && SUITS.includes(c.suit) && VALUES.includes(c.value) &&
        !!(CARD_DATA[c.suit] && CARD_DATA[c.suit][c.value]);
}

// ---------------------------------------------------------------------------
// Deck
// ---------------------------------------------------------------------------
function buildShuffledDeck(exclude) {
    const skip = new Set((exclude || []).map(c => c.suit + ':' + c.value));
    const deck = [];
    for (const suit of SUITS) {
        for (const value of VALUES) {
            if (!skip.has(suit + ':' + value)) deck.push({ suit, value });
        }
    }
    for (let i = deck.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [deck[i], deck[j]] = [deck[j], deck[i]];
    }
    return deck;
}

function initializeDeck() {
    gameState.deck = buildShuffledDeck();
}

function reshuffleDeck() {
    // Cards still on the table this turn are not put back in the deck.
    gameState.deck = buildShuffledDeck(gameState.drawnCards.map(c => c.card));
    gameState.cardHistory = [];
    notify('The deck was empty and has been reshuffled.');
}

// ---------------------------------------------------------------------------
// Turn flow
// ---------------------------------------------------------------------------
function turnInProgress() {
    return gameState.cardsToDraw > 0 &&
        (gameState.cardsDrawnThisTurn < gameState.cardsToDraw || gameState.drawnCards.some(c => !c.resolved));
}

function showDice(values, sides, label) {
    const container = el('diceContainer');
    if (!container) return;
    container.innerHTML = values.map(v =>
        `<div class="die rolling">${v}<div class="die-label">d${sides}</div></div>`).join('');
    setTimeout(() => container.querySelectorAll('.die').forEach(d => d.classList.remove('rolling')), 600);
}

function setDiceResult(text) {
    const r = el('diceResult');
    if (r) r.textContent = text;
}

// Roll the turn dice (config: mechanics.dice.main) to find how many cards to draw.
function rollForCardCount() {
    if (gameState.gameEnded) return;
    if (turnInProgress() &&
        !confirm('This turn is not finished (cards still to draw or resolve). Start a new turn anyway?')) {
        return;
    }

    const rolls = [];
    for (let i = 0; i < TURN_DICE.count; i++) rolls.push(rollDie(TURN_DICE.sides));
    let total = rolls.reduce((a, b) => a + b, 0);
    total = Math.max(MIN_CARDS, Math.min(MAX_CARDS, total));

    let note = '';
    const remaining = gameState.deck.length;
    if (WIN && remaining > 0 && total > remaining) {
        total = remaining;
        note = ` Only ${remaining} ${plural(remaining, 'card is', 'cards are')} left in the deck.`;
    }

    gameState.cardsToDraw = total;
    gameState.cardsDrawnThisTurn = 0;
    gameState.drawnCards = [];
    gameState.activeCardIndex = null;
    gameState.turn++;

    showDice(rolls, TURN_DICE.sides);
    setDiceResult(`Turn dice: ${rolls.join(' + ')} = ${rolls.reduce((a, b) => a + b, 0)}. Draw ${total} ${plural(total, 'card', 'cards')}.${note}`);
    notify('');
    refreshAll();
    saveGameState();
}

function drawCard() {
    if (gameState.gameEnded) return;

    if (gameState.cardsToDraw === 0) {
        notify('Roll the turn dice first to find out how many cards to draw.');
        return;
    }
    if (gameState.cardsDrawnThisTurn >= gameState.cardsToDraw) {
        notify(`You have drawn all ${gameState.cardsToDraw} cards for this turn. Resolve them, then roll to start a new turn.`);
        return;
    }
    if (gameState.deck.length === 0) {
        if (MECH.deck && MECH.deck.reshuffle === false) {
            notify('The deck is empty.');
            return;
        }
        reshuffleDeck();
    }

    const card = gameState.deck.pop();
    gameState.cardHistory.push(card);
    gameState.cardsDrawnThisTurn++;
    gameState.drawnCards.push({ card, resolved: false, applied: false, special: null, log: [] });

    if (QUEEN && card.value === 'Q') {
        gameState.queens++;
        if (gameState.queens >= (QUEEN.threshold || 4)) {
            refreshAll();
            endGame('queens');
            return;
        }
    }

    notify('');
    refreshAll();
    saveGameState();
}

function viewCard(index) {
    if (gameState.gameEnded) return;
    if (!gameState.drawnCards[index]) return;
    gameState.activeCardIndex = index;
    refreshAll();
    saveGameState();
}

function pendingEffects(obj) {
    const data = CARD_DATA[obj.card.suit][obj.card.value];
    const hasBasic = !obj.applied && ((data.tokens || 0) !== 0 || (data.blocks || 0) > 0);
    const spec = findSpecial(obj.card);
    const hasSpecial = !!spec && !obj.special;
    return hasBasic || hasSpecial;
}

function markCardResolved(index) {
    const obj = gameState.drawnCards[index];
    if (!obj || obj.resolved || gameState.gameEnded) return;

    if (pendingEffects(obj) &&
        !confirm('This card has effects you have not applied. Mark it done anyway?')) {
        return;
    }
    obj.resolved = true;
    gameState.activeCardIndex = null;
    refreshAll();
    saveGameState();
    checkWin();
}

// ---------------------------------------------------------------------------
// Card effects
// ---------------------------------------------------------------------------
function changeTokens(amount) {
    if (!TOK) return;
    gameState.tokens += amount;
    if (TOK.allow_negative === false && gameState.tokens < 0) gameState.tokens = 0;
}

// Find the special_cards entry (if any) that applies to a card.
function findSpecial(card) {
    const data = CARD_DATA[card.suit][card.value];
    const rank = RANK_NAMES[card.value];
    const candidates = [`${rank}_of_${card.suit}`, `${card.value}_of_${card.suit}`];
    if (data.special) candidates.push(data.special);
    for (const key of candidates) {
        const spec = SPECIAL_CARDS[key];
        if (spec && SPECIAL[key] && SPECIAL[key].enabled === false) continue;
        if (spec && spec.type === 'roll_check') return Object.assign({ key }, spec);
    }
    for (const key of Object.keys(SPECIAL_CARDS)) {
        const spec = SPECIAL_CARDS[key];
        if (spec && spec.card === `${card.suit}.${card.value}` && spec.type === 'roll_check' &&
            !(SPECIAL[key] && SPECIAL[key].enabled === false)) {
            return Object.assign({ key }, spec);
        }
    }
    return null;
}

function applyOutcome(obj, outcome) {
    if (!outcome) return;
    if (outcome.tokens) changeTokens(outcome.tokens);
    for (let i = 0; i < (outcome.blocks || 0) && gameState.stability > 0; i++) {
        obj.log.push(performPull().text);
    }
}

function applyBasicCardEffects(index) {
    const obj = gameState.drawnCards[index];
    if (!obj || obj.applied || gameState.gameEnded) return;
    const data = CARD_DATA[obj.card.suit][obj.card.value];
    obj.applied = true;

    if (TOK && (data.tokens || 0) !== 0) {
        changeTokens(data.tokens);
        obj.log.push(`${signed(data.tokens)} ${TOKEN_NAME}.`);
    }
    for (let i = 0; i < (data.blocks || 0) && gameState.stability > 0; i++) {
        obj.log.push(performPull().text);
    }
    refreshAll();
    saveGameState();
    checkGameEnd();
}

function rollSpecial(index) {
    const obj = gameState.drawnCards[index];
    if (!obj || obj.special || gameState.gameEnded) return;
    const spec = findSpecial(obj.card);
    if (!spec) return;

    const dice = parseDice(spec.die);
    const rolls = [];
    for (let i = 0; i < dice.count; i++) rolls.push(rollDie(dice.sides));
    const total = rolls.reduce((a, b) => a + b, 0);
    const success = total >= (spec.success_value !== undefined ? spec.success_value : dice.sides);
    const outcome = success ? spec.on_success : spec.on_failure;

    showDice(rolls, dice.sides);
    setDiceResult(`Rolled ${rolls.join(' + ')}${rolls.length > 1 ? ' = ' + total : ''}.`);
    obj.special = {
        roll: total,
        success,
        message: (outcome && outcome.message) || (success ? 'Success.' : 'Failure.')
    };
    applyOutcome(obj, outcome);
    refreshAll();
    saveGameState();
    checkGameEnd();
}

// ---------------------------------------------------------------------------
// Dice oracle (free rolls the cards may ask for)
// ---------------------------------------------------------------------------
function rollOneDie() {
    if (gameState.gameEnded) return 0;
    const die = rollDie(6);
    showDice([die], 6);
    setDiceResult(`Rolled ${die}: ${die <= BINARY.split ? BINARY.negative : BINARY.positive}`);
    return die;
}

function rollTwoDice() {
    if (gameState.gameEnded) return 0;
    const d1 = rollDie(6), d2 = rollDie(6), total = d1 + d2;
    showDice([d1, d2], 6);
    const tier = INTERPRET.find(t => total <= t.max) || INTERPRET[INTERPRET.length - 1];
    setDiceResult(`Rolled ${d1} + ${d2} = ${total}: ${tier.label}`);
    return total;
}

// ---------------------------------------------------------------------------
// Stability (the tower)
// ---------------------------------------------------------------------------
function riskTier(stability) {
    if (stability <= THRESHOLDS.critical) return 'critical';
    if (stability <= THRESHOLDS.danger) return 'danger';
    return 'safe';
}

// Config: failure_thresholds (a die in the pool is "lost" on a roll <= this value).
function failureThresholdFor(stability) {
    if (STAB && STAB.risk_scaling === false) return FAILURE.safe;
    return FAILURE[riskTier(stability)];
}

// Pool size defaults to the current stability, as described in config.yaml.
// Optional config `stability.pool_size: N` uses a fixed pool of N dice instead.
function poolSizeFor(stability) {
    const p = STAB && STAB.pool_size;
    return (typeof p === 'number' && p > 0) ? p : stability;
}

function performPull() {
    if (!STAB) return { lost: 0, text: '' };
    const before = gameState.stability;
    const threshold = failureThresholdFor(before);
    const pool = poolSizeFor(before);
    let lost = 0;
    for (let i = 0; i < pool; i++) {
        if (rollDie(6) <= threshold) lost++;
    }
    const minLoss = (STAB && Number.isFinite(STAB.min_loss)) ? STAB.min_loss : 1;
    lost = Math.min(before, Math.max(lost, minLoss));
    gameState.stability = before - lost;

    let note;
    if (gameState.stability <= 0) {
        note = STAB.collapse_message || `${STAB_NAME} has collapsed.`;
    } else {
        note = pick((STAB.messages || {})[riskTier(gameState.stability)]) || '';
    }
    gameState.stabilityNote = note;

    return {
        lost,
        text: `Pulled a block: ${STAB_NAME} ${before} → ${gameState.stability} (−${lost}).` + (note ? ` ${note}` : '')
    };
}

// Manual "Pull Block" button.
function pullBlock() {
    if (!STAB || gameState.gameEnded) return;
    performPull();
    refreshAll();
    saveGameState();
    checkGameEnd();
}

// ---------------------------------------------------------------------------
// Tokens
// ---------------------------------------------------------------------------
function adjustTokens(direction) {
    if (!TOK || gameState.gameEnded) return;
    const step = Number.isFinite(TOK.controls && TOK.controls.increment) ? TOK.controls.increment : 1;
    changeTokens(direction * step);
    refreshAll();
    saveGameState();
    checkGameEnd();
}

// ---------------------------------------------------------------------------
// End conditions
// ---------------------------------------------------------------------------
const WIN_CHECKS = {
    tokens_positive: () => !TOK || gameState.tokens > 0,
    stability_above_zero: () => !STAB || gameState.stability > 0
};

function checkGameEnd() {
    if (gameState.gameEnded) return true;
    if (STAB && gameState.stability <= 0) { endGame('stability'); return true; }
    if (TOKENS_END_GAME && gameState.tokens <= 0) { endGame('tokens'); return true; }
    return false;
}

// Win: deck exhausted and every card resolved (config: conditions.win, type deck_empty).
function checkWin() {
    if (!WIN || gameState.gameEnded) return false;
    if (gameState.deck.length > 0 || gameState.drawnCards.length === 0) return false;
    if (gameState.drawnCards.some(c => !c.resolved)) return false;
    const ok = (WIN.additional_checks || []).every(name => !WIN_CHECKS[name] || WIN_CHECKS[name]());
    if (!ok) return false;
    endGame('win');
    return true;
}

function endGame(reason) {
    if (gameState.gameEnded) return;
    gameState.gameEnded = true;
    gameState.activeCardIndex = null;

    const parts = [];
    let kind = 'lose';
    let title = LABELS.game_over_title || 'Game Over';

    if (reason === 'win') {
        kind = 'win';
        title = LABELS.win_title || 'The End';
        parts.push({ text: (WIN && WIN.message) || 'You survived to the end.' });
    } else if (reason === 'stability') {
        const cond = loseCond('stability_zero') || {};
        if (STAB && STAB.collapse_message) parts.push({ text: STAB.collapse_message, strong: true });
        const ending = pick(cond.endings);
        if (ending) parts.push({ heading: ending.title, text: ending.text });
        parts.push({ text: cond.message || `${STAB_NAME} has collapsed.` });
    } else if (reason === 'tokens') {
        const cond = loseCond('tokens_zero') || {};
        parts.push({ text: cond.message || `All ${TOKEN_NAME} are gone.` });
    } else if (reason === 'queens') {
        title = (QUEEN.ending && QUEEN.ending.title) || title;
        parts.push({ text: (QUEEN.ending && QUEEN.ending.text) || QUEEN.message || 'An alternate ending claims you.' });
    }

    const body = parts.map(p =>
        (p.heading ? `<h3>${esc(p.heading)}</h3>` : '') +
        `<p class="end-text${p.strong ? ' end-strong' : ''}">${esc(p.text)}</p>`).join('');

    gameState.endInfo = { reason, kind, title, html: body };
    refreshAll();
    saveGameState();
}

function endScreenHtml(info) {
    return `<div class="game-end ${esc(info.kind)}" role="alert">
        <h2>${esc(info.title)}</h2>
        ${info.html}
        <button class="btn-newgame" onclick="newGame()">${esc(LABELS.new_game_label || 'Begin Another Game')}</button>
    </div>`;
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
function notify(msg) {
    const n = el('notice');
    if (n) n.textContent = msg || '';
}

function updateTokenDisplay() {
    const v = el('tokenValue');
    const n = el('tokenName');
    if (v) v.textContent = gameState.tokens;
    if (n) n.textContent = TOKEN_NAME;
}

function updateStabilityDisplay() {
    if (!STAB) return;
    const tier = riskTier(gameState.stability);
    const v = el('stabilityValue');
    const n = el('stabilityName');
    if (v) {
        v.textContent = gameState.stability;
        v.className = 'stability-' + tier;
    }
    if (n) n.textContent = STAB_NAME;

    const bar = el('stabilityBar');
    if (bar) {
        const pct = Math.max(0, Math.min(100, (gameState.stability / STAB.initial) * 100));
        bar.style.width = pct + '%';
        bar.className = 'stability-fill' + (tier === 'safe' ? '' : ' ' + tier);
        const wrap = bar.parentElement;
        if (wrap) wrap.setAttribute('aria-valuenow', String(Math.max(0, gameState.stability)));
    }
    const note = el('stabilityNote');
    if (note) note.textContent = gameState.stabilityNote || '';
}

function updateDeckDisplay() {
    const c = el('deckCount');
    if (c) c.textContent = gameState.deck.length;
    const q = el('queenCount');
    if (q && QUEEN) q.textContent = gameState.queens;
}

function updateHistoryDisplay() {
    const h = el('cardHistory');
    if (!h) return;
    h.innerHTML = gameState.cardHistory.slice(-10).reverse().map(card => {
        const red = card.suit === 'hearts' || card.suit === 'diamonds';
        return `<div class="history-item ${red ? 'red-suit' : ''}">${SUIT_SYMBOLS[card.suit]} ${esc(card.value)}</div>`;
    }).join('');
}

function updateTurnDisplay() {
    const box = el('cardCountResult');
    if (!box) return;
    box.style.display = gameState.cardsToDraw > 0 ? 'block' : 'none';
    const a = el('cardsToDraw');
    const b = el('cardsDrawnCount');
    if (a) a.textContent = gameState.cardsToDraw;
    if (b) b.textContent = gameState.cardsDrawnThisTurn;
}

function updateCardsDrawnDisplay() {
    const container = el('cardsDrawnArea');
    if (!container) return;

    if (gameState.drawnCards.length === 0) {
        container.className = 'cards-drawn-area empty';
        container.innerHTML = '<div class="empty-cards-message">No cards drawn yet. Roll the turn dice and draw cards to begin.</div>';
        return;
    }
    container.className = 'cards-drawn-area';
    container.innerHTML = gameState.drawnCards.map((obj, index) => {
        const card = obj.card;
        const red = card.suit === 'hearts' || card.suit === 'diamonds';
        const classes = ['drawn-card', red ? 'red-card' : 'black-card',
            obj.resolved ? 'resolved' : '', gameState.activeCardIndex === index ? 'active' : ''].join(' ');
        return `<div class="${classes}" role="button" tabindex="0"
                    aria-label="${esc(card.value)} of ${esc(card.suit)}${obj.resolved ? ', resolved' : ''}"
                    onclick="viewCard(${index})"
                    onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();viewCard(${index});}">
                ${obj.resolved ? '<div class="drawn-card-resolved-badge">✓</div>' : ''}
                <div class="drawn-card-value">${esc(card.value)}</div>
                <div class="drawn-card-suit">${SUIT_SYMBOLS[card.suit]}</div>
            </div>`;
    }).join('');
}

function cardPromptHtml(index) {
    const obj = gameState.drawnCards[index];
    const { suit, value } = obj.card;
    const data = CARD_DATA[suit][value];
    const red = suit === 'hearts' || suit === 'diamonds';
    const suitInfo = ((MECH.deck && MECH.deck.suits) || {})[suit] || {};

    let html = `<h3 class="prompt-title ${red ? 'red-suit' : ''}">${SUIT_SYMBOLS[suit]} ${esc(value)} – ${esc(data.title)}</h3>`;
    if (suitInfo.name) html += `<p class="prompt-suit">${esc(suitInfo.name)}</p>`;
    html += `<div class="prompt-desc">${data.description_html || esc(data.description)}</div>`;

    const tokens = data.tokens || 0;
    const blocks = data.blocks || 0;
    let effects = '';
    if (TOK && tokens !== 0) effects += `<li>${signed(tokens)} ${esc(TOKEN_NAME)}</li>`;
    if (STAB && blocks > 0) effects += `<li>Pull ${blocks} ${plural(blocks, 'block', 'blocks')} (tests your ${esc(STAB_NAME)})</li>`;
    if (effects) html += `<ul class="effects">${effects}</ul>`;

    const spec = findSpecial(obj.card);
    const buttons = [];
    if (!obj.resolved) {
        if (effects && !obj.applied) {
            buttons.push(`<button class="game-action btn-apply" onclick="applyBasicCardEffects(${index})">Apply Effects</button>`);
        }
        if (spec && !obj.special) {
            const label = spec.button_label || `Roll ${spec.die || '1d6'}`;
            buttons.push(`<button class="game-action btn-apply" onclick="rollSpecial(${index})">${esc(label)}</button>`);
        }
        buttons.push(`<button class="game-action btn-done" onclick="markCardResolved(${index})">✓ Done with This Card</button>`);
    }

    if (obj.special) {
        html += `<p class="special-result ${obj.special.success ? 'good' : 'bad'}"><strong>${esc(obj.special.message)}</strong></p>`;
    }
    if (obj.log.length) {
        html += `<ul class="effect-log">${obj.log.map(l => `<li>${esc(l)}</li>`).join('')}</ul>`;
    }
    if (!obj.resolved && pendingEffects(obj)) {
        html += '<p class="hint">Write your response in the journal, then apply the effects.</p>';
    }
    if (obj.resolved) html += '<p class="hint">This card is resolved.</p>';
    return html + (buttons.length ? `<div class="prompt-buttons">${buttons.join('')}</div>` : '');
}

function hintHtml() {
    const g = gameState;
    if (g.cardsToDraw === 0) {
        const start = (GAME_CONFIG.flow && GAME_CONFIG.flow.starting_prompt) ||
            'Roll the turn dice to start, then draw and click cards to see their prompts.';
        return `<p class="hint start-prompt">${esc(start.trim())}</p>`;
    }
    const left = g.cardsToDraw - g.cardsDrawnThisTurn;
    if (left > 0) {
        return `<p class="hint">Draw ${left} more ${plural(left, 'card', 'cards')}, then click a card to read its prompt.</p>`;
    }
    const open = g.drawnCards.filter(c => !c.resolved).length;
    if (open > 0) {
        return `<p class="hint">${open} ${plural(open, 'card', 'cards')} remaining. Click any unresolved card to continue.</p>`;
    }
    return '<p class="hint done">All cards resolved! Roll to start your next turn.</p>';
}

function renderPromptPanel() {
    const panel = el('cardPrompt');
    if (!panel) return;
    if (gameState.gameEnded && gameState.endInfo) {
        panel.innerHTML = endScreenHtml(gameState.endInfo);
    } else if (gameState.activeCardIndex !== null && gameState.drawnCards[gameState.activeCardIndex]) {
        panel.innerHTML = cardPromptHtml(gameState.activeCardIndex);
    } else {
        panel.innerHTML = hintHtml();
    }
}

function updateButtonState() {
    document.querySelectorAll('.game-action').forEach(btn => { btn.disabled = gameState.gameEnded; });
}

function refreshAll() {
    updateTokenDisplay();
    updateStabilityDisplay();
    updateDeckDisplay();
    updateHistoryDisplay();
    updateTurnDisplay();
    updateCardsDrawnDisplay();
    renderPromptPanel();
    updateButtonState();
}

function clearHistory() {
    gameState.cardHistory = [];
    updateHistoryDisplay();
    saveGameState();
}

// ---------------------------------------------------------------------------
// Persistence
// ---------------------------------------------------------------------------
function saveGameState() {
    store.set(STORAGE_KEY, JSON.stringify(gameState));
}

function loadGameState() {
    const raw = store.get(STORAGE_KEY);
    if (!raw) return false;
    let s;
    try { s = JSON.parse(raw); } catch (e) { return false; }
    if (!s || s.v !== STATE_VERSION) return false;

    const fresh = freshState();
    const num = (v, d) => (typeof v === 'number' && Number.isFinite(v)) ? v : d;  // 0 is a valid value
    gameState = Object.assign(fresh, {
        tokens: num(s.tokens, fresh.tokens),
        stability: num(s.stability, fresh.stability),
        gameEnded: s.gameEnded === true,
        endInfo: s.endInfo && typeof s.endInfo.html === 'string' ? s.endInfo : null,
        cardsToDraw: num(s.cardsToDraw, 0),
        cardsDrawnThisTurn: num(s.cardsDrawnThisTurn, 0),
        queens: num(s.queens, 0),
        turn: num(s.turn, 0),
        stabilityNote: typeof s.stabilityNote === 'string' ? s.stabilityNote : ''
    });
    gameState.deck = Array.isArray(s.deck) ? s.deck.filter(isValidCard) : [];
    gameState.cardHistory = Array.isArray(s.cardHistory) ? s.cardHistory.filter(isValidCard) : [];
    gameState.drawnCards = Array.isArray(s.drawnCards)
        ? s.drawnCards.filter(o => o && isValidCard(o.card)).map(o => ({
            card: o.card, resolved: o.resolved === true, applied: o.applied === true,
            special: o.special || null, log: Array.isArray(o.log) ? o.log.map(String) : []
        }))
        : [];
    const idx = s.activeCardIndex;
    gameState.activeCardIndex = (Number.isInteger(idx) && idx >= 0 && idx < gameState.drawnCards.length) ? idx : null;

    // A game flagged as ended but missing its end screen: re-derive the ending.
    if (gameState.gameEnded && !gameState.endInfo) {
        gameState.gameEnded = false;
        checkGameEnd();
    }
    return true;
}

function newGame() {
    const confirmNeeded = !UI.controls || UI.controls.new_game_confirmation !== false;
    if (confirmNeeded && !confirm('Start a new game? This erases your progress and your journal. (Use "Save to File" first if you want to keep it.)')) {
        return;
    }
    store.remove(STORAGE_KEY);
    store.remove(JOURNAL_KEY);
    location.reload();
}

// ---------------------------------------------------------------------------
// Journal
// ---------------------------------------------------------------------------
const JOURNAL_AUTOSAVE = !UI.journal || UI.journal.autosave !== false;
const SAVE_INDICATOR = !UI.journal || UI.journal.save_indicator !== false;
let journalTimer = null;

function saveJournal() {
    const j = el('journal');
    if (!j) return;
    const ok = store.set(JOURNAL_KEY, j.value);
    const ind = el('saveIndicator');
    if (ind && SAVE_INDICATOR) {
        ind.textContent = ok ? 'Saved ✓ ' + new Date().toLocaleTimeString() : 'Could not save (browser storage unavailable)';
    }
}

function autoSaveJournal() {
    if (!JOURNAL_AUTOSAVE) return;
    clearTimeout(journalTimer);
    journalTimer = setTimeout(saveJournal, 600);
}

function downloadJournal() {
    const j = el('journal');
    if (!j) return;
    saveJournal();
    const blob = new Blob([j.value], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${GAME_META.slug}-journal-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function loadJournalFile(event) {
    const file = event.target.files && event.target.files[0];
    const j = el('journal');
    if (!file || !j) return;
    if (j.value.trim() && !confirm('Replace the current journal text with the contents of this file?')) {
        event.target.value = '';
        return;
    }
    const reader = new FileReader();
    reader.onload = () => {
        j.value = String(reader.result || '');
        saveJournal();
        event.target.value = '';
    };
    reader.readAsText(file);
}

// ---------------------------------------------------------------------------
// Startup
// ---------------------------------------------------------------------------
function initGame() {
    if (!loadGameState()) {
        gameState = freshState();
        initializeDeck();
    } else if (!gameState.gameEnded && gameState.deck.length === 0 && gameState.drawnCards.length === 0) {
        initializeDeck();   // saved state had no usable deck
    }

    const j = el('journal');
    if (j) {
        const saved = store.get(JOURNAL_KEY);
        if (saved !== null) j.value = saved;
        j.addEventListener('input', autoSaveJournal);
    }

    refreshAll();
    saveGameState();
    if (!gameState.gameEnded) checkGameEnd();
    checkWin();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGame);
} else {
    initGame();
}
