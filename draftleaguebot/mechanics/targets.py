from poke_env.battle.target import Target


SELF_OR_SIDE_TARGETS = {
    Target.SELF,
    Target.ALLY_SIDE,
    Target.ALLIES,
    Target.FOE_SIDE,
    Target.ALL,
    Target.RANDOM_NORMAL,
    Target.SCRIPTED,
}

# may want to consider 100% crit moves in the future - for anger point tech
ALLY_TARGET_MOVE_IDS = {
    "shadowsneak",
    "aquajet",
    "iceshard",
    "vacuumwave",
    "bulletpunch",
    "machpunch",
    "watershuriken",
    "fling",
    "pinmissile",
    "beatup",
    "bulletseed",
    "spikecannon",
    "accelerock",
    "iciclespear"
}


def candidate_targets(battle, attacker, move, opponents, setup_move_ids):
    """Return the Pokemon that should be scored as possible targets."""
    move_target = getattr(move, "deduced_target", None) or getattr(move, "target", None)
    if not isinstance(move_target, Target):
        return list(opponents)
    if move_targets_self_or_side(move_target, move, setup_move_ids):
        return [attacker]

    candidates = []
    if move_allows_foe(move_target):
        candidates.extend(list(opponents))
    if move_allows_ally(move_target, move):
        partner = get_partner(battle, attacker)
        if partner is not None:
            candidates.append(partner)
    return candidates


def move_allows_foe(move_target):
    """Return whether this move target mode can select an opponent."""
    return move_target in {
        Target.NORMAL,
        Target.ADJACENT_FOE,
        Target.ANY,
        Target.ALL_ADJACENT,
        Target.ALL_ADJACENT_FOES,
    }


def move_allows_ally(move_target, move):
    """Return whether this move target mode can select an ally."""
    if move_target in {Target.ADJACENT_ALLY, Target.ADJACENT_ALLY_OR_SELF, Target.SELF}:
        return True
    if move_target in {Target.NORMAL, Target.ANY}:
        return ally_target_allowed(move)
    return False


def ally_target_allowed(move):
    """Return whether a normally flexible move may intentionally target a partner."""
    move_id = getattr(move, "id", None)
    return move_id in ALLY_TARGET_MOVE_IDS


def move_targets_self_or_side(move_target, move, setup_move_ids):
    """Return whether scoring should evaluate the attacker instead of a foe."""
    if move_target in SELF_OR_SIDE_TARGETS:
        return True
    move_id = getattr(move, "id", None)
    return move_id in setup_move_ids


def is_partner(battle, attacker, target):
    """Return whether target is the attacker's active doubles partner."""
    partner = get_partner(battle, attacker)
    return partner is not None and target is partner


def get_partner(battle, attacker):
    """Return the other active ally in a doubles battle, if one exists."""
    active = battle.active_pokemon
    if not isinstance(active, list):
        return None
    if len(active) >= 1 and active[0] is attacker:
        return active[1] if len(active) > 1 else None
    if len(active) >= 2 and active[1] is attacker:
        return active[0]
    return None
