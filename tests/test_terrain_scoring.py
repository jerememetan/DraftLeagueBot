from types import SimpleNamespace

from poke_env.battle.field import Field
from poke_env.battle.status import Status
from poke_env.battle.pokemon_type import PokemonType

from draftleaguebot.mechanics import damage_calc, terrain
from draftleaguebot.scoring import status


def pokemon(*, types=("Normal",), ability=None, item=None):
    return SimpleNamespace(
        types=list(types),
        ability=ability,
        item=item,
        stats={"atk": 100, "def": 100, "spa": 100, "spd": 100},
        level=100,
    )


def test_psychic_terrain_blocks_priority_on_grounded_targets_only():
    battle = SimpleNamespace(fields={Field.PSYCHIC_TERRAIN})
    move = SimpleNamespace(id="fakeout", priority=3)
    grounded = pokemon()
    flying = pokemon(types=("Flying",))

    assert terrain.priority_move_blocked_by_psychic_terrain(battle, move, grounded)
    assert not terrain.priority_move_blocked_by_psychic_terrain(battle, move, flying)


def test_electric_and_misty_terrain_block_status_moves_on_grounded_targets():
    grounded = pokemon()
    flying = pokemon(types=("Flying",))
    sleep = SimpleNamespace(id="spore", status=Status.SLP)
    burn = SimpleNamespace(id="willowisp", status=Status.BRN)

    assert terrain.sleep_move_blocked_by_electric_terrain(
        SimpleNamespace(fields={Field.ELECTRIC_TERRAIN}), sleep, grounded
    )
    assert not terrain.sleep_move_blocked_by_electric_terrain(
        SimpleNamespace(fields={Field.ELECTRIC_TERRAIN}), sleep, flying
    )
    assert terrain.status_move_blocked_by_misty_terrain(
        SimpleNamespace(fields={Field.MISTY_TERRAIN}), burn, grounded
    )
    assert not terrain.status_move_blocked_by_misty_terrain(
        SimpleNamespace(fields={Field.MISTY_TERRAIN}), burn, flying
    )


def test_status_scoring_returns_negative_for_electric_terrain_sleep():
    battle = SimpleNamespace(fields={Field.ELECTRIC_TERRAIN})
    move = SimpleNamespace(id="hypnosis", status=Status.SLP)
    assert status.score_status_move(SimpleNamespace(), battle, pokemon(), move, pokemon(), []) == -20


def test_rising_voltage_requires_grounded_target_without_ground_immunity_ability():
    battle = SimpleNamespace(fields={Field.ELECTRIC_TERRAIN})
    move = SimpleNamespace(id="risingvoltage")

    assert terrain.rising_voltage_is_boosted(battle, move, pokemon())
    assert not terrain.rising_voltage_is_boosted(battle, move, pokemon(types=("Ground",)))
    assert not terrain.rising_voltage_is_boosted(battle, move, pokemon(ability="voltabsorb"))


def test_terrain_damage_modifiers_apply_to_fallback_damage():
    attacker = pokemon(types=("Psychic",))
    target = pokemon()
    move = SimpleNamespace(
        id="psychic",
        base_power=90,
        type=PokemonType.PSYCHIC,
        category=SimpleNamespace(name="special"),
    )
    neutral = damage_calc.estimate_damage(
        SimpleNamespace(fields=set()), attacker, move, target
    )
    boosted = damage_calc.estimate_damage(
        SimpleNamespace(fields={Field.PSYCHIC_TERRAIN}), attacker, move, target
    )

    assert boosted > neutral
