#!/usr/bin/env python3
"""
Wretched & Alone Game Generator
Command-line interface

This CLI provides commands for:
- build: Generate HTML game from configuration files
- validate: Check configuration files for errors
- info: Display game metadata and mechanics summary
- new: Create a new game project from template
- serve: Run development server with live reload
"""

import sys
import argparse
import shutil
from pathlib import Path
from typing import Optional

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from builder import GameBuilder, ValidationError, BuildError


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @classmethod
    def disable(cls):
        """Disable colors (for non-terminal output)"""
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.ENDC = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''


def print_success(msg: str):
    """Print a success message in green"""
    print(f"{Colors.GREEN}✓{Colors.ENDC} {msg}")


def print_error(msg: str):
    """Print an error message in red"""
    print(f"{Colors.RED}✗{Colors.ENDC} {msg}")


def print_info(msg: str):
    """Print an info message in blue"""
    print(f"{Colors.BLUE}ℹ{Colors.ENDC} {msg}")


def print_warning(msg: str):
    """Print a warning message in yellow"""
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {msg}")


def build_command(args):
    """
    Build a game from config files.

    Args:
        args: Command-line arguments containing game_path, output, and minify

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    game_path = Path(args.game_path)

    if not game_path.exists():
        print_error(f"Game directory not found: {game_path}")
        return 1

    if not game_path.is_dir():
        print_error(f"Path is not a directory: {game_path}")
        return 1

    print(f"\n{Colors.BOLD}Building game from:{Colors.ENDC} {game_path}\n")

    try:
        builder = GameBuilder(game_path)

        # Loading configurations
        print_info("Loading configurations...")
        builder.load_config()
        print(f"  {Colors.CYAN}•{Colors.ENDC} config.yaml loaded")

        builder.load_cards()
        print(f"  {Colors.CYAN}•{Colors.ENDC} cards.yaml loaded")

        builder.load_theme()
        print(f"  {Colors.CYAN}•{Colors.ENDC} theme.yaml loaded")

        builder.load_story()
        print(f"  {Colors.CYAN}•{Colors.ENDC} story.md loaded")

        # Validating
        print_info("Validating game configuration...")
        errors = builder.validate()
        if errors:
            print_error(f"Validation failed with {len(errors)} error(s):")
            for error in errors:
                print(f"  {Colors.RED}•{Colors.ENDC} {error}")
            return 1
        print_success("Validation passed")

        # Generating
        print_info("Generating CSS from theme...")
        css = builder.generate_css()
        print(f"  {Colors.CYAN}•{Colors.ENDC} Generated {len(css)} bytes of CSS")

        print_info("Generating JavaScript game engine...")
        js = builder.generate_javascript()
        print(f"  {Colors.CYAN}•{Colors.ENDC} Generated {len(js)} bytes of JavaScript")

        print_info("Rendering HTML template...")

        # Build
        minify = getattr(args, 'minify', False)
        output_path = builder.build(args.output, minify=minify)

        # Success!
        file_size = output_path.stat().st_size / 1024
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Build successful!{Colors.ENDC}")
        print(f"  {Colors.BOLD}Output:{Colors.ENDC} {output_path}")
        print(f"  {Colors.BOLD}Size:{Colors.ENDC} {file_size:.1f} KB")

        if minify:
            print(f"  {Colors.BOLD}Minified:{Colors.ENDC} Yes")

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
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if args.debug if hasattr(args, 'debug') else False:
            import traceback
            traceback.print_exc()
        return 1


def validate_command(args):
    """
    Validate game configuration files.

    Args:
        args: Command-line arguments containing game_path

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    game_path = Path(args.game_path)

    if not game_path.exists():
        print_error(f"Game directory not found: {game_path}")
        return 1

    print(f"\n{Colors.BOLD}Validating game:{Colors.ENDC} {game_path}\n")

    try:
        builder = GameBuilder(game_path)

        # Check files exist
        print_info("Checking for required files...")
        files = {
            'config.yaml': game_path / 'config.yaml',
            'cards.yaml': game_path / 'cards.yaml',
            'theme.yaml': game_path / 'theme.yaml',
            'story.md': game_path / 'story.md'
        }

        all_found = True
        for name, path in files.items():
            if not path.exists():
                print_error(f"{name}: NOT FOUND")
                all_found = False
            else:
                print_success(f"{name}: Found")

        if not all_found:
            return 1

        # Load and validate
        print(f"\n{Colors.BOLD}Loading configurations...{Colors.ENDC}")
        try:
            builder.load_config()
            print_success("config.yaml loaded and parsed")
        except Exception as e:
            print_error(f"config.yaml: {e}")
            return 1

        try:
            builder.load_cards()
            print_success("cards.yaml loaded and parsed")
        except Exception as e:
            print_error(f"cards.yaml: {e}")
            return 1

        try:
            builder.load_theme()
            print_success("theme.yaml loaded and parsed")
        except Exception as e:
            print_error(f"theme.yaml: {e}")
            return 1

        try:
            builder.load_story()
            print_success("story.md loaded and converted")
        except Exception as e:
            print_error(f"story.md: {e}")
            return 1

        print(f"\n{Colors.BOLD}Validating content...{Colors.ENDC}")
        errors = builder.validate()

        if errors:
            print_error(f"Validation failed with {len(errors)} error(s):")
            for error in errors:
                print(f"  {Colors.RED}•{Colors.ENDC} {error}")
            return 1
        else:
            print_success("All validations passed!")
            print(f"\n{Colors.GREEN}Game configuration is valid and ready to build!{Colors.ENDC}\n")
            return 0

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


