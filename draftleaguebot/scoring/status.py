def score_status_move(context, battle, attacker, move, target, opponents):
    """Score one non-damaging move-target candidate."""
    move_id = getattr(move, "id", None)
    if move_id is None:
        return 0

    if move_id in {"tailwind"}:
        return context._score_tailwind(battle)

    if move_id in {"trickroom"}:
        return context._score_trick_room(battle)

    if move_id in {"helpinghand", "followme"}:
        if context._partner_using_support_or_status(battle, attacker):
            return -20
        return 6

    if move_id == "coaching":
        return context._score_coaching(battle, attacker)

    if move_id == "finalgambit":
        return context._score_final_gambit(battle, attacker, move, target)

    if move_id == "memento":
        return context._score_memento(battle, attacker)

    if move_id == "destinybond":
        return context._score_destiny_bond(battle, attacker, target)

    if move_id in {"thunderwave", "stunspore", "glare", "nuzzle", "zapcannon"}:
        return context._score_paralysis(attacker, target)

    if move_id == "willowisp":
        return context._score_wisp(battle, attacker, target)

    if context._is_sleep_status_move(move):
        return context._score_sleep_move(battle, attacker, move, target)

    if context._is_poison_status_move(move):
        return context._score_poison_move(battle, attacker, target)

    if context._is_setup_move(move):
        return context._score_setup_move(battle, attacker, target, move)

    if context._is_recovery_move(move):
        return context._score_recovery_move(battle, attacker, move)

    if context._is_hazard_move(move):
        return context._score_hazard_move(battle, attacker, move)

    if context._is_screen_move(move):
        return context._score_screen_move(battle, attacker, move)

    if move_id == "taunt":
        return context._score_taunt(battle, attacker, target)

    if move_id == "encore":
        return context._score_encore(attacker, target)

    if move_id in {"protect", "kingsshield"}:
        return context._score_protect(attacker, target)

    if move_id == "batonpass":
        return context._score_baton_pass(battle, attacker)

    return 0
