import random

from poke_env.battle.double_battle import DoubleBattle
from poke_env.battle.target import Target


SELF_OR_SIDE_TARGETS = {
    Target.SELF,
    Target.ALLY_SIDE,
    Target.ALLIES,
    Target.FOE_SIDE,
    Target.ALL,
    Target.ALL_ADJACENT,
    Target.ALL_ADJACENT_FOES,
    Target.RANDOM_NORMAL,
    Target.SCRIPTED,
}


def get_active_slots(battle):
    """Return each active slot with its Pokemon and available moves.

    poke-env represents doubles moves as a list per active Pokemon, but singles
    or fallback states may expose one flat move list. This normalizes both.
    """
    available = battle.available_moves
    active = battle.active_pokemon
    if isinstance(available, list) and available and isinstance(available[0], list):
        slots = []
        if isinstance(active, list):
            for index, moves in enumerate(available):
                attacker = active[index] if index < len(active) else None
                if attacker is None:
                    continue
                slots.append((index, attacker, moves))
        else:
            slots.append((0, active, available[0]))
        return slots
    return [(0, active, available)]


def fallback_order_for_slot(create_order, battle, slot_index):
    """Build a switch order for a slot when that active Pokemon has no moves."""
    available_switches = getattr(battle, "available_switches", None)
    if isinstance(available_switches, list):
        if slot_index < len(available_switches) and available_switches[slot_index]:
            return create_order(random.choice(available_switches[slot_index]))
    elif available_switches:
        return create_order(random.choice(available_switches))
    return None


def move_target_position(
    battle,
    attacker,
    move,
    target,
    ally_target_allowed,
    is_partner,
):
    """Convert a selected target Pokemon into poke-env's battle position value.

    Target choice is scored elsewhere. This only answers the order-building
    question: which position should be passed to `create_order`?
    """
    move_target = getattr(move, "deduced_target", None) or getattr(move, "target", None)
    if move_target is None or not isinstance(move_target, Target):
        return DoubleBattle.EMPTY_TARGET_POSITION

    if move_target in SELF_OR_SIDE_TARGETS:
        return DoubleBattle.EMPTY_TARGET_POSITION

    if move_target in {Target.NORMAL, Target.ANY, Target.ADJACENT_FOE}:
        if is_partner(battle, attacker, target) and ally_target_allowed(move):
            self_pos, ally_pos = ally_positions(battle, attacker)
            return ally_pos if ally_pos is not None else self_pos
        position = opponent_position(battle, target)
        return position if position is not None else DoubleBattle.EMPTY_TARGET_POSITION

    if move_target in {Target.ADJACENT_ALLY, Target.ADJACENT_ALLY_OR_SELF}:
        self_pos, ally_pos = ally_positions(battle, attacker)
        if move_target == Target.ADJACENT_ALLY:
            return ally_pos if ally_pos is not None else DoubleBattle.EMPTY_TARGET_POSITION
        return ally_pos if ally_pos is not None else self_pos

    return DoubleBattle.EMPTY_TARGET_POSITION


def opponent_position(battle, target):
    """Return the doubles position constant for an opposing active Pokemon."""
    for index, foe in enumerate(battle.opponent_active_pokemon):
        if foe is target:
            return DoubleBattle.OPPONENT_1_POSITION if index == 0 else DoubleBattle.OPPONENT_2_POSITION
    return None


def ally_positions(battle, attacker):
    """Return this attacker's own position and its partner's position."""
    active = battle.active_pokemon
    if not isinstance(active, list):
        return DoubleBattle.POKEMON_1_POSITION, None
    if len(active) >= 1 and active[0] is attacker:
        return DoubleBattle.POKEMON_1_POSITION, DoubleBattle.POKEMON_2_POSITION
    if len(active) >= 2 and active[1] is attacker:
        return DoubleBattle.POKEMON_2_POSITION, DoubleBattle.POKEMON_1_POSITION
    return DoubleBattle.POKEMON_1_POSITION, None
