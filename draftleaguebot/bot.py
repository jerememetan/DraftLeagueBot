import random
from typing import Any, List, Optional, Tuple

from poke_env.player import MaxBasePowerPlayer
from poke_env.player.battle_order import DoubleBattleOrder, PassBattleOrder
from poke_env.data import to_id_str

from draftleaguebot.bot_parts.damage_rules import DamageRulesMixin
from draftleaguebot.bot_parts.field_support import FieldSupportMixin
from draftleaguebot.bot_parts.mechanics_wrappers import MechanicsWrappersMixin
from draftleaguebot.bot_parts.move_helpers import MoveHelpersMixin
from draftleaguebot.bot_parts.setup_wrappers import SetupWrappersMixin
from draftleaguebot.bot_parts.state_orders import StateOrderMixin
from draftleaguebot.bot_parts.status_core import StatusCoreMixin
from draftleaguebot.bot_parts.status_helpers import StatusHelpersMixin
from draftleaguebot.mechanics import tera


class DoublesMvpBot(DamageRulesMixin, StateOrderMixin, StatusCoreMixin, FieldSupportMixin, SetupWrappersMixin, StatusHelpersMixin, MoveHelpersMixin, MechanicsWrappersMixin, MaxBasePowerPlayer):
	"""Doubles-only MVP logic scaffold based on AI_LOGIC_DOUBLES_MVP.txt."""

	def __init__(self, *args, debug=False, debug_turns=3, **kwargs):
		super().__init__(*args, **kwargs)
		self._debug = debug
		self._debug_turns = debug_turns


	@staticmethod
	def _slot_can_use(battle, field, used_field, slot_index):
		"""Read Showdown's per-active-slot permission, respecting previous use."""
		if getattr(battle, used_field, False):
			return False
		available = getattr(battle, field, ())
		return isinstance(available, (list, tuple)) and slot_index < len(available) and bool(available[slot_index])

	@staticmethod
	def _active_request(battle, slot_index):
		request = getattr(battle, "last_request", None) or {}
		active = request.get("active", ())
		return active[slot_index] if slot_index < len(active) else {}


	def _z_move_available(self, battle, slot_index, attacker, move):
		active_request = self._active_request(battle, slot_index)
		if "canZMove" in active_request:
			# Showdown sends one Z option (or null) for each original move slot.
			options = active_request["canZMove"] or ()
			for move_request, option in zip(active_request.get("moves", ()), options):
				if to_id_str(move_request.get("id", "")) == to_id_str(move.id) and option:
					return True
			return False
		# Fallback for synthetic states without the raw Showdown request.
		return any(z_move.id == move.id for z_move in (getattr(attacker, "available_z_moves", ()) or ()))


	def _tera_type(self, battle, slot_index, attacker):
		active_request = self._active_request(battle, slot_index)
		type_name = active_request.get("canTerastallize")
		if not type_name:
			request = getattr(battle, "last_request", None) or {}
			pokemon = request.get("side", {}).get("pokemon", ())
			if slot_index < len(pokemon):
				type_name = pokemon[slot_index].get("teraType")
		return type_name or getattr(attacker, "tera_type", None)


	def _special_action(self, battle, slot_index, attacker, move, target, opponents, chosen):
		"""Select at most one special action per type across both active slots."""
		if self._slot_can_use(battle, "can_mega_evolve", "used_mega_evolve", slot_index) and "mega" not in chosen:
			return "mega"

		if self._slot_can_use(battle, "can_tera", "used_tera", slot_index) and "terastallize" not in chosen:
			tera_type = self._tera_type(battle, slot_index, attacker)
			if tera.defensive_tera_saves_ko(self, battle, attacker, tera_type, opponents):
				return "terastallize"

		# Z-Moves are move-specific. can_z_move alone does not mean every move is legal.
		if target is not None and any(target is opponent for opponent in opponents) and self._is_damaging(move):
			if not self._is_immune_to_move(battle, move, target):
				if self._slot_can_use(battle, "can_z_move", "used_z_move", slot_index) and "z_move" not in chosen:
					if self._z_move_available(battle, slot_index, attacker, move):
						if getattr(move, "z_move_power", 0) > getattr(move, "base_power", 0):
							return "z_move"

				if self._slot_can_use(battle, "can_tera", "used_tera", slot_index) and "terastallize" not in chosen:
					# Use offensive Tera only when this move gains a Tera STAB boost.
					tera_type = self._tera_type(battle, slot_index, attacker)
					move_type = getattr(move, "type", None)
					tera_name = to_id_str(getattr(tera_type, "name", tera_type)) if tera_type is not None else None
					move_name = to_id_str(getattr(move_type, "name", move_type)) if move_type is not None else None
					if tera_name is not None and move_name is not None and tera.offensive_tera_is_valuable(
						self, battle, attacker, tera_type, move, target
					):
						return "terastallize"
		return None


	def choose_move(self, battle):
		forced_switch_order = self._forced_switch_order(battle)
		if forced_switch_order is not None:
			if self._should_debug(battle):
				self._log_final_orders([
					forced_switch_order.first_order,
					forced_switch_order.second_order,
				])
			return forced_switch_order

		if not battle.available_moves:
			return self.choose_random_move(battle)

		opponents = [p for p in battle.opponent_active_pokemon if p is not None]
		if not opponents:
			return self.choose_random_move(battle)

		orders = []
		selected_moves = []
		chosen_actions = set()
		for slot_index, attacker, moves in self._get_active_slots(battle):
			if not moves:
				order = self._fallback_order_for_slot(battle, slot_index)
				if order is not None:
					orders.append(order)
				continue

			scored: List[Tuple[float, Any, Optional[Any]]] = []
			for move in moves:
				if not hasattr(move, "id"):
					continue
				targets = self._candidate_targets(battle, attacker, move, opponents)
				for target in targets:
					score = self._score_move(battle, attacker, move, target, opponents, moves)
					if self._same_turn_support_conflict(move, selected_moves):
						score = -20
					scored.append((score, move, target))

			if not scored:
				order = self._fallback_order_for_slot(battle, slot_index)
				if order is not None:
					orders.append(order)
				continue

			best_score = max(s[0] for s in scored)
			best = [s for s in scored if s[0] == best_score]
			_, best_move, best_target = random.choice(best)
			selected_moves.append(best_move)
			if self._should_debug(battle):
				self._log_decision(battle, slot_index, attacker, scored, best_move, best_target)

			move_target = self._move_target_position(battle, attacker, best_move, best_target)
			action = self._special_action(
				battle, slot_index, attacker, best_move, best_target, opponents, chosen_actions
			)
			if action:
				chosen_actions.add(action)
			orders.append(self.create_order(best_move, move_target=move_target, **({action: True} if action else {})))

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
		from draftleaguebot import debug as debug_helpers

		return debug_helpers.should_debug(self._debug, self._debug_turns, battle)


	def _log_decision(self, battle, slot_index, attacker, scored, best_move, best_target):
		from draftleaguebot import debug as debug_helpers

		debug_helpers.log_decision(battle, slot_index, attacker, scored)


	def _log_final_orders(self, orders):
		from draftleaguebot import debug as debug_helpers

		debug_helpers.log_final_orders(orders)


	def _forced_switch_order(self, battle):
		force_switch = getattr(battle, "force_switch", None)
		if not isinstance(force_switch, list) or not any(force_switch):
			return None

		orders = []
		selected_switches = []
		for slot_index in range(2):
			if slot_index < len(force_switch) and force_switch[slot_index]:
				switch = self._forced_switch_for_slot(battle, slot_index, selected_switches)
				if switch is None:
					orders.append(PassBattleOrder())
				else:
					selected_switches.append(switch)
					orders.append(self.create_order(switch))
			else:
				orders.append(PassBattleOrder())
		return DoubleBattleOrder(first_order=orders[0], second_order=orders[1])


	def _forced_switch_for_slot(self, battle, slot_index, selected_switches):
		available_switches = getattr(battle, "available_switches", None)
		if isinstance(available_switches, list):
			if slot_index >= len(available_switches):
				return None
			candidates = list(available_switches[slot_index])
		elif available_switches:
			candidates = list(available_switches)
		else:
			return None

		candidates = [pokemon for pokemon in candidates if pokemon not in selected_switches]
		if not candidates:
			return None
		return random.choice(candidates)


	def _score_move(self, battle, attacker, move, target, opponents, attacker_moves):
		from draftleaguebot.scoring import move_scorer

		return move_scorer.score_move(self, battle, attacker, move, target, opponents, attacker_moves)


	def _same_turn_support_conflict(self, move, selected_moves):
		from draftleaguebot.scoring import doubles

		return doubles.same_turn_support_conflict(self, move, selected_moves)
