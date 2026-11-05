"""Builder and CLI tests (no browser needed). Run: python3 -m unittest discover -s tests"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'lib'))

import yaml  # noqa: E402
from builder import (BuildError, GameBuilder, ValidationError, available_themes,  # noqa: E402
                     create_project, js_json, slugify)

CLI = str(ROOT / 'cli' / 'wretched.py')


def copy_example(tmp: Path) -> Path:
    dest = tmp / 'game'
    shutil.copytree(ROOT / 'example-game', dest, ignore=shutil.ignore_patterns('*.html'))
    return dest


class BuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_example_validates_without_errors(self):
        b = GameBuilder(ROOT / 'example-game')
        b.load_all()
        self.assertEqual(b.validate(), [])
        self.assertEqual(b.count_cards(), 52)      # special_cards is not counted as a suit

    def test_build_produces_html(self):
        out = GameBuilder(copy_example(self.tmp)).build()
        html = out.read_text(encoding='utf-8')
        self.assertEqual(out.name, 'what-lies-beneath.html')
        self.assertIn('<title>What Lies Beneath', html)
        self.assertNotIn('__WRETCHED_', html)

    def test_minify_option_and_config(self):
        g = copy_example(self.tmp)
        plain = GameBuilder(g).build(g / 'a.html', minify=False).stat().st_size
        small = GameBuilder(g).build(g / 'b.html', minify=True).stat().st_size
        self.assertLess(small, plain)
        cfg = yaml.safe_load((g / 'config.yaml').read_text())
        cfg['build']['minify'] = True
        (g / 'config.yaml').write_text(yaml.safe_dump(cfg, allow_unicode=True))
        self.assertEqual(GameBuilder(g).build(g / 'c.html').stat().st_size, small)

    def test_missing_card_is_an_error(self):
        g = copy_example(self.tmp)
        cards = yaml.safe_load((g / 'cards.yaml').read_text())
        del cards['hearts']['7']
        (g / 'cards.yaml').write_text(yaml.safe_dump(cards, allow_unicode=True))
        b = GameBuilder(g)
        b.load_all()
        self.assertIn('Missing card: 7 of hearts', b.validate())
        with self.assertRaises(ValidationError):
            GameBuilder(g).build()

    def test_unquoted_numeric_rank_keys_are_accepted(self):
        g = copy_example(self.tmp)
        text = (g / 'cards.yaml').read_text()
        text = text.replace("'10':", "10:").replace('"10":', "10:").replace("'9':", "9:").replace('"9":', "9:")
        (g / 'cards.yaml').write_text(text)
        b = GameBuilder(g)
        b.load_all()
        self.assertEqual(b.validate(), [])

    def test_bad_config_values_give_errors_not_crashes(self):
        g = copy_example(self.tmp)
        cfg = yaml.safe_load((g / 'config.yaml').read_text())
        cfg['mechanics']['stability']['thresholds'] = {'critical': 60, 'danger': 50}
        cfg['mechanics']['dice']['main']['sides'] = 1
        del cfg['game']['author']
        (g / 'config.yaml').write_text(yaml.safe_dump(cfg, allow_unicode=True))
        b = GameBuilder(g)
        b.load_all()
        errors = ' | '.join(b.validate())
        self.assertIn('thresholds', errors)
        self.assertIn('dice.main', errors)
        self.assertIn('author', errors)

    def test_incomplete_theme_is_an_error(self):
        g = copy_example(self.tmp)
        (g / 'theme.yaml').write_text('theme:\n  colors:\n    primary: "#000"\n')
        b = GameBuilder(g)
        b.load_all()
        self.assertTrue(any('theme.colors is missing' in e for e in b.validate()))

    def test_custom_css_and_js_from_top_level_are_applied(self):
        g = copy_example(self.tmp)
        theme = yaml.safe_load((g / 'theme.yaml').read_text())
        theme['custom_css'] = '.zzz-marker { color: red; }'
        theme['custom_js'] = 'window.__zzzMarker = 1;'
        (g / 'theme.yaml').write_text(yaml.safe_dump(theme))
        html = GameBuilder(g).build(minify=False).read_text(encoding='utf-8')
        self.assertIn('.zzz-marker', html)
        self.assertIn('__zzzMarker', html)

    def test_theme_override(self):
        g = copy_example(self.tmp)
        html = GameBuilder(g, theme_file=available_themes()['arctic']).build(g / 'x.html').read_text(encoding='utf-8')
        self.assertIn('#c5d8e1', html)

    def test_google_fonts_url_is_valid_css2_syntax(self):
        url = GameBuilder._google_fonts_url([
            {'family': 'Crimson Text', 'weights': [400, 600], 'styles': ['normal', 'italic']},
            {'family': 'Cinzel', 'weights': [400], 'styles': ['normal']}])
        self.assertEqual(url, 'https://fonts.googleapis.com/css2?'
                              'family=Crimson+Text:ital,wght@0,400;0,600;1,400;1,600&'
                              'family=Cinzel:ital,wght@0,400&display=swap')
        self.assertIsNone(GameBuilder._google_fonts_url([]))

    def test_script_breaking_text_is_escaped(self):
        g = copy_example(self.tmp)
        cards = yaml.safe_load((g / 'cards.yaml').read_text())
        cards['spades']['A']['title'] = 'Evil </script><b>x</b>'
        (g / 'cards.yaml').write_text(yaml.safe_dump(cards, allow_unicode=True))
        cfg = yaml.safe_load((g / 'config.yaml').read_text())
        cfg['game']['title'] = 'Fish & <Chips>'
        (g / 'config.yaml').write_text(yaml.safe_dump(cfg, allow_unicode=True))
        html = GameBuilder(g).build(g / 'e.html').read_text(encoding='utf-8')
        self.assertEqual(html.lower().count('</script>'), 2)      # engine + (none custom) -> only real ones
        self.assertIn('Fish &amp; &lt;Chips&gt;', html)
        self.assertTrue((g / 'e.html').exists())

    def test_card_markdown_is_rendered(self):
        b = GameBuilder(ROOT / 'example-game')
        b.load_cards()
        self.assertIn('<em>', b.cards['spades']['A']['description_html'])

    def test_helpers(self):
        self.assertEqual(slugify('What Lies Beneath!'), 'what-lies-beneath')
        self.assertEqual(slugify('???'), 'game')
        self.assertNotIn('</', js_json({'a': '</script>'}))

    def test_new_starter_validates_and_builds(self):
        dest = create_project(self.tmp / 'fresh', theme='mobile')
        b = GameBuilder(dest)
        b.load_all()
        self.assertEqual(b.validate(), [])
        self.assertEqual(b.count_cards(), 52)
        self.assertNotIn('Blackwood', (dest / 'story.md').read_text())
        self.assertTrue(b.build().exists())

    def test_new_refuses_existing_dir_and_unknown_theme(self):
        (self.tmp / 'there').mkdir()
        with self.assertRaises(BuildError):
            create_project(self.tmp / 'there')
        with self.assertRaises(BuildError):
            create_project(self.tmp / 'other', theme='nope')

    def test_all_bundled_themes_build(self):
        g = copy_example(self.tmp)
        for name, path in available_themes().items():
            out = GameBuilder(g, theme_file=path).build(g / f'{name}.html')
            self.assertGreater(out.stat().st_size, 10000, name)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, CLI, *args], capture_output=True, text=True)

    def test_global_flags_work_before_and_after_subcommand(self):
        ex = str(ROOT / 'example-game')
        for argv in (['--no-color', 'validate', ex], ['validate', ex, '--no-color'], ['validate', ex, '--debug']):
            r = self.run_cli(*argv)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_exit_codes(self):
        self.assertEqual(self.run_cli('build', '/no/such/dir').returncode, 1)
        self.assertEqual(self.run_cli().returncode, 1)

    def test_info_reports_52_cards(self):
        r = self.run_cli('info', str(ROOT / 'example-game'))
        self.assertIn('Cards defined: 52/52', r.stdout)

    def test_wrapper_script_is_executable(self):
        self.assertTrue((ROOT / 'wretched').stat().st_mode & 0o111)


if __name__ == '__main__':
    unittest.main()
