import random

from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target


class MechanicsWrappersMixin:
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
		from draftleaguebot.scoring import speed_control

		return speed_control.team_is_slower(self, battle)


	def _speed_profile(self, battle):
		from draftleaguebot.scoring import speed_control

		return speed_control.speed_profile(self, battle)


	def _ally_side_condition_active(self, battle, condition):
		from draftleaguebot.mechanics import effects

		return effects.ally_side_condition_active(battle, condition)


	def _score_tailwind(self, battle):
		from draftleaguebot.scoring import speed_control

		return speed_control.score_tailwind(self, battle)


	def _score_trick_room(self, battle):
		from draftleaguebot.scoring import speed_control

		return speed_control.score_trick_room(self, battle)


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
