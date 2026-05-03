"""
Parametrized tests for threat and speed evaluation helpers.

Tests cover:
- _is_faster: simple speed comparison
- _is_threatened_by: max-roll damage threat detection
- _speed_profile: team-wide min/max speed analysis
- _score_tailwind: speed-boost move scoring (AI_LOGIC.txt, Tailwind section)
- _score_trick_room: speed-reversal move scoring (AI_LOGIC.txt, Trick Room section)

Reference: AI_LOGIC.txt Tailwind (line ~456) and Trick Room (line ~465)
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot_logic import DoublesMvpBot
from mocks import MoveCategory, DummyMove, DummyPokemon, DummyBattle


class TestIsFaster(unittest.TestCase):
    """Tests for _is_faster helper (simple speed comparison)."""

    def setUp(self):
        self.bot = DoublesMvpBot()
    
    def test_is_faster_higher_speed(self):
        """Test Pokemon with higher speed stat is faster."""
        faster = DummyPokemon("Alakazam", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 120
        })
        slower = DummyPokemon("Blissey", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 55
        })
        
        self.assertTrue(self.bot._is_faster(faster, slower))
        self.assertFalse(self.bot._is_faster(slower, faster))
    
    def test_is_faster_equal_speed(self):
        """Test Pokemon with equal speed are not considered faster."""
        pokemon1 = DummyPokemon("Pikachu", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        pokemon2 = DummyPokemon("Raichu", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        # Equal speed means neither is faster
        self.assertFalse(self.bot._is_faster(pokemon1, pokemon2))
        self.assertFalse(self.bot._is_faster(pokemon2, pokemon1))
    
    def test_is_faster_ignores_stat_boosts(self):
        """Test that speed comparison ignores stat boosts (compares raw stats only).
        
        _is_faster just compares raw stats["spe"], doesn't use boost multipliers.
        """
        faster_boosted = DummyPokemon("Pikachu", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 60
        })
        slower = DummyPokemon("Machamp", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        # Pikachu 60 < Machamp 100, even if boosts were applied
        self.assertFalse(self.bot._is_faster(faster_boosted, slower))


class TestIsThreatenedBy(unittest.TestCase):
    """Tests for _is_threatened_by helper (max-roll kill detection).
    
    Reference: AI_LOGIC.txt threat evaluation for setup moves and recovery decisions.
    _is_threatened_by(battle, attacker, defender) checks if attacker can KO defender with max rolls.
    """

    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_is_threatened_by_strong_opponent(self):
        """Test Pokemon is threatened if opponent has KO move."""
        defender = DummyPokemon(
            "Charizard", current_hp=100, max_hp=100, stats={
                "hp": 100, "atk": 100, "def": 65, "spa": 100, "spd": 80, "spe": 100
            }
        )
        # Add defender to battle
        self.battle.active_pokemon[0] = defender
        
        attacker = DummyPokemon(
            "Alakazam", stats={
                "hp": 100, "atk": 100, "def": 100, "spa": 185, "spd": 100, "spe": 120
            }
        )
        # Alakazam with strong moves in its move pool
        attacker.moves = {
            "psychic": DummyMove(base_power=120, category="special", move_type="Psychic")
        }
        # Add attacker to opponent side for threat evaluation
        self.battle.opponent_active_pokemon[0] = attacker
        
        threat = self.bot._is_threatened_by(self.battle, attacker, defender)
        self.assertTrue(threat)
    
    def test_is_not_threatened_by_weak_opponent(self):
        """Test Pokemon is not threatened by weak opponents."""
        defender = DummyPokemon(
            "Blissey", current_hp=300, max_hp=300, stats={
                "hp": 300, "atk": 100, "def": 100, "spa": 100, "spd": 200, "spe": 100
            }
        )
        # Add defender to battle
        self.battle.active_pokemon[0] = defender
        
        attacker = DummyPokemon(
            "Pikachu", stats={
                "hp": 100, "atk": 50, "def": 100, "spa": 60, "spd": 100, "spe": 100
            }
        )
        # Weak moves
        attacker.moves = {
            "thunderbolt": DummyMove(base_power=90, category="special", move_type="Electric")
        }
        
        threat = self.bot._is_threatened_by(self.battle, attacker, defender)
        # Weak Pokemon with bulky defender shouldn't threaten
        self.assertFalse(threat)


class TestSpeedProfile(unittest.TestCase):
    """Tests for _speed_profile helper (team-wide min/max speed analysis).
    
    Returns tuple: (min_ally_speed, max_ally_speed, min_opponent_speed, max_opponent_speed)
    """

    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_speed_profile_single_pokemon_each_side(self):
        """Test speed profile with one active Pokemon on each side."""
        self.battle.active_pokemon[0] = DummyPokemon(
            "Pikachu", stats={"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100}
        )
        self.battle.opponent_active_pokemon[0] = DummyPokemon(
            "Alakazam", stats={"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 120}
        )
        
        profile = self.bot._speed_profile(self.battle)
        
        self.assertIsNotNone(profile)
        min_ally, max_ally, min_opp, max_opp = profile
        self.assertEqual(min_ally, 100)
        self.assertEqual(max_ally, 100)
        self.assertEqual(min_opp, 120)
        self.assertEqual(max_opp, 120)
    
    def test_speed_profile_multiple_pokemon_per_side(self):
        """Test speed profile with multiple Pokemon per side (doubles)."""
        self.battle.active_pokemon[0] = DummyPokemon(
            "Pikachu", stats={"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100}
        )
        self.battle.active_pokemon[1] = DummyPokemon(
            "Raichu", stats={"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 110}
        )
        self.battle.opponent_active_pokemon[0] = DummyPokemon(
            "Alakazam", stats={"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 120}
        )
        self.battle.opponent_active_pokemon[1] = DummyPokemon(
            "Gengar", stats={"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 130}
        )
        
        profile = self.bot._speed_profile(self.battle)
        
        self.assertIsNotNone(profile)
        min_ally, max_ally, min_opp, max_opp = profile
        # Allies: Pikachu 100, Raichu 110
        self.assertEqual(min_ally, 100)
        self.assertEqual(max_ally, 110)
        # Opponents: Alakazam 120, Gengar 130
        self.assertEqual(min_opp, 120)
        self.assertEqual(max_opp, 130)


class TestScoreTailwind(unittest.TestCase):
    """Tests for _score_tailwind helper.
    
    Reference: AI_LOGIC.txt Tailwind section
    Base: +6, Additional scores based on speed comparisons
    - If already active: -20
    """
    
    TAILWIND_BASE_SCORE = 6
    ALREADY_ACTIVE_PENALTY = -20

    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_tailwind_already_active_via_side_conditions(self):
        """Tailwind scores -20 when already active on ally side."""
        self.battle.active_pokemon[0] = DummyPokemon("Pikachu")
        self.battle.trick_room = False
        
        # Import SideCondition to test with real enum
        try:
            from poke_env.battle.side_condition import SideCondition
            self.battle.side_conditions = {SideCondition.TAILWIND: (100, 3)}
            
            score = self.bot._score_tailwind(self.battle)
            self.assertEqual(score, -20)
        except ImportError:
            # Skip if poke_env not available in test context
            self.skipTest("poke_env not available")
    
    def test_tailwind_team_slower_than_opponent(self):
        """Tailwind scores higher when AI team is slower (base scoring)."""
        # Setup: AI team slower than opponent team
        self.battle.active_pokemon[0] = DummyPokemon(
            "Blissey", stats={"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 200, "spe": 55}
        )
        self.battle.opponent_active_pokemon[0] = DummyPokemon(
            "Alakazam", stats={"hp": 100, "atk": 100, "def": 100, "spa": 185, "spd": 100, "spe": 120}
        )
        self.battle.trick_room = False
        self.battle.side_conditions = {}
        
        score = self.bot._score_tailwind(self.battle)
        # Base is 6, + bonuses for being slower = should be > 6
        self.assertGreater(score, self.TAILWIND_BASE_SCORE)


class TestScoreTrickRoom(unittest.TestCase):
    """Tests for _score_trick_room helper.
    
    Reference: AI_LOGIC.txt Trick Room section
    Base: +6, Additional scoring based on speed/conditions
    - If already active: -20
    """
    
    TRICK_ROOM_BASE_SCORE = 6
    ALREADY_ACTIVE_PENALTY = -20

    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_trick_room_already_active(self):
        """Trick Room scores -20 when already active in battle."""
        self.battle.active_pokemon[0] = DummyPokemon("Pikachu")
        self.battle.trick_room = True  # Already active
        
        score = self.bot._score_trick_room(self.battle)
        self.assertEqual(score, -20)
    
    def test_trick_room_team_slower_than_opponent(self):
        """Trick Room scores bonus when AI team is slower (reversal beneficial)."""
        # Setup: AI team slower than opponent
        self.battle.active_pokemon[0] = DummyPokemon(
            "Blissey", stats={"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 200, "spe": 55}
        )
        self.battle.opponent_active_pokemon[0] = DummyPokemon(
            "Alakazam", stats={"hp": 100, "atk": 100, "def": 100, "spa": 185, "spd": 100, "spe": 120}
        )
        self.battle.trick_room = False
        self.battle.side_conditions = {}
        
        score = self.bot._score_trick_room(self.battle)
        # Base is 6, + bonuses for being slower = should be > 6
        self.assertGreater(score, self.TRICK_ROOM_BASE_SCORE)
    
    def test_trick_room_team_faster_than_opponent(self):
        """Trick Room scores lower when AI team is faster (reversal not beneficial)."""
        # Setup: AI team faster than opponent
        self.battle.active_pokemon[0] = DummyPokemon(
            "Alakazam", stats={"hp": 100, "atk": 100, "def": 100, "spa": 185, "spd": 100, "spe": 120}
        )
        self.battle.opponent_active_pokemon[0] = DummyPokemon(
            "Blissey", stats={"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 200, "spe": 55}
        )
        self.battle.trick_room = False
        self.battle.side_conditions = {}
        
        score = self.bot._score_trick_room(self.battle)
        # When faster, trick room gets penalty (max_ally > max_foe reduces score by 5)
        self.assertLess(score, self.TRICK_ROOM_BASE_SCORE)


if __name__ == "__main__":
    unittest.main()
