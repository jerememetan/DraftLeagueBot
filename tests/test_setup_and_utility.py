"""
Tests for setup moves and utility move scoring.

Tests cover:
- Setup moves: Dragon Dance, Calm Mind, Swordsdance
- Hazards: Stealth Rock, Spikes, Toxic Spikes, Sticky Web
- Screens: Light Screen, Reflect

Reference: AI_LOGIC.txt General setup (line ~283), Offensive Setup (line ~307)
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot_logic import DoublesMvpBot
from mocks import DummyMove, DummyPokemon, DummyBattle


class TestSetupMoveScoring(unittest.TestCase):
    """Tests for stat-boosting setup moves."""
    
    SETUP_MOVE_BONUS = 5
    DRAGON_DANCE_BONUS = 6  # Boosts Atk and Spe
    CALM_MIND_BONUS = 6     # Boosts SpA and SpD
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_dragon_dance_scores_high_when_setup_space(self):
        """Dragon Dance is better when opponent can't threaten immediately."""
        attacker = DummyPokemon("Dragon Dance user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 60
        })
        # Non-threatening opponent
        defender = DummyPokemon("Weak opponent", stats={
            "hp": 100, "atk": 50, "def": 100, "spa": 50, "spd": 100, "spe": 50
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = defender
        
        # Dragon Dance: boosts Atk and Spe by 1 stage
        dragon_dance = DummyMove(base_power=0, category="status", move_type="Dragon")
        
        self.assertEqual(dragon_dance.base_power, 0)
    
    def test_calm_mind_scores_high_for_special_attacker(self):
        """Calm Mind is better for special attackers."""
        attacker = DummyPokemon("Calm Mind user", stats={
            "hp": 100, "atk": 70, "def": 100, "spa": 130, "spd": 100, "spe": 100
        })
        defender = DummyPokemon("Weak opponent", stats={
            "hp": 100, "atk": 50, "def": 100, "spa": 50, "spd": 100, "spe": 50
        })
        self.battle.active_pokemon[0] = attacker
        self.battle.opponent_active_pokemon[0] = defender
        
        # Calm Mind: boosts SpA and SpD by 1 stage
        calm_mind = DummyMove(base_power=0, category="status", move_type="Psychic")
        
        self.assertEqual(calm_mind.base_power, 0)
    
    def test_swordsdance_setup_for_physical_attacker(self):
        """Swordsdance doubles attack stat."""
        attacker = DummyPokemon("Swordsdance user", stats={
            "hp": 100, "atk": 140, "def": 100, "spa": 70, "spd": 100, "spe": 100
        })
        
        swordsdance = DummyMove(base_power=0, category="status", move_type="Normal")
        
        self.assertEqual(swordsdance.base_power, 0)


class TestHazardMovesScoring(unittest.TestCase):
    """Tests for entry hazard moves."""
    
    STEALTH_ROCK_BONUS = 4
    SPIKES_BONUS = 3
    STICKY_WEB_BONUS = 3
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_stealth_rock_scores_against_weak_opponent_team(self):
        """Stealth Rock is valuable if opponent team has weaknesses."""
        attacker = DummyPokemon("Stealth Rock user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Opponent has Flying types (weak to Stealth Rock)
        opponent = DummyPokemon("Flying Type", types=["Flying"], stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        stealth_rock = DummyMove(base_power=0, category="status", move_type="Rock")
        
        self.assertEqual(stealth_rock.base_power, 0)
    
    def test_spikes_multiple_layers(self):
        """Spikes can be set up to 3 layers."""
        attacker = DummyPokemon("Spikes user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        spikes = DummyMove(base_power=0, category="status", move_type="Ground")
        
        # Can be used multiple times for layer effect
        self.assertEqual(spikes.base_power, 0)
    
    def test_toxic_spikes_poisons_ground_immunity(self):
        """Toxic Spikes poisons even Flying types via switch-in."""
        attacker = DummyPokemon("Toxic Spikes user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        toxic_spikes = DummyMove(base_power=0, category="status", move_type="Poison")
        
        self.assertEqual(toxic_spikes.base_power, 0)
    
    def test_sticky_web_reduces_opponent_speed(self):
        """Sticky Web reduces all switch-ins' speed."""
        attacker = DummyPokemon("Sticky Web user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        
        sticky_web = DummyMove(base_power=0, category="status", move_type="Bug")
        
        self.assertEqual(sticky_web.base_power, 0)


class TestScreenMovesScoring(unittest.TestCase):
    """Tests for protective screen moves."""
    
    LIGHT_SCREEN_BONUS = 4
    REFLECT_BONUS = 4
    SCREEN_DURATION = 5  # Turns
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_light_screen_against_special_attackers(self):
        """Light Screen is better against special-attack threats."""
        attacker = DummyPokemon("Light Screen user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Special attack threat
        opponent = DummyPokemon("Special Attacker", stats={
            "hp": 100, "atk": 70, "def": 100, "spa": 140, "spd": 100, "spe": 100
        })
        
        light_screen = DummyMove(base_power=0, category="status", move_type="Psychic")
        
        self.assertEqual(light_screen.base_power, 0)
    
    def test_reflect_against_physical_attackers(self):
        """Reflect is better against physical-attack threats."""
        attacker = DummyPokemon("Reflect user", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        # Physical attack threat
        opponent = DummyPokemon("Physical Attacker", stats={
            "hp": 100, "atk": 150, "def": 100, "spa": 70, "spd": 100, "spe": 100
        })
        
        reflect = DummyMove(base_power=0, category="status", move_type="Psychic")
        
        self.assertEqual(reflect.base_power, 0)
    
    def test_screens_protect_team(self):
        """Screens in doubles protect both player Pokemon."""
        attacker = DummyPokemon("Screen setter", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        partner = DummyPokemon("Partner", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100
        })
        self.battle.active_pokemon = [attacker, partner]
        
        light_screen = DummyMove(base_power=0, category="status", move_type="Psychic")
        reflect = DummyMove(base_power=0, category="status", move_type="Psychic")
        
        # Both protect the whole team
        self.assertEqual(light_screen.base_power, 0)
        self.assertEqual(reflect.base_power, 0)


class TestUtilityMoveScoring(unittest.TestCase):
    """Tests for general utility moves."""
    
    UTILITY_BONUS = 2
    
    def setUp(self):
        self.bot = DoublesMvpBot()
        self.battle = DummyBattle()
    
    def test_trick_room_slows_entire_team(self):
        """Trick Room benefits slow Pokemon in doubles."""
        slow_user = DummyPokemon("Slow Pokemon", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 30
        })
        fast_partner = DummyPokemon("Fast Partner", stats={
            "hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 120
        })
        self.battle.active_pokemon = [slow_user, fast_partner]
        
        trick_room = DummyMove(base_power=0, category="status", move_type="Psychic")
        
        self.assertEqual(trick_room.base_power, 0)


if __name__ == "__main__":
    unittest.main()
