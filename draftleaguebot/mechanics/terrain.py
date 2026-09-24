from poke_env.battle.field import Field
from poke_env.battle.pokemon_type import PokemonType


TERRAIN_FIELDS = {
    Field.ELECTRIC_TERRAIN,
    Field.MISTY_TERRAIN,
    Field.PSYCHIC_TERRAIN,
}


def current_terrain(battle):
    fields = getattr(battle, "fields", ()) or ()
    for terrain in TERRAIN_FIELDS:
        if terrain in fields:
            return terrain
    return None


def has_type(pokemon, type_name):
    wanted = type_name.lower()
    for pokemon_type in getattr(pokemon, "types", ()) or ():
        value = getattr(pokemon_type, "name", None) or getattr(pokemon_type, "value", None) or pokemon_type
        if str(value).lower() == wanted:
            return True
    return False


def is_immune_to_ground(pokemon):
    if pokemon is None:
        return False
    if getattr(pokemon, "ability", None) == "levitate":
        return True
    if getattr(pokemon, "item", None) == "airballoon":
        return True
    try:
        return pokemon.damage_multiplier(PokemonType.GROUND) == 0
    except Exception:
        return has_type(pokemon, "flying")


def is_grounded(pokemon):
    return pokemon is not None and not is_immune_to_ground(pokemon)


def ability_is_or_may_be(pokemon, abilities):
    values = {getattr(pokemon, "ability", None)}
    for field in ("possible_abilities", "abilities"):
        possible = getattr(pokemon, field, ()) or ()
        values.update(possible if not isinstance(possible, str) else (possible,))
    return any(str(value).replace(" ", "").lower() in abilities for value in values if value)


def move_type_name(move):
    move_type = getattr(move, "type", None)
    return str(getattr(move_type, "name", None) or getattr(move_type, "value", None) or move_type).lower()


def terrain_damage_multiplier(battle, attacker, move, target):
    terrain = current_terrain(battle)
    move_type = move_type_name(move)
    if terrain == Field.PSYCHIC_TERRAIN and move_type == "psychic":
        if getattr(move, "id", None) == "expandingforce":
            return 1.5
        return 1.3
    if terrain == Field.ELECTRIC_TERRAIN and move_type == "electric":
        return 1.3
    if terrain == Field.MISTY_TERRAIN:
        if move_type == "fairy":
            if getattr(move, "id", None) == "mistyexplosion":
                return 1.3 * 1.5
            return 1.3
        if move_type == "dragon":
            return 0.5
    return 1.0


def priority_move_blocked_by_psychic_terrain(battle, move, target):
    return (
        current_terrain(battle) == Field.PSYCHIC_TERRAIN
        and getattr(move, "priority", 0) > 0
        and is_grounded(target)
    )


def sleep_move_blocked_by_electric_terrain(battle, move, target):
    if current_terrain(battle) != Field.ELECTRIC_TERRAIN or not is_grounded(target):
        return False
    return getattr(move, "id", None) in {"spore", "sleeppowder", "hypnosis", "darkvoid", "rest"}


def status_move_blocked_by_misty_terrain(battle, move, target):
    if current_terrain(battle) != Field.MISTY_TERRAIN or not is_grounded(target):
        return False
    return getattr(move, "status", None) is not None


def rising_voltage_is_boosted(battle, move, target):
    if current_terrain(battle) != Field.ELECTRIC_TERRAIN or getattr(move, "id", None) != "risingvoltage":
        return False
    if not is_grounded(target) or is_immune_to_electric(target):
        return False
    return not ability_is_or_may_be(
        target,
        {"voltabsorb", "motordrive", "lightningrod"},
    )


def is_immune_to_electric(pokemon):
    if pokemon is None:
        return False
    if has_type(pokemon, "ground"):
        return True
    if ability_is_or_may_be(pokemon, {"voltabsorb", "motordrive", "lightningrod"}):
        return True
    try:
        return pokemon.damage_multiplier(PokemonType.ELECTRIC) == 0
    except Exception:
        return False
