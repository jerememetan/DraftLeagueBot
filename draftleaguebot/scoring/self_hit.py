def self_hit_partner_boost_bonus(context, battle, attacker, move, target):
    """Score intentional partner hits that activate beneficial partner effects."""
    partner = context._get_partner(battle, attacker)
    if partner is None or target is not partner:
        return 0

    boosted_stat = boosted_stat_for_partner_combo(partner, move)
    if boosted_stat is None:
        return 0

    safety = self_hit_safety_score(context, battle, attacker, move, partner, boosted_stat)
    if safety != 0:
        return safety
    return 0


def boosted_stat_for_partner_combo(partner, move):
    """Return the stat boosted by the partner self-hit combo, if supported."""
    ability = normalize_id(getattr(partner, "ability", None))
    if ability == "stamina":
        return "def"
    if ability == "watercompaction" and move_is_water_type(move):
        return "def"
    return None


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
