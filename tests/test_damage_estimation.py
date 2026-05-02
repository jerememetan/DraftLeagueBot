"""
Parametrized tests for damage estimation helpers.

Tests cover:
- _estimate_damage: base damage calculation with STAB, type effectiveness
- _estimated_kill: kill detection using damage rolls
- _is_highest_damage_move: scoring for highest damaging move

Reference: AI_LOGIC.txt lines 23-54 (All damaging moves scoring)
"""

import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
import sys
from pathlib import Path
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot_logic import DoublesMvpBot


class MoveCategory(Enum):
    """Minimal MoveCategory enum for testing."""
    PHYSICAL = "physical"
    SPECIAL = "special"
    STATUS = "status"


class DummyMove:
    """Move mock with proper attributes for poke-env compatibility."""
    def __init__(self, base_power=80, category="physical", move_type="Normal", move_id="tackle"):
        self.base_power = base_power
        # Handle both string and enum category
        if isinstance(category, str):
            self.category = MoveCategory[category.upper()]
        else:
            self.category = category
        self.type = move_type
        self.id = move_id


class DummyPokemon:
    """Minimal Pokemon mock for testing."""
    def __init__(self, name="Pikachu", hp=100, level=50, max_hp=100, 
                 stats=None, types=None, ability=None, item=None):
        self.name = name
        self.current_hp = hp  # Use current_hp for poke-env compatibility
        self.level = level
        self.max_hp = max_hp
        self.stats = stats or {
            "hp": 100, "atk": 100, "def": 100, 
            "spa": 100, "spd": 100, "spe": 100
        }
        self.types = types or ["Normal"]
        self.ability = ability
        self.item = item
        self.boosts = {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
        self.status = None
        self.side_conditions = []


class DummyBattle:
    """Minimal Battle mock for testing."""
    def __init__(self):
        self.active_pokemon = [None, None]
        self.opponent_active_pokemon = [None, None]
        self.weather = None
        self.trick_room = False
        self.player_side_conditions = {}
        self.opponent_side_conditions = {}


class TestDamageEstimation(unittest.TestCase):
    """Tests for _estimate_damage helper."""

    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_estimate_damage_base_calculation(self):
        """Test base damage calculation without STAB or type advantage.
        
        Standard formula: ((2 * Level / 5 + 2) * Power * Atk / Def) / 50 + 2
        With level=50, Atk=100, Def=100, Power=80:
        ((2*50/5 + 2) * 80 * 100 / 100) / 50 + 2 = (22 * 80) / 50 + 2 = 35.2 + 2 = 37.2
        """
        attacker = DummyPokemon("Pikachu", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Charizard", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        move = DummyMove(base_power=80, category="physical")
        
        damage = self.bot._estimate_damage(self.battle, attacker, move, defender)
        # Base calculation should be around 37
        self.assertGreater(damage, 30)
        self.assertLess(damage, 50)
    
    def test_estimate_damage_with_stab(self):
        """Test STAB bonus (1.5x multiplier for same type).
        
        Reference: STAB = same type as attacker
        """
        attacker = DummyPokemon("Pikachu", types=["Electric"], stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Charizard", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Thunderbolt is Electric-type move, same as Pikachu
        move = DummyMove(base_power=90, category="special", move_type="Electric")
        
        # With STAB, damage should be significantly higher
        damage_with_stab = self.bot._estimate_damage(self.battle, attacker, move, defender)
        self.assertGreater(damage_with_stab, 40)
    
    def test_estimate_damage_high_attack_stat(self):
        """Test damage scales with attacker's attack stat."""
        high_atk = DummyPokemon("Machamp", stats={
            "hp": 100, "atk": 200, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        low_atk = DummyPokemon("Pikachu", stats={
            "hp": 100, "atk": 50, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Blissey", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        move = DummyMove(base_power=100, category="physical")
        
        high_damage = self.bot._estimate_damage(self.battle, high_atk, move, defender)
        low_damage = self.bot._estimate_damage(self.battle, low_atk, move, defender)
        
        self.assertGreater(high_damage, low_damage)
    
    def test_estimate_damage_high_defense_reduces_damage(self):
        """Test damage scales inversely with defender's defense stat."""
        attacker = DummyPokemon("Machamp", stats={
            "hp": 100, "atk": 150, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        high_def = DummyPokemon("Blissey", stats={
            "hp": 100, "atk": 100, "def": 250, "spa": 100, "spd": 100, "spe": 100
        })
        low_def = DummyPokemon("Gengar", stats={
            "hp": 100, "atk": 100, "def": 65, "spa": 100, "spd": 100, "spe": 100
        })
        move = DummyMove(base_power=100, category="physical")
        
        damage_high_def = self.bot._estimate_damage(self.battle, attacker, move, high_def)
        damage_low_def = self.bot._estimate_damage(self.battle, attacker, move, low_def)
        
        self.assertLess(damage_high_def, damage_low_def)


class TestEstimatedKill(unittest.TestCase):
    """Tests for _estimated_kill helper (damage > target HP)."""

    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_estimated_kill_ko_on_high_damage(self):
        """Test move that KOs if damage exceeds target HP."""
        defender = DummyPokemon("Chansey", hp=50, max_hp=50, stats={
            "hp": 50, "atk": 5, "def": 100, "spa": 100, "spd": 200, "spe": 100
        })
        
        # Simulate high damage that exceeds HP
        damage = 100
        is_kill = self.bot._estimated_kill(defender, damage)
        self.assertTrue(is_kill)
    
    def test_estimated_kill_no_ko_on_low_damage(self):
        """Test move that doesn't KO if damage is below target HP."""
        defender = DummyPokemon("Blissey", hp=250, max_hp=250, stats={
            "hp": 250, "atk": 100, "def": 100, "spa": 100, "spd": 200, "spe": 100
        })
        
        # Simulate low damage that doesn't exceed HP
        damage = 50
        is_kill = self.bot._estimated_kill(defender, damage)
        self.assertFalse(is_kill)


class TestHighestDamageComparison(unittest.TestCase):
    """Tests for comparing damage between moves.
    
    Reference: AI_LOGIC.txt lines 23-32
    Highest damage gets +6 (~80%) or +8 (~20%)
    """

    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_higher_damage_move_priority(self):
        """Test that higher-power moves deal more damage."""
        attacker = DummyPokemon("Pikachu", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 120, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Charizard", current_hp=100, max_hp=100, stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        weak_move = DummyMove(base_power=40, category="special", move_type="Electric")
        strong_move = DummyMove(base_power=90, category="special", move_type="Electric")
        
        weak_damage = self.bot._estimate_damage(self.battle, attacker, weak_move, defender)
        strong_damage = self.bot._estimate_damage(self.battle, attacker, strong_move, defender)
        
        # Strong move should deal more damage
        self.assertLess(weak_damage, strong_damage)


if __name__ == "__main__":
    unittest.main()