def info_command(args):
    """
    Show information about a game.

    Args:
        args: Command-line arguments containing game_path

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    game_path = Path(args.game_path)

    if not game_path.exists():
        print_error(f"Game directory not found: {game_path}")
        return 1

    try:
        builder = GameBuilder(game_path)
        builder.load_config()

        config = builder.config
        game = config['game']

        print(f"\n{'='*60}")
        print(f"{Colors.BOLD}{Colors.CYAN}Game: {game['title']}{Colors.ENDC}")
        if 'subtitle' in game:
            print(f"Subtitle: {game['subtitle']}")
        print(f"Author: {game['author']}")
        if 'version' in game:
            print(f"Version: {game['version']}")
        if 'description' in game:
            print(f"\n{game['description']}")
        print(f"{'='*60}\n")

        # Show mechanics
        mechanics = config['mechanics']
        print(f"{Colors.BOLD}Mechanics:{Colors.ENDC}")
        print(f"  {Colors.CYAN}•{Colors.ENDC} Systems: {', '.join(mechanics['systems'])}")

        if 'tokens' in mechanics:
            tokens = mechanics['tokens']
            print(f"  {Colors.CYAN}•{Colors.ENDC} Tokens: {tokens['name']} (start: {tokens['initial']})")

        if 'stability' in mechanics:
            stability = mechanics['stability']
            print(f"  {Colors.CYAN}•{Colors.ENDC} Stability: {stability['name']} (start: {stability['initial']})")

        # Count cards
        builder.load_cards()
        total_cards = sum(len(suit_cards) for suit_cards in builder.cards.values() if isinstance(suit_cards, dict))

        if total_cards == 52:
            print(f"\n{Colors.GREEN}Cards defined: {total_cards}/52 ✓{Colors.ENDC}")
        else:
            print(f"\n{Colors.YELLOW}Cards defined: {total_cards}/52 (incomplete){Colors.ENDC}")

        print()
        return 0

    except Exception as e:
        print_error(f"Error: {e}")
        return 1


def new_command(args):
    """
    Create a new game project from template.

    Args:
        args: Command-line arguments containing project_name and template

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    project_name = args.project_name
    template = getattr(args, 'template', 'example')

    # Create project directory
    project_path = Path(project_name)

    if project_path.exists():
        print_error(f"Directory already exists: {project_path}")
        print_info("Choose a different name or remove the existing directory")
        return 1

    print(f"\n{Colors.BOLD}Creating new game project:{Colors.ENDC} {project_name}\n")

    try:
        # Find template directory
        cli_dir = Path(__file__).parent
        template_source = cli_dir.parent / 'example-game'

        if not template_source.exists():
            print_error(f"Template not found: {template_source}")
            return 1

        # Copy template
        print_info(f"Copying template files from example-game...")
        shutil.copytree(template_source, project_path)

        # Remove any generated HTML files from template
        for html_file in project_path.glob('*.html'):
            html_file.unlink()
            print(f"  {Colors.CYAN}•{Colors.ENDC} Removed {html_file.name}")

        print_success(f"Project created: {project_path}")

        # Show next steps
        print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
        print(f"  1. cd {project_name}")
        print(f"  2. Edit config.yaml (game title, author, description)")
        print(f"  3. Edit cards.yaml (your 52 card prompts)")
        print(f"  4. Edit theme.yaml (colors and styling)")
        print(f"  5. Edit story.md (game introduction and rules)")
        print(f"\n{Colors.BOLD}Then build your game:{Colors.ENDC}")
        print(f"  python3 ../cli/wretched.py build .")
        print(f"\n{Colors.CYAN}Happy game making!{Colors.ENDC}\n")

        return 0

    except Exception as e:
        print_error(f"Failed to create project: {e}")
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description=f'{Colors.BOLD}Wretched & Alone Game Generator{Colors.ENDC}\n'
                    'Build self-contained HTML games from YAML and Markdown',
        epilog='Examples:\n'
               '  wretched new my-game              # Create new game project\n'
               '  wretched build my-game            # Build game to HTML\n'
               '  wretched build my-game --minify   # Build and minify\n'
               '  wretched validate my-game         # Validate configuration\n'
               '  wretched info my-game             # Show game info',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Global options
    parser.add_argument('--no-color', action='store_true',
                       help='Disable colored output')
    parser.add_argument('--debug', action='store_true',
                       help='Show debug information and tracebacks')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # New command
    new_parser = subparsers.add_parser(
        'new',
        help='Create a new game project from template'
    )
    new_parser.add_argument('project_name', help='Name for the new game project')
    new_parser.add_argument('-t', '--template', default='example',
                           help='Template to use (default: example)')
    new_parser.set_defaults(func=new_command)

    # Build command
    build_parser = subparsers.add_parser(
        'build',
        help='Build a game from config files'
    )
    build_parser.add_argument('game_path', help='Path to game directory')
    build_parser.add_argument('-o', '--output', help='Output file path')
    build_parser.add_argument('-m', '--minify', action='store_true',
                             help='Minify the output HTML')
    build_parser.set_defaults(func=build_command)

    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate game configuration'
    )
    validate_parser.add_argument('game_path', help='Path to game directory')
    validate_parser.set_defaults(func=validate_command)

    # Info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show game information and mechanics'
    )
    info_parser.add_argument('game_path', help='Path to game directory')
    info_parser.set_defaults(func=info_command)

    args = parser.parse_args()

    # Disable colors if requested or if not a terminal
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
