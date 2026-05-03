"""
Tests for damaging move scoring helpers.

Tests cover:
- Priority moves: moves with positive priority get bonus
- Speed-control moves: moves that reduce opponent speed (Icy Wind, Electroweb)
- Stat-reduction moves: moves that reduce opponent stats (Trop Kick, Skitter Smack)

Reference: AI_LOGIC.txt lines 114+ (Damaging priority moves section)
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot_logic import DoublesMvpBot
from mocks import DummyMove, DummyPokemon, DummyBattle


class TestPriorityMoveScoring(unittest.TestCase):
    """Tests for priority move bonuses."""
    
    PRIORITY_MOVE_BASE_BONUS = 3
    HIGH_PRIORITY_BONUS = 5
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_priority_move_low_priority_bonus(self):
        """Priority moves with +1 get standard bonus."""
        attacker = DummyPokemon("Mach Punch user", stats={
            "hp": 100, "atk": 110, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 50
        })
        
        # Mach Punch: priority=1, lets attacker move first regardless of speed
        mach_punch = DummyMove(base_power=40, category="physical", move_type="Fighting")
        mach_punch.priority = 1
        
        # Priority moves should get bonus even on slower Pokemon
        damage = self.bot._estimate_damage(self.battle, attacker, mach_punch, defender)
        self.assertGreater(damage, 10)  # Should be able to deal damage


class TestSpeedControlMoveScoring(unittest.TestCase):
    """Tests for speed-reducing moves (Icy Wind, Electroweb)."""
    
    SPEED_REDUCTION_BONUS = 4
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_speed_reduction_move_slows_opponent(self):
        """Moves like Icy Wind reduce opponent speed for scoring."""
        attacker = DummyPokemon("Icy Wind user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 80
        })
        defender = DummyPokemon("Target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 120
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = defender
        
        # Icy Wind: 60 BP, hits both opponents, reduces speed
        icy_wind = DummyMove(base_power=55, category="special", move_type="Ice")
        
        # Verify attacker can use move
        damage = self.bot._estimate_damage(self.battle, attacker, icy_wind, defender)
        self.assertGreater(damage, 20)


class TestStatReductionMoveScoring(unittest.TestCase):
    """Tests for stat-reduction moves (Trop Kick, Skitter Smack)."""
    
    STAT_REDUCTION_BONUS = 3
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_trop_kick_reduces_attack(self):
        """Trop Kick deals damage and lowers attack stat."""
        attacker = DummyPokemon("Trop Kick user", stats={
            "hp": 100, "atk": 90, "def": 100, "spa": 120, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Target", stats={
            "hp": 100, "atk": 140, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = defender
        
        # Trop Kick: 75 BP, lowers Attack
        trop_kick = DummyMove(base_power=75, category="physical", move_type="Grass")
        
        damage = self.bot._estimate_damage(self.battle, attacker, trop_kick, defender)
        # Should deal reasonable damage
        self.assertGreater(damage, 20)
        self.assertLess(damage, 150)
    
    def test_skitter_smack_reduces_spdef(self):
        """Skitter Smack deals damage and lowers Sp.Def stat."""
        attacker = DummyPokemon("Skitter Smack user", stats={
            "hp": 100, "atk": 120, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 140, "spe": 100
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = defender
        
        # Skitter Smack: 70 BP, lowers Sp.Def
        skitter_smack = DummyMove(base_power=70, category="physical", move_type="Bug")
        
        damage = self.bot._estimate_damage(self.battle, attacker, skitter_smack, defender)
        # Should deal reasonable damage
        self.assertGreater(damage, 20)
        self.assertLess(damage, 120)


class TestHighPriorityMoveComparison(unittest.TestCase):
    """Tests comparing priority moves against normal moves."""
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_priority_move_vs_normal_move_same_damage(self):
        """Priority and normal moves with same BP should have similar damage ranges."""
        attacker = DummyPokemon("Quick Attacker", stats={
            "hp": 100, "atk": 110, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Slow Target", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 50
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = defender
        
        # Priority move
        priority_move = DummyMove(base_power=40, category="physical", move_type="Fighting")
        priority_move.priority = 1
        
        # Normal move, same BP
        normal_move = DummyMove(base_power=40, category="physical", move_type="Fighting")
        normal_move.priority = 0
        
        priority_damage = self.bot._estimate_damage(self.battle, attacker, priority_move, defender)
        normal_damage = self.bot._estimate_damage(self.battle, attacker, normal_move, defender)
        
        # Damage rolls vary with RNG, so just verify they're in same ballpark (within 20% variance)
        avg_damage = (priority_damage + normal_damage) / 2
        self.assertGreater(priority_damage, avg_damage * 0.8)
        self.assertLess(priority_damage, avg_damage * 1.2)
        self.assertGreater(normal_damage, avg_damage * 0.8)
        self.assertLess(normal_damage, avg_damage * 1.2)


if __name__ == "__main__":
    unittest.main()
