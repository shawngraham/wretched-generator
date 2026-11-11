# Wretched & Alone Game Generator

A static site generator for solo journaling RPGs in the "Wretched & Alone" style. In this kind of game you will most likely die wretched and alone, but how you get there is up to you. Roll the dice, draw cards, follow the prompts, write your story.

You write four plain-text files. You get one self-contained HTML game that works offline in any browser.

| You write | It controls |
|---|---|
| `config.yaml` | rules, dice, the tower, tokens, win/lose conditions, UI options |
| `cards.yaml` | the 52 card prompts, their effects, and special card rolls |
| `theme.yaml` | colours, fonts, layout, optional custom CSS/JS |
| `story.md` | the introduction and rules shown in the game |

This work is based on [The Wretched](http://loottheroom.itch.io/wretched), product of Chris Bissette and Loot The Room, and licensed for our use under the [Creative Commons Attribution 3.0 Unported license](http://creativecommons.org/licenses/by/3.0/). Based on the "Wretched & Alone" system by Chris Bissette. The included example game, "What Lies Beneath", is by Shawn Graham.

## Quick start

```bash
pip install -r requirements.txt          # Python 3.9+; PyYAML, Jinja2, markdown

python3 cli/wretched.py build example-game
# -> example-game/what-lies-beneath.html   (open it in a browser)
```

Make your own game:

```bash
python3 cli/wretched.py new my-game                  # blank starter with 52 placeholder cards
python3 cli/wretched.py new my-game --theme arctic   # ...with another theme
python3 cli/wretched.py new my-game --from-example   # or start from the finished example

# edit my-game/config.yaml, cards.yaml, story.md, then:
python3 cli/wretched.py validate my-game
python3 cli/wretched.py build my-game
```

On Linux/macOS you can also run `./wretched build my-game` (a small wrapper around the same script).

## Commands

| Command | What it does |
|---|---|
| `new <dir> [-t THEME] [--from-example]` | Create a project. Default is a blank starter; `--from-example` copies the example game. |
| `build <dir> [-o FILE] [-t THEME] [-m \| --no-minify]` | Validate and build. Default output: `<dir>/<game-title>.html`. `--theme` takes a bundled name or a path and overrides `theme.yaml` for that build. Minification follows `build.minify` in config unless a flag overrides it. |
| `validate <dir>` | Report errors (build-blocking) and warnings (settings that have no effect). |
| `info <dir>` | Show title, author, mechanics and card count. |
| `themes` | List bundled themes. |

`--no-color` and `--debug` (full tracebacks) work before or after the command. Exit code is 0 on success, 1 on any failure.

## How the game plays

1. **Roll the turn dice** (default 2d6). The total is the number of cards to draw this turn (bounded by `special.turn_sequence`; set `max_cards: 6` for a six-card ceiling).
2. **Draw the cards** one at a time. Click a card to read its prompt; resolve them in any order.
3. **Journal** your response, then press **Apply Effects**. A card can change your tokens, pull blocks from the tower, or ask for a special roll (for example the Ace of Hearts).
4. **Pulling a block** rolls one die per point of the tower's current stability. Every die at or under the current risk number is lost; you always lose at least one. The risk number rises as stability falls (see `failure_thresholds`).
5. **The game ends** when stability reaches 0 (collapse), when tokens reach 0 (if configured), when the Queen tracker triggers (if enabled), or when you **resolve every card in the deck** (the win condition).

Progress and journal are saved automatically in the browser (one save per game title). A finished game is restored exactly as you left it after a reload.

## Configuration reference

All keys are optional unless marked *required*. Anything omitted falls back to a default. `wretched validate` tells you about mistakes and about keys that have no effect.

### `game`
`title` *(required)*, `author` *(required)*, `subtitle`, `version`, `description`.

### `mechanics`
```yaml
mechanics:
  systems: [dice, cards, stability, tokens]   # must include "cards"; remove "stability"/"tokens" to switch them off

  stability:                                  # the tower
    initial: 100
    name: "Academic Credibility"
    thresholds: {critical: 20, danger: 50}    # tier boundaries: <=critical, <=danger, otherwise safe
    failure_thresholds: {critical: 3, danger: 2, safe: 1}   # a die is lost on a roll <= this
    risk_scaling: true                        # false = always use the "safe" number
    pool_size: 10                             # optional: fixed pool of N dice instead of one per point
    min_loss: 1                               # optional: minimum lost per pull (default 1)
    messages: {safe: [...], danger: [...], critical: [...]}   # shown after each pull (random pick)
    collapse_message: "Your reputation is ruined."

  tokens:
    initial: 10
    name: "Evidence Fragments"
    allow_negative: true                      # false = clamp at 0
    controls: {show_manual_adjust: true, increment: 1}   # the +/- buttons

  deck:
    reshuffle: true            # used when there is no deck_empty win condition
    track_history: true
    show_remaining_count: true
    suits:                     # names for the suit reference and card prompts
      spades: {name: "...", description: "..."}   # likewise hearts, diamonds, clubs

  dice:
    main: {count: 2, sides: 6}                # turn dice; total = cards to draw
    binary: {split: 3, negative: "...", positive: "..."}      # the free "Roll 1d6" button
    interpret:                                # the free "Roll 2d6" button; first row with max >= total wins
      - {max: 5, label: "..."}
      - {max: 8, label: "..."}
      - {max: 12, label: "..."}
```

> **About `pool_size`.** By default (and as originally specified) a pull rolls one die per remaining point. Because the risk number also rises at each threshold, average loss per pull is not smooth: roughly stability / 6 in the safe tier, / 3 in the danger tier and / 2 in the critical tier, so it drops sharply just below 51 and 21. If you want steady escalation, set `pool_size` (for example `10`) so loss per pull is bounded and rises only with the risk number.

### `conditions`
```yaml
conditions:
  win:
    - type: deck_empty                        # every card drawn and resolved
      additional_checks: [tokens_positive, stability_above_zero]
      message: "..."
  lose:
    - type: stability_zero
      endings: [{title: "...", text: "..."}]  # one is picked at random
      message: "..."
    - type: tokens_zero                       # omit this entry to make tokens harmless at 0
      message: "..."
```
With a `deck_empty` win condition the deck is never reshuffled: the last turn simply draws what is left. Without one, the deck reshuffles when it runs out. A game with no `conditions.lose` list uses both losses.

### `special`
```yaml
special:
  turn_sequence: {min_cards: 2, max_cards: 12}   # clamp for the turn roll (defaults: dice count .. count*sides)
  queen_tracker:                                 # optional alternate ending
    enabled: true
    threshold: 4                                 # Queens drawn (default 4)
    ending: {title: "...", text: "..."}
  ace_of_hearts: {enabled: false}                # set false to switch off the matching special_cards entry
```
`max_cards` is a hard ceiling per turn: with `main: {count: 1, sides: 6}` and `{min_cards: 1, max_cards: 6}` a turn is one to six cards, and even a 2d6 roll never draws more than the cap.
Any `special_cards` entry can be switched off the same way, using `special.<name>.enabled: false`.

### `ui` and `flow`
```yaml
ui:
  panels: {show_instructions: true, show_help_button: false, show_card_reference: false, left_width: "400px"}
  journal: {placeholder: "...", autosave: true, save_indicator: true, download_button: true, load_button: true}
  controls: {new_game_confirmation: true, show_card_history: true, history_clear_button: false}
  labels: {turn_heading: "Start Your Turn", turn_flavor: "", new_game_label: "Begin Another Game",
           game_over_title: "Game Over", win_title: "The End"}
flow:
  starting_prompt: |      # shown in the prompt panel before the first turn
    ...
build:
  minify: false
locale:
  language: "en"          # <html lang>
```
`left_width` is used only when the theme has no `layout.grid_columns`.

### Keys that do nothing
`mechanics.tokens.count_up`, `mechanics.tokens.display_type`, `mechanics.stability.narrative_flavor`, `ui.layout`, `flow.end_turn_button`, `flow.auto_advance`, `locale.date_format`, `locale.time_format`, `build.inline_assets`, `build.generate_print_version`. `validate` warns if you set them.

## `cards.yaml`

```yaml
spades:
  A:                       # A K Q J 10 9 8 7 6 5 4 3 2, in each of spades/hearts/diamonds/clubs
    title: "The First Chamber"
    description: |         # Markdown is rendered (paragraphs, *italics*, lists, ...)
      You push through the narrow entrance...
    tokens: 2              # added to your tokens (negative subtracts)
    blocks: 0              # how many tower blocks the card pulls

special_cards:
  ace_of_hearts:           # name = <rank>_of_<suit> (ace, king, queen, jack, ten..two) ...
    type: roll_check       # ... or give any name and set `card: hearts.A`, or reference it with `special:` on the card
    die: "1d6"
    success_value: 6       # success on a roll >= this
    on_success: {tokens: 1, message: "..."}     # tokens and/or blocks
    on_failure: {tokens: -1, message: "..."}
    button_label: "Roll 1d6"                    # optional
```
Quote number ranks (`"10":`) to be safe; unquoted ones are accepted too. Only `roll_check` special cards are supported.

## Themes

Bundled in `themes/`: **dark-archaeology** (the default), **arctic** (light, icy), **mobile** (dark, large touch targets). List them with `wretched themes`.

```bash
python3 cli/wretched.py build my-game --theme arctic     # one-off
python3 cli/wretched.py new my-game --theme mobile       # at creation
cp themes/theme-arctic.yaml my-game/theme.yaml           # permanently
```

A theme file is read for: `theme.colors` (**required**: primary, secondary, tertiary, accent_primary, text_primary, text_secondary, borders; optional: success, warning, danger, shadows, ...), `theme.fonts`, `theme.layout`, and top-level `custom_css` / `custom_js` (added after the engine loads). All surfaces are derived from these colours, so light and dark palettes both work. Other sections in the bundled theme files (components, background, animations, ...) are design notes and are not applied.

Playing-card faces always use paper colours; override `--card-face`, `--card-ink-black` and `--card-ink-red` in `custom_css` if you want something else.

Fonts: if `fonts.google_fonts` is set, the game loads them from Google Fonts when online and falls back to the theme's font stack offline. Everything else is inlined. Use `google_fonts: []` (as the mobile theme does) for a fully offline-clean file.

## On a phone

No setup needed. On narrow screens (up to 768px) and short landscape touch screens the page switches to a single-column layout:

- A **sticky status strip** at the top shows tokens, the tower, cards left in the deck and cards drawn this turn, plus a 📖 rules button.
- **Cards come first**, then the card prompt, the dice, and the journal. Tower, tokens, suit reference and New Game sit below.
- A fixed **bottom bar** has Cards and Journal jump buttons and one large primary button that changes with the game: *Roll*, *Draw a card (N left)*, *Apply effects*, a special-roll button, *Done with this card*, *Open next card*, or the new-game button when the game is over. The bar hides while you type in the journal so it never covers the keyboard.
- Touch targets are at least 44px, journal text is 16px (no zoom on iOS), and safe-area insets are respected.

Everything is derived from your theme colours, so all themes work. Wide screens keep the two-column layout.

## Output

One HTML file with all CSS, JavaScript, card data and story inlined. No server needed. Works in current Chrome, Edge, Firefox and Safari, on desktop and mobile. Game text from your files is escaped when embedded, so quotes, `&` and even `</script>` in prompts are safe.

## Project layout

```
cli/wretched.py        command-line interface
lib/builder.py         loading, validation, CSS/JS/HTML generation, `new`
templates/             base.html, base.css, engine.js (the game engine), starter/
themes/                bundled themes + their notes
example-game/          "What Lies Beneath" (complete, 52 cards)
tests/                 unit tests and browser tests
```

## Tests

```bash
python3 -m unittest discover -s tests          # builder, CLI, and (if Playwright is installed) browser play-through
pip install -r requirements-dev.txt && playwright install chromium   # to enable the browser tests
```

## Troubleshooting

- **"Missing card" / "Missing suit"**: all 52 cards (A K Q J 10 9 ... 2 in four suits) need a `title` and `description`.
- **"Invalid YAML"**: use spaces (not tabs), a colon after each key, and quotes around text that contains `:` or `#`.
- **Game loads but looks wrong**: run `validate`, then check the browser console.
- **Progress seems lost**: saves live in the browser's local storage for that file; private windows and cleared site data discard them. Use "Save to File" for your journal.

## License and credits

> This work is based on The Wretched (found at http://loottheroom.itch.io/wretched), product of Chris Bissette and Loot The Room, and licensed for our use under the Creative Commons Attribution 3.0 Unported license (http://creativecommons.org/licenses/by/3.0/).

This attribution is built into every game the generator produces (journal footer, rules dialog, and the HTML source). See `NOTICE.md`.

Open source: use it however you like.

- System: "Wretched & Alone" by Chris Bissette ([SRD](https://sealedlibrary.itch.io/wretched-alone-srd))
- Example game: ["What Lies Beneath"](https://shawngraham.github.io/what-lies-beneath.html) by Shawn Graham
- `wretched-generator-strategy.md` is the original design/vision document and is not a description of current behaviour
