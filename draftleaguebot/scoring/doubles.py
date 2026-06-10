import random

from poke_env.battle.effect import Effect
from poke_env.battle.pokemon_type import PokemonType
from draftleaguebot.scoring import self_hit

def score_coaching(context, battle, attacker, random_roll=None):
    """Score Coaching based on the active partner's boost value and ability."""
    partner = context._get_partner(battle, attacker)
    if partner is None:
        return -20
    if getattr(partner, "ability", None) == "contrary":
        return -20

    roll = random.random if random_roll is None else random_roll
    score = 6
    atk_boost = context._get_boost(partner, "atk")
    def_boost = context._get_boost(partner, "def")
    if atk_boost < 2:
        score += 1 - atk_boost
    if def_boost < 2:
        score += 1 - def_boost
    if roll() < 0.8:
        score += 1
    return score


def partner_using_support_or_status(context, battle, attacker):
    """Return whether the partner's last known move was support/status."""
    partner = context._get_partner(battle, attacker)
    if partner is None:
        return False
    last_move = getattr(partner, "last_move", None)
    if last_move is None:
        return False
    move_id = getattr(last_move, "id", None)
    if move_id in {"helpinghand", "followme"}:
        return True
    category = getattr(last_move, "category", None)
    return category is not None and category.name.lower() == "status"


def same_turn_support_conflict(context, move, selected_moves):
    """Return whether Helping Hand is paired with a non-damaging partner move."""
    move_id = getattr(move, "id", None)
    if move_id == "helpinghand":
        return any(not context._is_damaging(selected) for selected in selected_moves)
    if context._is_damaging(move):
        return False
    return any(getattr(selected, "id", None) == "helpinghand" for selected in selected_moves)


def partner_has_hex(context, battle, attacker):
    """Return whether the active partner has Hex available."""
    partner = context._get_partner(battle, attacker)
    if partner is None:
        return False
    return context._has_hex_move(partner)


def apply_doubles_damage_bonuses(context, battle, attacker, move, target):
    """Score extra doubles interactions for one damaging move target."""
    move_id = getattr(move, "id", None)
    if move_id is None:
        return 0

    bonus = 0
    if move_id in {"shadowsneak", "aquajet", "iceshard", "vacuumwave", "bulletpunch", "machpunch", "watershuriken"}:
        bonus += weakness_policy_partner_bonus(context, battle, attacker, move, target)
    if move_id == "fling":
        bonus += fling_speed_bonus(context, battle, attacker, move, target)
    if move_id in {"earthquake", "magnitude", "bulldoze"}:
        bonus += earthquake_partner_bonus(context, battle)
    bonus += self_hit.self_hit_partner_boost_bonus(context, battle, attacker, move, target)
    return bonus


def weakness_policy_partner_bonus(context, battle, attacker, move, target):
    """Reward intentionally triggering a partner's Weakness Policy."""
    partner = context._get_partner(battle, attacker)
    if partner is None or target is None:
        return 0
    if partner.item != "weaknesspolicy":
        return 0
    if target is not partner:
        return 0
    if context._is_super_effective_on_target(move, partner):
        return 12
    return 0


def fling_speed_bonus(context, battle, attacker, move, target):
    """Score Fling into a partner for Salac Berry or Weakness Policy value."""
    partner = context._get_partner(battle, attacker)
    if partner is None or target is None:
        return 0
    if target is not partner:
        return 0
    if attacker.item not in {"salacberry"}:
        return 0
    if partner.item == "weaknesspolicy" and context._is_super_effective_on_target(move, partner):
        return 12
    return 9


def earthquake_partner_bonus(context, battle):
    """Score Ground spread moves based on how safely the partner handles them."""
    attacker = None
    active = battle.active_pokemon
    if isinstance(active, list) and active:
        attacker = active[0]
    elif active is not None:
        attacker = active

    partner = context._get_partner(battle, attacker) if attacker is not None else None
    if partner is None:
        return 0

    partner_immune = is_immune_to_ground(partner)
    partner_levitating = Effect.MAGNET_RISE in getattr(partner, "effects", {})
    partner_faster = False
    if attacker is not None:
        partner_faster = context._is_faster(partner, attacker)

    if partner_immune or (partner_levitating and partner_faster):
        return 2
    if has_any_type(partner, {PokemonType.FIRE, PokemonType.POISON, PokemonType.ELECTRIC, PokemonType.ROCK}):
        return -10
    return -3


def is_immune_to_ground(pokemon):
    """Return whether a Pokemon ignores Ground damage."""
    try:
        if getattr(pokemon, "ability", None) == "levitate":
            return True
        if getattr(pokemon, "item", None) == "airballoon":
            return True
        return pokemon.damage_multiplier(PokemonType.GROUND) == 0
    except Exception:
        return False


def has_any_type(pokemon, types):
    """Return whether a Pokemon has any of the given types."""
    pokemon_types = set(getattr(pokemon, "types", []) or [])
    return any(pokemon_type in pokemon_types for pokemon_type in types)
