#!/usr/bin/env python3
"""
Wretched & Alone Game Generator
Command-line interface
"""

import sys
import argparse
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from builder import GameBuilder


def build_command(args):
    """Build a game from config files"""
    game_path = Path(args.game_path)
    
    if not game_path.exists():
        print(f"Error: Game directory not found: {game_path}")
        return 1
    
    print(f"Building game from: {game_path}")
    
    try:
        builder = GameBuilder(game_path)
        
        print("Loading configurations...")
        builder.load_config()
        builder.load_cards()
        builder.load_theme()
        builder.load_story()
        
        print("Validating...")
        errors = builder.validate()
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
            return 1
        
        print("Generating CSS...")
        print("Generating JavaScript...")
        print("Rendering template...")
        
        output_path = builder.build(args.output)
        output_path = Path(output_path)
        
        print(f"✓ Successfully built: {output_path}")
        print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def validate_command(args):
    """Validate game configuration files"""
    game_path = Path(args.game_path)
    
    if not game_path.exists():
        print(f"Error: Game directory not found: {game_path}")
        return 1
    
    print(f"Validating game: {game_path}")
    
    try:
        builder = GameBuilder(game_path)
        
        # Check files exist
        files = {
            'config.yaml': game_path / 'config.yaml',
            'cards.yaml': game_path / 'cards.yaml',
            'theme.yaml': game_path / 'theme.yaml',
            'story.md': game_path / 'story.md'
        }
        
        for name, path in files.items():
            if not path.exists():
                print(f"  ✗ {name}: NOT FOUND")
            else:
                print(f"  ✓ {name}: Found")
        
        # Load and validate
        print("\nLoading configurations...")
        builder.load_config()
        print("  ✓ config.yaml loaded")
        
        builder.load_cards()
        print("  ✓ cards.yaml loaded")
        
        builder.load_theme()
        print("  ✓ theme.yaml loaded")
        
        builder.load_story()
        print("  ✓ story.md loaded")
        
        print("\nValidating content...")
        errors = builder.validate()
        
        if errors:
            print("  Validation errors found:")
            for error in errors:
                print(f"    ✗ {error}")
            return 1
        else:
            print("  ✓ All validations passed!")
            return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def info_command(args):
    """Show information about a game"""
    game_path = Path(args.game_path)
    
    if not game_path.exists():
        print(f"Error: Game directory not found: {game_path}")
        return 1
    
    try:
        builder = GameBuilder(game_path)
        builder.load_config()
        
        config = builder.config
        game = config['game']
        
        print(f"\n{'='*50}")
        print(f"Game: {game['title']}")
        if 'subtitle' in game:
            print(f"Subtitle: {game['subtitle']}")
        print(f"Author: {game['author']}")
        if 'version' in game:
            print(f"Version: {game['version']}")
        if 'description' in game:
            print(f"\n{game['description']}")
        print(f"{'='*50}\n")
        
        # Show mechanics
        mechanics = config['mechanics']
        print("Mechanics:")
        print(f"  Systems: {', '.join(mechanics['systems'])}")
        
        if 'tokens' in mechanics:
            tokens = mechanics['tokens']
            print(f"  Tokens: {tokens['name']} (start: {tokens['initial']})")
        
        if 'stability' in mechanics:
            stability = mechanics['stability']
            print(f"  Stability: {stability['name']} (start: {stability['initial']})")
        
        # Count cards
        builder.load_cards()
        total_cards = sum(len(suit_cards) for suit_cards in builder.cards.values() if isinstance(suit_cards, dict))
        print(f"\nCards defined: {total_cards}/52")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Wretched & Alone Game Generator',
        epilog='Examples:\n'
               '  wretched build my-game\n'
               '  wretched validate my-game\n'
               '  wretched info my-game',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build a game from config files')
    build_parser.add_argument('game_path', help='Path to game directory')
    build_parser.add_argument('-o', '--output', help='Output file path')
    build_parser.set_defaults(func=build_command)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate game configuration')
    validate_parser.add_argument('game_path', help='Path to game directory')
    validate_parser.set_defaults(func=validate_command)
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show game information')
    info_parser.add_argument('game_path', help='Path to game directory')
    info_parser.set_defaults(func=info_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
