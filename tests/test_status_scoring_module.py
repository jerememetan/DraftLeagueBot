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


def test_score_status_move_routes_tailwind_to_context_helper():
    from draftleaguebot.scoring import status

    context = SimpleNamespace(_score_tailwind=lambda _battle: 9)
    expected = 9

    result = status.score_status_move(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        move=SimpleNamespace(id="tailwind"),
        target=SimpleNamespace(),
        opponents=[],
    )

    assert result == expected


def test_score_status_move_blocks_helping_hand_when_partner_uses_support():
    from draftleaguebot.scoring import status

    context = SimpleNamespace(_partner_using_support_or_status=lambda _battle, _attacker: True)
    expected = -20

    result = status.score_status_move(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        move=SimpleNamespace(id="helpinghand"),
        target=SimpleNamespace(),
        opponents=[],
    )

    assert result == expected


def test_score_status_move_routes_setup_moves_to_context_helper():
    from draftleaguebot.scoring import status

    context = SimpleNamespace(
        _is_sleep_status_move=lambda _move: False,
        _is_poison_status_move=lambda _move: False,
        _is_setup_move=lambda _move: True,
        _score_setup_move=lambda _battle, _attacker, _target, _move: 12,
    )
    move = SimpleNamespace(id="swordsdance")
    expected = 12

    result = status.score_status_move(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        move=move,
        target=SimpleNamespace(),
        opponents=[],
    )

    assert result == expected
