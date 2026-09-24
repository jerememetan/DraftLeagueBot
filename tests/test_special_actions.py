from types import SimpleNamespace

from draftleaguebot.bot import DoublesMvpBot
from draftleaguebot.mechanics import tera
from poke_env.battle.move import Move
from poke_env.battle.pokemon_type import PokemonType
from poke_env.player.battle_order import DoubleBattleOrder


def select_orders(
    *, mega=(False, False), z=(False, False), tera=(False, False),
    used_mega=False, used_z=False, used_tera=False, z_eligible=(False, False),
    tera_matches=(False, False), damaging=True,
):
    bot = DoublesMvpBot.__new__(DoublesMvpBot)
    foes = [SimpleNamespace(name="foe1"), SimpleNamespace(name="foe2")]
    moves = [
        SimpleNamespace(
            id=f"move{index}", base_power=80 if damaging else 0,
            z_move_power=160 if damaging else 0,
            type="fire", category=SimpleNamespace(name="PHYSICAL" if damaging else "STATUS"),
        ) for index in range(2)
    ]
    active = [
        SimpleNamespace(
            available_z_moves=[moves[index]] if z_eligible[index] else [],
            tera_type="fire" if tera_matches[index] else "water",
        ) for index in range(2)
    ]
    battle = SimpleNamespace(
        available_moves=[[moves[0]], [moves[1]]],
        opponent_active_pokemon=foes,
        force_switch=[False, False],
        can_mega_evolve=list(mega), used_mega_evolve=used_mega,
        can_z_move=list(z), used_z_move=used_z,
        can_tera=list(tera), used_tera=used_tera,
    )
    bot._get_active_slots = lambda _: [(i, active[i], [moves[i]]) for i in range(2)]
    bot._candidate_targets = lambda *_: [foes[0]]
    bot._score_move = lambda *_: 10
    bot._same_turn_support_conflict = lambda *_: False
    bot._move_target_position = lambda *_: 1
    bot._is_immune_to_move = lambda *_: False
    bot._should_debug = lambda *_: False
    return bot.choose_move(battle)


def test_only_one_mega_per_turn_and_not_after_prior_use():
    order = select_orders(mega=(True, True))
    assert isinstance(order, DoubleBattleOrder)
    assert order.first_order.mega
    assert not order.second_order.mega
    assert not select_orders(mega=(True, True), used_mega=True).first_order.mega


def test_z_move_requires_slot_and_move_permission():
    order = select_orders(z=(True, True), z_eligible=(False, True))
    assert not order.first_order.z_move
    assert order.second_order.z_move
    assert not select_orders(z=(True, False), z_eligible=(True, False), used_z=True).first_order.z_move
    assert not select_orders(z=(True, False), z_eligible=(True, False), damaging=False).first_order.z_move


def test_only_one_z_move_per_turn():
    order = select_orders(z=(True, True), z_eligible=(True, True))
    assert order.first_order.z_move
    assert not order.second_order.z_move


def test_only_one_tera_per_turn_and_not_after_prior_use():
    order = select_orders(tera=(True, True), tera_matches=(True, True))
    assert order.first_order.terastallize
    assert not order.second_order.terastallize
    assert not select_orders(tera=(True, True), tera_matches=(True, True), used_tera=True).first_order.terastallize


def test_tera_only_when_move_matches_tera_type():
    order = select_orders(tera=(True, True), tera_matches=(False, True))
    assert not order.first_order.terastallize
    assert order.second_order.terastallize


def test_defensive_tera_prevents_known_faster_ko():
    bot = DoublesMvpBot.__new__(DoublesMvpBot)
    attacker = SimpleNamespace(types=["water"], tera_type="grass", current_hp=100, max_hp=100)
    opponent = SimpleNamespace(
        moves={"earthquake": SimpleNamespace(id="earthquake", base_power=100, category=SimpleNamespace(name="PHYSICAL"))},
    )
    move = SimpleNamespace(id="protect", base_power=0, category=SimpleNamespace(name="STATUS"))
    target = SimpleNamespace()
    battle = SimpleNamespace(
        can_mega_evolve=[False, False], used_mega_evolve=False,
        can_z_move=[False, False], used_z_move=False,
        can_tera=[True, False], used_tera=False,
    )
    bot._is_faster = lambda faster, slower: faster is opponent
    bot._is_damaging = lambda move: move.base_power > 0
    bot._get_target_current_hp = lambda pokemon: pokemon.current_hp
    bot._estimate_damage = lambda _battle, _attacker, _move, defender, use_max_roll=False: (
        120 if defender.types == ["water"] else 50
    )
    bot._is_immune_to_move = lambda *_: False
    assert bot._special_action(battle, 0, attacker, move, target, [opponent], set()) == "terastallize"
    assert tera.defensive_tera_saves_ko(bot, battle, attacker, "grass", [opponent])


