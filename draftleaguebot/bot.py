import random
from typing import Any, List, Optional, Tuple

from poke_env.player import MaxBasePowerPlayer
from poke_env.player.battle_order import DoubleBattleOrder, PassBattleOrder

from draftleaguebot.bot_parts.damage_rules import DamageRulesMixin
from draftleaguebot.bot_parts.field_support import FieldSupportMixin
from draftleaguebot.bot_parts.mechanics_wrappers import MechanicsWrappersMixin
from draftleaguebot.bot_parts.move_helpers import MoveHelpersMixin
from draftleaguebot.bot_parts.setup_wrappers import SetupWrappersMixin
from draftleaguebot.bot_parts.state_orders import StateOrderMixin
from draftleaguebot.bot_parts.status_core import StatusCoreMixin
from draftleaguebot.bot_parts.status_helpers import StatusHelpersMixin


class DoublesMvpBot(DamageRulesMixin, StateOrderMixin, StatusCoreMixin, FieldSupportMixin, SetupWrappersMixin, StatusHelpersMixin, MoveHelpersMixin, MechanicsWrappersMixin, MaxBasePowerPlayer):
	"""Doubles-only MVP logic scaffold based on AI_LOGIC_DOUBLES_MVP.txt."""

	def __init__(self, *args, debug=False, debug_turns=3, **kwargs):
		super().__init__(*args, **kwargs)
		self._debug = debug
		self._debug_turns = debug_turns


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
		selected_moves = []
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

			try:
				move_target = self._move_target_position(battle, attacker, best_move, best_target)
				# Prefer explicit battle-provided availability: can_mega_evolve per active slot
				can_mega_from_battle = False
				try:
					can_mega_from_battle = bool(battle.can_mega_evolve[slot_index])
				except Exception:
					can_mega_from_battle = False
				# Also respect whether we've already used Mega this battle
				if getattr(battle, "used_mega_evolve", False):
					can_mega_from_battle = False
				# Use battle-provided availability; strategic gating removed
				orders.append(self.create_order(best_move, move_target=move_target, mega=can_mega_from_battle))
			except Exception:
				can_mega_from_battle = False
				try:
					can_mega_from_battle = bool(battle.can_mega_evolve[slot_index])
				except Exception:
					can_mega_from_battle = False
				if getattr(battle, "used_mega_evolve", False):
					can_mega_from_battle = False
				orders.append(self.create_order(best_move, mega=can_mega_from_battle))

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


	def _score_move(self, battle, attacker, move, target, opponents, attacker_moves):
		from draftleaguebot.scoring import move_scorer

		return move_scorer.score_move(self, battle, attacker, move, target, opponents, attacker_moves)


	def _same_turn_support_conflict(self, move, selected_moves):
		from draftleaguebot.scoring import doubles

		return doubles.same_turn_support_conflict(self, move, selected_moves)
