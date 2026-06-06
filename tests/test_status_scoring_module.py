from types import SimpleNamespace


def test_score_status_move_returns_zero_when_move_id_is_missing():
    from draftleaguebot.scoring import status

    expected = 0

    result = status.score_status_move(
        SimpleNamespace(),
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        move=SimpleNamespace(id=None),
        target=SimpleNamespace(),
        opponents=[],
    )

    assert result == expected


def test_score_status_move_routes_tailwind_to_speed_control_module():
    from draftleaguebot.scoring import status

    context = SimpleNamespace(
        _ally_side_condition_active=lambda _battle, _condition: False,
        _is_trick_room_active=lambda _battle: False,
        _side_condition_active=lambda _battle, _condition: False,
        _safe_speed=lambda pokemon: pokemon.stats["spe"],
        _should_debug=lambda _battle: False,
    )
    battle = SimpleNamespace(
        active_pokemon=[SimpleNamespace(stats={"spe": 70}, name="ally")],
        opponent_active_pokemon=[SimpleNamespace(stats={"spe": 120}, name="foe")],
    )
    expected = 11

    result = status.score_status_move(
        context,
        battle=battle,
        attacker=SimpleNamespace(),
        move=SimpleNamespace(id="tailwind"),
        target=SimpleNamespace(),
        opponents=[],
    )

    assert result == expected


def test_score_status_move_scores_helping_hand_without_last_turn_penalty():
    from draftleaguebot.scoring import status

    expected = 6

    result = status.score_status_move(
        SimpleNamespace(),
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        move=SimpleNamespace(id="helpinghand"),
        target=SimpleNamespace(),
        opponents=[],
    )

    assert result == expected


def test_score_status_move_routes_setup_moves_to_setup_module():
    from draftleaguebot.scoring import status

    context = SimpleNamespace(
        _is_sleep_status_move=lambda _move: False,
        _is_poison_status_move=lambda _move: False,
        _threatened_by_ko=lambda _battle, _attacker, _target: False,
        _target_has_unaware=lambda _target: False,
        _is_incapacitated=lambda _target: True,
        _is_faster=lambda _attacker, _target: True,
    )
    move = SimpleNamespace(id="swordsdance")
    expected = 9

    result = status.score_status_move(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        move=move,
        target=SimpleNamespace(),
        opponents=[],
    )

    assert result == expected
