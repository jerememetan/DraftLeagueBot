from copy import copy

from poke_env.battle.pokemon_type import PokemonType
from poke_env.data import to_id_str


def pokemon_type(type_name):
    name = to_id_str(getattr(type_name, "name", type_name))
    try:
        return PokemonType[name.upper()]
    except KeyError:
        return type_name


def with_tera_type(pokemon, tera_type, preserve_original=False):
    hypothetical = copy(pokemon)
    tera = pokemon_type(tera_type)
    original_types = list(getattr(pokemon, "types", ()) or ())
    hypothetical.types = original_types + [tera] if preserve_original else [tera]
    return hypothetical


def defensive_tera_saves_ko(context, battle, attacker, tera_type, opponents):
    """Use defensive Tera only when a known faster attack would otherwise KO."""
    if not tera_type:
        return False
    get_current_hp = getattr(context, "_get_target_current_hp", None)
    is_faster = getattr(context, "_is_faster", None)
    estimate_damage = getattr(context, "_estimate_damage", None)
    is_damaging = getattr(context, "_is_damaging", None)
    if not all((get_current_hp, is_faster, estimate_damage, is_damaging)):
        return False
    current_hp = get_current_hp(attacker)
    if current_hp is None:
        return False
    hypothetical = with_tera_type(attacker, tera_type)
    for opponent in opponents:
        if not is_faster(opponent, attacker):
            continue
        for incoming_move in (getattr(opponent, "moves", {}) or {}).values():
            if not is_damaging(incoming_move):
                continue
            before = estimate_damage(
                battle, opponent, incoming_move, attacker, use_max_roll=True
            )
            if before < current_hp:
                continue
            after = estimate_damage(
                battle, opponent, incoming_move, hypothetical, use_max_roll=True
            )
            if after < current_hp:
                return True
    return False


def offensive_tera_is_valuable(context, battle, attacker, tera_type, move, target):
    """Require a meaningful estimated gain from offensive Tera."""
    move_name = to_id_str(
        getattr(getattr(move, "type", None), "name", getattr(move, "type", None))
    )
    tera_name = to_id_str(getattr(tera_type, "name", tera_type))
    if tera_name == "stellar":
        return True
    if move_name != tera_name:
        return False
    if not hasattr(attacker, "stats"):
        return True
    try:
        before = context._estimate_damage(battle, attacker, move, target)
        original_types = {
            to_id_str(getattr(value, "name", value))
            for value in getattr(attacker, "types", ()) or ()
        }
        tera_stab = 2.0 if move_name in original_types else 1.5
        current_stab = 1.5 if move_name in original_types else 1.0
        after = before * tera_stab / current_stab
        return after > before * 1.1
    except (AttributeError, KeyError, TypeError, ValueError):
        return True
