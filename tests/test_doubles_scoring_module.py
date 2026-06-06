from types import SimpleNamespace


def test_score_coaching_rejects_contrary_partner():
    from draftleaguebot.scoring import doubles

    partner = SimpleNamespace(ability="contrary")
    context = SimpleNamespace(_get_partner=lambda _battle, _attacker: partner)
    expected = -20

    result = doubles.score_coaching(context, battle=SimpleNamespace(), attacker=SimpleNamespace())

    assert result == expected


def test_score_coaching_rewards_unboosted_partner_stats():
    from draftleaguebot.scoring import doubles

    partner = SimpleNamespace(ability=None)
    context = SimpleNamespace(
        _get_partner=lambda _battle, _attacker: partner,
        _get_boost=lambda _pokemon, _stat: 0,
    )
    expected = 9

    result = doubles.score_coaching(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        random_roll=lambda: 0.0,
    )

    assert result == expected


def test_partner_using_support_or_status_detects_last_status_move():
    from draftleaguebot.scoring import doubles

    partner = SimpleNamespace(last_move=SimpleNamespace(id="tailwind", category=SimpleNamespace(name="status")))
    context = SimpleNamespace(_get_partner=lambda _battle, _attacker: partner)
    expected = True

    result = doubles.partner_using_support_or_status(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
    )

    assert result == expected


def test_weakness_policy_partner_bonus_rewards_super_effective_partner_hit():
    from draftleaguebot.scoring import doubles

    partner = SimpleNamespace(item="weaknesspolicy")
    context = SimpleNamespace(
        _get_partner=lambda _battle, _attacker: partner,
        _is_super_effective_on_target=lambda _move, _target: True,
    )
    expected = 12

    result = doubles.weakness_policy_partner_bonus(
        context,
        battle=SimpleNamespace(),
        attacker=SimpleNamespace(),
        move=SimpleNamespace(),
        target=partner,
    )

    assert result == expected


def test_apply_doubles_damage_bonuses_routes_ground_spread_moves():
    from draftleaguebot.scoring import doubles

    attacker = SimpleNamespace()
    partner = SimpleNamespace(
        ability=None,
        item=None,
        effects={},
        types=[],
        damage_multiplier=lambda _move_type: 1,
    )
    battle = SimpleNamespace(active_pokemon=[attacker, partner])
    context = SimpleNamespace(
        _get_partner=lambda _battle, _attacker: partner,
        _is_faster=lambda _attacker, _defender: False,
    )
    expected = -3

    result = doubles.apply_doubles_damage_bonuses(
        context,
        battle=battle,
        attacker=attacker,
        move=SimpleNamespace(id="earthquake"),
        target=SimpleNamespace(),
    )

    assert result == expected


def test_same_turn_support_conflict_blocks_second_support_move():
    from draftleaguebot.scoring import doubles

    selected_moves = [SimpleNamespace(id="helpinghand")]
    context = SimpleNamespace(_is_damaging=lambda _move: False)
    expected = True

    result = doubles.same_turn_support_conflict(context, SimpleNamespace(id="helpinghand"), selected_moves)

    assert result == expected


def test_same_turn_support_conflict_allows_two_non_helping_hand_status_moves():
    from draftleaguebot.scoring import doubles

    selected_moves = [SimpleNamespace(id="tailwind")]
    context = SimpleNamespace(_is_damaging=lambda _move: False)
    expected = False

    result = doubles.same_turn_support_conflict(context, SimpleNamespace(id="protect"), selected_moves)

    assert result == expected


def test_same_turn_support_conflict_allows_damaging_move_after_helping_hand():
    from draftleaguebot.scoring import doubles

    selected_moves = [SimpleNamespace(id="helpinghand")]
    context = SimpleNamespace(_is_damaging=lambda move: getattr(move, "base_power", 0) > 0)
    expected = False

    result = doubles.same_turn_support_conflict(context, SimpleNamespace(id="tackle", base_power=40), selected_moves)

    assert result == expected


def test_same_turn_support_conflict_blocks_helping_hand_after_status_move():
    from draftleaguebot.scoring import doubles

    selected_moves = [SimpleNamespace(id="tailwind")]
    context = SimpleNamespace(_is_damaging=lambda _move: False)
    expected = True

    result = doubles.same_turn_support_conflict(context, SimpleNamespace(id="helpinghand"), selected_moves)

    assert result == expected
