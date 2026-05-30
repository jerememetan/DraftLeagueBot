from types import SimpleNamespace

from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather

from draftleaguebot.mechanics import effects


def test_is_damaging_requires_power_and_non_status_category():
    physical = SimpleNamespace(base_power=80, category=SimpleNamespace(name="physical"))
    status = SimpleNamespace(base_power=0, category=SimpleNamespace(name="status"))

    assert effects.is_damaging(physical) is True
    assert effects.is_damaging(status) is False


def test_type_effectiveness_helpers_use_battle_multiplier():
    battle = SimpleNamespace(damage_multiplier=lambda _move, _target: 2.0)

    assert effects.is_super_effective(battle, object(), object()) is True
    assert effects.is_not_very_effective(battle, object(), object()) is False


def test_resisted_penalty_scales_below_neutral_hits():
    battle = SimpleNamespace(damage_multiplier=lambda _move, _target: 0.5)

    assert effects.resisted_penalty(battle, object(), object(), scale=10) == -5


def test_is_immune_to_move_falls_back_to_target_multiplier():
    target = SimpleNamespace(damage_multiplier=lambda _move: 0)

    assert effects.is_immune_to_move(SimpleNamespace(), object(), target) is True


def test_weather_helpers_detect_sun_rain_snow_and_sand():
    assert effects.is_sun_active(SimpleNamespace(weather={Weather.SUNNYDAY: 1})) is True
    assert effects.is_rain_active(SimpleNamespace(weather={Weather.RAINDANCE: 1})) is True
    assert effects.is_snow_active(SimpleNamespace(weather={Weather.SNOWSCAPE: 1})) is True
    assert effects.is_sand_active(SimpleNamespace(weather={Weather.SANDSTORM: 1})) is True


def test_side_condition_helpers_check_correct_sides():
    battle = SimpleNamespace(
        side_conditions={SideCondition.TAILWIND: 1},
        opponent_side_conditions={SideCondition.REFLECT: 1},
    )

    assert effects.ally_side_condition_active(battle, SideCondition.TAILWIND) is True
    assert effects.side_condition_active(battle, SideCondition.REFLECT) is True


def test_is_trick_room_active_reads_flags_and_field_names():
    assert effects.is_trick_room_active(SimpleNamespace(trick_room=True)) is True
    assert effects.is_trick_room_active(SimpleNamespace(fields={"trickroom": 1})) is True
    assert effects.is_trick_room_active(SimpleNamespace(fields={})) is False
