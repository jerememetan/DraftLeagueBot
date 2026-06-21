import random

from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target


class StatusHelpersMixin:
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
		if self._has_type_name(target, "electric"):
			return -20
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


	def _has_type_name(self, pokemon, type_name):
		target_name = type_name.lower()
		for pokemon_type in getattr(pokemon, "types", []) or []:
			value = getattr(pokemon_type, "name", None) or getattr(pokemon_type, "value", None) or pokemon_type
			if str(value).lower() == target_name:
				return True
		return False


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
