from types import SimpleNamespace

from poke_env.battle.target import Target

from draftleaguebot.mechanics import targets


def test_candidate_targets_returns_opponents_for_unknown_target_metadata():
    opponents = [SimpleNamespace(name="foe-1"), SimpleNamespace(name="foe-2")]
    move = SimpleNamespace(target=None, deduced_target=None)

    assert targets.candidate_targets(None, None, move, opponents, setup_move_ids=set()) == opponents


def test_candidate_targets_returns_attacker_for_side_or_setup_targets():
    attacker = SimpleNamespace(name="attacker")
    opponents = [SimpleNamespace(name="foe")]
    setup_move = SimpleNamespace(id="swordsdance", target=Target.NORMAL, deduced_target=Target.NORMAL)

    assert targets.candidate_targets(None, attacker, setup_move, opponents, {"swordsdance"}) == [attacker]


def test_candidate_targets_includes_partner_when_ally_target_is_allowed():
    attacker = SimpleNamespace(name="attacker")
    partner = SimpleNamespace(name="partner")
    opponent = SimpleNamespace(name="foe")
    battle = SimpleNamespace(active_pokemon=[attacker, partner])
    move = SimpleNamespace(id="fling", target=Target.ANY, deduced_target=Target.ANY)

    assert targets.candidate_targets(battle, attacker, move, [opponent], setup_move_ids=set()) == [
        opponent,
        partner,
    ]


def test_ally_target_allowed_preserves_current_policy():
    assert targets.ally_target_allowed(SimpleNamespace(id="fling")) is True
    assert targets.ally_target_allowed(SimpleNamespace(id="beatup")) is True
    assert targets.ally_target_allowed(SimpleNamespace(id="pinmissile")) is True
    assert targets.ally_target_allowed(SimpleNamespace(id="tackle")) is False
