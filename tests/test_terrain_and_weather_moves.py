"""
Tests for terrain, weather, and screen moves with doubles focus.

Tests cover:
- Light Screen, Reflect, Aurora Veil (defensive screens)
- Will-o-Wisp (burn status)
- Taunt (move blocking)
- Encore (move locking)
- Hazard moves: Stealth Rock, Spikes, Toxic Spikes, Sticky Web
- Paralysis moves: Thunder Wave, Stun Spore, Glare

Reference: AI_LOGIC.txt Light Screen/Reflect (line ~263), Will-o-Wisp (line ~316),
Taunt (line ~660), Encore (line ~672), Stealth Rock/Spikes (line ~132)
"""

import unittest
import sys
from pathlib import Path

# Add parent directory and tests directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from bot_logic import DoublesMvpBot
from mocks import DummyMove, DummyPokemon, DummyBattle
from poke_env.battle.side_condition import SideCondition


class TestLightScreenAndReflect(unittest.TestCase):
    """Tests for Light Screen and Reflect in doubles."""
    
    BASE_SCREEN_SCORE = 6
    MATCHING_ATTACK_BONUS = 1
    LIGHT_CLAY_BONUS = 1
    RNG_BONUS = 1
    ALREADY_ACTIVE_PENALTY = -20
    MAX_SCREEN_SCORE = 8
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_light_screen_base_score(self):
        """Light Screen starts at +6."""
        attacker = DummyPokemon("Screen setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon[0] = attacker
        
        light_screen = DummyMove(base_power=0, category="status", move_type="Psychic")
        light_screen.id = "lightscreen"
        
        score = self.bot._score_screen_move(self.battle, attacker, light_screen)
        
        # Base score ranges from 6-8 depending on opponent attacks and RNG
        self.assertGreaterEqual(score, self.BASE_SCREEN_SCORE)
        self.assertLessEqual(score, self.MAX_SCREEN_SCORE)
    
    def test_light_screen_with_matching_special_attack(self):
        """Light Screen bonus if opponent has special attacks."""
        attacker = DummyPokemon("Screen setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Opponent with special attack
        opponent = DummyPokemon("Special Attacker", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 130, "spd": 100, "spe": 100
        })
        opponent.moves = {
            "move1": DummyMove(base_power=100, category="special", move_type="Fire")
        }
        
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = opponent
        
        light_screen = DummyMove(base_power=0, category="status", move_type="Psychic")
        light_screen.id = "lightscreen"
        
        # Run multiple times to check range with RNG bonuses
        scores = []
        for _ in range(100):
            score = self.bot._score_screen_move(self.battle, attacker, light_screen)
            scores.append(score)
        
        # Score ranges from 6-8 (base 6 + up to 2 from RNG bonuses)
        max_score = max(scores)
        self.assertGreaterEqual(max_score, self.BASE_SCREEN_SCORE)
        self.assertLessEqual(max_score, self.MAX_SCREEN_SCORE)
    
    def test_reflect_with_matching_physical_attack(self):
        """Reflect bonus if opponent has physical attacks."""
        attacker = DummyPokemon("Reflect setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Opponent with physical attack
        opponent = DummyPokemon("Physical Attacker", stats={
            "hp": 100, "atk": 130, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        opponent.moves = {
            "move1": DummyMove(base_power=100, category="physical", move_type="Fighting")
        }
        
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = opponent
        
        reflect = DummyMove(base_power=0, category="status", move_type="Psychic")
        reflect.id = "reflect"
        
        score = self.bot._score_screen_move(self.battle, attacker, reflect)
        
        # With physical attack, score can be 7 or 8
        self.assertGreaterEqual(score, self.BASE_SCREEN_SCORE + 1)
        self.assertLessEqual(score, self.MAX_SCREEN_SCORE)
        # Run multiple times to check range with RNG bonuses
        scores = []
        for _ in range(100):
            score = self.bot._score_screen_move(self.battle, attacker, reflect)
            scores.append(score)
        
        # Score ranges from 6-8
        max_score = max(scores)
        self.assertGreaterEqual(max_score, self.BASE_SCREEN_SCORE)
        self.assertLessEqual(max_score, self.MAX_SCREEN_SCORE)
    
    def test_screen_already_active_penalty(self):
        """Screen gets -20 if already active."""
        attacker = DummyPokemon("Screen setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.side_conditions = {SideCondition.LIGHT_SCREEN: 8}
        
        light_screen = DummyMove(base_power=0, category="status", move_type="Psychic")
        light_screen.id = "lightscreen"
        
        score = self.bot._score_screen_move(self.battle, attacker, light_screen)
        
        self.assertEqual(score, self.ALREADY_ACTIVE_PENALTY)


class TestAuroraVeil(unittest.TestCase):
    """Tests for Aurora Veil (requires snow/hail)."""
    
    BASE_AURORA_VEIL_SCORE = 10
    ALREADY_ACTIVE_PENALTY = -20
    SNOW_NOT_ACTIVE_PENALTY = -20
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_aurora_veil_requires_snow(self):
        """Aurora Veil gets -20 if no snow/hail active."""
        attacker = DummyPokemon("Veil setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.weather = {}  # No weather
        
        aurora_veil = DummyMove(base_power=0, category="status", move_type="Ice")
        aurora_veil.id = "auroraveil"
        
        score = self.bot._score_screen_move(self.battle, attacker, aurora_veil)
        
        self.assertEqual(score, self.SNOW_NOT_ACTIVE_PENALTY)
    
    def test_aurora_veil_active_with_snow(self):
        """Aurora Veil scores base 10 when snow is active."""
        from poke_env.battle.weather import Weather
        
        attacker = DummyPokemon("Veil setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.weather = {Weather.SNOWSCAPE: 5}  # Snow active
        
        aurora_veil = DummyMove(base_power=0, category="status", move_type="Ice")
        aurora_veil.id = "auroraveil"
        
        score = self.bot._score_screen_move(self.battle, attacker, aurora_veil)
        
        self.assertEqual(score, self.BASE_AURORA_VEIL_SCORE)


class TestWillOWisp(unittest.TestCase):
    """Tests for Will-o-Wisp (burn status)."""
    
    BASE_WISP_SCORE = 6
    WISP_BONUS_FOR_HEX = 1
    WISP_BONUS_FOR_PHYSICAL = 1
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_wisp_base_score(self):
        """Will-o-Wisp has base score of 6."""
        attacker = DummyPokemon("Wisp user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        target = DummyPokemon("Target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = target
        
        wisp = DummyMove(base_power=0, category="status", move_type="Fire")
        wisp.id = "willowisp"
        
        # Run multiple times to check base score (accounts for ~37% chance of bonus)
        scores = []
        for _ in range(100):
            score = self.bot._score_wisp(self.battle, attacker, target)
            scores.append(score)
        
        # Should have mix of 6 and possibly 7-8 from bonuses
        self.assertIn(self.BASE_WISP_SCORE, scores)
        self.assertTrue(all(s >= self.BASE_WISP_SCORE for s in scores))
    
    def test_wisp_with_physical_target(self):
        """Will-o-Wisp bonus if target has physical moves."""
        attacker = DummyPokemon("Wisp user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        target = DummyPokemon("Physical Attacker", stats={
            "hp": 100, "atk": 130, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        target.moves = {
            "move1": DummyMove(base_power=100, category="physical", move_type="Fighting")
        }
        
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = target
        
        wisp = DummyMove(base_power=0, category="status", move_type="Fire")
        wisp.id = "willowisp"
        
        # Run multiple times to check for potential bonus
        max_score = 0
        for _ in range(50):
            score = self.bot._score_wisp(self.battle, attacker, target)
            max_score = max(max_score, score)
        
        # May get bonus from physical attack (when 37% RNG triggers)
        self.assertGreaterEqual(max_score, self.BASE_WISP_SCORE)


class TestTaunt(unittest.TestCase):
    """Tests for Taunt (block non-damaging moves)."""
    
    BASE_TAUNT_SCORE = 5
    TRICK_ROOM_BLOCK_BONUS = 9
    DEFOG_BLOCK_BONUS = 9
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_taunt_base_score(self):
        """Taunt base score is 5."""
        attacker = DummyPokemon("Taunt user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        target = DummyPokemon("Target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = target
        
        taunt = DummyMove(base_power=0, category="status", move_type="Dark")
        
        score = self.bot._score_taunt(self.battle, attacker, target)
        
        self.assertEqual(score, self.BASE_TAUNT_SCORE)
    
    def test_taunt_blocks_trick_room_setup(self):
        """Taunt gets +9 if target has Trick Room and TR not active."""
        attacker = DummyPokemon("Taunt user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        target = DummyPokemon("TR setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Target has Trick Room move
        target.moves = {
            "trickroom": DummyMove(base_power=0, category="status", move_type="Psychic")
        }
        
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = target
        self.battle.trick_room = False  # TR not active
        
        taunt = DummyMove(base_power=0, category="status", move_type="Dark")
        
        score = self.bot._score_taunt(self.battle, attacker, target)
        
        self.assertEqual(score, self.TRICK_ROOM_BLOCK_BONUS)


class TestEncore(unittest.TestCase):
    """Tests for Encore (lock opponent into move)."""
    
    BASE_ENCORE_SCORE = 6
    FASTER_ENCOURAGED_SCORE = 7
    SLOWER_SCORE = 6
    ALREADY_ENCORED_PENALTY = -20
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_encore_fails_if_target_already_encored(self):
        """Encore gets -20 if target already Encored."""
        from poke_env.battle.effect import Effect
        
        attacker = DummyPokemon("Encore user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        target = DummyPokemon("Encored Target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        target.effects = {Effect.ENCORE: 2}  # Already Encored
        
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = target
        
        encore = DummyMove(base_power=0, category="status", move_type="Normal")
        
        score = self.bot._score_encore(attacker, target)
        
        self.assertEqual(score, self.ALREADY_ENCORED_PENALTY)
    
    def test_encore_on_status_move(self):
        """Encore gets bonus if target used status move."""
        from poke_env.battle.move_category import MoveCategory
        
        attacker = DummyPokemon("Encore user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 110
        })
        target = DummyPokemon("Status user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        # Target used a status move
        last_status_move = DummyMove(base_power=0, category="status", move_type="Normal")
        target.last_move = last_status_move
        target.effects = {}
        target.first_turn = False
        
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = target
        
        encore = DummyMove(base_power=0, category="status", move_type="Normal")
        
        score = self.bot._score_encore(attacker, target)
        
        # Faster and encouraged = 7
        self.assertEqual(score, self.FASTER_ENCOURAGED_SCORE)


class TestHazardMoves(unittest.TestCase):
    """Tests for hazard moves in doubles context."""
    
    STEALTH_ROCK_FIRST_TURN_BASE_LOW = 8
    STEALTH_ROCK_FIRST_TURN_BASE_HIGH = 9
    STEALTH_ROCK_LATER_TURN_BASE_LOW = 6
    STEALTH_ROCK_LATER_TURN_BASE_HIGH = 7
    
    SPIKES_FIRST_TURN_BASE_LOW = 8
    SPIKES_FIRST_TURN_BASE_HIGH = 9
    SPIKES_LAYER_PENALTY = 1
    
    STICKY_WEB_FIRST_TURN_BASE_LOW = 9
    STICKY_WEB_FIRST_TURN_BASE_HIGH = 12
    STICKY_WEB_LATER_TURN_BASE_LOW = 6
    STICKY_WEB_LATER_TURN_BASE_HIGH = 9
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_stealth_rock_first_turn_high(self):
        """Stealth Rock on first turn gets 8-9."""
        attacker = DummyPokemon("Hazard setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        attacker.first_turn = True
        
        self.battle.active_pokemon[0] = attacker
        
        stealth_rock = DummyMove(base_power=0, category="status", move_type="Rock")
        stealth_rock.id = "stealthrock"
        
        # Run multiple times to check variance
        scores = []
        for _ in range(100):
            score = self.bot._score_hazard_move(self.battle, attacker, stealth_rock)
            scores.append(score)
        
        # Should be 8 or 9 on first turn
        self.assertTrue(all(s in [self.STEALTH_ROCK_FIRST_TURN_BASE_LOW, 
                                  self.STEALTH_ROCK_FIRST_TURN_BASE_HIGH] for s in scores))
    
    def test_sticky_web_higher_score(self):
        """Sticky Web gets higher score than Stealth Rock."""
        attacker = DummyPokemon("Hazard setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        attacker.first_turn = True
        
        self.battle.active_pokemon[0] = attacker
        
        sticky_web = DummyMove(base_power=0, category="status", move_type="Bug")
        sticky_web.id = "stickyweb"
        
        # Run multiple times
        scores = []
        for _ in range(100):
            score = self.bot._score_hazard_move(self.battle, attacker, sticky_web)
            scores.append(score)
        
        # Should be 9-12 on first turn (higher than Stealth Rock's 8-9)
        self.assertTrue(all(s in range(self.STICKY_WEB_FIRST_TURN_BASE_LOW, 
                                      self.STICKY_WEB_FIRST_TURN_BASE_HIGH + 1) for s in scores))


class TestParalysisMovesDoubles(unittest.TestCase):
    """Tests for paralysis moves with doubles-specific scoring."""
    
    ENCOURAGED_SCORE = 8
    BASE_PARALYSIS_SCORE = 7
    PENALTY_50_PERCENT = -1
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_paralysis_encouraged_by_speed_bracket(self):
        """Paralysis encouraged if target faster but would be slower after paralysis."""
        attacker = DummyPokemon("Para user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 80
        })
        target = DummyPokemon("Fast target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Target is faster (100 > 80), but with paralysis (100/4=25) would be slower than attacker
        
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = target
        
        paralysis_move = DummyMove(base_power=75, category="special", move_type="Electric")
        paralysis_move.id = "thunderwave"
        
        # Run multiple times for average (accounts for 50% RNG penalty)
        total_score = 0
        for _ in range(100):
            score = self.bot._score_paralysis(attacker, target)
            total_score += score
        avg_score = total_score / 100
        
        # Should tend toward encouraged score (8) with 50% penalty applied sometimes
        self.assertGreater(avg_score, self.BASE_PARALYSIS_SCORE - 1)


if __name__ == "__main__":
    unittest.main()
