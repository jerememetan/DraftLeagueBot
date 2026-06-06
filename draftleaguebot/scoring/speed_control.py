from poke_env.battle.side_condition import SideCondition


SPEED_CONTROL_DAMAGE_MOVES = {
    "icywind",
    "electroweb",
    "rocktomb",
    "mudshot",
    "lowsweep",
    "bulldoze",
}

SPEED_DROP_IMMUNE_ABILITIES = {"contrary", "clearbody", "whitesmoke"}
SPREAD_SPEED_CONTROL_MOVES = {"icywind", "electroweb"}


def team_is_slower(context, battle):
    allies = [p for p in battle.active_pokemon if p is not None]
    opponents = [p for p in battle.opponent_active_pokemon if p is not None]
    if not allies or not opponents:
        return False
    ally_speeds = [context._safe_speed(p) for p in allies]
    foe_speeds = [context._safe_speed(p) for p in opponents]
    if not ally_speeds or not foe_speeds:
        return False
    return max(ally_speeds) < max(foe_speeds)


def speed_profile(context, battle):
    allies = [p for p in battle.active_pokemon if p is not None]
    opponents = [p for p in battle.opponent_active_pokemon if p is not None]
    if not allies or not opponents:
        return None
    ally_speeds_raw = [context._safe_speed(p) for p in allies]
    foe_speeds_raw = [context._safe_speed(p) for p in opponents]
    ally_speeds = [speed for speed in ally_speeds_raw if speed > 0]
    foe_speeds = [speed for speed in foe_speeds_raw if speed > 0]
    if context._should_debug(battle):
        turn = getattr(battle, "turn", "?")
        ally_names = [getattr(p, "name", "?") for p in allies]
        foe_names = [getattr(p, "name", "?") for p in opponents]
        print(
            "[AI DEBUG] "
            f"turn={turn} speed_raw allies={list(zip(ally_names, ally_speeds_raw))} "
            f"foes={list(zip(foe_names, foe_speeds_raw))}"
        )
        print(
            "[AI DEBUG] "
            f"turn={turn} speed_filtered allies={ally_speeds} foes={foe_speeds}"
        )
    if not ally_speeds or not foe_speeds:
        return None
    return min(ally_speeds), max(ally_speeds), min(foe_speeds), max(foe_speeds)


def score_tailwind(context, battle):
    if context._ally_side_condition_active(battle, SideCondition.TAILWIND):
        return -20
    if context._is_trick_room_active(battle):
        return -8
    score = 6
    profile = speed_profile(context, battle)
    if context._should_debug(battle):
        turn = getattr(battle, "turn", "?")
        print(f"[AI DEBUG] turn={turn} move=tailwind speed_profile={profile}")
    if context._side_condition_active(battle, SideCondition.TAILWIND):
        score += 5
    if profile is None:
        return score
    _min_ally, max_ally, min_foe, max_foe = profile
    if max_ally < max_foe:
        score += 3
    if max_ally < min_foe:
        score += 2
    if max_ally > max_foe:
        score -= 2
    return score


def score_trick_room(context, battle):
    if context._is_trick_room_active(battle):
        return -20
    score = 6
    if context._ally_side_condition_active(battle, SideCondition.TAILWIND):
        score -= 4
    if context._side_condition_active(battle, SideCondition.TAILWIND):
        score += 3
    profile = speed_profile(context, battle)
    if context._should_debug(battle):
        turn = getattr(battle, "turn", "?")
        print(f"[AI DEBUG] turn={turn} move=trickroom speed_profile={profile}")
    if profile is None:
        return score
    _min_ally, max_ally, min_foe, max_foe = profile
    if max_ally < max_foe:
        score += 4
    if max_ally < min_foe:
        score += 2
    if max_ally > max_foe:
        score -= 5
    return score


def is_speed_control_damage_move(move):
    return getattr(move, "id", None) in SPEED_CONTROL_DAMAGE_MOVES


def score_speed_control_damage(context, battle, attacker, move, target, highest_damage):
    if highest_damage:
        return 0
    if is_immune_to_speed_drop(target):
        base = 5
    else:
        base = 6 if not context._is_faster(attacker, target) else 5
    if context._is_spread_move(move) and getattr(move, "id", None) in SPREAD_SPEED_CONTROL_MOVES:
        base += 1
    return base


def is_immune_to_speed_drop(target):
    if target is None:
        return False
    return getattr(target, "ability", None) in SPEED_DROP_IMMUNE_ABILITIES
