from draftleaguebot.scoring import damage, status


def score_move(context, battle, attacker, move, target, opponents, attacker_moves):
    """Score one move-target candidate using the current bot as rule context."""
    if context._is_damaging(move):
        return damage.score_damaging_move(context, battle, attacker, move, target, opponents, attacker_moves)
    return status.score_status_move(context, battle, attacker, move, target, opponents)
