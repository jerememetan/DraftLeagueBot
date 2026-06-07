import random

from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target


class SetupWrappersMixin:
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
