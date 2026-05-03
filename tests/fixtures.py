"""
Shared test fixtures and factory functions.

Provides:
- make_pokemon(): Factory for creating test Pokemon with specified attributes
- make_move(): Factory for creating test moves
"""

from mocks import DummyPokemon, DummyMove, MoveCategory


def make_pokemon(name="Pikachu", hp=100, level=50, max_hp=None, stats=None,
                 types=None, ability=None, item=None, **extra):
    """Factory for creating test Pokemon with defaults.
    
    Args:
        name: Pokemon name
        hp: Current HP
        level: Level (default 50)
        max_hp: Maximum HP (defaults to hp)
        stats: Dict with hp/atk/def/spa/spd/spe keys
        types: List of type strings
        ability: Ability name
        item: Item name
        **extra: Additional attributes (e.g., damage_multiplier_value)
    
    Returns:
        DummyPokemon with specified configuration
    """
    pokemon = DummyPokemon(
        name=name,
        hp=hp,
        level=level,
        max_hp=max_hp or hp,
        stats=stats,
        types=types,
        ability=ability,
        item=item
    )
    # Apply any extra attributes
    for key, value in extra.items():
        setattr(pokemon, key, value)
    return pokemon


def make_move(move_id="tackle", base_power=80, category="physical",
              move_type="Normal", **extra):
    """Factory for creating test moves with defaults.
    
    Args:
        move_id: Move identifier
        base_power: Base power (0 for status moves)
        category: "physical", "special", or "status"
        move_type: Type string
        **extra: Additional attributes
    
    Returns:
        DummyMove with specified configuration
    """
    move = DummyMove(
        move_id=move_id,
        base_power=base_power,
        category=category,
        move_type=move_type
    )
    # Apply any extra attributes
    for key, value in extra.items():
        setattr(move, key, value)
    return move
