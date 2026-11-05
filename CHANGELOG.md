# Changelog

## [2.0.0] - Unreleased

Where the docs/config and the engine disagreed, the docs/config were treated as correct.

### Fixed (gameplay)
- **Win condition now works.** Resolving every card in the deck ends the game with the configured `conditions.win` message; the deck is no longer silently reshuffled. The final turn is capped to the cards left.
- **Turn dice follow the config:** 2d6 (`mechanics.dice.main`), bounded by `special.turn_sequence` (was a hard-coded 1d6).
- **Saved games load correctly.** A saved value of `0` (tokens, stability, active card) is kept instead of being replaced by the starting value; a finished game restores its end screen; corrupt or old saves are ignored safely.
- **Tokens reaching 0 end the game** (`tokens_zero`), as the rules and config say. Tokens may still go below 0 when `allow_negative` is true.
- **`failure_thresholds`, `risk_scaling`, `messages`, `collapse_message` and loss `endings` are used.** Risk-band text is generated from your thresholds. New optional `stability.pool_size` / `min_loss` for a bounded, smoother tower.
- **Special cards:** `special_cards` (Ace of Hearts roll) is implemented; `special.<name>.enabled: false` switches one off. Queen tracker implemented.
- Card effects can only be applied once; marking a card done with unapplied effects asks first.
- Game over no longer disables Save to File, Instructions or the journal. Cards can be re-read after being resolved.
- Reshuffling no longer deals cards that are on the table. `New Game` clears only this game's storage (per-title key), not all of `localStorage`.

### Fixed (build)
- **`custom_css` and `custom_js` in theme files are now applied** (they were read from the wrong place).
- **Arctic and other light themes are readable:** all surfaces are derived from theme colours; the old stylesheet hard-coded dark brown panels.
- Google Fonts URL was malformed (wrong separators, spaces, missing italics); fixed. Fonts fall back offline.
- Card text is rendered as Markdown (no more literal `*asterisks*`). Titles, authors and card text are escaped; `</script>` in text can no longer break the page.
- `info` no longer reports 53/52 cards; unquoted rank keys (`10:`) are accepted.
- Validation is much stricter (types, ranges, thresholds, dice, special cards, theme colours) and reports clean errors instead of Python tracebacks. Settings that have no effect produce warnings.
- `build.minify` is honoured; minification is built in (no `htmlmin`) and never touches `<pre>` content or joins JavaScript lines.
- Engine moved from `new_js_template.txt` to `templates/engine.js`; stylesheet to `templates/base.css`.

### Added
- Config-driven text: suit names/descriptions, dice labels, button labels, game-over/win titles, `flow.starting_prompt`.
- UI options now honoured: `show_help_button`, `show_card_reference`, `show_remaining_count`, `history_clear_button`, `load_button`, `download_button`, `save_indicator`, `autosave`, `new_game_confirmation`, `tokens.controls`, `left_width`.
- CLI: `themes` command; `build/validate --theme`; `new --theme`; `new --from-example`; `--no-minify`; `--no-color` and `--debug` work anywhere; `NO_COLOR` respected.
- `new` now creates a blank starter (placeholder prompts for all 52 cards, generic rules) instead of copying the archaeology game.
- Keyboard-accessible cards, reduced-motion support, one-line print stylesheet fixes.
- Tests: `python3 -m unittest discover -s tests` (builder, CLI, and a headless-browser play-through).

### Documentation
- README, GETTING-STARTED and theme notes rewritten to match the code (paths, flags, output names, theme names). A full configuration reference was added. The strategy document is marked as the original vision.

### Removed
- The unused `-t/--template` option of `new` (replaced by `--theme`), stray `__pycache__`, and the `htmlmin` mention.

## [1.0.0] - Previous

Initial release: YAML configuration, CSS/JS generation, card deck, dice, tower, tokens, autosave, journal download, basic CLI.
