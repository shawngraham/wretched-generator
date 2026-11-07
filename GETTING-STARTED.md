# Getting Started

## Install (30 seconds)

```bash
python3 --version                  # 3.9 or newer
cd wretched-generator-main         # the folder containing cli/, lib/, templates/
pip install -r requirements.txt
```

## Build and play the example

```bash
python3 cli/wretched.py build example-game
```

You will see each step (loading, validating, generating) and then:

```
✓ Build successful!
  Output: example-game/what-lies-beneath.html
```

Open that file in a browser. That is the whole game: one file, works offline.

On Linux/macOS, `./wretched build example-game` does the same thing.

## Make your own game (5 minutes)

```bash
python3 cli/wretched.py new my-game          # blank starter project
```

This creates `my-game/` with:

```
my-game/
├── config.yaml   rules: dice, tower, tokens, win/lose, UI
├── cards.yaml    52 placeholder prompts: replace them with yours
├── theme.yaml    colours and fonts
└── story.md      the introduction and rules text
```

Prefer to start from a finished game? `python3 cli/wretched.py new my-game --from-example`.

1. **config.yaml**: set your title, author, token and tower names, and the win/lose messages.
2. **cards.yaml**: for each of the 52 cards write a `title` and `description`. Add `tokens: -1` or `blocks: 1` to give a card an effect.
3. **story.md**: write your introduction and explain your rules.
4. Check and build:

```bash
python3 cli/wretched.py validate my-game
python3 cli/wretched.py build my-game
```

Open `my-game/<your-title>.html`. Repeat: edit, validate, build, play.

## Pick a theme

```bash
python3 cli/wretched.py themes                          # list them
python3 cli/wretched.py build my-game --theme arctic    # try one without changing files
python3 cli/wretched.py new other-game --theme mobile   # choose at creation
```

## What you can change

**Easy:** title, author, names of the tower and tokens, starting values, card text, colours.
**Medium:** win and lose conditions, risk thresholds, the dice labels, suit names, the Ace-of-Hearts style special rolls, the Queen tracker, which UI panels show.
**Advanced:** `custom_css` and `custom_js` in `theme.yaml`.

The full list of settings is in the README ("Configuration reference").

## Commands cheat sheet

```bash
wretched new <dir> [--theme NAME] [--from-example]
wretched validate <dir>
wretched build <dir> [-o file.html] [--theme NAME] [--minify | --no-minify]
wretched info <dir>
wretched themes
wretched --help
```

(`wretched` here means `python3 cli/wretched.py` or `./wretched`.)

## Tips

1. Start by editing a few cards, then build and play.
2. Validate often. It tells you exactly which card or setting is wrong.
3. Playtest the tower: 100 stability with the default rules lasts about 11 pulls. Lower `initial`, or set `pool_size`, to change the pace.
4. Use "Save to File" in the game to keep your journal.
5. Want shorter turns? Set `special.turn_sequence.max_cards` (for example 6). Playing on a phone needs no setup: the game switches layout by itself.

## Troubleshooting

- **`./wretched: Permission denied`**: run `chmod +x wretched`, or use `python3 cli/wretched.py`.
- **`ModuleNotFoundError`**: `pip install -r requirements.txt`.
- **Validation errors**: the message names the file and card. All 52 cards need a title and description; keep indentation to 2 spaces.
- **Game doesn't work in the browser**: run `validate`, then check the browser console for errors.
