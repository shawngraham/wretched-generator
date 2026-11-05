"""
Wretched & Alone Game Generator
Core builder module

GameBuilder turns a game directory (config.yaml, cards.yaml, theme.yaml, story.md)
into a single self-contained HTML file:

- loads and normalises the configuration files
- validates them (errors stop the build, warnings do not)
- generates CSS from the theme, and the JavaScript engine from templates/engine.js
- renders templates/base.html
"""

import copy
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / 'templates'
THEMES_DIR = ROOT / 'themes'

SUITS = ['spades', 'hearts', 'diamonds', 'clubs']
VALUES = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
SUIT_SYMBOLS = {'spades': '\u2660', 'hearts': '\u2665', 'diamonds': '\u2666', 'clubs': '\u2663'}
RANK_NAMES = {'A': 'ace', 'K': 'king', 'Q': 'queen', 'J': 'jack', '10': 'ten', '9': 'nine',
              '8': 'eight', '7': 'seven', '6': 'six', '5': 'five', '4': 'four', '3': 'three', '2': 'two'}

REQUIRED_THEME_COLORS = ['primary', 'secondary', 'tertiary', 'accent_primary',
                         'text_primary', 'text_secondary', 'borders']

# Defaults merged under whatever config.yaml provides.
DEFAULT_CONFIG: Dict[str, Any] = {
    'game': {},
    'mechanics': {
        'systems': ['dice', 'cards', 'stability', 'tokens'],
        'tokens': {
            'initial': 10, 'name': 'Tokens', 'allow_negative': True,
            'controls': {'show_manual_adjust': True, 'increment': 1},
        },
        'stability': {
            'initial': 100, 'name': 'Stability', 'risk_scaling': True,
            'thresholds': {'critical': 20, 'danger': 50},
            'failure_thresholds': {'critical': 3, 'danger': 2, 'safe': 1},
            'messages': {},
        },
        'deck': {'reshuffle': True, 'track_history': True, 'show_remaining_count': True, 'suits': {}},
        'dice': {
            'main': {'count': 2, 'sides': 6},
            'binary': {'split': 3, 'negative': 'Negative Outcome', 'positive': 'Positive Outcome'},
            'interpret': [
                {'max': 5, 'label': 'Low / Troubling'},
                {'max': 8, 'label': 'Middling / Ambiguous'},
                {'max': 12, 'label': 'High / Favourable'},
            ],
        },
    },
    'conditions': {},
    'ui': {
        'panels': {'show_instructions': True, 'show_help_button': False, 'show_card_reference': False},
        'journal': {
            'placeholder': 'Write your journal here...', 'autosave': True, 'save_indicator': True,
            'download_button': True, 'load_button': True,
        },
        'controls': {'new_game_confirmation': True, 'show_card_history': True, 'history_clear_button': False},
        'labels': {
            'turn_heading': 'Start Your Turn', 'turn_flavor': '',
            'new_game_label': 'Begin Another Game', 'game_over_title': 'Game Over', 'win_title': 'The End',
        },
    },
    'special': {},
    'flow': {},
    'locale': {'language': 'en'},
    'build': {'minify': False},
}

# Keys that older docs and examples mention but that this generator does not act on.
# They are reported as warnings by validate() so nobody expects them to work.
IGNORED_KEYS = [
    ('mechanics.tokens.count_up', 'tokens are always a plain number that cards and buttons add to or subtract from'),
    ('mechanics.tokens.display_type', 'tokens are always shown as a number'),
    ('mechanics.stability.narrative_flavor', 'not used'),
    ('ui.layout', 'the layout is always two columns (one column on narrow screens)'),
    ('flow.end_turn_button', 'turns end when you roll again'),
    ('flow.auto_advance', 'not used'),
    ('locale.date_format', 'not used'),
    ('locale.time_format', 'not used'),
    ('build.inline_assets', 'output is always a single self-contained file'),
    ('build.generate_print_version', 'not used (a print stylesheet is always included)'),
]


