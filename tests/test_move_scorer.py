from types import SimpleNamespace


def test_score_move_dispatches_damaging_moves_to_context_helpers():
    from draftleaguebot.scoring import move_scorer

    context = SimpleNamespace(
        _is_damaging=lambda _move: True,
        _is_immune_to_move=lambda _battle, _move, _target: False,
        _estimate_damage=lambda _battle, _attacker, _move, _target: 50,
        _should_debug=lambda _battle: False,
        _is_highest_damage_move=lambda *_args: True,
        _rng_weight=lambda low, _high, _prob: low,
        _estimated_kill=lambda _target, _damage: False,
        _is_high_crit=lambda _move: False,
        _is_super_effective=lambda _battle, _move, _target: False,
        _resisted_penalty=lambda _battle, _move, _target, scale=10: 0,
        _is_threatened_by_any_faster_opponent=lambda _battle, _attacker: False,
        _is_speed_control_damage_move=lambda _move: False,
        _is_offense_drop_damage_move=lambda _move: False,
        _is_spdef_drop_damage_move=lambda _move: False,
        _score_move_specific_damage=lambda _battle, _attacker, _move, _target: 0,
        _is_contrary_setup_attack=lambda _attacker, _move, _highest, _damage, _target: False,
        _apply_doubles_damage_bonuses=lambda _battle, _attacker, _move, _target: 0,
    )
    move = SimpleNamespace(priority=0)
    expected = 6.0

    result = move_scorer.score_move(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        move=move,
        target=SimpleNamespace(),
        opponents=[],
        attacker_moves=[move],
    )

    assert result == expected


def test_score_move_dispatches_status_moves_to_context_helper():
    from draftleaguebot.scoring import move_scorer

    context = SimpleNamespace(
        _is_damaging=lambda _move: False,
        _score_status_move=lambda _battle, _attacker, _move, _target, _opponents: 9,
    )
    expected = 9.0

    result = move_scorer.score_move(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        move=SimpleNamespace(),
        target=SimpleNamespace(),
        opponents=[],
        attacker_moves=[],
    )

    assert result == expected
