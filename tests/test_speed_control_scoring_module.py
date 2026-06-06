from types import SimpleNamespace


def make_context(**overrides):
    defaults = {
        "_safe_speed": lambda pokemon: pokemon.stats.get("spe", 0),
        "_should_debug": lambda _battle: False,
        "_ally_side_condition_active": lambda _battle, _condition: False,
        "_side_condition_active": lambda _battle, _condition: False,
        "_is_trick_room_active": lambda battle: getattr(battle, "trick_room", False),
        "_is_faster": lambda attacker, target: attacker.stats["spe"] > target.stats["spe"],
        "_is_spread_move": lambda move: getattr(move, "deduced_target", None) == "spread",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_pokemon(speed, ability=None):
    return SimpleNamespace(stats={"spe": speed}, ability=ability, name=f"spe{speed}")


def make_battle(allies, opponents, **overrides):
    defaults = {
        "active_pokemon": allies,
        "opponent_active_pokemon": opponents,
        "trick_room": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_speed_profile_returns_team_min_and_max_speeds():
    from draftleaguebot.scoring import speed_control

    context = make_context()
    battle = make_battle(
        allies=[make_pokemon(55), make_pokemon(80)],
        opponents=[make_pokemon(120), make_pokemon(100)],
    )
    expected = (55, 80, 100, 120)

    result = speed_control.speed_profile(context, battle)

    assert result == expected


def test_score_tailwind_rewards_slower_team():
    from draftleaguebot.scoring import speed_control

    context = make_context()
    battle = make_battle(allies=[make_pokemon(70)], opponents=[make_pokemon(120)])
    expected = 11

    result = speed_control.score_tailwind(context, battle)

    assert result == expected


def test_score_trick_room_penalizes_faster_team():
    from draftleaguebot.scoring import speed_control

    context = make_context()
    battle = make_battle(allies=[make_pokemon(130)], opponents=[make_pokemon(70)])
    expected = 1

    result = speed_control.score_trick_room(context, battle)

    assert result == expected


def test_score_speed_control_damage_rewards_non_highest_spread_speed_drop():
    from draftleaguebot.scoring import speed_control

    context = make_context()
    attacker = make_pokemon(70)
    target = make_pokemon(120)
    move = SimpleNamespace(id="icywind", deduced_target="spread")
    expected = 7

    result = speed_control.score_speed_control_damage(
        context,
        battle=SimpleNamespace(),
        attacker=attacker,
        move=move,
        target=target,
        highest_damage=False,
    )

    assert result == expected


def test_score_status_move_routes_tailwind_to_speed_control_module():
    from draftleaguebot.scoring import status

    context = make_context()
    battle = make_battle(allies=[make_pokemon(70)], opponents=[make_pokemon(120)])
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


def test_score_status_move_routes_trick_room_to_speed_control_module():
    from draftleaguebot.scoring import status

    context = make_context()
    battle = make_battle(allies=[make_pokemon(70)], opponents=[make_pokemon(120)])
    expected = 12

    result = status.score_status_move(
        context,
        battle=battle,
        attacker=SimpleNamespace(),
        move=SimpleNamespace(id="trickroom"),
        target=SimpleNamespace(),
        opponents=[],
    )

    assert result == expected


def test_score_damaging_move_routes_speed_control_to_module():
    from draftleaguebot.scoring import damage

    context = make_context(
        _is_immune_to_move=lambda _battle, _move, _target: False,
        _estimate_damage=lambda _battle, _attacker, _move, _target: 50,
        _is_highest_damage_move=lambda *_args: False,
        _estimated_kill=lambda _target, _damage: False,
        _is_high_crit=lambda _move: False,
        _is_super_effective=lambda _battle, _move, _target: False,
        _resisted_penalty=lambda _battle, _move, _target, scale=10: 0,
        _is_threatened_by_any_faster_opponent=lambda _battle, _attacker: False,
        _is_offense_drop_damage_move=lambda _move: False,
        _is_spdef_drop_damage_move=lambda _move: False,
        _score_move_specific_damage=lambda _battle, _attacker, _move, _target: 0,
        _is_contrary_setup_attack=lambda _attacker, _move, _highest, _damage, _target: False,
    )
    attacker = make_pokemon(70)
    target = make_pokemon(120)
    move = SimpleNamespace(id="icywind", priority=0, deduced_target="spread")
    expected = 7.0

    result = damage.score_damaging_move(
        context,
        battle=SimpleNamespace(),
        attacker=attacker,
        move=move,
        target=target,
        opponents=[],
        attacker_moves=[move],
    )

    assert result == expected
