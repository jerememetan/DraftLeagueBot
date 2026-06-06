def score_move(context, battle, attacker, move, target, opponents, attacker_moves):
    """Score one move-target candidate using the current bot as rule context."""
    score = 0.0

    if context._is_damaging(move):
        if context._is_immune_to_move(battle, move, target):
            return -20
        damage = context._estimate_damage(battle, attacker, move, target)

        if context._should_debug(battle):
            target_name = getattr(target, "name", "?")
            move_name = getattr(move, "id", "?")
            print(f"    [DAMAGE] {move_name}->{target_name}: {damage:.1f}", end="")

        highest_damage = context._is_highest_damage_move(
            battle, attacker, move, target, opponents, attacker_moves, damage
        )
        if highest_damage:
            if context._should_debug(battle):
                print(" (HIGHEST)", end="")
            score += context._rng_weight(6, 8, 0.8)

        if context._should_debug(battle):
            print()

        if context._estimated_kill(target, damage):
            if context._is_faster(attacker, target) or (
                move.priority > 0 and not context._is_faster(attacker, target)
            ):
                score += 6
            else:
                score += 3

            if context._has_snowball_ability(attacker):
                score += 1

        if context._is_high_crit(move) and context._is_super_effective(battle, move, target):
            score += context._rng_weight(3, 5, 0.3)
        if context._is_super_effective(battle, move, target):
            score += context._rng_weight(2, 4, 0.3)
        # Almost guarantee to to click pirority if its slow and sees OHKO from opponent
        score += context._resisted_penalty(battle, move, target, scale=10)
        if move.priority > 0 and context._is_threatened_by_any_faster_opponent(battle, attacker):
            score += 11

        if context._is_speed_control_damage_move(move):
            score += context._score_speed_control_damage(battle, attacker, move, target, highest_damage)

        if context._is_offense_drop_damage_move(move):
            score += context._score_offense_drop_damage(battle, attacker, move, target, highest_damage)

        if context._is_spdef_drop_damage_move(move):
            score += 6

        score += context._score_move_specific_damage(battle, attacker, move, target)

        if context._is_contrary_setup_attack(attacker, move, highest_damage, damage, target):
            score += context._score_contrary_setup(attacker, target, move)

        score += context._apply_doubles_damage_bonuses(battle, attacker, move, target)
    else:
        score += context._score_status_move(battle, attacker, move, target, opponents)

    return score
