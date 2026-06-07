import random

from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target


class MoveHelpersMixin:
	def _partner_using_support_or_status(self, battle, attacker):
		from draftleaguebot.scoring import doubles

		return doubles.partner_using_support_or_status(self, battle, attacker)


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
		from draftleaguebot.scoring import doubles

		return doubles.partner_has_hex(self, battle, attacker)


	def _get_partner(self, battle, attacker):
		from draftleaguebot.mechanics import targets

		return targets.get_partner(battle, attacker)


	def _apply_doubles_damage_bonuses(self, battle, attacker, move, target):
		from draftleaguebot.scoring import doubles

		return doubles.apply_doubles_damage_bonuses(self, battle, attacker, move, target)


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
		from draftleaguebot.scoring import speed_control

		return speed_control.is_speed_control_damage_move(move)


	def _score_speed_control_damage(self, battle, attacker, move, target, highest_damage):
		from draftleaguebot.scoring import speed_control

		return speed_control.score_speed_control_damage(
			self, battle, attacker, move, target, highest_damage
		)


	def _is_immune_to_speed_drop(self, target):
		from draftleaguebot.scoring import speed_control

		return speed_control.is_immune_to_speed_drop(target)


	def _is_spread_move(self, move):
		move_target = getattr(move, "deduced_target", None) or getattr(move, "target", None)
		return move_target in {Target.ALL_ADJACENT_FOES, Target.ALL_ADJACENT, Target.ALL}


	def _weakness_policy_partner_bonus(self, battle, attacker, move, target):
		from draftleaguebot.scoring import doubles

		return doubles.weakness_policy_partner_bonus(self, battle, attacker, move, target)


	def _fling_speed_bonus(self, battle, attacker, move, target):
		from draftleaguebot.scoring import doubles

		return doubles.fling_speed_bonus(self, battle, attacker, move, target)


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
		from draftleaguebot.scoring import doubles

		return doubles.earthquake_partner_bonus(self, battle)


	def _is_immune_to_ground(self, pokemon):
		from draftleaguebot.scoring import doubles

		return doubles.is_immune_to_ground(pokemon)
