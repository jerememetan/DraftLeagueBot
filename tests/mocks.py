"""
Shared mock classes for all tests.

Provides unified mock implementations for:
- MoveCategory enum
- DummyMove
- DummyPokemon
- DummyBattle
"""

from enum import Enum
from types import SimpleNamespace


class MoveCategory(Enum):
    """MoveCategory enum matching poke-env structure."""
    PHYSICAL = "physical"
    SPECIAL = "special"
    STATUS = "status"


class DummyMove:
    """Move mock with poke-env compatibility.
    
    Attributes:
        base_power: Base power of the move (0 for status moves)
        category: MoveCategory enum value
        type: PokemonType of the move
        id: Move identifier string
    """
    def __init__(self, base_power=80, category="physical", move_type="Normal", move_id="tackle"):
        self.base_power = base_power
        # Handle both string and enum category
        if isinstance(category, str):
            self.category = MoveCategory[category.upper()]
        else:
            self.category = category
        self.type = move_type
        self.id = move_id


class DummyPokemon:
    """Pokemon mock with poke-env compatibility.
    
    Attributes:
        name: Pokemon name
        current_hp: Current HP (for poke-env compatibility)
        max_hp: Maximum HP
        level: Pokemon level
        stats: Dict with keys: hp, atk, def, spa, spd, spe
        types: List of type strings
        ability: Pokemon ability name
        item: Held item name
        boosts: Dict of stat boosts
        status: Status condition if any
        moves: Dict of move_id -> move objects
    """
    def __init__(self, name="Pikachu", hp=100, level=50, max_hp=None,
                 stats=None, types=None, ability=None, item=None, current_hp=None):
        self.name = name
        # Accept both hp and current_hp parameters
        hp_value = current_hp if current_hp is not None else hp
        self.current_hp = hp_value
        self.current_hp_fraction = hp_value / max_hp if (max_hp and hp_value > 1) else hp_value
        self.max_hp = max_hp if max_hp is not None else hp
        self.level = level
        self.stats = stats or {
            "hp": 100, "atk": 100, "def": 100,
            "spa": 100, "spd": 100, "spe": 100
        }
        self.types = types or ["Normal"]
        self.ability = ability
        self.item = item
        self.boosts = {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
        self.status = None
        self.moves = {}
        self.effects = {}
        self.fainted = False


class DummyBattle:
    """Battle mock for testing.
    
    Supports both SimpleNamespace (test_bot_logic_regression) and plain class approaches.
    """
    def __init__(self, active_pokemon=None, opponent_active_pokemon=None, **kwargs):
        # Doubles format: list of 2 Pokemon
        self.active_pokemon = active_pokemon if active_pokemon is not None else [None, None]
        self.opponent_active_pokemon = opponent_active_pokemon if opponent_active_pokemon is not None else [None, None]
        
        # Side conditions and field effects
        self.side_conditions = kwargs.get('side_conditions', {})
        self.player_side_conditions = kwargs.get('player_side_conditions', {})
        self.opponent_side_conditions = kwargs.get('opponent_side_conditions', {})
        
        # Weather and terrain
        self.weather = kwargs.get('weather', None)
        self.trick_room = kwargs.get('trick_room', False)
        
        # Team references
        self.player_team = kwargs.get('player_team', {})
        self.opponent_team = kwargs.get('opponent_team', {})
    
    def damage_multiplier(self, move, target):
        """Simulate damage multiplier for type effectiveness.
        
        Checks target for damage_multiplier_value attribute.
        """
        return getattr(target, 'damage_multiplier_value', 1.0)
