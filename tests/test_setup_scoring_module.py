from types import SimpleNamespace


def test_is_setup_move_recognizes_known_setup_move():
    from draftleaguebot.scoring import setup

    expected = True

    result = setup.is_setup_move(SimpleNamespace(id="swordsdance"))

    assert result == expected


def test_score_setup_move_rejects_setup_against_unaware_target():
    from draftleaguebot.scoring import setup

    context = SimpleNamespace(
        _threatened_by_ko=lambda _battle, _attacker, _target: False,
        _target_has_unaware=lambda _target: True,
    )
    expected = -20

    result = setup.score_setup_move(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        target=SimpleNamespace(),
        move=SimpleNamespace(id="calmmind"),
    )

    assert result == expected


def test_setup_synergy_bonus_rewards_body_press_with_defensive_setup():
    from draftleaguebot.scoring import setup

    attacker = SimpleNamespace(moves={"bodypress": SimpleNamespace()})
    move = SimpleNamespace(id="irondefense")
    expected = 1

    result = setup.setup_synergy_bonus(attacker, move)

    assert result == expected
