import random
from typing import List, Optional, Tuple

from poke_env.player import MaxBasePowerPlayer
from poke_env.battle.double_battle import DoubleBattle
from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target
from poke_env.player.battle_order import DoubleBattleOrder, PassBattleOrder


class DoublesMvpBot(MaxBasePowerPlayer):
	"""Doubles-only MVP logic scaffold based on AI_LOGIC_DOUBLES_MVP.txt."""

	def __init__(self, *args, debug=False, debug_turns=3, **kwargs):
		super().__init__(*args, **kwargs)
		self._debug = debug
		self._debug_turns = debug_turns

	def _should_mega_evolve(self, pokemon, battle):
		return False

	def _should_z_move(self, pokemon, battle):
		return False

	def _should_terastallize(self, pokemon, battle):
		return False

	def choose_move(self, battle):
		# Forced switch handling (Perish Song) can be added here once battle effects are exposed.
		if not battle.available_moves:
			return self.choose_random_move(battle)

		opponents = [p for p in battle.opponent_active_pokemon if p is not None]
		if not opponents:
			return self.choose_random_move(battle)

		orders = []
		for slot_index, attacker, moves in self._get_active_slots(battle):
			if not moves:
				order = self._fallback_order_for_slot(battle, slot_index)
				if order is not None:
					orders.append(order)
				continue

			scored: List[Tuple[float, object, Optional[object]]] = []
			for move in moves:
				if not hasattr(move, "id"):
					continue
				targets = self._candidate_targets(battle, attacker, move, opponents)
				for target in targets:
					score = self._score_move(battle, attacker, move, target, opponents, moves)
					scored.append((score, move, target))

			if not scored:
				order = self._fallback_order_for_slot(battle, slot_index)
				if order is not None:
					orders.append(order)
				continue

			best_score = max(s[0] for s in scored)
			best = [s for s in scored if s[0] == best_score]
			_, best_move, best_target = random.choice(best)
			if self._should_debug(battle):
				self._log_decision(battle, slot_index, attacker, scored, best_move, best_target)

			try:
				move_target = self._move_target_position(battle, attacker, best_move, best_target)
				orders.append(self.create_order(best_move, move_target=move_target))
			except Exception:
				orders.append(self.create_order(best_move))

		if not orders:
			return self.choose_random_move(battle)
		if len(orders) == 1:
			if self._should_debug(battle):
				self._log_final_orders([orders[0]])
			return orders[0]
		if len(orders) >= 2:
			if self._should_debug(battle):
				self._log_final_orders([orders[0], orders[1]])
			return DoubleBattleOrder(first_order=orders[0], second_order=orders[1])
		if self._should_debug(battle):
			self._log_final_orders([orders[0], PassBattleOrder()])
		return DoubleBattleOrder(first_order=orders[0], second_order=PassBattleOrder())

	def _should_debug(self, battle):
		if not self._debug:
			return False
		turn = getattr(battle, "turn", None)
		if turn is None:
			return True
		return turn <= self._debug_turns

	def _log_decision(self, battle, slot_index, attacker, scored, best_move, best_target):
		turn = getattr(battle, "turn", "?")
		move_id = getattr(best_move, "id", "?")
		target_name = getattr(best_target, "name", "?")
		attacker_name = getattr(attacker, "name", "?")
		best_score = max(s[0] for s in scored) if scored else 0
		print(
			f"[AI DEBUG] turn={turn} slot={slot_index} attacker={attacker_name} "
			f"move={move_id} target={target_name} score={best_score:.2f}"
		)

	def _log_final_orders(self, orders):
		messages = [order.message for order in orders]
		print(f"[AI DEBUG] final_orders={messages}")

	def _score_move(self, battle, attacker, move, target, opponents, attacker_moves):
		score = 0.0

		if self._is_damaging(move):
			damage = self._estimate_damage(battle, attacker, move, target)
			highest_damage = self._is_highest_damage_move(
				battle, attacker, move, target, opponents, attacker_moves, damage
			)
			if highest_damage:
				score += self._rng_weight(6, 8, 0.8)

			if self._estimated_kill(target, damage):
				if self._is_faster(attacker, target) or (
					move.priority > 0 and not self._is_faster(attacker, target)
				):
					score += 6
				else:
					score += 3

				if self._has_snowball_ability(attacker):
					score += 1

			if self._is_high_crit(move) and self._is_super_effective(battle, move, target):
				score += self._rng_weight(1, 0, 0.5)

			if move.priority > 0 and self._is_threatened_by(battle, target, attacker):
				if not self._is_faster(attacker, target):
					score += 11

			if self._is_speed_control_damage_move(move):
				score += self._score_speed_control_damage(battle, attacker, move, target, highest_damage)

			score += self._apply_doubles_damage_bonuses(battle, attacker, move, target)

		else:
			score += self._score_status_move(battle, attacker, move, target, opponents)

		return score

	def _move_target_position(self, battle, attacker, move, target):
		move_target = getattr(move, "deduced_target", None) or getattr(move, "target", None)
		if move_target is None:
			return DoubleBattle.EMPTY_TARGET_POSITION
		if not isinstance(move_target, Target):
			return DoubleBattle.EMPTY_TARGET_POSITION

		if move_target in {Target.NORMAL, Target.ANY, Target.ADJACENT_FOE}:
			if self._is_partner(battle, attacker, target):
				self_pos, ally_pos = self._ally_positions(battle, attacker)
				return ally_pos if ally_pos is not None else self_pos
			position = self._opponent_position(battle, target)
			return position if position is not None else DoubleBattle.EMPTY_TARGET_POSITION

		if move_target in {Target.ADJACENT_ALLY, Target.ADJACENT_ALLY_OR_SELF}:
			self_pos, ally_pos = self._ally_positions(battle, attacker)
			if move_target == Target.ADJACENT_ALLY:
				return ally_pos if ally_pos is not None else DoubleBattle.EMPTY_TARGET_POSITION
			return ally_pos if ally_pos is not None else self_pos

		if move_target == Target.SELF:
			self_pos, _ = self._ally_positions(battle, attacker)
			return self_pos if self_pos is not None else DoubleBattle.EMPTY_TARGET_POSITION

		return DoubleBattle.EMPTY_TARGET_POSITION

	def _opponent_position(self, battle, target):
		for index, foe in enumerate(battle.opponent_active_pokemon):
			if foe is target:
				return DoubleBattle.OPPONENT_1_POSITION if index == 0 else DoubleBattle.OPPONENT_2_POSITION
		return None

	def _ally_positions(self, battle, attacker):
		active = battle.active_pokemon
		if not isinstance(active, list):
			return DoubleBattle.POKEMON_1_POSITION, None
		if len(active) >= 1 and active[0] is attacker:
			return DoubleBattle.POKEMON_1_POSITION, DoubleBattle.POKEMON_2_POSITION
		if len(active) >= 2 and active[1] is attacker:
			return DoubleBattle.POKEMON_2_POSITION, DoubleBattle.POKEMON_1_POSITION
		return DoubleBattle.POKEMON_1_POSITION, None

	def _score_status_move(self, battle, attacker, move, target, opponents):
		move_id = getattr(move, "id", None)
		if move_id is None:
			return 0

		if move_id in {"tailwind"}:
			if self._team_is_slower(battle):
				return 9
			return 5

		if move_id in {"trickroom"}:
			if getattr(battle, "trick_room", False):
				return -20
			if self._team_is_slower(battle):
				return 10
			return 5

		if move_id in {"helpinghand", "followme"}:
			if self._partner_using_support_or_status(battle, attacker):
				return -20
			return 6

		if move_id in {"thunderwave", "stunspore", "glare", "nuzzle", "zapcannon"}:
			return self._score_paralysis(attacker, target)

		if move_id == "willowisp":
			return self._score_wisp(battle, attacker, target)

		if self._is_sleep_status_move(move):
			return self._score_sleep_move(battle, attacker, move, target)

		if self._is_poison_status_move(move):
			return self._score_poison_move(battle, attacker, target)

		if move_id == "taunt":
			return self._score_taunt(battle, attacker, target)

		if move_id == "encore":
			return self._score_encore(attacker, target)

		if move_id in {"protect", "kingsshield"}:
			return self._score_protect(attacker, target)

		return 0

	def _score_protect(self, attacker, target):
		score = 6
		if self._has_protect_penalty(attacker):
			return -20
		if self._has_status_or_effect(attacker):
			score -= 2
		if self._has_status_or_effect(target):
			score += 1
		if self._dies_to_secondary(attacker):
			return -20
		return score

	def _score_sleep_move(self, battle, attacker, move, target):
		score = 7
		if getattr(move, "id", None) == "spore":
			score += 2
		if random.random() < 0.25:
			if self._can_sleep_target(target):
				score += 1
				if self._has_move_id(attacker, "dreameater") or self._has_move_id(attacker, "nightmare"):
					if not self._has_move_id(target, "snore") and not self._has_move_id(target, "sleeptalk"):
						score += 1
				if self._has_hex_move(attacker) or self._partner_has_hex(battle, attacker):
					score += 1
		return score

	def _score_poison_move(self, battle, attacker, target):
		score = 6
		if random.random() < 0.38:
			if not self._can_ko_target(battle, attacker, target) and self._can_poison_target(target):
				if self._has_poison_synergy(attacker) and not self._has_damaging_move(target):
					score += 2
		return score

	def _is_sleep_status_move(self, move):
		status = getattr(move, "status", None)
		category = getattr(move, "category", None)
		return status == Status.SLP and category is not None and category.name.lower() == "status"

	def _is_poison_status_move(self, move):
		status = getattr(move, "status", None)
		category = getattr(move, "category", None)
		return status in {Status.PSN, Status.TOX} and category is not None and category.name.lower() == "status"

	def _can_sleep_target(self, target):
		if target is None:
			return False
		if getattr(target, "status", None) is not None:
			return False
		return True

	def _can_poison_target(self, target):
		if target is None:
			return False
		if getattr(target, "status", None) is not None:
			return False
		if self._has_any_type(target, {PokemonType.POISON, PokemonType.STEEL}):
			return False
		hp_frac = getattr(target, "current_hp_fraction", 0)
		return hp_frac is not None and hp_frac > 0.2

	def _can_ko_target(self, battle, attacker, target):
		moves = getattr(attacker, "moves", {})
		if not moves:
			return False
		current_hp = self._get_target_current_hp(target)
		if current_hp is None:
			return False
		for move in moves.values():
			if not self._is_damaging(move):
				continue
			damage = self._estimate_damage(battle, attacker, move, target, use_max_roll=True)
			if damage >= current_hp:
				return True
		return False

	def _has_poison_synergy(self, pokemon):
		return (
			self._has_move_id(pokemon, "hex")
			or self._has_move_id(pokemon, "venomdrench")
			or self._has_move_id(pokemon, "venoshock")
			or getattr(pokemon, "ability", None) == "merciless"
		)

	def _has_damaging_move(self, pokemon):
		moves = getattr(pokemon, "moves", {})
		for move in moves.values():
			if self._is_damaging(move):
				return True
		return False

	def _score_paralysis(self, attacker, target):
		if target is None:
			return 0
		attacker_speed = self._safe_speed(attacker)
		target_speed = self._safe_speed(target)
		faster_then_slow = target_speed > attacker_speed and (target_speed / 4) < attacker_speed
		encouraged = faster_then_slow or self._has_hex_move(attacker) or self._has_flinch_move(attacker)
		if self._has_status_or_effect(target, include_confusion=True):
			encouraged = True
		if encouraged:
			score = 8
		else:
			score = 7
		if random.random() < 0.5:
			score -= 1
		return score

	def _score_wisp(self, battle, attacker, target):
		score = 6
		if random.random() < 0.37:
			if self._has_physical_move(target):
				score += 1
			if self._has_hex_move(attacker) or self._partner_has_hex(battle, attacker):
				score += 1
		return score

	def _score_taunt(self, battle, attacker, target):
		if target is None:
			return 5
		if self._has_move_id(target, "trickroom") and not getattr(battle, "trick_room", False):
			return 9
		if self._has_move_id(target, "defog"):
			side_conditions = getattr(battle, "side_conditions", {})
			if SideCondition.AURORA_VEIL in side_conditions and self._is_faster(attacker, target):
				return 9
		return 5

	def _score_encore(self, attacker, target):
		if target is None:
			return 0
		effects = getattr(target, "effects", {})
		if Effect.ENCORE in effects or getattr(target, "first_turn", False):
			return -20
		encouraged = self._encore_encouraged(target)
		if self._is_faster(attacker, target) and encouraged:
			return 7
		if not self._is_faster(attacker, target):
			return 6 if random.random() < 0.5 else 5
		return 6

	def _encore_encouraged(self, target):
		last_move = getattr(target, "last_move", None)
		if last_move is None:
			return False
		category = getattr(last_move, "category", None)
		return category is not None and category.name.lower() == "status"

	def _has_protect_penalty(self, attacker):
		counter = getattr(attacker, "protect_counter", 0)
		if counter >= 2:
			return True
		if counter == 1:
			return random.random() < 0.5
		return False

	def _has_status_or_effect(self, pokemon, include_confusion=False):
		if pokemon is None:
			return False
		if getattr(pokemon, "status", None) in {Status.PSN, Status.TOX, Status.BRN}:
			return True
		effects = getattr(pokemon, "effects", {})
		if include_confusion and Effect.CONFUSION in effects:
			return True
		for effect in self._protect_effects():
			if effect in effects:
				return True
		return False

	def _protect_effects(self):
		return {
			Effect.CURSE,
			Effect.ATTRACT,
			Effect.LEECH_SEED,
			Effect.YAWN,
			Effect.PERISH0,
			Effect.PERISH1,
			Effect.PERISH2,
			Effect.PERISH3,
		}

	def _dies_to_secondary(self, pokemon):
		if pokemon is None:
			return False
		hp_frac = getattr(pokemon, "current_hp_fraction", 0)
		if hp_frac is None:
			return False
		if hp_frac > 0.1:
			return False
		return self._has_status_or_effect(pokemon)

	def _partner_using_support_or_status(self, battle, attacker):
		partner = self._get_partner(battle, attacker)
		if partner is None:
			return False
		last_move = getattr(partner, "last_move", None)
		if last_move is None:
			return False
		move_id = getattr(last_move, "id", None)
		if move_id in {"helpinghand", "followme"}:
			return True
		category = getattr(last_move, "category", None)
		return category is not None and category.name.lower() == "status"

	def _has_move_id(self, pokemon, move_id):
		moves = getattr(pokemon, "moves", {})
		return move_id in moves

	def _has_physical_move(self, pokemon):
		moves = getattr(pokemon, "moves", {})
		for move in moves.values():
			category = getattr(move, "category", None)
			if category is not None and category.name.lower() == "physical":
				return True
		return False

	def _has_flinch_move(self, pokemon):
		moves = getattr(pokemon, "moves", {})
		flinch_moves = {
			"airslash",
			"rockslide",
			"ironhead",
			"zenheadbutt",
			"darkpulse",
			"waterfall",
			"bite",
			"stomp",
			"fakeout",
			"headbutt",
			"twister",
		}
		for move in moves.values():
			move_id = getattr(move, "id", None)
			if move_id in flinch_moves:
				return True
		return False

	def _has_hex_move(self, pokemon):
		moves = getattr(pokemon, "moves", {})
		return "hex" in moves

	def _partner_has_hex(self, battle, attacker):
		partner = self._get_partner(battle, attacker)
		if partner is None:
			return False
		return self._has_hex_move(partner)

	def _get_partner(self, battle, attacker):
		active = battle.active_pokemon
		if not isinstance(active, list):
			return None
		if len(active) >= 1 and active[0] is attacker:
			return active[1] if len(active) > 1 else None
		if len(active) >= 2 and active[1] is attacker:
			return active[0]
		return None

	def _apply_doubles_damage_bonuses(self, battle, attacker, move, target):
		move_id = getattr(move, "id", None)
		if move_id is None:
			return 0
		bonus = 0

		if move_id in {"shadowsneak", "aquajet", "iceshard", "vacuumwave", "bulletpunch", "machpunch", "watershuriken"}:
			bonus += self._weakness_policy_partner_bonus(battle, attacker, move, target)

		if move_id == "fling":
			bonus += self._fling_speed_bonus(battle, attacker, move, target)

		if move_id in {"earthquake", "magnitude"}:
			bonus += self._earthquake_partner_bonus(battle)

		return bonus

	def _is_speed_control_damage_move(self, move):
		move_id = getattr(move, "id", None)
		return move_id in {"icywind", "electroweb", "rocktomb", "mudshot", "lowsweep"}

	def _score_speed_control_damage(self, battle, attacker, move, target, highest_damage):
		if highest_damage:
			return 0
		if self._is_immune_to_speed_drop(target):
			base = 5
		else:
			base = 6 if not self._is_faster(attacker, target) else 5
		if self._is_spread_move(move) and getattr(move, "id", None) in {"icywind", "electroweb"}:
			base += 1
		return base

	def _is_immune_to_speed_drop(self, target):
		if target is None:
			return False
		ability = getattr(target, "ability", None)
		return ability in {"contrary", "clearbody", "whitesmoke"}

	def _is_spread_move(self, move):
		move_target = getattr(move, "deduced_target", None) or getattr(move, "target", None)
		return move_target in {Target.ALL_ADJACENT_FOES, Target.ALL_ADJACENT, Target.ALL}

	def _weakness_policy_partner_bonus(self, battle, attacker, move, target):
		partner = self._get_partner(battle, attacker)
		if partner is None or target is None:
			return 0
		if partner.item != "weaknesspolicy":
			return 0
		if target is not partner:
			return 0
		if self._is_super_effective_on_target(move, partner):
			return 12
		return 0

	def _fling_speed_bonus(self, battle, attacker, move, target):
		partner = self._get_partner(battle, attacker)
		if partner is None or target is None:
			return 0
		if target is not partner:
			return 0
		if attacker.item not in {"salacberry"}:
			return 0
		if partner.item == "weaknesspolicy" and self._is_super_effective_on_target(move, partner):
			return 12
		return 9

	def _candidate_targets(self, battle, attacker, move, opponents):
		move_target = getattr(move, "deduced_target", None) or getattr(move, "target", None)
		if not isinstance(move_target, Target):
			return list(opponents)
		targets = []
		if self._move_allows_foe(move_target):
			targets.extend(list(opponents))
		if self._move_allows_ally(move_target):
			partner = self._get_partner(battle, attacker)
			if partner is not None:
				targets.append(partner)
		return targets

	def _move_allows_foe(self, move_target):
		return move_target in {Target.NORMAL, Target.ADJACENT_FOE, Target.ANY, Target.ALL_ADJACENT_FOES}

	def _move_allows_ally(self, move_target):
		return move_target in {Target.NORMAL, Target.ADJACENT_ALLY, Target.ADJACENT_ALLY_OR_SELF, Target.ANY}

	def _is_partner(self, battle, attacker, target):
		partner = self._get_partner(battle, attacker)
		return partner is not None and target is partner

	def _earthquake_partner_bonus(self, battle):
		attacker = None
		active = battle.active_pokemon
		if isinstance(active, list) and active:
			attacker = active[0]
		elif active is not None:
			attacker = active
		partner = self._get_partner(battle, attacker) if attacker is not None else None
		if partner is None:
			return 0

		partner_immune = self._is_immune_to_ground(partner)
		partner_levitating = Effect.MAGNET_RISE in getattr(partner, "effects", {})
		partner_faster = False
		if attacker is not None:
			partner_faster = self._is_faster(partner, attacker)

		if partner_immune or (partner_levitating and partner_faster):
			return 2

		if self._has_any_type(partner, {PokemonType.FIRE, PokemonType.POISON, PokemonType.ELECTRIC, PokemonType.ROCK}):
			return -10
		return -3

	def _is_immune_to_ground(self, pokemon):
		try:
			if getattr(pokemon, "ability", None) == "levitate":
				return True
			if getattr(pokemon, "item", None) == "airballoon":
				return True
			return pokemon.damage_multiplier(PokemonType.GROUND) == 0
		except Exception:
			return False

	def _has_any_type(self, pokemon, types):
		try:
			return any(t in types for t in pokemon.types)
		except Exception:
			return False

	def _is_damaging(self, move):
		return getattr(move, "base_power", 0) > 0 and move.category.name.lower() != "status"

	def _estimate_damage(self, battle, attacker, move, target, use_max_roll=False):
		base = getattr(move, "base_power", 0)
		if base <= 0:
			return 0.0

		level = getattr(attacker, "level", 100) or 100
		attack_stat, defense_stat = self._get_offense_defense_stats(attacker, target, move)
		stab = 1.5 if self._has_stab(attacker, move) else 1.0
		multiplier = 1.0
		if hasattr(battle, "damage_multiplier"):
			try:
				multiplier = battle.damage_multiplier(move, target)
			except Exception:
				multiplier = 1.0
		roll = 1.0 if use_max_roll else self._damage_roll_factor()

		base_damage = (((2 * level / 5 + 2) * base * attack_stat / max(1, defense_stat)) / 50) + 2
		return base_damage * stab * multiplier * roll

	def _is_highest_damage_move(self, battle, attacker, move, target, opponents, attacker_moves, current_damage):
		current = current_damage
		for other in attacker_moves:
			if not self._is_damaging(other):
				continue
			other_damage = self._estimate_damage(battle, attacker, other, target)
			if other_damage > current:
				return False
		return True

	def _estimated_kill(self, target, damage):
		current_hp = self._get_target_current_hp(target)
		if current_hp is None:
			return False
		return damage >= current_hp

	def _is_faster(self, attacker, defender):
		try:
			return attacker.stats["spe"] > defender.stats["spe"]
		except Exception:
			return False

	def _team_is_slower(self, battle):
		allies = [p for p in battle.active_pokemon if p is not None]
		opponents = [p for p in battle.opponent_active_pokemon if p is not None]
		if not allies or not opponents:
			return False
		ally_speeds = [self._safe_speed(p) for p in allies]
		foe_speeds = [self._safe_speed(p) for p in opponents]
		if not ally_speeds or not foe_speeds:
			return False
		fastest_ally = max(ally_speeds)
		fastest_foe = max(foe_speeds)
		return fastest_ally < fastest_foe

	def _safe_speed(self, pokemon):
		try:
			speed = pokemon.stats.get("spe", 0)
			return 0 if speed is None else speed
		except Exception:
			return 0

	def _is_high_crit(self, move):
		return getattr(move, "crit_ratio", 0) > 1

	def _is_super_effective(self, battle, move, target):
		multiplier = 1.0
		if hasattr(battle, "damage_multiplier"):
			try:
				multiplier = battle.damage_multiplier(move, target)
			except Exception:
				multiplier = 1.0
		return multiplier > 1.0

	def _is_super_effective_on_target(self, move, target):
		try:
			return target.damage_multiplier(move) > 1.0
		except Exception:
			return False

	def _has_snowball_ability(self, pokemon):
		ability = getattr(pokemon, "ability", None)
		return ability in {"moxie", "beastboost", "chillingneigh", "grimneigh"}

	def _is_threatened_by(self, battle, attacker, defender):
		moves = getattr(attacker, "moves", None)
		if not moves:
			return False
		current_hp = self._get_target_current_hp(defender)
		if current_hp is None:
			return False

		for move in moves.values():
			if not self._is_damaging(move):
				continue
			damage = self._estimate_damage(battle, attacker, move, defender, use_max_roll=True)
			if damage >= current_hp:
				return True
		return False

	def _get_active_slots(self, battle):
		available = battle.available_moves
		active = battle.active_pokemon
		if isinstance(available, list) and available and isinstance(available[0], list):
			slots = []
			if isinstance(active, list):
				for index, moves in enumerate(available):
					attacker = active[index] if index < len(active) else None
					if attacker is None:
						continue
					slots.append((index, attacker, moves))
			else:
				slots.append((0, active, available[0]))
			return slots
		return [(0, active, available)]

	def _fallback_order_for_slot(self, battle, slot_index):
		available_switches = getattr(battle, "available_switches", None)
		if isinstance(available_switches, list):
			if slot_index < len(available_switches) and available_switches[slot_index]:
				return self.create_order(random.choice(available_switches[slot_index]))
		elif available_switches:
			return self.create_order(random.choice(available_switches))
		return None

	def _get_offense_defense_stats(self, attacker, target, move):
		category = move.category.name.lower()
		if category == "physical":
			return self._stat(attacker, "atk"), self._stat(target, "def")
		if category == "special":
			return self._stat(attacker, "spa"), self._stat(target, "spd")
		return 1, 1

	def _stat(self, pokemon, key):
		try:
			return max(1, pokemon.stats.get(key, 1))
		except Exception:
			return 1

	def _has_stab(self, attacker, move):
		move_type = getattr(move, "type", None)
		if move_type is None:
			return False
		try:
			return move_type in attacker.types
		except Exception:
			return False

	def _damage_roll_factor(self):
		return random.uniform(0.85, 1.0)

	def _get_target_current_hp(self, target):
		current_hp = getattr(target, "current_hp", None)
		if current_hp is not None:
			return current_hp
		current_hp_fraction = getattr(target, "current_hp_fraction", None)
		max_hp = self._get_target_max_hp(target)
		if current_hp_fraction is None or max_hp is None:
			return None
		return max_hp * current_hp_fraction

	def _get_target_max_hp(self, target):
		max_hp = getattr(target, "max_hp", None)
		if max_hp is not None:
			return max_hp
		current_hp = getattr(target, "current_hp", None)
		current_hp_fraction = getattr(target, "current_hp_fraction", None)
		if current_hp is None or current_hp_fraction in (None, 0):
			return None
		return current_hp / current_hp_fraction

	def _rng_weight(self, low, high, low_prob):
		return low if random.random() < low_prob else high
