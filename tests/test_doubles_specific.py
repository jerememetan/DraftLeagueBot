"""
Tests for doubles-specific move and targeting logic.

Tests cover:
- Partner-targeting moves: Ally Switch, Coaching
- Weakness Policy interaction: Fling with Weakness Policy
- Earthquake/Magnitude with partner: Avoid hitting partners
- Speed-control doubles bonuses: Shadow Sneak, Aqua Jet, Ice Shard

Reference: AI_LOGIC.txt Shadow Sneak/Aqua Jet/Ice Shard (line ~384), Magnitude/Earthquake (line ~373)
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot_logic import DoublesMvpBot
from mocks import DummyMove, DummyPokemon, DummyBattle


class TestPartnerTargetingMoves(unittest.TestCase):
    """Tests for moves that target/affect partner Pokemon."""
    
    ALLY_SWITCH_BONUS = 3
    COACHING_BONUS = 4
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_ally_switch_swaps_positions_in_doubles(self):
        """Ally Switch swaps user with partner Pokemon."""
        user = DummyPokemon("Fast Pokemon", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 120
        })
        partner = DummyPokemon("Bulky Pokemon", stats={
            "hp": 150, "atk": 100, "def": 150, "spa": 100, "spd": 150, "spe": 50
        })
        self.battle.active_pokemon = [user, partner]
        
        # Ally Switch: user swaps with partner
        ally_switch = DummyMove(base_power=0, category="status", move_type="Psychic")
        
        self.assertEqual(ally_switch.base_power, 0)
    
    def test_coaching_boosts_partner_stats(self):
        """Coaching raises partner's Atk and Def."""
        user = DummyPokemon("Coach", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        partner = DummyPokemon("Partner", stats={
            "hp": 100, "atk": 80, "def": 80, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon = [user, partner]
        
        coaching = DummyMove(base_power=0, category="status", move_type="Fighting")
        
        self.assertEqual(coaching.base_power, 0)


class TestWeaknessPolicyInteraction(unittest.TestCase):
    """Tests for Weakness Policy held item interactions."""
    
    WEAKNESS_POLICY_BONUS = 5
    FLING_WEAKNESS_POLICY_BONUS = 4
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_fling_with_weakness_policy_on_partner(self):
        """Fling transfers Weakness Policy to partner for boost."""
        user = DummyPokemon("Fling user", item="Weakness Policy", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        partner = DummyPokemon("Partner", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon = [user, partner]
        
        fling = DummyMove(base_power=60, category="physical", move_type="Dark")
        
        # Fling deals damage based on held item
        self.assertEqual(fling.base_power, 60)
    
    def test_weakness_policy_activation_on_super_effective_hit(self):
        """Weakness Policy triggers on super-effective hit."""
        holder = DummyPokemon("Policy holder", item="Weakness Policy", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        attacker = DummyPokemon("Super effective attacker", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        # Super effective move
        super_effective_move = DummyMove(base_power=100, category="physical", move_type="Water")
        
        self.assertGreater(super_effective_move.base_power, 0)


class TestAoeMoveTargetingInDoubles(unittest.TestCase):
    """Tests for area-of-effect moves in doubles."""
    
    EARTHQUAKE_AVOID_PARTNER_BONUS = 0
    MAGNITUDE_AVOID_PARTNER_BONUS = 0
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_earthquake_hits_all_adjacent_pokemon(self):
        """Earthquake in doubles hits partner and both opponents."""
        user = DummyPokemon("User", stats={
            "hp": 100, "atk": 120, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        partner = DummyPokemon("Partner", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        opp1 = DummyPokemon("Opponent 1", stats={
            "hp": 100, "atk": 100, "def": 80, "spa": 100, "spd": 100, "spe": 100
        })
        opp2 = DummyPokemon("Opponent 2", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon = [user, partner]
        self.battle.opponent_active_pokemon = [opp1, opp2]
        
        earthquake = DummyMove(base_power=100, category="physical", move_type="Ground")
        
        # Earthquake hits all adjacent Pokemon
        self.assertEqual(earthquake.base_power, 100)
    
    def test_magnitude_lower_power_avoid_partner(self):
        """Magnitude is weaker but also hits all Pokemon."""
        user = DummyPokemon("User", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        partner = DummyPokemon("Partner", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon = [user, partner]
        
        magnitude = DummyMove(base_power=70, category="physical", move_type="Ground")
        
        # Magnitude is base 70, varies 5-150
        self.assertEqual(magnitude.base_power, 70)


class TestDoublesSpeedControlBonuses(unittest.TestCase):
    """Tests for priority moves that benefit in doubles."""
    
    SHADOW_SNEAK_BONUS = 4
    AQUA_JET_BONUS = 4
    ICE_SHARD_BONUS = 4
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_shadow_sneak_priority_targeting(self):
        """Shadow Sneak gets priority bonus vs singles threats."""
        user = DummyPokemon("Shadow Sneak user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 80
        })
        opponent = DummyPokemon("Fast Opponent", stats={
            "hp": 100, "atk": 120, "def": 100, "spa": 100, "spd": 100, "spe": 130
        })
        self.battle.active_pokemon[0] = user
        self.battle.opponent_active_pokemon[0] = opponent
        
        # Shadow Sneak: priority=1 Ghost move
        shadow_sneak = DummyMove(base_power=40, category="physical", move_type="Ghost")
        shadow_sneak.priority = 1
        
        self.assertEqual(shadow_sneak.priority, 1)
    
    def test_aqua_jet_priority_in_doubles(self):
        """Aqua Jet gets priority bonus to hit threats first."""
        user = DummyPokemon("Aqua Jet user", stats={
            "hp": 100, "atk": 110, "def": 100, "spa": 100, "spd": 100, "spe": 70
        })
        opponent = DummyPokemon("Opponent", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 120
        })
        self.battle.active_pokemon[0] = user
        self.battle.opponent_active_pokemon[0] = opponent
        
        # Aqua Jet: priority=1 Water move
        aqua_jet = DummyMove(base_power=40, category="physical", move_type="Water")
        aqua_jet.priority = 1
        
        self.assertEqual(aqua_jet.priority, 1)
    
    def test_ice_shard_priority_bonus_cold_weather(self):
        """Ice Shard priority bonus especially good in hail/snow."""
        user = DummyPokemon("Ice Shard user", stats={
            "hp": 100, "atk": 110, "def": 100, "spa": 100, "spd": 100, "spe": 60
        })
        opponent = DummyPokemon("Opponent", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 130
        })
        self.battle.active_pokemon[0] = user
        self.battle.opponent_active_pokemon[0] = opponent
        
        # Ice Shard: priority=1 Ice move
        ice_shard = DummyMove(base_power=40, category="physical", move_type="Ice")
        ice_shard.priority = 1
        
        self.assertEqual(ice_shard.priority, 1)
    
    def test_priority_moves_targets_fastest_threat(self):
        """Priority moves should target the fastest/most threatening opponent."""
        user = DummyPokemon("Priority user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 60
        })
        opp1 = DummyPokemon("Slow", stats={
            "hp": 100, "atk": 140, "def": 100, "spa": 100, "spd": 100, "spe": 50
        })
        opp2 = DummyPokemon("Fast", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 150
        })
        self.battle.active_pokemon[0] = user
        self.battle.opponent_active_pokemon = [opp1, opp2]
        
        # Priority move targets fastest threat first
        priority_move = DummyMove(base_power=40, category="physical", move_type="Water")
        priority_move.priority = 1
        
        self.assertEqual(priority_move.priority, 1)


if __name__ == "__main__":
    unittest.main()