class ValidationError(Exception):
    """Raised when game configuration validation fails."""


class BuildError(Exception):
    """Raised when game building fails."""


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Return base with override merged on top (dicts merge, everything else replaces)."""
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def slugify(text: str, fallback: str = 'game') -> str:
    text = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return text or fallback


def parse_dice(spec: Any) -> Optional[tuple]:
    m = re.fullmatch(r'\s*(\d+)d(\d+)\s*', str(spec), re.IGNORECASE)
    return (int(m.group(1)), int(m.group(2))) if m else None


def js_json(obj: Any) -> str:
    """JSON that is safe to embed inside an HTML <script> element."""
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    return (text.replace('</', '<\\/').replace('<!--', '<\\!--')
                .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def available_themes() -> Dict[str, Path]:
    """Map theme name -> file for every themes/theme-*.yaml."""
    return {p.stem[len('theme-'):]: p for p in sorted(THEMES_DIR.glob('theme-*.yaml'))}


class GameBuilder:
    """
    Builds a Wretched & Alone style game from a directory of config files.

    Example:
        >>> builder = GameBuilder('example-game')
        >>> output = builder.build()
    """

    def __init__(self, game_path: Any, theme_file: Optional[Any] = None):
        self.game_path = Path(game_path)
        self.theme_file = Path(theme_file) if theme_file else None
        self.config: Optional[Dict[str, Any]] = None
        self.cards: Optional[Dict[str, Any]] = None
        self.special_cards: Dict[str, Any] = {}
        self.theme: Optional[Dict[str, Any]] = None
        self.story: Optional[str] = None
        self.warnings: List[str] = []

    # ------------------------------------------------------------------ loading

    def _read_yaml(self, path: Path, label: str) -> Any:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"{label} not found: {path}\nMake sure {path.name} exists in {path.parent}")
        except yaml.YAMLError as e:
            raise BuildError(f"Invalid YAML in {path.name}: {e}")

    def load_config(self) -> Dict[str, Any]:
        """Load config.yaml and merge it over DEFAULT_CONFIG."""
        raw = self._read_yaml(self.game_path / 'config.yaml', 'Config file')
        if not isinstance(raw, dict):
            raise BuildError("config.yaml must contain a YAML mapping (key: value pairs)")
        self.config = deep_merge(DEFAULT_CONFIG, raw)
        self._raw_config = raw
        return self.config

    def load_cards(self) -> Dict[str, Any]:
        """
        Load cards.yaml. Rank keys are normalised to strings (YAML reads an unquoted
        `10:` as an integer), the optional `special_cards` section is split off, and each
        card's description is converted from Markdown to HTML.
        """
        raw = self._read_yaml(self.game_path / 'cards.yaml', 'Cards file')
        if not isinstance(raw, dict):
            raise BuildError("cards.yaml must contain a YAML mapping of suits")
        self.special_cards = raw.get('special_cards') or {}
        cards: Dict[str, Any] = {}
        for suit, ranks in raw.items():
            if str(suit).lower() not in SUITS:
                continue
            cards[str(suit).lower()] = {
                str(rank).strip(): self._normalise_card(card) for rank, card in (ranks or {}).items()
            } if isinstance(ranks, dict) else ranks
        self._raw_cards = raw
        self.cards = cards
        return self.cards

    @staticmethod
    def _normalise_card(card: Any) -> Any:
        if not isinstance(card, dict):
            return card
        card = dict(card)
        desc = str(card.get('description') or '').strip()
        card['description'] = desc
        card['description_html'] = markdown.markdown(desc) if desc else ''
        for field in ('tokens', 'blocks'):
            card.setdefault(field, 0)
        return card

    def load_theme(self) -> Dict[str, Any]:
        path = self.theme_file or (self.game_path / 'theme.yaml')
        raw = self._read_yaml(path, 'Theme file')
        if not isinstance(raw, dict):
            raise BuildError(f"{path.name} must contain a YAML mapping")
        self.theme = raw
        return self.theme

    def load_story(self) -> str:
        story_file = self.game_path / 'story.md'
        try:
            md_content = story_file.read_text(encoding='utf-8')
        except FileNotFoundError:
            raise FileNotFoundError(f"Story file not found: {story_file}\nMake sure story.md exists in {self.game_path}")
        self.story = markdown.markdown(md_content, extensions=['extra', 'nl2br', 'sane_lists'])
        return self.story

    def load_all(self) -> None:
        self.load_config()
        self.load_cards()
        self.load_theme()
        self.load_story()

    def _ensure_loaded(self) -> None:
        if self.config is None:
            self.load_config()
        if self.cards is None:
            self.load_cards()
        if self.theme is None:
            self.load_theme()
        if self.story is None:
            self.load_story()

    # --------------------------------------------------------------- validation

    def count_cards(self) -> int:
        """Number of standard playing cards defined (special_cards is not a suit)."""
        return sum(len(v) for v in (self.cards or {}).values() if isinstance(v, dict))

    def validate(self) -> List[str]:
        """
        Check everything that was loaded. Returns a list of error strings (empty = OK).
        Non-fatal problems are collected in self.warnings.
        """
        errors: List[str] = []
        self.warnings = []

        if not self.config:
            errors.append("Config file not loaded - call load_config() first")
        if not self.cards:
            errors.append("Cards file not loaded - call load_cards() first")
        if not self.theme:
            errors.append("Theme file not loaded - call load_theme() first")

        if self.config:
            errors += self._validate_config(self.config)
        if self.cards:
            errors += self._validate_cards(self.cards)
        if self.theme:
            errors += self._validate_theme(self.theme)
        return errors

    def _validate_config(self, cfg: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        raw = getattr(self, '_raw_config', cfg)

        for field in ('game', 'mechanics'):
            if field not in raw:
                errors.append(f"Missing required config field: {field}")
        game = cfg.get('game') or {}
        for field in ('title', 'author'):
            if not game.get(field):
                errors.append(f"Missing required game field: {field}")

        mech = cfg['mechanics']
        systems = mech.get('systems')
        if not isinstance(systems, list):
            errors.append("mechanics.systems must be a list")
            systems = []
        if 'cards' not in systems:
            errors.append("mechanics.systems must include 'cards'")
        for s in systems:
            if s not in ('dice', 'cards', 'stability', 'tokens'):
                self.warnings.append(f"mechanics.systems: unknown system '{s}' is ignored")

        def is_int(v):
            return isinstance(v, int) and not isinstance(v, bool)

        if 'tokens' in systems:
            t = mech['tokens']
            if not is_int(t.get('initial')):
                errors.append("mechanics.tokens.initial must be a whole number")
            if not is_int((t.get('controls') or {}).get('increment', 1)):
                errors.append("mechanics.tokens.controls.increment must be a whole number")

        if 'stability' in systems:
            st = mech['stability']
            init = st.get('initial')
            if not is_int(init) or init < 1:
                errors.append("mechanics.stability.initial must be a whole number of at least 1")
            else:
                th = st.get('thresholds') or {}
                crit, dang = th.get('critical'), th.get('danger')
                if not (is_int(crit) and is_int(dang)):
                    errors.append("mechanics.stability.thresholds.critical and .danger must be whole numbers")
                elif not (0 <= crit <= dang < init):
                    errors.append("mechanics.stability.thresholds must satisfy 0 <= critical <= danger < initial")
            for key, val in (st.get('failure_thresholds') or {}).items():
                if not (is_int(val) and 1 <= val <= 6):
                    errors.append(f"mechanics.stability.failure_thresholds.{key} must be a whole number from 1 to 6")
            pool = st.get('pool_size')
            if pool is not None and not (is_int(pool) and pool >= 1):
                errors.append("mechanics.stability.pool_size must be a whole number of at least 1")

        main = (mech.get('dice') or {}).get('main') or {}
        count, sides = main.get('count'), main.get('sides')
        if not (is_int(count) and count >= 1 and is_int(sides) and sides >= 2):
            errors.append("mechanics.dice.main needs count >= 1 and sides >= 2")
        else:
            seq = cfg.get('special', {}).get('turn_sequence') or {}
            lo = seq.get('min_cards', count)
            hi = seq.get('max_cards', count * sides)
            if not (is_int(lo) and is_int(hi) and 1 <= lo <= hi):
                errors.append("special.turn_sequence: min_cards and max_cards must be whole numbers with 1 <= min <= max")
        interp = (mech.get('dice') or {}).get('interpret')
        if interp is not None:
            if not (isinstance(interp, list) and interp and all(
                    isinstance(i, dict) and is_int(i.get('max')) and i.get('label') for i in interp)):
                errors.append("mechanics.dice.interpret must be a list of {max: number, label: text}")

        cond = cfg.get('conditions') or {}
        for w in cond.get('win') or []:
            if w.get('type') != 'deck_empty':
                self.warnings.append(f"conditions.win: type '{w.get('type')}' is not supported and is ignored")
            for chk in w.get('additional_checks') or []:
                if chk not in ('tokens_positive', 'stability_above_zero'):
                    self.warnings.append(f"conditions.win.additional_checks: '{chk}' is not supported and is ignored")
        for l in cond.get('lose') or []:
            if l.get('type') not in ('stability_zero', 'tokens_zero'):
                self.warnings.append(f"conditions.lose: type '{l.get('type')}' is not supported and is ignored")

        for dotted, why in IGNORED_KEYS:
            node: Any = raw
            for part in dotted.split('.'):
                node = node.get(part) if isinstance(node, dict) else None
                if node is None:
                    break
            if node is not None:
                self.warnings.append(f"{dotted} has no effect: {why}")
        return errors

    def _validate_cards(self, cards: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        raw = getattr(self, '_raw_cards', {})
        for suit in raw:
            if suit not in SUITS and suit != 'special_cards':
                self.warnings.append(f"cards.yaml: unknown top-level key '{suit}' is ignored")

        special_keys = set(self.special_cards or {})
        for suit in SUITS:
            if suit not in cards:
                errors.append(f"Missing suit: {suit}")
                continue
            if not isinstance(cards[suit], dict):
                errors.append(f"Suit {suit} must be a mapping of card values")
                continue
            for extra in cards[suit]:
                if extra not in VALUES:
                    self.warnings.append(f"cards.yaml: '{extra}' of {suit} is not a valid card value and is ignored")
            for value in VALUES:
                if value not in cards[suit]:
                    errors.append(f"Missing card: {value} of {suit}")
                    continue
                card = cards[suit][value]
                if not isinstance(card, dict):
                    errors.append(f"Invalid card data for {value} of {suit}")
                    continue
                for field in ('title', 'description'):
                    if not card.get(field):
                        errors.append(f"Card {value} of {suit} missing required field: {field}")
                for field in ('tokens', 'blocks'):
                    v = card.get(field, 0)
                    if not (isinstance(v, int) and not isinstance(v, bool)):
                        errors.append(f"Card {value} of {suit}: {field} must be a whole number")
                    elif field == 'blocks' and v < 0:
                        errors.append(f"Card {value} of {suit}: blocks cannot be negative")
                sp = card.get('special')
                auto = f"{RANK_NAMES[value]}_of_{suit}"
                if sp and sp not in special_keys and auto not in special_keys:
                    self.warnings.append(
                        f"Card {value} of {suit}: special '{sp}' matches nothing in special_cards and is ignored")

        for key, spec in (self.special_cards or {}).items():
            if not isinstance(spec, dict) or spec.get('type') != 'roll_check':
                self.warnings.append(f"special_cards.{key}: only type 'roll_check' is supported; entry is ignored")
                continue
            if spec.get('die') is not None and parse_dice(spec['die']) is None:
                errors.append(f"special_cards.{key}.die must look like '1d6'")
            if not (isinstance(spec.get('on_success'), dict) and isinstance(spec.get('on_failure'), dict)):
                errors.append(f"special_cards.{key} needs on_success and on_failure")
        return errors

    def _validate_theme(self, theme: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        t = theme.get('theme')
        if not isinstance(t, dict):
            return ["theme.yaml must have a top-level 'theme:' section"]
        colors = t.get('colors') or {}
        missing = [c for c in REQUIRED_THEME_COLORS if c not in colors]
        if missing:
            errors.append("theme.colors is missing: " + ', '.join(missing))
        return errors

    # ---------------------------------------------------------------- generation

    @staticmethod
    def _google_fonts_url(fonts: List[Any]) -> Optional[str]:
        families = []
        for font in fonts or []:
            if isinstance(font, dict):
                family = str(font.get('family', '')).strip()
                if not family:
                    continue
                weights = sorted({int(w) for w in font.get('weights', [400])})
                styles = font.get('styles', ['normal'])
                axes = []
                for ital in (0, 1):
                    if ital == 1 and 'italic' not in styles:
                        continue
                    if ital == 0 and 'normal' not in styles and 'italic' in styles:
                        continue
                    axes += [(ital, w) for w in weights]
                spec = ';'.join(f"{i},{w}" for i, w in axes)
                families.append(f"family={family.replace(' ', '+')}:ital,wght@{spec}")
            elif font:
                families.append(f"family={str(font).replace(' ', '+')}")
        if not families:
            return None
        return 'https://fonts.googleapis.com/css2?' + '&'.join(families) + '&display=swap'

    def generate_css(self) -> str:
        """Theme variables + templates/base.css + the theme's custom_css."""
        self._ensure_theme_and_config()
        theme = self.theme.get('theme') or {}
        colors = theme.get('colors') or {}
        fonts = theme.get('fonts') or {}
        layout = theme.get('layout') or {}

        parts: List[str] = []
        url = self._google_fonts_url(fonts.get('google_fonts', []))
        if url:
            parts.append(f"@import url('{url}');")

        left = (self.config.get('ui', {}).get('panels') or {}).get('left_width')
        columns = layout.get('grid_columns') or (f"{left} 1fr" if left else '400px 1fr')

        root = [':root {']
        for key, value in colors.items():
            if isinstance(value, dict):
                for sub, subval in value.items():
                    root.append(f"  --color-{key}-{sub}: {subval};")
            else:
                root.append(f"  --color-{key}: {value};")
        for key, value in fonts.items():
            if key not in ('google_fonts', 'sizes', 'line_heights', 'letter_spacing') and isinstance(value, str):
                root.append(f"  --font-{key}: {value};")
        root.append(f"  --layout-max-width: {layout.get('container_max_width', '1600px')};")
        root.append(f"  --layout-columns: {columns};")
        root.append(f"  --layout-gap: {layout.get('grid_gap', '30px')};")
        root.append('}')
        parts.append('\n'.join(root))

        parts.append((TEMPLATES_DIR / 'base.css').read_text(encoding='utf-8'))

        # custom_css / custom_js sit at the top level of theme files (next to `theme:`);
        # accept them nested inside `theme:` too.
        custom = self.theme.get('custom_css') or theme.get('custom_css')
        if custom:
            parts.append('/* Custom CSS */\n' + str(custom))
        return '\n\n'.join(parts)

    def _ensure_theme_and_config(self) -> None:
        if self.config is None:
            self.load_config()
        if self.theme is None:
            self.load_theme()

    def _storage_key(self) -> str:
        return 'wretched:' + slugify(self.config['game']['title'])

    def generate_javascript(self) -> str:
        """Fill templates/engine.js with this game's config and cards."""
        if self.config is None:
            self.load_config()
        if self.cards is None:
            self.load_cards()
        engine = (TEMPLATES_DIR / 'engine.js').read_text(encoding='utf-8')
        meta = {'storageKey': self._storage_key(), 'slug': slugify(self.config['game']['title'])}
        replacements = {
            '__WRETCHED_CONFIG__': js_json(self.config),
            '__WRETCHED_CARDS__': js_json(self.cards),
            '__WRETCHED_SPECIAL_CARDS__': js_json(self.special_cards or {}),
            '__WRETCHED_META__': js_json(meta),
        }
        for placeholder, value in replacements.items():
            if placeholder not in engine:
                raise BuildError(f"engine.js is missing placeholder {placeholder}")
            engine = engine.replace(placeholder, value)
        return engine

    def _template_context(self) -> Dict[str, Any]:
        cfg = self.config
        mech = cfg['mechanics']
        main = mech['dice']['main']
        count, sides = main['count'], main['sides']
        seq = cfg.get('special', {}).get('turn_sequence') or {}

        binary = mech['dice']['binary']
        split = binary['split']
        binary_text = f"1\u2013{split} = {binary['negative']}, {split + 1}\u20136 = {binary['positive']}"

        lo, parts = 2, []
        for tier in mech['dice']['interpret']:
            parts.append(f"{lo}\u2013{tier['max']} = {tier['label']}")
            lo = tier['max'] + 1

        bands = []
        if 'stability' in mech['systems']:
            st = mech['stability']
            th, ft, init = st['thresholds'], st['failure_thresholds'], st['initial']

            def lose_on(n):
                return 'a 1' if n == 1 else f'1\u2013{n}'
            if st.get('risk_scaling', True):
                bands = [
                    f"{th['danger'] + 1}\u2013{init}: normal risk (a die is lost on {lose_on(ft.get('safe', 1))})",
                    f"{th['critical'] + 1}\u2013{th['danger']}: high risk (a die is lost on {lose_on(ft.get('danger', 2))})",
                    f"1\u2013{th['critical']}: CRITICAL risk (a die is lost on {lose_on(ft.get('critical', 3))})",
                ]
            else:
                bands = [f"Constant risk (a die is lost on {lose_on(ft.get('safe', 1))})"]

        suit_cfg = mech['deck'].get('suits') or {}
        suit_reference = []
        for suit in SUITS:
            info = suit_cfg.get(suit) or {}
            suit_reference.append({
                'symbol': SUIT_SYMBOLS[suit],
                'red': suit in ('hearts', 'diamonds'),
                'name': info.get('name') or suit.capitalize(),
                'description': info.get('description', ''),
            })

        queen = (cfg.get('special') or {}).get('queen_tracker') or {}
        return {
            'config': cfg,
            'labels': cfg['ui']['labels'],
            'turn_dice': f"{count}d{sides}",
            'min_cards': seq.get('min_cards', count),
            'max_cards': seq.get('max_cards', count * sides),
            'binary_text': binary_text,
            'interpret_text': ', '.join(parts),
            'risk_bands': bands,
            'suit_reference': suit_reference,
            'show_history': bool(mech['deck'].get('track_history')) and
                            cfg['ui']['controls'].get('show_card_history', True) is not False,
            'queen_tracker': bool(queen.get('enabled')),
            'queen_threshold': queen.get('threshold', 4),
        }

    def render(self) -> str:
        self._ensure_loaded()
        css = self.generate_css()
        js = self.generate_javascript()
        if not TEMPLATES_DIR.exists():
            raise BuildError(f"Templates directory not found: {TEMPLATES_DIR}")
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
        template = env.get_template('base.html')
        custom_js = self.theme.get('custom_js') or (self.theme.get('theme') or {}).get('custom_js')
        ctx = self._template_context()
        return template.render(story=self.story, css=css, js=js, custom_js=custom_js, **ctx)

    # ------------------------------------------------------------------- output

    @staticmethod
    def minify_html(html: str) -> str:
        """
        Conservative built-in minifier (no extra dependency). Removes HTML and CSS
        comments, indentation and blank lines; leaves <pre>/<textarea> alone and never
        joins JavaScript lines.
        """
        pattern = re.compile(r'(<pre\b.*?</pre>|<textarea\b.*?</textarea>|<script\b.*?</script>|<style\b.*?</style>)',
                             re.DOTALL | re.IGNORECASE)

        def squeeze(text: str) -> str:
            lines = [ln.strip() for ln in text.splitlines()]
            return '\n'.join(ln for ln in lines if ln)

        out = []
        for chunk in pattern.split(html):
            low = chunk[:8].lower()
            if low.startswith('<pre') or low.startswith('<textare'):
                out.append(chunk)
            elif low.startswith('<script'):
                chunk = re.sub(r'^[ \t]*/\*.*?\*/[ \t]*$', '', chunk, flags=re.DOTALL | re.MULTILINE)
                chunk = re.sub(r'^[ \t]*//.*$', '', chunk, flags=re.MULTILINE)
                out.append(squeeze(chunk))
            elif low.startswith('<style'):
                chunk = re.sub(r'/\*.*?\*/', '', chunk, flags=re.DOTALL)
                out.append(squeeze(chunk))
            else:
                chunk = re.sub(r'<!--.*?-->', '', chunk, flags=re.DOTALL)
                out.append(squeeze(chunk))
        return '\n'.join(s for s in out if s)

    def build(self, output_path: Optional[Any] = None, minify: Optional[bool] = None) -> Path:
        """
        Validate and build the game. `minify=None` follows config.yaml build.minify.
        """
        try:
            self._ensure_loaded()
            errors = self.validate()
            if errors:
                raise ValidationError(
                    f"Validation failed with {len(errors)} error(s):\n" + "\n".join(f"  - {e}" for e in errors))

            html = self.render()
            if minify is None:
                minify = bool(self.config.get('build', {}).get('minify'))
            if minify:
                html = self.minify_html(html)

            if not output_path:
                output_path = self.game_path / f"{slugify(self.config['game']['title'])}.html"
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding='utf-8')
            return output_path
        except (FileNotFoundError, ValidationError, BuildError):
            raise
        except Exception as e:
            raise BuildError(f"Build failed: {type(e).__name__}: {e}")


