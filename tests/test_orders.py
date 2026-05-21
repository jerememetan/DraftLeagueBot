from types import SimpleNamespace

from poke_env.battle.double_battle import DoubleBattle
from poke_env.battle.target import Target

from draftleaguebot import orders


def test_get_active_slots_handles_doubles_move_lists():
    first = SimpleNamespace(name="first")
    second = SimpleNamespace(name="second")
    battle = SimpleNamespace(
        active_pokemon=[first, second],
        available_moves=[["move-a"], ["move-b"]],
    )

    assert orders.get_active_slots(battle) == [
        (0, first, ["move-a"]),
        (1, second, ["move-b"]),
    ]


def test_fallback_order_for_slot_uses_matching_switch_slot():
    switch = SimpleNamespace(name="bench")
    battle = SimpleNamespace(available_switches=[[], [switch]])

    order = orders.fallback_order_for_slot(lambda pokemon: ("order", pokemon), battle, 1)

    assert order == ("order", switch)


def test_move_target_position_maps_foe_targets():
    target = SimpleNamespace(name="foe")
    battle = SimpleNamespace(
        active_pokemon=[SimpleNamespace(name="ally")],
        opponent_active_pokemon=[SimpleNamespace(name="other"), target],
    )
    move = SimpleNamespace(target=Target.NORMAL, deduced_target=Target.NORMAL)

    position = orders.move_target_position(
        battle,
        battle.active_pokemon[0],
        move,
        target,
        ally_target_allowed=lambda _move: False,
        is_partner=lambda _battle, _attacker, _target: False,
    )

    assert position == DoubleBattle.OPPONENT_2_POSITION


def test_move_target_position_maps_allowed_partner_target():
    attacker = SimpleNamespace(name="attacker")
    partner = SimpleNamespace(name="partner")
    battle = SimpleNamespace(active_pokemon=[attacker, partner], opponent_active_pokemon=[])
    move = SimpleNamespace(target=Target.ANY, deduced_target=Target.ANY)

    position = orders.move_target_position(
        battle,
        attacker,
        move,
        partner,
        ally_target_allowed=lambda _move: True,
        is_partner=lambda _battle, _attacker, target: target is partner,
    )

    assert position == DoubleBattle.POKEMON_2_POSITION
