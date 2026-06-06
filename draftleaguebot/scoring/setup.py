import random


def score_setup_move(context, battle, attacker, target, move):
    """Score one setup or stat-boosting move."""
    if context._threatened_by_ko(battle, attacker, target):
        return -20
    if context._target_has_unaware(target) and move.id not in {"howl"}:
        return -20

    synergy_bonus = setup_synergy_bonus(attacker, move)

    if is_special_setup(move):
        return score_special_setup(context, attacker, target) + synergy_bonus
    if is_defensive_setup(move):
        boosts_both = move.id in {"cosmicpower", "stockpile", "defendorder"}
        return score_defensive_setup(context, attacker, target, boosts_both=boosts_both) + synergy_bonus
    if is_mixed_setup(move):
        return score_mixed_setup(context, attacker, target, move) + synergy_bonus
    if is_speed_setup(move):
        return score_speed_setup(context, attacker, target) + synergy_bonus
    if move.id in {"shellsmash"}:
        return score_shell_smash(context, battle, attacker, target) + synergy_bonus
    if move.id in {"bellydrum"}:
        return score_belly_drum(context, battle, attacker, target) + synergy_bonus
    if move.id in {"clangoroussoul"}:
        return score_clangorous_soul(context, battle, attacker, target) + synergy_bonus
    return score_offensive_setup(context, attacker, target) + synergy_bonus


def score_offensive_setup(context, attacker, target):
    """Score setup that mainly increases offensive pressure."""
    score = 6
    if context._is_incapacitated(target):
        score += 3
    if not context._is_faster(attacker, target) and is_two_hko_threat(context, attacker, target):
        score -= 5
    return score


def score_defensive_setup(context, attacker, target, boosts_both=False):
    """Score setup that mainly increases bulk."""
    score = 6
    if not context._is_faster(attacker, target) and is_two_hko_threat(context, attacker, target):
        score -= 5
    if random.random() < 0.95:
        if context._is_incapacitated(target):
            score += 2
        if boosts_both and (context._get_boost(attacker, "def") < 2 or context._get_boost(attacker, "spd") < 2):
            score += 2
    return score


def score_special_setup(context, attacker, target):
    """Score setup that boosts special offense."""
    score = 6
    if context._is_incapacitated(target):
        score += 3
    elif not is_three_hko_threat(context, attacker, target):
        score += 1
        if context._is_faster(attacker, target):
            score += 1
    if not context._is_faster(attacker, target) and is_two_hko_threat(context, attacker, target):
        score -= 5
    if context._get_boost(attacker, "spa") >= 2:
        score -= 1
    return score


def score_speed_setup(context, attacker, target):
    """Score setup that fixes a speed disadvantage."""
    if not context._is_faster(attacker, target):
        return 7
    return -20


def score_shell_smash(context, battle, attacker, target):
    """Score Shell Smash using payoff versus post-defense-drop danger."""
    score = 6
    if context._is_incapacitated(target):
        score += 3
    if not can_be_ko_after_setup(context, battle, attacker, target):
        score += 2
    else:
        score -= 2
    if context._get_boost(attacker, "atk") >= 1 or context._get_boost(attacker, "spa") >= 6:
        return -20
    return score


def score_belly_drum(context, battle, attacker, target):
    """Score Belly Drum using setup space and half-HP risk."""
    if context._is_incapacitated(target):
        return 9
    if not can_be_ko_after_setup(context, battle, attacker, target, hp_multiplier=0.5):
        return 8
    return 4


def score_mixed_setup(context, attacker, target, move):
    """Choose offensive or defensive scoring for setup that boosts mixed stats."""
    if move.id in {"coil", "bulkup", "noretreat","victorydance"}:
        if context._has_physical_move(target) and not context._has_special_move(target):
            return score_defensive_setup(context, attacker, target)
        return score_offensive_setup(context, attacker, target)
    if move.id in {"calmmind", "quiverdance"}:
        if context._has_special_move(target) and not context._has_physical_move(target):
            return score_defensive_setup(context, attacker, target)
        return score_offensive_setup(context, attacker, target)
    return score_offensive_setup(context, attacker, target)


