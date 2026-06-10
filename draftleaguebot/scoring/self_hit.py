import random


FIXED_HIT_COUNTS = {
    "bonemerang": 2,
    "doublehit": 2,
    "doubleironbash": 2,
    "doublekick": 2,
    "dragondarts": 2,
    "dualchop": 2,
    "dualwingbeat": 2,
    "geargrind": 2,
    "surgingstrikes": 3,
    "tachyoncutter": 2,
    "tripledive": 3,
    "twinbeam": 2,
    "twineedle": 2,
    "watershuriken": 3,
}

VARIABLE_TWO_TO_FIVE_HIT_MOVES = {
    "armthrust",
    "barrage",
    "bonerush",
    "bulletseed",
    "cometpunch",
    "doubleslap",
    "furyattack",
    "furyswipes",
    "iciclespear",
    "pinmissile",
    "rockblast",
    "scaleshot",
    "spikecannon",
    "tailslap",
}


def self_hit_partner_boost_bonus(context, battle, attacker, move, target, hit_roll=None):
    """Score intentional partner hits that activate beneficial partner effects."""
    get_partner = getattr(context, "_get_partner", None)
    if get_partner is None:
        return 0
    partner = get_partner(battle, attacker)
    if partner is None or target is not partner:
        return 0

    combo = partner_combo_kind(partner, move)
    if combo is None:
        return 0

    safety = self_hit_safety_score(context, battle, attacker, move, partner, "def")
    if safety != 0:
        return safety

    if combo == "stamina":
        return score_stamina_combo(context, battle, attacker, partner, move, hit_roll=hit_roll)
    if combo == "watercompaction":
        return score_water_compaction_combo(
            context, battle, attacker, partner, move, hit_roll=hit_roll
        )
    return 0


def partner_combo_kind(partner, move):
    """Return the supported self-hit combo kind for this partner and move."""
    ability = normalize_id(getattr(partner, "ability", None))
    if ability == "stamina":
        return "stamina"
    if ability == "watercompaction" and move_is_water_type(move):
        return "watercompaction"
    return None


def score_stamina_combo(context, battle, attacker, partner, move, hit_roll=None):
    """Score a safe Stamina activation against the current opponent board."""
    score = 3
    extra_hits = max(expected_hit_count(move, attacker, hit_roll=hit_roll) - 1, 0)
    score += min(extra_hits, 4)
    score += physical_pressure_bonus(context, battle)
    if context._has_move_id(partner, "bodypress"):
        score += 1
    return min(score, 10)


def score_water_compaction_combo(context, battle, attacker, partner, move, hit_roll=None):
    """Score a safe Water Compaction activation against the current board."""
    score = 5
    extra_hits = max(expected_hit_count(move, attacker, hit_roll=hit_roll) - 1, 0)
    score += min(extra_hits * 2, 4)
    score += physical_pressure_bonus(context, battle)
    if context._has_move_id(partner, "bodypress"):
        score += 1
    return min(score, 12)


def expected_hit_count(move, attacker, hit_roll=None):
    """Return the hit count to use when scoring multi-hit self-hit combos."""
    move_id = normalize_id(getattr(move, "id", None))
    if move_id in FIXED_HIT_COUNTS:
        return FIXED_HIT_COUNTS[move_id]
    if move_id not in VARIABLE_TWO_TO_FIVE_HIT_MOVES:
        return 1
    if has_guaranteed_five_hit_modifier(attacker):
        return 5
    roll = random.randint(2, 5) if hit_roll is None else hit_roll()
    return max(2, min(int(roll), 5))


def has_guaranteed_five_hit_modifier(attacker):
    """Return whether attacker forces 2-5 hit moves to hit five times."""
    ability = normalize_id(getattr(attacker, "ability", None))
    item = normalize_id(getattr(attacker, "item", None))
    return ability == "skilllink" or item == "loadeddice"


def physical_pressure_bonus(context, battle):
    """Reward Defense boosts more when active opponents lean physical."""
    opponents = [p for p in getattr(battle, "opponent_active_pokemon", []) if p is not None]
    physical_count = sum(1 for opponent in opponents if attack_stat_leans_physical(opponent))
    if physical_count >= 2:
        return 4
    if physical_count == 1:
        return 1
    return 0


def attack_stat_leans_physical(opponent):
    """Return whether Attack is meaningfully higher than Special Attack."""
    stats = getattr(opponent, "stats", {}) or {}
    attack = stats.get("atk", 0) or 0
    special_attack = stats.get("spa", 0) or 0
    return attack >= special_attack * 1.1 and attack > 0


def self_hit_safety_score(context, battle, attacker, move, partner, boosted_stat):
    """Return a hard safety score or 0 when positive scoring may continue."""
    damage = context._estimate_damage(battle, attacker, move, partner, use_max_roll=True)
    if context._estimated_kill(partner, damage):
        return -20

    max_hp = max(getattr(partner, "max_hp", 100) or 100, 1)
    damage_ratio = damage / max_hp
    if damage_ratio >= 0.25:
        return -20
    if damage_ratio >= 0.15:
        return -6

    boost = context._get_boost(partner, boosted_stat)
    if boost >= 6:
        return -20
    if boost >= 4:
        return -6
    return 0


def move_is_water_type(move):
    """Return whether a move's type is Water across string/enum shapes."""
    move_type = getattr(move, "type", None)
    value = getattr(move_type, "name", None) or getattr(move_type, "value", None) or move_type
    return str(value).lower() == "water"


def normalize_id(value):
    """Normalize poke-env ids, item ids, and ability ids for scoring checks."""
    if value is None:
        return None
    return str(value).replace(" ", "").replace("-", "").lower()
