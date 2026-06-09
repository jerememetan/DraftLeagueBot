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


def test_stamina_scores_safe_single_hit():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = make_context(partner, damage=5)
    battle = SimpleNamespace(opponent_active_pokemon=[])
    move = SimpleNamespace(id="tackle", type="Normal")
    expected = 3

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner
    )

    assert result == expected


def test_stamina_adds_multi_hit_body_press_and_two_physical_stat_pressure():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={"bodypress": SimpleNamespace()},
    )
    physical_1 = SimpleNamespace(moves={}, stats={"atk": 150, "spa": 90})
    physical_2 = SimpleNamespace(moves={}, stats={"atk": 130, "spa": 80})
    context = make_context(partner, damage=5)
    battle = SimpleNamespace(opponent_active_pokemon=[physical_1, physical_2])
    move = SimpleNamespace(id="pinmissile", type="Bug")
    expected = 10

    result = self_hit.self_hit_partner_boost_bonus(
        context,
        battle,
        attacker=SimpleNamespace(),
        move=move,
        target=partner,
        hit_roll=lambda: 5,
    )

    assert result == expected


def test_variable_multi_hit_forces_five_hits_with_skill_link():
    from draftleaguebot.scoring import self_hit

    attacker = SimpleNamespace(ability="skilllink", item=None)
    move = SimpleNamespace(id="pinmissile")
    expected = 5

    result = self_hit.expected_hit_count(move, attacker, hit_roll=lambda: 2)

    assert result == expected


def test_beat_up_is_not_treated_as_generic_multi_hit():
    from draftleaguebot.scoring import self_hit

    attacker = SimpleNamespace(ability=None, item=None)
    move = SimpleNamespace(id="beatup")
    expected = 1

    result = self_hit.expected_hit_count(move, attacker, hit_roll=lambda: 5)

    assert result == expected


def test_physical_pressure_uses_attack_stat_when_moves_unknown():
    from draftleaguebot.scoring import self_hit

    context = make_context(partner=SimpleNamespace(), damage=0)
    opponent = SimpleNamespace(moves={}, stats={"atk": 140, "spa": 100})
    battle = SimpleNamespace(opponent_active_pokemon=[opponent])
    expected = 1

    result = self_hit.physical_pressure_bonus(context, battle)

    assert result == expected


def test_physical_pressure_uses_attack_stat_over_revealed_move_category():
    from draftleaguebot.scoring import self_hit

    context = make_context(partner=SimpleNamespace(), damage=0)
    opponent = SimpleNamespace(moves={}, stats={"atk": 140, "spa": 100})
    battle = SimpleNamespace(opponent_active_pokemon=[opponent])
    context._has_physical_move = lambda _pokemon: False
    context._has_special_move = lambda _pokemon: True
    expected = 1

    result = self_hit.physical_pressure_bonus(context, battle)

    assert result == expected
