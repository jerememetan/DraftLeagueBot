import random
from typing import Any, List, Optional, Tuple
from poke_env.player import MaxBasePowerPlayer
from poke_env.battle.double_battle import DoubleBattle
from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target
from poke_env.player.battle_order import DoubleBattleOrder, PassBattleOrder


class DoublesMvpBot(MaxBasePowerPlayer):
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

	def _is_last_mon(self, battle):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.is_last_mon(battle)

	def _both_last_mon(self, battle):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.both_last_mon(battle)

	def _opponent_has_multiple_alive(self, battle):
		from draftleaguebot.mechanics import pokemon_state
		return pokemon_state.opponent_has_multiple_alive(battle)

	def _alive_counts(self, battle):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.alive_counts(battle)

	def _active_list(self, active):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.active_list(active)

	def _count_alive(self, team):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.count_alive(team)

	def _move_target_position(self, battle, attacker, move, target):
		from draftleaguebot import orders

		return orders.move_target_position(
			battle,
			attacker,
			move,
			target,
			ally_target_allowed=self._ally_target_allowed,
			is_partner=self._is_partner,
		)

	def _opponent_position(self, battle, target):
		from draftleaguebot import orders

		return orders.opponent_position(battle, target)

	def _ally_positions(self, battle, attacker):
		from draftleaguebot import orders

		return orders.ally_positions(battle, attacker)

	def _score_status_move(self, battle, attacker, move, target, opponents):
		from draftleaguebot.scoring import status

		return status.score_status_move(self, battle, attacker, move, target, opponents)

	def _score_coaching(self, battle, attacker):
		partner = self._get_partner(battle, attacker)
		if partner is None:
			return -20
		if getattr(partner, "ability", None) == "contrary":
			return -20
		score = 6
		atk_boost = self._get_boost(partner, "atk")
		def_boost = self._get_boost(partner, "def")
		if atk_boost < 2:
			score += 1 - atk_boost
		if def_boost < 2:
			score += 1 - def_boost
		if random.random() < 0.8:
			score += 1
		return score

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

	def _score_setup_move(self, battle, attacker, target, move):
		from draftleaguebot.scoring import setup

		return setup.score_setup_move(self, battle, attacker, target, move)

	def _score_offensive_setup(self, attacker, target):
		from draftleaguebot.scoring import setup

		return setup.score_offensive_setup(self, attacker, target)

	def _score_defensive_setup(self, attacker, target, boosts_both=False):
		from draftleaguebot.scoring import setup

		return setup.score_defensive_setup(self, attacker, target, boosts_both=boosts_both)

	def _score_special_setup(self, attacker, target):
		from draftleaguebot.scoring import setup

		return setup.score_special_setup(self, attacker, target)

	def _score_speed_setup(self, attacker, target):
		from draftleaguebot.scoring import setup

		return setup.score_speed_setup(self, attacker, target)

	def _score_shell_smash(self, battle, attacker, target):
		from draftleaguebot.scoring import setup

		return setup.score_shell_smash(self, battle, attacker, target)

	def _score_belly_drum(self, battle, attacker, target):
		from draftleaguebot.scoring import setup

		return setup.score_belly_drum(self, battle, attacker, target)

	def _score_mixed_setup(self, attacker, target, move):
		from draftleaguebot.scoring import setup

		return setup.score_mixed_setup(self, attacker, target, move)

	def _setup_synergy_bonus(self, attacker, move):
		from draftleaguebot.scoring import setup

		return setup.setup_synergy_bonus(attacker, move)

	def _is_setup_move(self, move):
		from draftleaguebot.scoring import setup

		return setup.is_setup_move(move)

	def _setup_move_ids(self):
		from draftleaguebot.scoring import setup

		return setup.setup_move_ids()

	def _is_special_setup(self, move):
		from draftleaguebot.scoring import setup

		return setup.is_special_setup(move)

	def _is_defensive_setup(self, move):
		from draftleaguebot.scoring import setup

		return setup.is_defensive_setup(move)

	def _is_mixed_setup(self, move):
		from draftleaguebot.scoring import setup

		return setup.is_mixed_setup(move)

	def _is_speed_setup(self, move):
		from draftleaguebot.scoring import setup

		return setup.is_speed_setup(move)

	def _threatened_by_ko(self, battle, attacker, target):
		from draftleaguebot.scoring import setup

		return setup.threatened_by_ko(self, battle, attacker, target)

	def _is_two_hko_threat(self, attacker, target):
		from draftleaguebot.scoring import setup

		return setup.is_two_hko_threat(self, attacker, target)

	def _is_three_hko_threat(self, attacker, target):
		from draftleaguebot.scoring import setup

		return setup.is_three_hko_threat(self, attacker, target)

	def _estimate_max_damage_ratio(self, attacker, target):
		from draftleaguebot.scoring import setup

		return setup.estimate_max_damage_ratio(self, attacker, target)

	def _can_be_ko_after_setup(self, battle, attacker, target, hp_multiplier=1.0):
		from draftleaguebot.scoring import setup

		return setup.can_be_ko_after_setup(self, battle, attacker, target, hp_multiplier=hp_multiplier)

	def _get_boost(self, pokemon, stat):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.get_boost(pokemon, stat)

	def _is_incapacitated(self, target):
		if target is None:
			return False
		if getattr(target, "status", None) in {Status.SLP, Status.FRZ}:
			return True
		return bool(getattr(target, "must_recharge", False))

	def _target_has_unaware(self, target):
		return getattr(target, "ability", None) == "unaware"

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
   # why is this checking the last move (previous turn??) instead of the current move?
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

	def _has_special_move(self, pokemon):
		moves = getattr(pokemon, "moves", {})
		for move in moves.values():
			category = getattr(move, "category", None)
			if category is not None and category.name.lower() == "special":
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
		from draftleaguebot.mechanics import targets

		return targets.get_partner(battle, attacker)

	def _apply_doubles_damage_bonuses(self, battle, attacker, move, target):
		move_id = getattr(move, "id", None)
		if move_id is None:
			return 0
		bonus = 0

		if move_id in {"shadowsneak", "aquajet", "iceshard", "vacuumwave", "bulletpunch", "machpunch", "watershuriken"}:
			bonus += self._weakness_policy_partner_bonus(battle, attacker, move, target)

		if move_id == "fling":
			bonus += self._fling_speed_bonus(battle, attacker, move, target)

		if move_id in {"earthquake", "magnitude", "bulldoze"}:
			bonus += self._earthquake_partner_bonus(battle)

		return bonus

	def _is_offense_drop_damage_move(self, move):
		move_id = getattr(move, "id", None)
		return move_id in {
			"tropkick",
			"skittersmack",
			"lunge",
			"mysticalfire",
			"strugglebug",
			"breakingswipe",
			"chillingwater",
			"snarl",
			"spiritbreak",
		}

	def _score_offense_drop_damage(self, battle, attacker, move, target, highest_damage):
		if highest_damage:
			return 0
		if target is None:
			return 5
		if self._is_immune_to_speed_drop(target):
			return 5
		if self._target_has_corresponding_attack(move, target):
			base = 6
		else:
			base = 5
		if self._is_spread_move(move):
			base += 1
		return base

	def _is_spdef_drop_damage_move(self, move):
		return getattr(move, "id", None) == "acidspray"

	def _target_has_corresponding_attack(self, move, target):
		if target is None:
			return False
		move_id = getattr(move, "id", None)
		if move_id in {"tropkick", "lunge", "breakingswipe", "chillingwater"}:
			return self._has_physical_move(target)
		if move_id in {"skittersmack", "mysticalfire", "strugglebug", "snarl", "spiritbreak"}:
			return self._has_special_move(target)
		return False

	def _is_speed_control_damage_move(self, move):
		move_id = getattr(move, "id", None)
		return move_id in {"icywind", "electroweb", "rocktomb", "mudshot", "lowsweep", "bulldoze"}

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
		from draftleaguebot.mechanics import targets
		return targets.candidate_targets(
			battle,
			attacker,
			move,
			opponents,
			setup_move_ids=self._setup_move_ids(),
		)

	def _move_allows_foe(self, move_target):
		from draftleaguebot.mechanics import targets
		return targets.move_allows_foe(move_target)

	def _move_allows_ally(self, move_target, move):
		from draftleaguebot.mechanics import targets

		return targets.move_allows_ally(move_target, move)

	def _ally_target_allowed(self, move):
		from draftleaguebot.mechanics import targets
		return targets.ally_target_allowed(move)

	def _move_targets_self_or_side(self, move_target, move):
		from draftleaguebot.mechanics import targets

		return targets.move_targets_self_or_side(
			move_target,
			move,
			setup_move_ids=self._setup_move_ids(),
		)

	def _is_partner(self, battle, attacker, target):
		from draftleaguebot.mechanics import targets

		return targets.is_partner(battle, attacker, target)

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

	def _is_immune_to_move(self, battle, move, target):
		from draftleaguebot.mechanics import effects

		return effects.is_immune_to_move(battle, move, target)

	def _has_any_type(self, pokemon, types):
		from draftleaguebot.mechanics import effects

		return effects.has_any_type(pokemon, types)

	def _is_damaging(self, move):
		from draftleaguebot.mechanics import effects

		return effects.is_damaging(move)

	def _estimate_damage(self, battle, attacker, move, target, use_max_roll=False):
		from draftleaguebot.mechanics import damage_calc

		return damage_calc.estimate_damage(
			battle,
			attacker,
			move,
			target,
			use_max_roll=use_max_roll,
			debug=self._should_debug(battle),
		)

	def _resolve_identifier_side(self, battle, pokemon):
		from draftleaguebot.mechanics import damage_calc

		return damage_calc.resolve_identifier_side(battle, pokemon)

	def _hydrate_damage_stats(self, pokemon):
		from draftleaguebot.mechanics import damage_calc

		return damage_calc.hydrate_damage_stats(pokemon)

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
		from draftleaguebot.mechanics import damage_calc

		return damage_calc.estimated_kill(target, damage)

	def _is_faster(self, attacker, defender):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.is_faster(attacker, defender)

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

	def _speed_profile(self, battle):
		allies = [p for p in battle.active_pokemon if p is not None]
		opponents = [p for p in battle.opponent_active_pokemon if p is not None]
		if not allies or not opponents:
			return None
		ally_speeds_raw = [self._safe_speed(p) for p in allies]
		foe_speeds_raw = [self._safe_speed(p) for p in opponents]
		ally_speeds = [s for s in ally_speeds_raw if s > 0]
		foe_speeds = [s for s in foe_speeds_raw if s > 0]
		if self._should_debug(battle):
			turn = getattr(battle, "turn", "?")
			ally_names = [getattr(p, "name", "?") for p in allies]
			foe_names = [getattr(p, "name", "?") for p in opponents]
			print(
				"[AI DEBUG] "
				f"turn={turn} speed_raw allies={list(zip(ally_names, ally_speeds_raw))} "
				f"foes={list(zip(foe_names, foe_speeds_raw))}"
			)
			print(
				"[AI DEBUG] "
				f"turn={turn} speed_filtered allies={ally_speeds} foes={foe_speeds}"
			)
		if not ally_speeds or not foe_speeds:
			return None
		return min(ally_speeds), max(ally_speeds), min(foe_speeds), max(foe_speeds)

	def _ally_side_condition_active(self, battle, condition):
		from draftleaguebot.mechanics import effects

		return effects.ally_side_condition_active(battle, condition)

	def _score_tailwind(self, battle):
		if self._ally_side_condition_active(battle, SideCondition.TAILWIND):
			return -20
		if self._is_trick_room_active(battle):
			return -8
		score = 6
		profile = self._speed_profile(battle)
		if self._should_debug(battle):
			turn = getattr(battle, "turn", "?")
			print(f"[AI DEBUG] turn={turn} move=tailwind speed_profile={profile}")
		if self._side_condition_active(battle, SideCondition.TAILWIND):
			score += 5
		if profile is None:
			return score
		min_ally, max_ally, min_foe, max_foe = profile
		if max_ally < max_foe:
			score += 3
		if max_ally < min_foe:
			score += 2
		if max_ally > max_foe:
			score -= 2
		return score

	def _score_trick_room(self, battle):
		if self._is_trick_room_active(battle):
			return -20
		score = 6
		if self._ally_side_condition_active(battle, SideCondition.TAILWIND):
			score -= 4
		if self._side_condition_active(battle, SideCondition.TAILWIND):
			score += 3
		profile = self._speed_profile(battle)
		if self._should_debug(battle):
			turn = getattr(battle, "turn", "?")
			print(f"[AI DEBUG] turn={turn} move=trickroom speed_profile={profile}")
		if profile is None:
			return score
		min_ally, max_ally, min_foe, max_foe = profile
		if max_ally < max_foe:
			score += 4
		if max_ally < min_foe:
			score += 2
		if max_ally > max_foe:
			score -= 5
		return score

	def _is_trick_room_active(self, battle):
		from draftleaguebot.mechanics import effects

		return effects.is_trick_room_active(battle)

	def _safe_speed(self, pokemon):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.safe_speed(pokemon)

	def _is_high_crit(self, move):
		from draftleaguebot.mechanics import effects

		return effects.is_high_crit(move)

	def _is_super_effective(self, battle, move, target):
		from draftleaguebot.mechanics import effects

		return effects.is_super_effective(battle, move, target)

	def _is_not_very_effective(self, battle, move, target):
		from draftleaguebot.mechanics import effects

		return effects.is_not_very_effective(battle, move, target)

	def _resisted_penalty(self, battle, move, target, scale=10):
		from draftleaguebot.mechanics import effects

		return effects.resisted_penalty(battle, move, target, scale=scale)

	def _is_super_effective_on_target(self, move, target):
		from draftleaguebot.mechanics import effects

		return effects.is_super_effective_on_target(move, target)

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

	def _is_threatened_by_any_faster_opponent(self, battle, attacker):
		opponents = [p for p in battle.opponent_active_pokemon if p is not None]
		for opponent in opponents:
			if not self._is_faster(opponent, attacker):
				continue
			if self._is_threatened_by(battle, opponent, attacker):
				return True
		return False

	def _get_active_slots(self, battle):
		from draftleaguebot import orders

		return orders.get_active_slots(battle)

	def _fallback_order_for_slot(self, battle, slot_index):
		from draftleaguebot import orders

		return orders.fallback_order_for_slot(self.create_order, battle, slot_index)

	def _get_offense_defense_stats(self, attacker, target, move):
		from draftleaguebot.mechanics import damage_calc

		return damage_calc.get_offense_defense_stats(attacker, target, move)

	def _stat(self, pokemon, key):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.stat(pokemon, key)

	def _has_stab(self, attacker, move):
		from draftleaguebot.mechanics import effects

		return effects.has_stab(attacker, move)

	def _damage_roll_factor(self):
		from draftleaguebot.mechanics import damage_calc

		return damage_calc.damage_roll_factor()

	def _get_target_current_hp(self, target):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.get_target_current_hp(target)

	def _get_target_max_hp(self, target):
		from draftleaguebot.mechanics import pokemon_state

		return pokemon_state.get_target_max_hp(target)

	def _rng_weight(self, low, high, low_prob):
		return low if random.random() < low_prob else high

