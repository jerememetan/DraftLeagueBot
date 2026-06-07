import random

from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target


class FieldSupportMixin:
	def _is_hazard_move(self, move):
		return move.id in {"stealthrock", "spikes", "toxicspikes", "stickyweb"}


	def _score_hazard_move(self, battle, attacker, move):
		first_turn = getattr(attacker, "first_turn", False)
		if move.id == "stealthrock":
			return self._hazard_score(first_turn, base_low=8, base_high=9)
		if move.id in {"spikes", "toxicspikes"}:
			score = self._hazard_score(first_turn, base_low=8, base_high=9)
			if self._side_condition_active(battle, SideCondition.SPIKES if move.id == "spikes" else SideCondition.TOXIC_SPIKES):
				score -= 1
			return score
		if move.id == "stickyweb":
			return self._hazard_score(first_turn, base_low=9, base_high=12)
		return 0


	def _hazard_score(self, first_turn, base_low, base_high):
		if first_turn:
			return base_high if random.random() < 0.75 else base_low
		return base_high if random.random() < 0.75 else base_low - 2


	def _is_screen_move(self, move):
		return move.id in {"lightscreen", "reflect", "auroraveil"}


	def _score_screen_move(self, battle, attacker, move):
		if move.id == "auroraveil" and not self._is_snow_active(battle):
			return -20
		if self._screen_already_active(battle, move.id):
			return -20
		score = 6
		if move.id == "auroraveil":
			score += 4
		if self._opponent_has_matching_attack(move, battle):
			if getattr(attacker, "item", None) == "lightclay":
				score += 1
			if random.random() < 0.5:
				score += 1
		return score


	def _screen_already_active(self, battle, move_id):
		active = getattr(battle, "side_conditions", {})
		if SideCondition.AURORA_VEIL in active:
			return move_id in {"auroraveil", "reflect", "lightscreen"}
		if move_id == "reflect" and SideCondition.REFLECT in active:
			return True
		if move_id == "lightscreen" and SideCondition.LIGHT_SCREEN in active:
			return True
		return False


	def _opponent_has_matching_attack(self, move, battle):
		if move.id not in {"lightscreen", "reflect"}:
			return False
		opponents = [p for p in battle.opponent_active_pokemon if p is not None]
		for opponent in opponents:
			moves = getattr(opponent, "moves", {})
			for op_move in moves.values():
				category = getattr(op_move, "category", None)
				if category is None:
					continue
				if move.id == "reflect" and category.name.lower() == "physical":
					return True
				if move.id == "lightscreen" and category.name.lower() == "special":
					return True
		return False


	def _side_condition_active(self, battle, condition):
		from draftleaguebot.mechanics import effects

		return effects.side_condition_active(battle, condition)


	def _is_snow_active(self, battle):
		from draftleaguebot.mechanics import effects

		return effects.is_snow_active(battle)


	def _is_recovery_move(self, move):
		return move.id in {
			"recover",
			"slackoff",
			"healorder",
			"softboiled",
			"roost",
			"strengthsap",
			"morningsun",
			"synthesis",
			"moonlight",
			"rest",
		}


	def _is_weather_recovery_move(self, move):
		return move.id in {"morningsun", "synthesis", "moonlight"}


	def _is_sun_active(self, battle):
		from draftleaguebot.mechanics import effects

		return effects.is_sun_active(battle)


	def _is_rain_active(self, battle):
		from draftleaguebot.mechanics import effects

		return effects.is_rain_active(battle)


	def _is_sand_active(self, battle):
		from draftleaguebot.mechanics import effects

		return effects.is_sand_active(battle)


	def _should_recover(self, battle, attacker, weather_boost=False, rest=False):
		hp_frac = getattr(attacker, "current_hp_fraction", 0)
		if getattr(attacker, "status", None) == Status.TOX:
			return False

		recovery_pct = 1.0 if rest else (0.67 if weather_boost else 0.5)
		recovery_hp = attacker.max_hp * recovery_pct

		if self._can_be_ko_by_opponents(battle, attacker, recovery_hp):
			return False

		if self._is_faster_than_any_opponent(battle, attacker):
			if self._can_be_ko_by_opponents(battle, attacker, recovery_hp, allow_after_recover=True):
				return True
			if 0.4 < hp_frac < 0.66:
				return random.random() < 0.5
			if hp_frac < 0.4:
				return True
		else:
			if hp_frac < 0.7:
				return random.random() < 0.75
			if hp_frac < 0.5:
				return True
		return False


	def _can_be_ko_by_opponents(self, battle, attacker, recovery_hp, allow_after_recover=False):
		opponents = [p for p in battle.opponent_active_pokemon if p is not None]
		if not opponents:
			return False
		current_hp = self._get_target_current_hp(attacker)
		if current_hp is None:
			return False
		post_recover_hp = min(attacker.max_hp, current_hp + recovery_hp)
		for opponent in opponents:
			if not allow_after_recover and self._can_ko_target(battle, opponent, attacker):
				return True
			if allow_after_recover:
				moves = getattr(opponent, "moves", {})
				for move in moves.values():
					if not self._is_damaging(move):
						continue
					if self._estimate_damage(battle, opponent, move, attacker, use_max_roll=True) >= post_recover_hp:
						return True
		return False


	def _is_faster_than_any_opponent(self, battle, attacker):
		opponents = [p for p in battle.opponent_active_pokemon if p is not None]
		return any(self._is_faster(attacker, opp) for opp in opponents)


	def _has_sleep_cure(self, attacker):
		item = getattr(attacker, "item", None)
		return item in {"lumberry", "chestoberry"}
