import random

from poke_env.battle.effect import Effect
from poke_env.battle.status import Status
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.target import Target


class StateOrderMixin:
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
