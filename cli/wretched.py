#!/usr/bin/env python3
"""
Wretched & Alone Game Generator - command-line interface

Commands:
  new       create a new game project (blank starter, or a copy of the example)
  build     generate the HTML game from a project directory
  validate  check a project's files for errors and warnings
  info      show a project's metadata and mechanics
  themes    list the bundled themes
"""

import argparse
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'lib'))

from builder import (BuildError, GameBuilder, ValidationError,  # noqa: E402
                     available_themes, create_project)


class Colors:
    """ANSI colour codes; disable() blanks them."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @classmethod
    def disable(cls):
        for name in ('HEADER', 'BLUE', 'CYAN', 'GREEN', 'YELLOW', 'RED', 'ENDC', 'BOLD'):
            setattr(cls, name, '')


def print_success(msg): print(f"{Colors.GREEN}✓{Colors.ENDC} {msg}")
def print_error(msg): print(f"{Colors.RED}✗{Colors.ENDC} {msg}")
def print_info(msg): print(f"{Colors.BLUE}ℹ{Colors.ENDC} {msg}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠{Colors.ENDC} {msg}")


def bullet(msg, color=None):
    print(f"  {(color or Colors.CYAN)}•{Colors.ENDC} {msg}")


def fail(args, exc):
    """Report an unexpected exception (full traceback with --debug)."""
    print_error(f"{type(exc).__name__}: {exc}")
    if getattr(args, 'debug', False):
        traceback.print_exc()
    return 1


def check_dir(game_path: Path) -> bool:
    if not game_path.exists():
        print_error(f"Game directory not found: {game_path}")
        return False
    if not game_path.is_dir():
        print_error(f"Path is not a directory: {game_path}")
        return False
    return True


def theme_file(args):
    """Resolve --theme (a bundled theme name or a path to a .yaml file)."""
    name = getattr(args, 'theme', None)
    if not name:
        return None
    themes = available_themes()
    if name in themes:
        return themes[name]
    if Path(name).is_file():
        return Path(name)
    raise BuildError(f"Unknown theme '{name}'. Bundled themes: {', '.join(themes)}")


def print_warnings(builder):
    for w in builder.warnings:
        print_warning(w)


def build_command(args):
    game_path = Path(args.game_path)
    if not check_dir(game_path):
        return 1
    print(f"\n{Colors.BOLD}Building game from:{Colors.ENDC} {game_path}\n")

    try:
        builder = GameBuilder(game_path, theme_file=theme_file(args))

        print_info("Loading configurations...")
        for label, loader in (('config.yaml', builder.load_config), ('cards.yaml', builder.load_cards),
                              ('theme.yaml' if not args.theme else f"theme '{args.theme}'", builder.load_theme),
                              ('story.md', builder.load_story)):
            loader()
            bullet(f"{label} loaded")

        print_info("Validating game configuration...")
        errors = builder.validate()
        print_warnings(builder)
        if errors:
            print_error(f"Validation failed with {len(errors)} error(s):")
            for error in errors:
                bullet(error, Colors.RED)
            return 1
        print_success("Validation passed")

        minify = True if args.minify else (False if args.no_minify else None)
        output_path = builder.build(args.output, minify=minify)

        size = output_path.stat().st_size / 1024
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Build successful!{Colors.ENDC}")
        print(f"  {Colors.BOLD}Output:{Colors.ENDC} {output_path}")
        print(f"  {Colors.BOLD}Size:{Colors.ENDC} {size:.1f} KB")
        if minify or (minify is None and builder.config['build'].get('minify')):
            print(f"  {Colors.BOLD}Minified:{Colors.ENDC} yes")
        print(f"\n{Colors.CYAN}Open {output_path.name} in your browser to play!{Colors.ENDC}\n")
        return 0

    except FileNotFoundError as e:
        print_error(f"File not found: {e}")
        return 1
    except ValidationError as e:
        print_error(f"Validation error: {e}")
        return 1
    except BuildError as e:
        print_error(f"Build error: {e}")
        return 1
    except Exception as e:  # noqa: BLE001
        return fail(args, e)


def validate_command(args):
    game_path = Path(args.game_path)
    if not check_dir(game_path):
        return 1
    print(f"\n{Colors.BOLD}Validating game:{Colors.ENDC} {game_path}\n")

    try:
        builder = GameBuilder(game_path, theme_file=theme_file(args))

        print_info("Checking for required files...")
        all_found = True
        for name in ('config.yaml', 'cards.yaml', 'theme.yaml', 'story.md'):
            if (game_path / name).exists() or (name == 'theme.yaml' and args.theme):
                print_success(f"{name}: Found")
            else:
                print_error(f"{name}: NOT FOUND")
                all_found = False
        if not all_found:
            return 1

        print(f"\n{Colors.BOLD}Loading configurations...{Colors.ENDC}")
        for name, loader in (('config.yaml', builder.load_config), ('cards.yaml', builder.load_cards),
                             ('theme.yaml', builder.load_theme), ('story.md', builder.load_story)):
            try:
                loader()
                print_success(f"{name} loaded and parsed")
            except Exception as e:  # noqa: BLE001
                print_error(f"{name}: {e}")
                return 1

        print(f"\n{Colors.BOLD}Validating content...{Colors.ENDC}")
        errors = builder.validate()
        print_warnings(builder)
        if errors:
            print_error(f"Validation failed with {len(errors)} error(s):")
            for error in errors:
                bullet(error, Colors.RED)
            return 1
        print_success("All validations passed!")
        print(f"\n{Colors.GREEN}Game configuration is valid and ready to build!{Colors.ENDC}\n")
        return 0
    except Exception as e:  # noqa: BLE001
        return fail(args, e)


def info_command(args):
    game_path = Path(args.game_path)
    if not check_dir(game_path):
        return 1
    try:
        builder = GameBuilder(game_path)
        builder.load_config()
        builder.load_cards()
        cfg = builder.config
        game = cfg['game']
        mech = cfg['mechanics']

        print(f"\n{'=' * 60}")
        print(f"{Colors.BOLD}{Colors.CYAN}Game: {game.get('title', '(untitled)')}{Colors.ENDC}")
        if game.get('subtitle'):
            print(f"Subtitle: {game['subtitle']}")
        print(f"Author: {game.get('author', '(none)')}")
        if game.get('version'):
            print(f"Version: {game['version']}")
        if game.get('description'):
            print(f"\n{game['description']}")
        print(f"{'=' * 60}\n")

        print(f"{Colors.BOLD}Mechanics:{Colors.ENDC}")
        bullet(f"Systems: {', '.join(mech['systems'])}")
        main = mech['dice']['main']
        bullet(f"Turn dice: {main['count']}d{main['sides']} (cards drawn per turn)")
        if 'tokens' in mech['systems']:
            bullet(f"Tokens: {mech['tokens']['name']} (start: {mech['tokens']['initial']})")
        if 'stability' in mech['systems']:
            bullet(f"Stability: {mech['stability']['name']} (start: {mech['stability']['initial']})")
        if any(w.get('type') == 'deck_empty' for w in cfg['conditions'].get('win') or []):
            bullet("Win condition: resolve the whole deck")

        total = builder.count_cards()
        if total == 52:
            print(f"\n{Colors.GREEN}Cards defined: {total}/52 ✓{Colors.ENDC}")
        else:
            print(f"\n{Colors.YELLOW}Cards defined: {total}/52 (incomplete){Colors.ENDC}")
        if builder.special_cards:
            print(f"Special card rules: {', '.join(builder.special_cards)}")
        print()
        return 0
    except Exception as e:  # noqa: BLE001
        return fail(args, e)


def new_command(args):
    project_path = Path(args.project_name)
    print(f"\n{Colors.BOLD}Creating new game project:{Colors.ENDC} {args.project_name}\n")
    try:
        create_project(project_path, theme=args.theme or 'dark-archaeology', from_example=args.from_example)
    except BuildError as e:
        print_error(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        return fail(args, e)

    print_success(f"Project created: {project_path}")
    if args.from_example:
        print_info("Copied the finished example game; edit every file to make it your own.")
    else:
        print_info("Created a blank starter with placeholder prompts for all 52 cards.")
    print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
    print(f"  1. Edit {project_path}/config.yaml  (title, author, mechanics, rules)")
    print(f"  2. Edit {project_path}/cards.yaml   (your 52 card prompts)")
    print(f"  3. Edit {project_path}/story.md     (introduction and rules)")
    print(f"  4. Build: wretched build {project_path}\n")
    return 0


def themes_command(args):
    print(f"\n{Colors.BOLD}Bundled themes:{Colors.ENDC}")
    for name, path in available_themes().items():
        bullet(f"{name}  ({path.name})")
    print("\nUse one with:  wretched new my-game --theme NAME   or   wretched build my-game --theme NAME\n")
    return 0


def main(argv=None):
    # Global flags are accepted both before and after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--no-color', action='store_true', default=argparse.SUPPRESS,
                        help='Disable colored output')
    common.add_argument('--debug', action='store_true', default=argparse.SUPPRESS,
                        help='Show full tracebacks for unexpected errors')

    parser = argparse.ArgumentParser(
        parents=[common],
        description='Wretched & Alone Game Generator\nBuild self-contained HTML games from YAML and Markdown',
        epilog='Examples:\n'
               '  wretched new my-game                    # blank starter project\n'
               '  wretched new my-game --theme arctic     # ...with the Arctic theme\n'
               '  wretched new my-game --from-example     # copy the finished example instead\n'
               '  wretched build my-game                  # build to my-game/<title>.html\n'
               '  wretched build my-game --theme mobile   # build with another theme\n'
               '  wretched validate my-game               # check files, show warnings\n'
               '  wretched info my-game                   # show game info\n'
               '  wretched themes                         # list bundled themes',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', help='Commands')

    p = sub.add_parser('new', parents=[common], help='Create a new game project')
    p.add_argument('project_name', help='Directory to create')
    p.add_argument('-t', '--theme', help='Bundled theme to start with (default: dark-archaeology)')
    p.add_argument('--from-example', action='store_true',
                   help='Copy the finished example game instead of a blank starter')
    p.set_defaults(func=new_command)

    p = sub.add_parser('build', parents=[common], help='Build a game from config files')
    p.add_argument('game_path', help='Path to game directory')
    p.add_argument('-o', '--output', help='Output file path (default: <game dir>/<title>.html)')
    p.add_argument('-t', '--theme', help='Use a bundled theme name or a theme .yaml path instead of theme.yaml')
    g = p.add_mutually_exclusive_group()
    g.add_argument('-m', '--minify', action='store_true', help='Minify the HTML (overrides config build.minify)')
    g.add_argument('--no-minify', action='store_true', help="Don't minify (overrides config build.minify)")
    p.set_defaults(func=build_command)

    p = sub.add_parser('validate', parents=[common], help='Validate game configuration')
    p.add_argument('game_path', help='Path to game directory')
    p.add_argument('-t', '--theme', help='Validate with this theme instead of theme.yaml')
    p.set_defaults(func=validate_command)

    p = sub.add_parser('info', parents=[common], help='Show game information and mechanics')
    p.add_argument('game_path', help='Path to game directory')
    p.set_defaults(func=info_command)

    p = sub.add_parser('themes', parents=[common], help='List bundled themes')
    p.set_defaults(func=themes_command)

    args = parser.parse_args(argv)

    if getattr(args, 'no_color', False) or os.environ.get('NO_COLOR') or not sys.stdout.isatty():
        Colors.disable()

    if not args.command:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
