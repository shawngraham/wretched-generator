"""
Browser tests: build the example game and play it in headless Chromium.
Skipped automatically if Playwright is not installed.
Run: python3 -m unittest discover -s tests
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'lib'))

from builder import GameBuilder, available_themes  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:          # pragma: no cover
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, 'playwright not installed')
class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        game = cls.tmp / 'game'
        shutil.copytree(ROOT / 'example-game', game, ignore=shutil.ignore_patterns('*.html'))
        cls.page_file = GameBuilder(game).build(game / 'game.html', minify=True)
        cls.theme_pages = {n: GameBuilder(game, theme_file=p).build(game / f'{n}.html')
                           for n, p in available_themes().items()}
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def open(self, path=None, width=1280, height=900):
        ctx = self.browser.new_context(viewport={'width': width, 'height': height})
        self.addCleanup(ctx.close)
        page = ctx.new_page()
        self.errors = []
        page.on('pageerror', lambda e: self.errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        page.goto('file://' + str(path or self.page_file))
        page.evaluate('localStorage.clear()')
        page.reload()
        return page

    def tearDown(self):
        self.assertEqual(getattr(self, 'errors', []), [])

    # ---- loading -------------------------------------------------------------

    def test_every_theme_loads_without_errors(self):
        for name, path in self.theme_pages.items():
            page = self.open(path)
            self.assertEqual(page.evaluate('gameState.deck.length'), 52, name)

    def test_no_horizontal_scroll_on_phone(self):
        page = self.open(width=390, height=800)
        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)

    # ---- turn flow -----------------------------------------------------------

    def test_turn_roll_is_2d6_and_draws_that_many(self):
        page = self.open()
        seen = set()
        for _ in range(60):
            page.evaluate('rollForCardCount()')
            n = page.evaluate('gameState.cardsToDraw')
            self.assertTrue(2 <= n <= 12)
            seen.add(n)
            page.evaluate('gameState.cardsDrawnThisTurn = 0; gameState.drawnCards = []')
        self.assertGreater(len(seen), 5)
        page.evaluate('rollForCardCount()')
        n = page.evaluate('gameState.cardsToDraw')
        for _ in range(n + 3):
            page.evaluate('drawCard()')
        self.assertEqual(page.evaluate('gameState.drawnCards.length'), n)

    def test_card_markdown_and_suit_name_render(self):
        page = self.open()
        page.evaluate("""gameState.deck.push({suit:'spades',value:'A'}); rollForCardCount(); drawCard(); viewCard(0);""")
        html = page.inner_html('#cardPrompt')
        self.assertIn('<em>', html)
        self.assertNotIn('*What', html)
        self.assertIn("The Cave", html)

    def test_effects_apply_only_once(self):
        page = self.open()
        page.evaluate("""gameState.deck.push({suit:'hearts',value:'K'}); rollForCardCount(); drawCard(); viewCard(0);
                         applyBasicCardEffects(0); applyBasicCardEffects(0); applyBasicCardEffects(0);""")
        self.assertEqual(page.evaluate('gameState.tokens'), 9)          # -1, once
        self.assertLess(page.evaluate('gameState.stability'), 100)

    # ---- special card ----------------------------------------------------------

    def test_ace_of_hearts_roll(self):
        page = self.open()
        for rnd, expected in ((0.99, 11), (0.0, 9)):
            page.evaluate('localStorage.clear()')
            page.reload()
            page.evaluate(f"""Math.random = () => {rnd};
                gameState.deck.push({{suit:'hearts',value:'A'}}); rollForCardCount(); drawCard(); viewCard(0);""")
            self.assertIn('Roll 1d6', page.inner_text('#cardPrompt'))
            page.evaluate('rollSpecial(0); rollSpecial(0)')                # second click is ignored
            self.assertEqual(page.evaluate('gameState.tokens'), expected)

    # ---- winning ---------------------------------------------------------------

    def test_resolving_whole_deck_wins_and_never_reshuffles(self):
        page = self.open()
        guard = 0
        while not page.evaluate('gameState.gameEnded') and guard < 100:
            guard += 1
            page.evaluate("""rollForCardCount();
                while (gameState.cardsDrawnThisTurn < gameState.cardsToDraw) drawCard();
                for (let i = 0; i < gameState.drawnCards.length; i++) markCardResolved(i);""")
        state = page.evaluate('({e: gameState.gameEnded, kind: gameState.endInfo && gameState.endInfo.kind, deck: gameState.deck.length, hist: gameState.cardHistory.length})')
        self.assertTrue(state['e'])
        self.assertEqual(state['kind'], 'win')
        self.assertEqual(state['deck'], 0)
        self.assertEqual(state['hist'], 52)
        self.assertIn('TRIUMPHANT', page.inner_text('#cardPrompt'))

    def test_last_turn_is_capped_to_remaining_cards(self):
        page = self.open()
        page.evaluate("gameState.deck = gameState.deck.slice(0, 3); Math.random = () => 0.99; rollForCardCount();")
        self.assertEqual(page.evaluate('gameState.cardsToDraw'), 3)

    # ---- losing and persistence ----------------------------------------------

    def test_stability_loss_survives_reload_with_end_screen(self):
        page = self.open()
        page.evaluate('gameState.stability = 1; pullBlock();')
        self.assertTrue(page.evaluate('gameState.gameEnded'))
        text = page.inner_text('#cardPrompt')
        self.assertIn('Game Over', text)
        self.assertIn('Academic Credibility Destroyed', text)
        self.assertTrue('Retreat in Shame' in text or 'Unpaid Assistant' in text)   # one random ending
        page.reload()
        self.assertEqual(page.evaluate('gameState.stability'), 0)        # not reset to 100
        self.assertTrue(page.evaluate('gameState.gameEnded'))
        self.assertEqual(page.inner_text('#cardPrompt'), text)           # same ending screen
        # Only game actions are locked; reading rules and saving the journal still work.
        self.assertTrue(page.evaluate("document.querySelector('.btn-newgame').disabled === false"))
        self.assertTrue(page.evaluate("[...document.querySelectorAll('button[onclick*=downloadJournal],button[onclick*=storyModal]')].every(b => !b.disabled)"))
        self.assertTrue(page.evaluate("[...document.querySelectorAll('.game-action')].every(b => b.disabled)"))

    def test_zero_tokens_ends_game_and_stays_zero(self):
        page = self.open()
        page.evaluate('gameState.tokens = 1; adjustTokens(-1);')
        self.assertTrue(page.evaluate('gameState.gameEnded'))
        self.assertIn('All Evidence Destroyed', page.inner_text('#cardPrompt'))
        page.reload()
        self.assertEqual(page.evaluate('gameState.tokens'), 0)           # not reset to 10
        self.assertTrue(page.evaluate('gameState.gameEnded'))

    def test_tokens_can_go_negative_and_still_end(self):
        page = self.open()
        page.evaluate('gameState.tokens = 1; changeTokens(-3); checkGameEnd();')
        self.assertEqual(page.evaluate('gameState.tokens'), -2)
        self.assertTrue(page.evaluate('gameState.gameEnded'))

    def test_active_card_zero_and_progress_persist(self):
        page = self.open()
        page.evaluate("rollForCardCount(); drawCard(); drawCard(); viewCard(0); applyBasicCardEffects(0);")
        before = page.evaluate('JSON.stringify([gameState.tokens, gameState.stability, gameState.deck.length])')
        page.reload()
        self.assertEqual(page.evaluate('gameState.activeCardIndex'), 0)
        self.assertEqual(page.evaluate('JSON.stringify([gameState.tokens, gameState.stability, gameState.deck.length])'), before)
        self.assertIn('prompt-title', page.inner_html('#cardPrompt'))

    def test_corrupt_save_does_not_break_the_game(self):
        page = self.open()
        page.evaluate("localStorage.setItem(GAME_META.storageKey, '{not json')")
        page.reload()
        self.assertEqual(page.evaluate('gameState.deck.length'), 52)
        page.evaluate("localStorage.setItem(GAME_META.storageKey, JSON.stringify({v:2, tokens:'x', deck:[{suit:'zzz'}], drawnCards:[{card:{}}]}))")
        page.reload()
        self.assertEqual(page.evaluate('gameState.tokens'), 10)
        self.assertEqual(page.evaluate('gameState.deck.length'), 52)

    def test_new_game_clears_only_this_games_storage(self):
        page = self.open()
        page.evaluate("localStorage.setItem('someOtherApp', 'keep'); document.getElementById('journal').value='x'; saveJournal();")
        with page.expect_navigation():
            page.evaluate('newGame()')
        self.assertEqual(page.evaluate("localStorage.getItem('someOtherApp')"), 'keep')
        self.assertEqual(page.evaluate("document.getElementById('journal').value"), '')

    def test_journal_persists(self):
        page = self.open()
        page.fill('#journal', 'Dear diary')
        page.wait_for_timeout(900)
        page.reload()
        self.assertEqual(page.input_value('#journal'), 'Dear diary')

    # ---- stability rules -------------------------------------------------------

    def test_failure_thresholds_come_from_config(self):
        page = self.open()
        got = page.evaluate('[100, 51, 50, 21, 20, 1].map(s => failureThresholdFor(s))')
        self.assertEqual(got, [1, 1, 2, 2, 3, 3])

    def test_pull_shows_flavour_message_and_always_costs_at_least_one(self):
        page = self.open()
        page.evaluate('Math.random = () => 0.99; pullBlock();')          # no die fails -> still lose 1
        self.assertEqual(page.evaluate('gameState.stability'), 99)
        self.assertNotEqual(page.inner_text('#stabilityNote').strip(), '')

    # ---- oracle dice -----------------------------------------------------------

    def test_oracle_labels_come_from_config(self):
        page = self.open()
        page.evaluate('Math.random = () => 0.0; rollTwoDice();')
        self.assertIn('Disturbing', page.inner_text('#diceResult'))
        page.evaluate('Math.random = () => 0.99; rollTwoDice();')
        self.assertIn('Scientifically Significant', page.inner_text('#diceResult'))
        page.evaluate('Math.random = () => 0.0; rollOneDie();')
        self.assertIn('Negative', page.inner_text('#diceResult'))

    # ---- UI config ------------------------------------------------------------

    def test_ui_config_is_honoured(self):
        page = self.open()
        self.assertTrue(page.is_visible('text=Load File'))
        self.assertTrue(page.is_visible('text=Help & Rules'))
        self.assertTrue(page.is_visible('text=Clear history'))
        self.assertIn('The Cave', page.inner_text('.card-reference'))
        self.assertIn('51–100', page.inner_text('.risk-bands'))

    def test_load_journal_file(self):
        page = self.open()
        f = self.tmp / 'j.txt'
        f.write_text('from file')
        page.set_input_files('#journalFile', str(f))
        page.wait_for_timeout(300)
        self.assertEqual(page.input_value('#journal'), 'from file')


@unittest.skipIf(sync_playwright is None, 'playwright not installed')
class ConfigVariantTests(unittest.TestCase):
    """Builds variants of the example with changed config and checks the engine follows it."""

    @classmethod
    def setUpClass(cls):
        import yaml
        cls.yaml = yaml
        cls.tmp = Path(tempfile.mkdtemp())
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def variant(self, name, mutate_config=None, mutate_cards=None):
        g = self.tmp / name
        shutil.copytree(ROOT / 'example-game', g, ignore=shutil.ignore_patterns('*.html'))
        for fname, fn in (('config.yaml', mutate_config), ('cards.yaml', mutate_cards)):
            if fn:
                data = self.yaml.safe_load((g / fname).read_text())
                fn(data)
                (g / fname).write_text(self.yaml.safe_dump(data, allow_unicode=True))
        out = GameBuilder(g).build(g / 'v.html')
        ctx = self.browser.new_context()
        self.addCleanup(ctx.close)
        page = ctx.new_page()
        self.errors = []
        page.on('pageerror', lambda e: self.errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        page.goto('file://' + str(out))
        return page

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def test_pool_size_bounds_loss_per_pull(self):
        page = self.variant('pool', lambda c: c['mechanics']['stability'].update(pool_size=10))
        worst = page.evaluate("""(() => { let max = 0;
            for (let i = 0; i < 3000; i++) { gameState.stability = 100; gameState.gameEnded = false;
                performPull(); max = Math.max(max, 100 - gameState.stability); } return max; })()""")
        self.assertLessEqual(worst, 10)

    def test_risk_scaling_off_uses_safe_number_everywhere(self):
        page = self.variant('noscale', lambda c: c['mechanics']['stability'].update(risk_scaling=False))
        self.assertEqual(page.evaluate('[100, 40, 5].map(failureThresholdFor)'), [1, 1, 1])

    def test_queen_tracker_ends_game(self):
        def cfg(c):
            c['special']['queen_tracker'] = {'enabled': True, 'threshold': 2,
                                             'ending': {'title': 'The Second Queen', 'text': 'Crowned.'}}
        page = self.variant('queens', cfg)
        page.evaluate("""rollForCardCount();
            gameState.deck.push({suit:'spades',value:'Q'}, {suit:'hearts',value:'Q'}); drawCard(); drawCard();""")
        self.assertTrue(page.evaluate('gameState.gameEnded'))
        self.assertIn('The Second Queen', page.inner_text('#cardPrompt'))
        self.assertIn('Queens drawn', page.inner_text('.deck-status >> nth=1'))

    def test_allow_negative_false_clamps_tokens(self):
        page = self.variant('clamp', lambda c: c['mechanics']['tokens'].update(allow_negative=False))
        page.evaluate('gameState.tokens = 1; changeTokens(-5);')
        self.assertEqual(page.evaluate('gameState.tokens'), 0)

    def test_no_win_condition_reshuffles_instead(self):
        page = self.variant('nowin', lambda c: c['conditions'].pop('win'))
        page.evaluate("""gameState.deck = []; gameState.cardsToDraw = 2; drawCard();""")
        self.assertEqual(page.evaluate('gameState.deck.length'), 51)
        self.assertFalse(page.evaluate('gameState.gameEnded'))

    def test_special_card_bound_with_card_key(self):
        def cards(c):
            c['special_cards']['my_roll'] = dict(c['special_cards']['ace_of_hearts'], card='spades.K', button_label='Try Luck')
        page = self.variant('bound', mutate_cards=cards)
        page.evaluate("""Math.random = () => 0.99; gameState.deck.push({suit:'spades',value:'K'});
            rollForCardCount(); drawCard(); viewCard(0);""")
        self.assertIn('Try Luck', page.inner_text('#cardPrompt'))

    def test_ace_special_can_be_disabled(self):
        page = self.variant('noace', lambda c: c['special'].update(ace_of_hearts={'enabled': False}))
        page.evaluate("gameState.deck.push({suit:'hearts',value:'A'}); rollForCardCount(); drawCard(); viewCard(0);")
        self.assertNotIn('Roll 1d6', page.inner_text('#cardPrompt'))

    def test_stability_system_can_be_switched_off(self):
        def cfg(c):
            c['mechanics']['systems'] = ['dice', 'cards', 'tokens']
        page = self.variant('nostab', cfg)
        self.assertEqual(page.locator('#stabilityValue').count(), 0)
        page.evaluate("gameState.deck.push({suit:'hearts',value:'K'}); rollForCardCount(); drawCard(); viewCard(0); applyBasicCardEffects(0);")
        self.assertEqual(page.evaluate('gameState.tokens'), 9)
        self.assertFalse(page.evaluate('gameState.gameEnded'))

    # ---- turn cap (special.turn_sequence.max_cards) --------------------------

    def test_max_cards_caps_turn_even_with_2d6(self):
        page = self.variant('cap', lambda c: c['special'].update(
            turn_sequence={'min_cards': 1, 'max_cards': 6}))
        worst = page.evaluate("""(() => { let max = 0;
            for (let i = 0; i < 400; i++) { gameState.cardsDrawnThisTurn = 0; rollForCardCount();
                max = Math.max(max, gameState.cardsToDraw); } return max; })()""")
        self.assertLessEqual(worst, 6)
        self.assertGreaterEqual(worst, 1)

    def test_single_die_turn_is_worded_as_one_die(self):
        def cfg(c):
            c['mechanics']['dice']['main'] = {'count': 1, 'sides': 6}
            c['special']['turn_sequence'] = {'min_cards': 1, 'max_cards': 6}
        page = self.variant('onedie', cfg)
        page.evaluate('Math.random = () => 0.99; rollForCardCount();')
        text = page.inner_text('#diceResult')
        self.assertIn('Turn die: 6', text)
        self.assertIn('Draw 6 cards', text)
        self.assertEqual(page.evaluate('gameState.cardsToDraw'), 6)


@unittest.skipIf(sync_playwright is None, 'playwright not installed')
class PhoneLayoutTests(unittest.TestCase):
    """The phone layout: sticky status strip, bottom action bar, one contextual primary button."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        game = cls.tmp / 'game'
        shutil.copytree(ROOT / 'example-game', game, ignore=shutil.ignore_patterns('*.html'))
        cls.pages = {n: GameBuilder(game, theme_file=p).build(game / f'{n}.html')
                     for n, p in available_themes().items()}
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def open(self, theme=None, width=390, height=844, touch=True):
        theme = theme or sorted(self.pages)[0]
        ctx = self.browser.new_context(viewport={'width': width, 'height': height},
                                       has_touch=touch, is_mobile=touch)
        self.addCleanup(ctx.close)
        page = ctx.new_page()
        self.errors = []
        page.on('pageerror', lambda e: self.errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        page.goto('file://' + str(self.pages[theme]))
        page.evaluate('localStorage.clear()')
        page.reload()
        return page

    def tearDown(self):
        self.assertEqual(getattr(self, 'errors', []), [])

    def test_bar_and_status_visible_on_phone_hidden_on_desktop(self):
        phone = self.open()
        self.assertTrue(phone.is_visible('.mobile-actions'))
        self.assertTrue(phone.is_visible('.mobile-status'))
        desktop = self.open(width=1280, height=900, touch=False)
        self.assertFalse(desktop.is_visible('.mobile-actions'))
        self.assertFalse(desktop.is_visible('.mobile-status'))

    def test_primary_button_follows_the_game(self):
        page = self.open()
        label = lambda: page.inner_text('#mobilePrimary')
        self.assertIn('Roll', label())
        page.click('#mobilePrimary')                       # roll the turn dice
        page.wait_for_timeout(100)
        self.assertIn('Draw a card', label())
        page.click('#mobilePrimary')                       # draw the first card
        page.wait_for_timeout(100)
        state = page.evaluate('({drawn: gameState.cardsDrawnThisTurn, active: gameState.activeCardIndex})')
        self.assertEqual(state['drawn'], 1)
        self.assertTrue(any(w in label() for w in ('Apply', 'Done', 'Roll 1d6', 'Draw', 'Open')))

    def test_status_strip_tracks_state(self):
        page = self.open()
        page.evaluate('gameState.tokens = 4; refreshAll();')
        self.assertEqual(page.inner_text('#msOil').strip(), '4')
        self.assertEqual(page.inner_text('#msDeck').strip(), '52')

    def test_status_strip_stays_in_view_after_scrolling(self):
        page = self.open()
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        box = page.locator('.mobile-status').bounding_box()
        self.assertLessEqual(abs(box['y']), 1)

    def test_every_theme_fits_every_phone_size_with_big_targets(self):
        for theme in self.pages:
            for w, h in ((360, 640), (390, 844), (844, 390)):
                page = self.open(theme, w, h)
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), w, (theme, w))
                self.assertTrue(page.is_visible('.mobile-actions'), (theme, w))
                small = page.evaluate("""[...document.querySelectorAll('.mobile-actions button, .ms-rules')]
                    .filter(b => b.offsetParent).map(b => b.getBoundingClientRect())
                    .filter(r => r.height < 44 || r.width < 44).length""")
                self.assertEqual(small, 0, (theme, w))

    def test_bar_hides_while_typing_in_journal(self):
        page = self.open()
        page.focus('#journal')
        self.assertFalse(page.is_visible('.mobile-actions'))
        page.evaluate('document.activeElement.blur()')
        self.assertTrue(page.is_visible('.mobile-actions'))


if __name__ == '__main__':
    unittest.main()
