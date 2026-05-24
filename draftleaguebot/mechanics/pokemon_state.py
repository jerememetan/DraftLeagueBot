from poke_env.data import GenData


def get_target_current_hp(target):
    """Return known current HP, or estimate it from HP fraction and max HP."""
    current_hp = getattr(target, "current_hp", None)
    if current_hp is not None:
        return current_hp
    current_hp_fraction = getattr(target, "current_hp_fraction", None)
    max_hp = get_target_max_hp(target)
    if current_hp_fraction is None or max_hp is None:
        return None
    return max_hp * current_hp_fraction


def get_target_max_hp(target):
    """Return known max HP, or infer it from current HP and HP fraction."""
    max_hp = getattr(target, "max_hp", None)
    if max_hp is not None:
        return max_hp
    current_hp = getattr(target, "current_hp", None)
    current_hp_fraction = getattr(target, "current_hp_fraction", None)
    if current_hp is None or current_hp_fraction in (None, 0):
        return None
    return current_hp / current_hp_fraction


def safe_speed(pokemon):
    """Return speed when known, falling back to an estimated max-invested value."""
    try:
        speed = pokemon.stats.get("spe", 0)
        if speed is None or speed == 0:
            base_stats = getattr(pokemon, "base_stats", None)
            if isinstance(base_stats, dict):
                base_speed = base_stats.get("spe", 0)
                if base_speed is None or base_speed == 0:
                    return 0
                return int(round(base_speed * 1.4))
        return speed
    except Exception:
        return 0


def is_faster(attacker, defender):
    """Return whether attacker is faster when both speed stats are available."""
    try:
        return attacker.stats["spe"] > defender.stats["spe"]
    except Exception:
        return False


def stat(pokemon, key):
    """Return a battle stat, falling back to Gen 9 base stats when needed."""
    try:
        if pokemon.stats and key in pokemon.stats:
            return max(1, int(pokemon.stats[key]))
    except Exception:
        pass
    # Fallback to base stats when actual battle stats are unavailable.
    try:
        species = getattr(pokemon, "species", None)
        if species:
            gen_data = GenData.from_gen(9)
            pokemon_data = gen_data.pokedex.get(species.lower())
            if pokemon_data and "baseStats" in pokemon_data:
                base_stat = pokemon_data["baseStats"].get(key, 1)
                return max(1, int(base_stat))
    except Exception:
        pass
    return 1


def get_boost(pokemon, stat_name):
    """Return a stat boost stage, defaulting to neutral when unavailable."""
    try:
        return pokemon.boosts.get(stat_name, 0)
    except Exception:
        return 0


def has_positive_boost(pokemon):
    """Return whether any tracked stat boost is above neutral."""
    try:
        boosts = pokemon.boosts
    except Exception:
        return False
    return any(value > 0 for value in boosts.values())


def active_list(active):
    """Normalize poke-env active Pokemon data to a list."""
    if isinstance(active, list):
        return active
    if active is None:
        return []
    return [active]


def count_alive(team):
    """Count Pokemon that are not fainted and do not have zero HP."""
    if not team:
        return 0
    pokemon_list = list(team.values()) if isinstance(team, dict) else list(team)
    count = 0
    for pokemon in pokemon_list:
        if pokemon is None:
            continue
        if getattr(pokemon, "fainted", False):
            continue
        current_hp = getattr(pokemon, "current_hp", None)
        if current_hp is not None and current_hp <= 0:
            continue
        current_frac = getattr(pokemon, "current_hp_fraction", None)
        if current_frac is not None and current_frac <= 0:
            continue
        count += 1
    return count


def alive_counts(battle):
    """Return alive counts for our side and the opponent side."""
    ally = count_alive(getattr(battle, "team", None))
    opp = count_alive(getattr(battle, "opponent_team", None))
    if ally == 0:
        ally = count_alive(active_list(battle.active_pokemon))
    if opp == 0:
        opp = count_alive(active_list(battle.opponent_active_pokemon))
    return ally, opp


def is_last_mon(battle):
    """Return whether our side has one or fewer Pokemon remaining."""
    ally_alive, _ = alive_counts(battle)
    return ally_alive <= 1


def both_last_mon(battle):
    """Return whether both sides are down to one or fewer Pokemon."""
    ally_alive, opp_alive = alive_counts(battle)
    return ally_alive <= 1 and opp_alive <= 1


def opponent_has_multiple_alive(battle):
    """Return whether the opponent has more than one Pokemon remaining."""
    _, opp_alive = alive_counts(battle)
    return opp_alive > 1
