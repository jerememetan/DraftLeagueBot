from types import SimpleNamespace

from draftleaguebot.mechanics import pokemon_state


def test_get_target_current_hp_uses_fraction_when_current_hp_is_missing(capsys):
    target = SimpleNamespace(current_hp_fraction=0.5, max_hp=200)

    assert pokemon_state.get_target_current_hp(target) == 100
    assert capsys.readouterr().out == ""


def test_get_target_current_hp_returns_none_without_enough_hp_data(capsys):
    target = SimpleNamespace(current_hp_fraction=None, max_hp=None)

    assert pokemon_state.get_target_current_hp(target) is None
    assert capsys.readouterr().out == ""


def test_safe_speed_falls_back_to_base_speed_estimate():
    pokemon = SimpleNamespace(stats={"spe": 0}, base_stats={"spe": 100})

    assert pokemon_state.safe_speed(pokemon) == 140


def test_count_alive_filters_fainted_and_zero_hp_pokemon():
    alive = SimpleNamespace(current_hp=10, fainted=False)
    fainted = SimpleNamespace(current_hp=10, fainted=True)
    zero_hp = SimpleNamespace(current_hp=0, fainted=False)

    assert pokemon_state.count_alive([alive, fainted, zero_hp, None]) == 1


def test_alive_counts_falls_back_to_active_pokemon_when_team_data_is_missing():
    ally = SimpleNamespace(current_hp=10, fainted=False)
    foe = SimpleNamespace(current_hp=10, fainted=False)
    battle = SimpleNamespace(
        team=None,
        opponent_team=None,
        active_pokemon=[ally],
        opponent_active_pokemon=[foe],
    )

    assert pokemon_state.alive_counts(battle) == (1, 1)


def test_has_positive_boost_reads_boost_values_defensively():
    boosted = SimpleNamespace(boosts={"atk": 1, "def": 0})
    unboosted = SimpleNamespace(boosts={"atk": 0})

    assert pokemon_state.has_positive_boost(boosted) is True
    assert pokemon_state.has_positive_boost(unboosted) is False
    assert pokemon_state.has_positive_boost(SimpleNamespace()) is False
