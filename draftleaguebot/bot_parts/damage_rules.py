import random

from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target


class DamageRulesMixin:
	def _is_contrary_setup_attack(self, attacker, move, highest_damage, damage, target):
		if getattr(attacker, "ability", None) != "contrary":
			return False
		if move.id not in {
			"clanging_scales",
			"closecombat",
			"dracometeor",
			"dragonascent",
			"fleurcannon",
			"hammerarm",
			"hyperspacefury",
			"icehammer",
			"leafstorm",
			"overheat",
			"psycho_boost",
			"superpower",
			"vcreate",
		}:
			return False
		if highest_damage:
			return False
		if self._estimated_kill(target, damage):
			return False
		return True


	def _score_contrary_setup(self, attacker, target, move):
		base_bonus = 2
		special_moves = {
			"clanging_scales",
			"dracometeor",
			"fleurcannon",
			"leafstorm",
			"overheat",
			"psycho_boost",
		}
		if move.id in special_moves:
			return base_bonus + self._score_special_setup(attacker, target)
		if move.id in {
			"closecombat",
			"dragonascent",
			"hammerarm",
			"hyperspacefury",
			"icehammer",
			"superpower",
			"vcreate",
		}:
			return base_bonus + self._score_offensive_setup(attacker, target)
		return base_bonus


	def _score_move_specific_damage(self, battle, attacker, move, target):
		move_id = getattr(move, "id", None)
		if move_id is None:
			return 0

		if move_id == "futuresight":
			if self._is_faster(attacker, target) and self._is_threatened_by(battle, target, attacker):
				return 8
			return 6

		if move_id == "relicsong":
			species = getattr(attacker, "species", "").lower()
			if "meloetta" in species and "pirouette" not in species:
				return 10
			if "pirouette" in species:
				return -20
			return 0

		if move_id == "suckerpunch":
			last_move = getattr(attacker, "last_move", None)
			last_id = getattr(last_move, "id", None)
			if last_id == "suckerpunch" and random.random() < 0.5:
				return -20
			return 0

		if move_id == "fakeout":
			if not getattr(attacker, "first_turn", False):
				return -20
			bonus = 8
			if self._is_faster(target, attacker):
				bonus += 2
			return bonus

		if move_id in {"explosion", "selfdestruct", "mistyexplosion"}:
			score = self._score_boom_move(battle, attacker)
			if score == -20:
				return score
			if self._both_last_mon(battle):
				score -= 1
			return score

		if move_id == "pursuit":
			bonus = 0
			if self._is_faster(attacker, target):
				bonus += 3
			if self._estimated_kill(target, self._estimate_damage(battle, attacker, move, target)):
				return bonus + 10
			hp_frac = getattr(target, "current_hp_fraction", 1)
			if hp_frac < 0.2:
				bonus += 10
			elif hp_frac < 0.4 and random.random() < 0.5:
				bonus += 8
			return bonus

		if move_id in {
			"meteorbeam",
			"freezeshock",
			"iceburn",
			"skullbash",
			"skyattack",
			"razorwind",
			"geomancy",
		}:
			base = 9 if getattr(attacker, "item", None) == "powerherb" else -20
			if base > 0 and move_id in {"meteorbeam", "electroshot"}:
				if not self._estimated_kill(target, self._estimate_damage(battle, attacker, move, target)):
					base += 1
			return base

		if move_id == "electroshot":
			if self._is_rain_active(battle):
				base = 9
			else:
				base = 9 if getattr(attacker, "item", None) == "powerherb" else -20
			if base > 0 and not self._estimated_kill(target, self._estimate_damage(battle, attacker, move, target)):
				base += 1
			return base

		if move_id in {"solarbeam", "solarblade"}:
			if self._is_sun_active(battle):
				return 9
			return 9 if getattr(attacker, "item", None) == "powerherb" else -20

		if move_id == "weatherball":
			# Weather Ball is 50 BP normally, 100 BP in active weather
			# Type changes based on weather: Fire/Water/Ice/Rock depending on conditions
			weather = getattr(battle, "weather", {})
			if not weather:
				# No weather; 50 BP normal type is weak
				return 2
			
			# Determine what type Weather Ball becomes
			weather_type = None
			if Weather.SUNNYDAY in weather or Weather.DESOLATELAND in weather:
				weather_type = PokemonType.FIRE
			elif Weather.RAINDANCE in weather or Weather.PRIMORDIALSEA in weather:
				weather_type = PokemonType.WATER
			elif Weather.SANDSTORM in weather:
				weather_type = PokemonType.ROCK
			elif Weather.HAIL in weather or Weather.SNOWSCAPE in weather:
				weather_type = PokemonType.ICE
			
			if weather_type is None:
				# Unknown weather; use neutral scoring
				return 5
			
			# Check effectiveness of the changed type against target
			if target is None:
				return 5  # No target data; assume neutral
			try:
				multiplier = target.damage_multiplier(weather_type)
				if multiplier > 1.0:
					# Super effective! 100 BP with SE is excellent
					return 10
				elif multiplier == 1.0:
					# Neutral; 100 BP is solid
					return 6
				elif multiplier == 0:
					return -20
					# Resisted or immune; don't use this
				return -int(round((1.0 - multiplier) * 12))
			except Exception:
				# Fallback: assume neutral
				return 5

		# Catch-all for unhandled moves
		return 0


	def _score_boom_move(self, battle, attacker):
		if self._is_last_mon(battle) and self._opponent_has_multiple_alive(battle):
			return -20
		hp_frac = getattr(attacker, "current_hp_fraction", 1.0)
		if hp_frac < 0.1:
			return 10
		if hp_frac < 0.33:
			return 8 if random.random() < 0.7 else 0
		if hp_frac < 0.66:
			return 7 if random.random() < 0.5 else 0
		return 7 if random.random() < 0.05 else 0
