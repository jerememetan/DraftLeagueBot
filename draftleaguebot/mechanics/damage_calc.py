import random

from poke_env.calc import calculate_damage
from poke_env.data import GenData
from poke_env.stats import compute_raw_stats

from draftleaguebot.mechanics import effects, pokemon_state


def estimate_damage(battle, attacker, move, target, use_max_roll=False, debug=False):
    """Estimate move damage with poke-env first, then local fallback math."""
    base = getattr(move, "base_power", 0)
    if base <= 0:
        return 0.0

    try:
        if battle is not None:
            attacker_side = resolve_identifier_side(battle, attacker)
            defender_side = resolve_identifier_side(battle, target)
            if attacker_side is not None and defender_side is not None:
                attacker_identifier = attacker.identifier(attacker_side)
                defender_identifier = target.identifier(defender_side)
                hydrate_damage_stats(attacker)
                hydrate_damage_stats(target)
                min_damage, max_damage = calculate_damage(
                    attacker_identifier,
                    defender_identifier,
                    move,
                    battle,
                )
                result = float(max_damage if use_max_roll else (min_damage + max_damage) / 2)
                if debug and result > 500:
                    print(
                        "      [CALC_DEBUG] "
                        f"Using poke-env calc: min={min_damage}, max={max_damage}, result={result:.1f}"
                    )
                return result
            if debug:
                print("      [CALC_DEBUG] Fallback: could not resolve sides for calc")
    except Exception as error:
        if debug:
            print(f"      [CALC_DEBUG] Fallback due to: {type(error).__name__}: {str(error)[:50]}")

    level = getattr(attacker, "level", 100) or 100
    attack_stat, defense_stat = get_offense_defense_stats(attacker, target, move)
    stab = 1.5 if effects.has_stab(attacker, move) else 1.0
    multiplier = 1.0
    if hasattr(battle, "damage_multiplier"):
        try:
            multiplier = battle.damage_multiplier(move, target)
        except Exception:
            multiplier = 1.0
    roll = 1.0 if use_max_roll else damage_roll_factor()

    base_damage = (((2 * level / 5 + 2) * base * attack_stat / max(1, defense_stat)) / 50) + 2
    result = base_damage * stab * multiplier * roll
    if debug and result > 500:
        print(
            "      [CALC_DEBUG] "
            f"Using fallback: base={base_damage:.1f}, stab={stab}, mult={multiplier}, "
            f"roll={roll}, result={result:.1f}"
        )
    return result


def resolve_identifier_side(battle, pokemon):
    """Return the battle side id needed by poke-env damage calculation."""
    if battle is None or pokemon is None:
        return None

    player_role = getattr(battle, "player_role", None) or "p1"
    opponent_role = getattr(battle, "opponent_role", None)
    if opponent_role is None:
        opponent_role = "p2" if player_role == "p1" else "p1"

    active = getattr(battle, "active_pokemon", None)
    if isinstance(active, list):
        if any(p is pokemon for p in active):
            return player_role
    elif active is pokemon:
        return player_role

    opponent_active = getattr(battle, "opponent_active_pokemon", None)
    if isinstance(opponent_active, list):
        if any(p is pokemon for p in opponent_active):
            return opponent_role
    elif opponent_active is pokemon:
        return opponent_role

    team = getattr(battle, "team", None)
    if isinstance(team, dict) and any(p is pokemon for p in team.values()):
        return player_role

    opponent_team = getattr(battle, "opponent_team", None)
    if isinstance(opponent_team, dict) and any(p is pokemon for p in opponent_team.values()):
        return opponent_role

    identifier = getattr(pokemon, "_identifier", None)
    if isinstance(identifier, str) and len(identifier) >= 2 and identifier[1].isdigit() and identifier[0] == "p":
        return identifier[:2]

    return None


def hydrate_damage_stats(pokemon):
    """Populate numeric stats for poke-env damage calculation when missing."""
    if pokemon is None:
        return
    try:
        stats = getattr(pokemon, "stats", None)
        if stats and all(isinstance(value, (int, float)) for value in stats.values()):
            return
        species = getattr(pokemon, "species", None)
        if not species:
            return
        level = getattr(pokemon, "level", 100) or 100
        gen_data = GenData.from_gen(getattr(pokemon, "gen", 9) or 9)
        raw_stats = compute_raw_stats(
            species,
            [0, 0, 0, 0, 0, 0],
            [31, 31, 31, 31, 31, 31],
            level,
            "hardy",
            gen_data,
        )
        pokemon.stats = {
            "hp": raw_stats[0],
            "atk": raw_stats[1],
            "def": raw_stats[2],
            "spa": raw_stats[3],
            "spd": raw_stats[4],
            "spe": raw_stats[5],
        }
    except Exception:
        return


def damage_roll_factor():
    """Return the standard Pokemon damage roll factor."""
    return random.uniform(0.85, 1.0)


def get_offense_defense_stats(attacker, target, move):
    """Return the attacking and defending stats used by a move category."""
    category = move.category.name.lower()
    if category == "physical":
        return pokemon_state.stat(attacker, "atk"), pokemon_state.stat(target, "def")
    if category == "special":
        return pokemon_state.stat(attacker, "spa"), pokemon_state.stat(target, "spd")
    return 1, 1


def estimated_kill(target, damage):
    """Return whether estimated damage is enough to KO the target."""
    current_hp = pokemon_state.get_target_current_hp(target)
    if current_hp is None:
        return False
    return damage >= current_hp
