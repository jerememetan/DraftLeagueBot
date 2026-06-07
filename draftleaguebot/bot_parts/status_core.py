import random

from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target


class StatusCoreMixin:
	def _score_status_move(self, battle, attacker, move, target, opponents):
		from draftleaguebot.scoring import status

		return status.score_status_move(self, battle, attacker, move, target, opponents)


	def _score_coaching(self, battle, attacker):
		from draftleaguebot.scoring import doubles

		return doubles.score_coaching(self, battle, attacker)


	def _score_baton_pass(self, battle, attacker):
		if not self._has_available_switch(battle):
			return -20
		if self._has_substitute(attacker) or self._has_positive_boost(attacker):
			return 14
		return 0


	def _score_final_gambit(self, battle, attacker, move, target):
		if attacker is None or target is None:
			return 0
		if self._is_immune_to_move(battle, move, target):
			return -20

		attacker_hp = self._get_target_current_hp(attacker)
		target_hp = self._get_target_current_hp(target)
		if attacker_hp is None or target_hp is None:
			return 6

		if self._is_faster(attacker, target):
			if attacker_hp > target_hp:
				return 8
			if self._is_threatened_by(battle, target, attacker):
				return 7
		return 6


	def _score_memento(self, battle, attacker):
		if self._is_last_mon(battle):
			return -20
		hp_frac = getattr(attacker, "current_hp_fraction", 0) or 0
		if hp_frac < 0.1:
			return 16
		if hp_frac < 0.33:
			return 14 if random.random() < 0.7 else 6
		if hp_frac < 0.66:
			return 13 if random.random() < 0.5 else 6
		return 13 if random.random() < 0.05 else 6


	def _score_destiny_bond(self, battle, attacker, target):
		if attacker is None or target is None:
			return 0
		if self._is_faster(attacker, target):
			if self._is_threatened_by(battle, target, attacker):
				return 7 if random.random() < 0.81 else 6
			return 6
		return 5 if random.random() < 0.5 else 6


	def _has_available_switch(self, battle):
		available = getattr(battle, "available_switches", None)
		if isinstance(available, list):
			return any(slot for slot in available)
		return bool(available)


	def _has_substitute(self, pokemon):
		effects = getattr(pokemon, "effects", {})
		return Effect.SUBSTITUTE in effects


	def _has_positive_boost(self, pokemon):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.has_positive_boost(pokemon)


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


	def _score_recovery_move(self, battle, attacker, move):
		if attacker is None:
			return 0
		hp_frac = getattr(attacker, "current_hp_fraction", 0)
		if hp_frac >= 1.0:
			return -20
		if hp_frac >= 0.85:
			return -6

		if self._is_weather_recovery_move(move):
			sun_active = self._is_sun_active(battle)
			recover_decision = self._should_recover(battle, attacker, weather_boost=sun_active)
			if sun_active and recover_decision:
				return 7
			recover_decision = self._should_recover(battle, attacker, weather_boost=False)
			return 7 if recover_decision else 5

		if move.id == "rest":
			recover_decision = self._should_recover(battle, attacker, weather_boost=False, rest=True)
			if recover_decision:
				if self._has_sleep_cure(attacker) or self._has_move_id(attacker, "sleeptalk") or self._has_move_id(attacker, "snore"):
					return 8
				return 7
			return 5

		recover_decision = self._should_recover(battle, attacker, weather_boost=False)
		return 7 if recover_decision else 5