def test_mega_z_and_tera_can_be_chosen_independently():
    order = select_orders(mega=(True, False), z=(True, True), z_eligible=(True, True))
    assert order.first_order.mega
    assert order.second_order.z_move


def test_never_use_z_or_tera_for_immune_target():
    # Normal move scoring rejects immune targets. Check the order layer too.
    bot = DoublesMvpBot.__new__(DoublesMvpBot)
    target = SimpleNamespace()
    move = SimpleNamespace(id="attack", base_power=80, z_move_power=160, type="fire", category=SimpleNamespace(name="PHYSICAL"))
    attacker = SimpleNamespace(available_z_moves=[move], tera_type="fire")
    battle = SimpleNamespace(can_z_move=[True, False], used_z_move=False, can_tera=[True, False], used_tera=False,
                             can_mega_evolve=[False, False], used_mega_evolve=False)
    bot._is_immune_to_move = lambda *_: True
    assert bot._special_action(battle, 0, attacker, move, target, [target], set()) is None


def test_showdown_request_restricts_z_to_the_exact_eligible_move():
    bot = DoublesMvpBot.__new__(DoublesMvpBot)
    battle = SimpleNamespace(last_request={"active": [{
        "moves": [{"id": "flamethrower"}, {"id": "protect"}],
        "canZMove": [{"move": "Inferno Overdrive"}, None],
    }]})
    attacker = SimpleNamespace(available_z_moves=[])
    assert bot._z_move_available(battle, 0, attacker, Move("flamethrower", gen=9))
    assert not bot._z_move_available(battle, 0, attacker, Move("protect", gen=9))


def test_tera_type_from_showdown_request_when_pokemon_lacks_it():
    bot = DoublesMvpBot.__new__(DoublesMvpBot)
    battle = SimpleNamespace(last_request={"active": [{"canTerastallize": "Fire"}]})
    attacker = SimpleNamespace(tera_type=None)
    assert bot._tera_type(battle, 0, attacker) == "Fire"
    move = Move("flamethrower", gen=9)
    battle.can_mega_evolve = [False, False]
    battle.used_mega_evolve = False
    battle.can_z_move = [False, False]
    battle.used_z_move = False
    battle.can_tera = [True, False]
    battle.used_tera = False
    target = SimpleNamespace()
    bot._is_immune_to_move = lambda *_: False
    assert move.type == PokemonType.FIRE
    assert bot._special_action(battle, 0, attacker, move, target, [target], set()) == "terastallize"


def test_tera_type_falls_back_to_own_side_request():
    bot = DoublesMvpBot.__new__(DoublesMvpBot)
    battle = SimpleNamespace(last_request={
        "active": [{}], "side": {"pokemon": [{"teraType": "Fire"}]},
    })
    assert bot._tera_type(battle, 0, SimpleNamespace(tera_type=None)) == "Fire"


def test_stellar_tera_can_boost_an_attacking_move():
    bot = DoublesMvpBot.__new__(DoublesMvpBot)
    target = SimpleNamespace()
    move = Move("flamethrower", gen=9)
    attacker = SimpleNamespace(tera_type=None)
    battle = SimpleNamespace(
        last_request={"active": [{"canTerastallize": "Stellar"}]},
        can_mega_evolve=[False, False], used_mega_evolve=False,
        can_z_move=[False, False], used_z_move=False,
        can_tera=[True, False], used_tera=False,
    )
    bot._is_immune_to_move = lambda *_: False
    assert bot._special_action(battle, 0, attacker, move, target, [target], set()) == "terastallize"


def test_poke_env_serializes_all_three_order_flags():
    bot = DoublesMvpBot.__new__(DoublesMvpBot)
    move = Move("flamethrower", gen=9)
    for action, suffix in (("mega", "mega"), ("z_move", "zmove"), ("terastallize", "terastallize")):
        order = bot.create_order(move, move_target=1, **{action: True})
        assert order.message == f"/choose move flamethrower {suffix} 1"