# ----------------------------------------------------------------- new projects

def create_project(dest: Any, theme: str = 'dark-archaeology', from_example: bool = False) -> Path:
    """
    Create a new game project.

    By default this is a blank starter: generic rules text, placeholder prompts for all
    52 cards, and the chosen theme. With from_example=True the finished example game
    is copied instead.
    """
    import shutil
    dest = Path(dest)
    if dest.exists():
        raise BuildError(f"Directory already exists: {dest}")

    themes = available_themes()
    if theme not in themes:
        raise BuildError(f"Unknown theme '{theme}'. Available: {', '.join(themes) or '(none)'}")

    if from_example:
        shutil.copytree(ROOT / 'example-game', dest, ignore=shutil.ignore_patterns('*.html', '__pycache__'))
        shutil.copyfile(themes[theme], dest / 'theme.yaml')
        return dest

    dest.mkdir(parents=True)
    starter = TEMPLATES_DIR / 'starter'
    shutil.copyfile(starter / 'config.yaml', dest / 'config.yaml')
    shutil.copyfile(starter / 'story.md', dest / 'story.md')
    shutil.copyfile(themes[theme], dest / 'theme.yaml')

    names = {'spades': 'Spades', 'hearts': 'Hearts', 'diamonds': 'Diamonds', 'clubs': 'Clubs'}
    lines = ["# Write one prompt for every card. Quote rank keys like \"10\".",
             "# Each card needs a title and description (Markdown allowed).",
             "# tokens: change to your token count (+/-), blocks: how many tower blocks to pull.", ""]
    for suit in SUITS:
        lines.append(f"{suit}:")
        for value in VALUES:
            lines += [f"  \"{value}\":",
                      f"    title: \"{names[suit]} {value}: replace this title\"",
                      "    description: |",
                      f"      Write the prompt for the {value} of {suit} here.",
                      "    tokens: 0",
                      "    blocks: 0"]
        lines.append("")
    (dest / 'cards.yaml').write_text('\n'.join(lines), encoding='utf-8')
    return dest
