import unittest

from poke_env.battle.weather import Weather

from bot_logic import DoublesMvpBot


class DummyTarget:
    def __init__(self, multiplier):
        self._mult = multiplier

    def damage_multiplier(self, _type):
        return self._mult


class DummyBattle:
    def __init__(self, weather):
        self.weather = weather


class DummyMove:
    def __init__(self, mid="weatherball"):
        self.id = mid


class WeatherBallTests(unittest.TestCase):
    def test_weatherball_scoring_and_resisted_penalty(self):
        bot = object.__new__(DoublesMvpBot)
        battle = DummyBattle({Weather.SUNNYDAY})
        move = DummyMove()

        cases = [
            (2.0, 10),   # super effective
            (1.0, 6),    # neutral
            (0.5, -6),   # resisted -> -(1-0.5)*12 = -6
            (0.0, -20),  # immune
        ]

        for mult, expected_weatherball in cases:
            with self.subTest(mult=mult):
                target = DummyTarget(mult)
                score = DoublesMvpBot._score_move_specific_damage(bot, battle, None, move, target)
                self.assertEqual(score, expected_weatherball)

    def test_resisted_penalty_scale(self):
        bot = object.__new__(DoublesMvpBot)
        battle = DummyBattle(set())
        move = DummyMove(mid="tackle")

        # 0.5 multiplier with scale=10 -> -(1-0.5)*10 = -5
        target_half = DummyTarget(0.5)
        pen = DoublesMvpBot._resisted_penalty(bot, battle, move, target_half, scale=10)
        self.assertEqual(pen, -5)

        # 0.25 multiplier with scale=10 -> -(1-0.25)*10 = -8 (rounding)
        target_quarter = DummyTarget(0.25)
        pen2 = DoublesMvpBot._resisted_penalty(bot, battle, move, target_quarter, scale=10)
        self.assertEqual(pen2, -8)


if __name__ == "__main__":
    unittest.main()
