import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from bot_logic import DoublesMvpBot
from poke_env.battle.side_condition import SideCondition
from mocks import DummyBattle
from fixtures import make_pokemon, make_move


class BotLogicRegressionTests(unittest.TestCase):
    def setUp(self):
        self.bot = DoublesMvpBot.__new__(DoublesMvpBot)
        self.bot._debug = False
        self.bot._debug_turns = 0

    def make_pokemon(self, name="mon", hp=100, speed=100, stats=None, moves=None, **extra):
        pokemon = SimpleNamespace(
            name=name,
            current_hp=hp,
            current_hp_fraction=hp / 100 if hp > 1 else hp,
            stats={"spe": speed, "atk": 100, "def": 100, "spa": 100, "spd": 100},
            moves=moves or {},
            effects={},
            ability=None,
            item=None,
            level=100,
            types=[],
            fainted=False,
            **extra,
        )
        if stats:
            pokemon.stats.update(stats)
        return pokemon

    def make_move(self, move_id, base_power=0, category="status", target=None, move_type=None):
        category_obj = SimpleNamespace(name=category)
        return SimpleNamespace(
            id=move_id,
            base_power=base_power,
            category=category_obj,
            target=target,
            deduced_target=target,
            type=move_type,
            priority=0,
            crit_ratio=0,
        )

    def test_final_gambit_scores_highest_when_faster_and_over_hps(self):
        attacker = self.make_pokemon(name="attacker", hp=80, speed=120)
        target = self.make_pokemon(name="target", hp=50, speed=80)
        battle = DummyBattle(active_pokemon=[attacker, None], opponent_active_pokemon=[target, None])
        move = self.make_move("finalgambit", base_power=0)

        score = self.bot._score_final_gambit(battle, attacker, move, target)

        self.assertEqual(score, 8)

    def test_final_gambit_scores_seven_when_faster_and_threatened(self):
        attacker = self.make_pokemon(name="attacker", hp=20, speed=120)
        target = self.make_pokemon(
            name="target",
            hp=80,
            speed=80,
            moves={"nuke": self.make_move("nuke", base_power=120, category="physical")},
        )
        battle = DummyBattle(active_pokemon=[attacker, None], opponent_active_pokemon=[target, None])
        move = self.make_move("finalgambit", base_power=0)

        score = self.bot._score_final_gambit(battle, attacker, move, target)

        self.assertEqual(score, 7)

    def test_final_gambit_scores_six_when_slower(self):
        attacker = self.make_pokemon(name="attacker", hp=80, speed=50)
        target = self.make_pokemon(name="target", hp=50, speed=100)
        battle = DummyBattle(active_pokemon=[attacker, None], opponent_active_pokemon=[target, None])
        move = self.make_move("finalgambit", base_power=0)

        score = self.bot._score_final_gambit(battle, attacker, move, target)

        self.assertEqual(score, 6)

    def test_final_gambit_rejects_immune_targets(self):
        attacker = self.make_pokemon(name="attacker", hp=80, speed=120)
        target = self.make_pokemon(name="target", hp=50, speed=80, damage_multiplier_value=0)
        battle = DummyBattle(active_pokemon=[attacker, None], opponent_active_pokemon=[target, None])
        move = self.make_move("finalgambit", base_power=0)

        score = self.bot._score_final_gambit(battle, attacker, move, target)

        self.assertEqual(score, -20)

    def test_memento_scores_high_when_very_low_hp(self):
        attacker = self.make_pokemon(name="attacker", hp=5, speed=100)
        partner = self.make_pokemon(name="partner", hp=100, speed=90)
        battle = DummyBattle(active_pokemon=[attacker, partner], opponent_active_pokemon=[self.make_pokemon(name="foe", hp=100, speed=80)])

        score = self.bot._score_memento(battle, attacker)

        self.assertEqual(score, 16)

    def test_memento_uses_probabilistic_branches(self):
        attacker = self.make_pokemon(name="attacker", hp=25, speed=100)
        partner = self.make_pokemon(name="partner", hp=100, speed=90)
        battle = DummyBattle(active_pokemon=[attacker, partner], opponent_active_pokemon=[self.make_pokemon(name="foe", hp=100, speed=80)])

        with patch.object(random, "random", return_value=0.2):
            self.assertEqual(self.bot._score_memento(battle, attacker), 14)

        with patch.object(random, "random", return_value=0.9):
            self.assertEqual(self.bot._score_memento(battle, attacker), 6)

    def test_destiny_bond_scores_higher_when_faster_and_threatened(self):
        attacker = self.make_pokemon(name="attacker", hp=20, speed=120)
        target = self.make_pokemon(
            name="target",
            hp=50,
            speed=80,
            moves={"nuke": self.make_move("nuke", base_power=120, category="physical")},
        )
        battle = DummyBattle(active_pokemon=[attacker, None], opponent_active_pokemon=[target, None])

        with patch.object(random, "random", return_value=0.5):
            score = self.bot._score_destiny_bond(battle, attacker, target)

        self.assertEqual(score, 7)

    def test_destiny_bond_scores_lower_when_slower(self):
        attacker = self.make_pokemon(name="attacker", hp=40, speed=80)
        target = self.make_pokemon(name="target", hp=50, speed=120)
        battle = DummyBattle(active_pokemon=[attacker, None], opponent_active_pokemon=[target, None])

        with patch.object(random, "random", return_value=0.1):
            score = self.bot._score_destiny_bond(battle, attacker, target)

        self.assertEqual(score, 5)

    def test_tailwind_prefers_when_team_is_slower(self):
        ally1 = self.make_pokemon(name="ally1", speed=80)
        ally2 = self.make_pokemon(name="ally2", speed=90)
        foe1 = self.make_pokemon(name="foe1", speed=100)
        foe2 = self.make_pokemon(name="foe2", speed=85)
        battle = DummyBattle(active_pokemon=[ally1, ally2], opponent_active_pokemon=[foe1, foe2], side_conditions={})

        self.assertEqual(self.bot._score_tailwind(battle), 9)

    def test_tailwind_is_blocked_when_already_active(self):
        ally1 = self.make_pokemon(name="ally1", speed=60)
        ally2 = self.make_pokemon(name="ally2", speed=70)
        foe1 = self.make_pokemon(name="foe1", speed=100)
        foe2 = self.make_pokemon(name="foe2", speed=90)
        battle = DummyBattle(
            active_pokemon=[ally1, ally2],
            opponent_active_pokemon=[foe1, foe2],
            side_conditions={SideCondition.TAILWIND: True},
        )

        self.assertEqual(self.bot._score_tailwind(battle), -20)

    def test_trick_room_scores_higher_when_team_is_slower(self):
        ally1 = self.make_pokemon(name="ally1", speed=80)
        ally2 = self.make_pokemon(name="ally2", speed=90)
        foe1 = self.make_pokemon(name="foe1", speed=100)
        foe2 = self.make_pokemon(name="foe2", speed=70)
        battle = DummyBattle(active_pokemon=[ally1, ally2], opponent_active_pokemon=[foe1, foe2], trick_room=False)

        self.assertEqual(self.bot._score_trick_room(battle), 10)

    def test_trick_room_is_blocked_when_active(self):
        ally1 = self.make_pokemon(name="ally1", speed=60)
        ally2 = self.make_pokemon(name="ally2", speed=70)
        foe1 = self.make_pokemon(name="foe1", speed=100)
        foe2 = self.make_pokemon(name="foe2", speed=90)
        battle = DummyBattle(active_pokemon=[ally1, ally2], opponent_active_pokemon=[foe1, foe2], trick_room=True)

        self.assertEqual(self.bot._score_trick_room(battle), -20)


if __name__ == "__main__":
    unittest.main()
