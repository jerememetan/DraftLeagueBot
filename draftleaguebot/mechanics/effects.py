from poke_env.battle.weather import Weather


def is_damaging(move):
    """Return whether a move should be scored as damaging."""
    return getattr(move, "base_power", 0) > 0 and move.category.name.lower() != "status"


def has_stab(attacker, move):
    """Return whether the move type matches one of the attacker's types."""
    move_type = getattr(move, "type", None)
    if move_type is None:
        return False
    try:
        return move_type in attacker.types
    except Exception:
        return False


def is_high_crit(move):
    """Return whether the move has an increased critical-hit ratio."""
    return getattr(move, "crit_ratio", 0) > 1


def is_super_effective(battle, move, target):
    """Return whether battle type effectiveness is above neutral."""
    multiplier = 1.0
    if hasattr(battle, "damage_multiplier"):
        try:
            multiplier = battle.damage_multiplier(move, target)
        except Exception:
            multiplier = 1.0
    return multiplier > 1.0


def is_not_very_effective(battle, move, target):
    """Return whether battle type effectiveness is below neutral."""
    multiplier = 1.0
    if hasattr(battle, "damage_multiplier"):
        try:
            multiplier = battle.damage_multiplier(move, target)
        except Exception:
            multiplier = 1.0
    return multiplier < 1.0


def is_super_effective_on_target(move, target):
    """Return whether target-specific type effectiveness is above neutral."""
    try:
        return target.damage_multiplier(move) > 1.0
    except Exception:
        return False


def resisted_penalty(battle, move, target, scale=10):
    """
    Return a negative penalty scaled by how much the move is resisted.
    - multiplier == 0 -> -20 handled elsewhere, but keep as safeguard
    - multiplier < 1.0 -> penalty = -round((1 - multiplier) * scale)
    - multiplier >= 1.0 -> 0
    """
    try:
        if hasattr(battle, "damage_multiplier"):
            mult = battle.damage_multiplier(move, target)
        else:
            mult = target.damage_multiplier(move)
    except Exception:
        return 0
    if mult == 0:
        return -20
    if mult < 1.0:
        return -int(round((1.0 - mult) * scale))
    return 0


def is_immune_to_move(battle, move, target):
    """Return whether the target is immune to the move."""
    if target is None:
        return False
    try:
        if hasattr(battle, "damage_multiplier"):
            multiplier = battle.damage_multiplier(move, target)
            return multiplier == 0
    except Exception:
        pass
    try:
        return target.damage_multiplier(move) == 0
    except Exception:
        return False


def has_any_type(pokemon, types):
    """Return whether a Pokemon has any type from the provided set."""
    try:
        return any(t in types for t in pokemon.types)
    except Exception:
        return False


def is_sun_active(battle):
    """Return whether sun or harsh sun is active."""
    weather = getattr(battle, "weather", {})
    return Weather.SUNNYDAY in weather or Weather.DESOLATELAND in weather


def is_rain_active(battle):
    """Return whether rain or heavy rain is active."""
    weather = getattr(battle, "weather", {})
    return Weather.RAINDANCE in weather or Weather.PRIMORDIALSEA in weather


def is_snow_active(battle):
    """Return whether snow or hail is active."""
    weather = getattr(battle, "weather", {})
    return Weather.SNOWSCAPE in weather or Weather.HAIL in weather


def is_sand_active(battle):
    """Return whether sandstorm is active."""
    weather = getattr(battle, "weather", {})
    return Weather.SANDSTORM in weather


def side_condition_active(battle, condition):
    """Return whether a condition is active on the opponent side."""
    try:
        return condition in getattr(battle, "opponent_side_conditions", {})
    except Exception:
        return False


def ally_side_condition_active(battle, condition):
    """Return whether a condition is active on our side."""
    try:
        return condition in getattr(battle, "side_conditions", {})
    except Exception:
        return False


def is_trick_room_active(battle):
    """Return whether Trick Room is active in known battle field data."""
    if getattr(battle, "trick_room", False):
        return True
    fields = getattr(battle, "fields", None)
    if fields is None:
        fields = getattr(battle, "field", None)
    if fields is None:
        return False
    if isinstance(fields, dict):
        iterable = fields.keys()
    elif isinstance(fields, (list, set, tuple)):
        iterable = fields
    else:
        iterable = [fields]
    for entry in iterable:
        name = str(entry).lower()
        if "trickroom" in name or "trick_room" in name:
            return True
    return False