def setup_synergy_bonus(attacker, move):
    """Reward setup moves that unlock Stored Power, Power Trip, or Body Press."""
    if attacker is None:
        return 0
    moves = getattr(attacker, "moves", {})
    if not moves:
        return 0
    power_trip = "powertrip" in moves
    stored_power = "storedpower" in moves
    body_press = "bodypress" in moves

    bonus = 0
    if power_trip:
        bonus += 1
    if stored_power:
        bonus += 1
    if body_press and is_defensive_setup(move):
        bonus += 1
    return bonus


def score_clangorous_soul(context, battle, attacker, target):
    """Score Clangorous Soul using all-stat payoff versus HP-loss risk."""
    if context._is_incapacitated(target):
        return 11
    if not can_be_ko_after_setup(context, battle, attacker, target, hp_multiplier=(2 / 3)):
        return 10
    return 2

def is_setup_move(move):
    """Return whether a move id is one of the bot's setup moves."""
    return move.id in setup_move_ids()


def setup_move_ids():
    """Return move ids treated as setup or stat-boosting moves."""
    return {
        "swordsdance",
        "howl",
        "stuffcheeks",
        "barrier",
        "acidarmor",
        "irondefense",
        "cottonguard",
        "harden",
        "tailglow",
        "nastyplot",
        "cosmicpower",
        "bulkup",
        "calmmind",
        "dragondance",
        "coil",
        "honeclaws",
        "quiverdance",
        "shiftgear",
        "shellsmash",
        "growth",
        "workup",
        "curse",
        "noretreat",
        "stockpile",
        "agility",
        "rockpolish",
        "autotomize",
        "bellydrum",
        "focusenergy",
        "laserfocus",
        "clangoroussoul",
        "meditate",
        "sharpen",
        "tidyup",
        "victorydance",
        "acupressure",
        "shelter",
        "withdraw",
        "defendorder"
        
    }


def is_special_setup(move):
    """Return whether a setup move primarily boosts special attack."""
    return move.id in {"tailglow", "nastyplot", "workup", "growth"}


def is_defensive_setup(move):
    """Return whether a setup move primarily boosts defenses."""
    return move.id in {"barrier", "acidarmor", "irondefense", "cottonguard", "harden", "stockpile", "cosmicpower","withdraw","acupressure","shelter", "defendorder"}


def is_mixed_setup(move):
    """Return whether a setup move can serve offensive and defensive plans."""
    return move.id in {"coil", "bulkup", "noretreat", "calmmind", "quiverdance", "victorydance"}


def is_speed_setup(move):
    """Return whether a setup move primarily boosts speed."""
    return move.id in {"agility", "rockpolish", "autotomize"}


def threatened_by_ko(context, battle, attacker, target):
    """Return whether the target can immediately KO the setup user."""
    if target is None:
        return False
    return context._can_ko_target(battle, target, attacker)


def is_two_hko_threat(context, attacker, target):
    """Return whether attacker can remove at least half of target's current HP."""
    return estimate_max_damage_ratio(context, attacker, target) >= 0.5


def is_three_hko_threat(context, attacker, target):
    """Return whether attacker can remove at least one third of target's current HP."""
    return estimate_max_damage_ratio(context, attacker, target) >= (1 / 3)


def estimate_max_damage_ratio(context, attacker, target):
    """Estimate the best available damage as a fraction of the target's current HP."""
    moves = getattr(attacker, "moves", {})
    if not moves:
        return 0
    current_hp = context._get_target_current_hp(target)
    if current_hp is None or current_hp == 0:
        return 0
    max_ratio = 0
    for move in moves.values():
        if not context._is_damaging(move):
            continue
        damage = context._estimate_damage(None, attacker, move, target, use_max_roll=True)
        ratio = damage / current_hp
        if ratio > max_ratio:
            max_ratio = ratio
    return max_ratio


def can_be_ko_after_setup(context, battle, attacker, target, hp_multiplier=1.0):
    """Return whether target can KO attacker after the setup move's HP/stat cost."""
    if target is None:
        return False
    current_hp = context._get_target_current_hp(attacker)
    if current_hp is None:
        return False
    current_hp *= hp_multiplier
    moves = getattr(target, "moves", {})
    for move in moves.values():
        if not context._is_damaging(move):
            continue
        damage = context._estimate_damage(battle, target, move, attacker, use_max_roll=True)
        if damage >= current_hp:
            return True
    return False
