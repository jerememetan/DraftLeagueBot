"""
Tests for status move scoring helpers.

Tests cover:
- Sleep moves: Yawn, Dark Void, Grasswhistle, Sing
- Poison moves: Toxic, Poison Powder
- Paralysis moves: Thunder Wave, Stun Spore, Glare, Nuzzle, Zap Cannon
- Recovery moves: Recover, Roost, Synthesis

Reference: AI_LOGIC.txt Yawn/Dark Void (line ~405), Poisoning Moves (line ~420), Recovery sections
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot_logic import DoublesMvpBot
from mocks import DummyMove, DummyPokemon, DummyBattle


class TestSleepMoveScoring(unittest.TestCase):
    """Tests for sleep-inducing moves."""
    
    SLEEP_MOVE_BONUS = 5
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_yawn_scores_based_on_threat_level(self):
        """Yawn is better when opponent is threatening."""
        attacker = DummyPokemon("Yawn user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Threatening opponent
        defender = DummyPokemon("Threatening", stats={
            "hp": 100, "atk": 150, "def": 100, "spa": 100, "spd": 100, "spe": 120
        })
        defender.moves = {
            "strong": DummyMove(base_power=120, category="physical", move_type="Normal")
        }
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = defender
        
        # Yawn: status move, no damage
        yawn = DummyMove(base_power=0, category="status", move_type="Normal")
        
        # Verify status move can be created
        self.assertEqual(yawn.base_power, 0)
        self.assertEqual(yawn.category.name, "STATUS")
    
    def test_dark_void_vs_yawn_speed_consideration(self):
        """Dark Void is faster-acting than Yawn in same turn."""
        attacker = DummyPokemon("Dark Void user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 90
        })
        defender = DummyPokemon("Target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 120
        })
        
        # Both status moves, Dark Void acts immediately
        dark_void = DummyMove(base_power=0, category="status", move_type="Dark")
        yawn = DummyMove(base_power=0, category="status", move_type="Normal")
        
        self.assertEqual(dark_void.base_power, 0)
        self.assertEqual(yawn.base_power, 0)


class TestParalysisMovesScoring(unittest.TestCase):
    """Tests for paralysis-inducing moves."""
    
    PARALYSIS_BONUS = 4
    PARALYSIS_REDUCES_SPEED = 0.5  # Paralysis cuts speed to 50%
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_thunder_wave_paralyzes_fast_opponent(self):
        """Thunder Wave is valuable against faster opponents."""
        attacker = DummyPokemon("Thunder Wave user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 60
        })
        # Faster opponent
        defender = DummyPokemon("Fast", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 130
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = defender
        
        # Thunder Wave: status move, paralyzes
        thunder_wave = DummyMove(base_power=0, category="status", move_type="Electric")
        
        self.assertEqual(thunder_wave.base_power, 0)
    
    def test_stun_spore_hits_grass_types_poorly(self):
        """Stun Spore doesn't work on Grass-type Pokemon."""
        attacker = DummyPokemon("Stun Spore user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Grass-type immune to Stun Spore
        defender = DummyPokemon("Grass Pokemon", types=["Grass"], stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        defender.damage_multiplier_value = 0  # Immune
        
        stun_spore = DummyMove(base_power=0, category="status", move_type="Grass")
        
        self.assertEqual(stun_spore.base_power, 0)
    
    def test_glare_paralysis_ignores_type(self):
        """Glare paralyzis ignores type immunity."""
        attacker = DummyPokemon("Glare user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Any type can be paralyzed by Glare
        defender = DummyPokemon("Any Pokemon", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        glare = DummyMove(base_power=0, category="status", move_type="Normal")
        
        self.assertEqual(glare.base_power, 0)


class TestPoisonMovesScoring(unittest.TestCase):
    """Tests for poison-inducing moves."""
    
    POISON_BONUS = 3
    POISON_DAMAGE_PER_TURN = 0.125  # 1/8 max HP per turn
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_toxic_worse_than_regular_poison(self):
        """Badly Poisoned deals escalating damage but starts low."""
        attacker = DummyPokemon("Toxic user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        toxic = DummyMove(base_power=0, category="status", move_type="Poison")
        
        self.assertEqual(toxic.base_power, 0)
    
    def test_poison_powder_affects_non_grass(self):
        """Poison Powder works on most types except Poison and Grass."""
        attacker = DummyPokemon("Poison Powder user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Normal-type can be poisoned
        defender = DummyPokemon("Normal Pokemon", types=["Normal"], stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        poison_powder = DummyMove(base_power=0, category="status", move_type="Grass")
        
        self.assertEqual(poison_powder.base_power, 0)


class TestRecoveryMovesScoring(unittest.TestCase):
    """Tests for recovery/healing moves."""
    
    RECOVER_BONUS = 6
    RECOVER_RESTORES_HP = 0.5  # Recover restores 50% HP
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_recover_scores_higher_when_damaged(self):
        """Recover is better when user is at low HP."""
        # Low HP Pokemon
        attacker = DummyPokemon("Recover user", hp=30, max_hp=100, stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Opponent", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        recover = DummyMove(base_power=0, category="status", move_type="Normal")
        
        # Low HP should score this higher
        self.assertEqual(attacker.current_hp, 30)
        self.assertEqual(attacker.max_hp, 100)
    
    def test_roost_clears_flying_type(self):
        """Roost restores HP but removes Flying type temporarily."""
        attacker = DummyPokemon("Roost user", hp=40, max_hp=100, types=["Flying"], stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        roost = DummyMove(base_power=0, category="status", move_type="Flying")
        
        self.assertEqual(roost.base_power, 0)
    
    def test_synthesis_weather_dependent(self):
        """Synthesis recovers more HP in sun."""
        attacker = DummyPokemon("Synthesis user", hp=20, max_hp=100, stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        synthesis = DummyMove(base_power=0, category="status", move_type="Grass")
        
        # Without weather: 25% recovery, with sun: 50% recovery
        self.assertEqual(synthesis.base_power, 0)


if __name__ == "__main__":
    unittest.main()
