from draftleaguebot.scoring import damage


def score_move(context, battle, attacker, move, target, opponents, attacker_moves):
    """Score one move-target candidate using the current bot as rule context."""
    if context._is_damaging(move):
        return damage.score_damaging_move(context, battle, attacker, move, target, opponents, attacker_moves)
    return context._score_status_move(battle, attacker, move, target, opponents)
