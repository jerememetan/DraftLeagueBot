from types import SimpleNamespace
from unittest.mock import patch

from draftleaguebot.mechanics import damage_calc


def test_estimated_kill_returns_true_when_damage_meets_current_hp():
    target = SimpleNamespace(current_hp=50)
    expected = True

    result = damage_calc.estimated_kill(target, damage=50)

    assert result is expected


def test_estimated_kill_returns_false_when_hp_is_unknown():
    target = SimpleNamespace(current_hp=None, current_hp_fraction=None, max_hp=None)
    expected = False

    result = damage_calc.estimated_kill(target, damage=999)

    assert result is expected


def test_get_offense_defense_stats_uses_physical_attack_and_defense():
    attacker = SimpleNamespace(stats={"atk": 120})
    target = SimpleNamespace(stats={"def": 80})
    move = SimpleNamespace(category=SimpleNamespace(name="physical"))
    expected = (120, 80)

    result = damage_calc.get_offense_defense_stats(attacker, target, move)

    assert result == expected


def test_get_offense_defense_stats_uses_special_attack_and_defense():
    attacker = SimpleNamespace(stats={"spa": 130})
    target = SimpleNamespace(stats={"spd": 90})
    move = SimpleNamespace(category=SimpleNamespace(name="special"))
    expected = (130, 90)

    result = damage_calc.get_offense_defense_stats(attacker, target, move)

    assert result == expected


def test_resolve_identifier_side_returns_player_role_for_active_pokemon():
    pokemon = SimpleNamespace()
    battle = SimpleNamespace(
        player_role="p2",
        opponent_role="p1",
        active_pokemon=[pokemon],
        opponent_active_pokemon=[],
        team={},
        opponent_team={},
    )
    expected = "p2"

    result = damage_calc.resolve_identifier_side(battle, pokemon)

    assert result == expected


def test_resolve_identifier_side_returns_opponent_role_for_opponent_active_pokemon():
    pokemon = SimpleNamespace()
    battle = SimpleNamespace(
        player_role="p1",
        opponent_role="p2",
        active_pokemon=[],
        opponent_active_pokemon=[pokemon],
        team={},
        opponent_team={},
    )
    expected = "p2"

    result = damage_calc.resolve_identifier_side(battle, pokemon)

    assert result == expected


def test_damage_roll_factor_uses_expected_random_range():
    expected = 0.91

    with patch("draftleaguebot.mechanics.damage_calc.random.uniform", return_value=expected):
        result = damage_calc.damage_roll_factor()

    assert result == expected
