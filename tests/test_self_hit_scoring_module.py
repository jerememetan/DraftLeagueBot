from types import SimpleNamespace


def make_context(partner, damage):
    return SimpleNamespace(
        _get_partner=lambda _battle, _attacker: partner,
        _estimate_damage=lambda _battle, _attacker, _move, _target, use_max_roll=False: damage,
        _estimated_kill=lambda target, amount: amount >= getattr(target, "current_hp", 100),
        _get_boost=lambda pokemon, stat: getattr(pokemon, "boosts", {}).get(stat, 0),
        _has_move_id=lambda pokemon, move_id: move_id in getattr(pokemon, "moves", {}),
        _has_physical_move=lambda pokemon: False,
        _has_special_move=lambda pokemon: True,
    )


def test_self_hit_rejects_partner_ko():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=20,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = make_context(partner, damage=20)
    battle = SimpleNamespace(opponent_active_pokemon=[])
    move = SimpleNamespace(id="pinmissile", type="Bug")
    expected = -20

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner
    )

    assert result == expected


def test_self_hit_rejects_damage_at_25_percent_of_partner_max_hp():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = make_context(partner, damage=25)
    battle = SimpleNamespace(opponent_active_pokemon=[])
    move = SimpleNamespace(id="pinmissile", type="Bug")
    expected = -20

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner
    )

    assert result == expected


def test_self_hit_penalizes_damage_at_15_percent_of_partner_max_hp():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = make_context(partner, damage=15)
    battle = SimpleNamespace(opponent_active_pokemon=[])
    move = SimpleNamespace(id="pinmissile", type="Bug")
    expected = -6

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner
    )

    assert result == expected
