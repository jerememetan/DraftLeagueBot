# Bot Logic Refactor Design

## Goal

Refactor `bot_logic.py` into a navigable Python package where every project-owned Python file stays under 300 lines, while preserving the bot's current battle behavior.

## Non-Goals

- Do not change the AI scoring rules during the first refactor.
- Do not change the CLI flow in `test_bot.py`.
- Do not rename `DoublesMvpBot` or break `from bot_logic import DoublesMvpBot`.
- Do not introduce a new dependency or framework.

## Current State

`bot_logic.py` is about 1,950 lines and contains every major responsibility for the battle bot:

- `DoublesMvpBot` construction and `choose_move` orchestration.
- Double battle order construction.
- Candidate target selection and move target position mapping.
- Damage estimation through `poke_env.calc.calculate_damage` plus fallback math.
- Damaging move scoring.
- Status, support, setup, recovery, hazard, and screen scoring.
- Doubles-specific partner interactions such as Weakness Policy, Fling, and Earthquake.
- Battle-state helpers for HP, speed, boosts, alive counts, weather, fields, side conditions, immunities, and move categories.
- Debug gates and debug print formatting.

The main problem is not only file length. The class acts as a broad namespace, so helpers that only need battle facts or move facts still depend on `self`. That makes future changes harder to locate, test, and debug.

## Design Principles

- Preserve behavior first. The first pass is a mechanical extraction with compatibility wrappers.
- Split by reason to change, not by arbitrary line count.
- Keep files small enough to read in one screen session. Enforce the 300-line limit with a test.
- Keep the public import stable through a root-level `bot_logic.py` shim.
- Make debugging easier by keeping decision logging explicit and centralized.
- Prefer plain functions for stateless mechanics; use small classes only where state or injected collaborators make the code clearer.

## Target Structure

```text
draftleaguebot/
  __init__.py
  bot.py
  debug.py
  orders.py
  scoring/
    __init__.py
    move_scorer.py
    damage.py
    status.py
    doubles.py
    setup.py
    speed_control.py
  mechanics/
    __init__.py
    damage_calc.py
    targets.py
    pokemon_state.py
    effects.py
bot_logic.py
tests/
  test_import_contract.py
  test_file_size_limits.py
```

## File Responsibilities

`bot_logic.py`

- Compatibility shim only.
- Re-export `DoublesMvpBot` from `draftleaguebot.bot`.
- Stay under 20 lines.

`draftleaguebot/bot.py`

- Define `DoublesMvpBot`.
- Own `choose_move`, `_should_z_move`, and `_should_terastallize`.
- Delegate scoring, targets, orders, and debug formatting to focused modules.

`draftleaguebot/orders.py`

- Build active slot tuples from `battle.available_moves` and `battle.active_pokemon`.
- Build fallback switch orders.
- Convert selected target objects into `DoubleBattle` target positions.
- Keep all `DoubleBattleOrder`, `PassBattleOrder`, and `DoubleBattle.*_POSITION` logic here.

`draftleaguebot/debug.py`

- Decide whether debug output should be printed for the current turn.
- Format candidate ranking logs.
- Format final order logs.
- Keep debug output behavior equivalent to today.

`draftleaguebot/scoring/move_scorer.py`

- Provide the top-level `score_move` dispatcher.
- Route damaging moves to `scoring.damage`.
- Route status/support moves to `scoring.status`.
- Avoid holding detailed rule logic directly.

`draftleaguebot/scoring/damage.py`

- Score damaging moves.
- Include damage-specific bonuses such as highest damage, KO scoring, crit and super-effective bonuses, priority threat scoring, and move-specific damage rules.

`draftleaguebot/scoring/status.py`

- Score non-damaging moves.
- Include paralysis, burn, sleep, poison, recovery, hazards, screens, Taunt, Encore, Protect, Final Gambit, Memento, Destiny Bond, and support move routing.

`draftleaguebot/scoring/doubles.py`

- Score doubles-only partner interactions.
- Include Weakness Policy partner triggers, Fling speed bonus, Earthquake and Bulldoze partner checks, Helping Hand and Follow Me partner gating, Coaching, and spread-move bonuses.

`draftleaguebot/scoring/setup.py`

- Score setup moves and setup-related synergy.
- Include Contrary setup attacks, Shell Smash, Belly Drum, Stored Power, Power Trip, Body Press, Baton Pass, and boost helpers if they are not more naturally shared.

`draftleaguebot/scoring/speed_control.py`

- Score Tailwind, Trick Room, and damaging speed-control moves.
- Own speed-profile calculations that are specific to speed-control decisions.

`draftleaguebot/mechanics/damage_calc.py`

- Estimate damage using `poke_env.calc.calculate_damage`.
- Hydrate damage stats for incomplete poke-env Pokemon objects.
- Provide fallback damage math when poke-env cannot calculate.

`draftleaguebot/mechanics/targets.py`

- Determine candidate targets for a move.
- Decide whether a move allows foe, ally, self, side, or setup targets.
- Identify ally partner relationships.

`draftleaguebot/mechanics/pokemon_state.py`

- Read HP, max HP, boosts, stats, speed, alive counts, and team state safely from poke-env objects.
- Keep defensive `getattr` compatibility helpers here.

`draftleaguebot/mechanics/effects.py`

- Read battle effects, side conditions, weather, screens, hazards, status immunity, type effectiveness, and move category facts.
- Keep low-level battle fact checks separate from scoring policy.

## Public Interface

The following imports must continue to work:

```python
from bot_logic import DoublesMvpBot
from draftleaguebot import DoublesMvpBot
from draftleaguebot.bot import DoublesMvpBot
```

`test_bot.py` may keep its current import. Updating it to `draftleaguebot` is optional after the compatibility tests pass.

## Debugging Design

The refactor must preserve the current `--debug` behavior:

- Per-turn candidate logs still show the top scored move-target candidates.
- Damage calculation debug output still appears when enabled.
- Final orders are still printed before returning the order.

After extraction, debugging should become easier because:

- Decision flow starts in `bot.py`.
- Score composition starts in `scoring/move_scorer.py`.
- Damage math lives in `mechanics/damage_calc.py`.
- Targeting questions live in `mechanics/targets.py` and `orders.py`.

## File Size Rule

Every project-owned Python file must stay under 300 physical lines.

Included:

- Root Python files such as `bot_logic.py`, `test_bot.py`, and `inspect_doublebattle.py`.
- Python files under `draftleaguebot/`.
- Python files under `tests/`.

Excluded:

- `.venv/`
- `.git/`
- `__pycache__/`
- `.pytest_cache/`

The limit is enforced with `tests/test_file_size_limits.py`.

## Testing Strategy

Add tests before moving behavior:

- Import contract test: verifies old and new imports resolve to the same class.
- File-size test: fails while `bot_logic.py` is still too large, passes after extraction.
- Lightweight behavioral smoke tests around public helpers where existing tests already cover behavior.

Then run the existing test suite after each extraction slice:

```powershell
.venv/Scripts/python.exe -m pytest
```

If the virtualenv is unavailable, use:

```powershell
python -m pytest
```

## Migration Strategy

1. Create package skeleton and import contract tests.
2. Add file-size enforcement test.
3. Extract debug helpers.
4. Extract order and target helpers.
5. Extract low-level Pokemon and battle-state mechanics.
6. Extract damage calculation mechanics.
7. Extract damaging move scoring.
8. Extract status and setup scoring.
9. Extract doubles and speed-control scoring.
10. Replace root `bot_logic.py` with a compatibility shim.
11. Run full tests and line-limit verification.

Each extraction should move one coherent responsibility and keep behavior green before the next move.

## Risks

- Method calls currently depend heavily on `self`, so extraction can accidentally change binding or access to `create_order`.
- Random scoring makes snapshot-style tests brittle.
- poke-env battle objects may expose attributes inconsistently, so defensive helper behavior must be preserved.
- A pure mechanical split can leave some awkward cross-module calls. Accept this in the first pass if behavior stays stable; clean architecture can follow once the code is navigable.

## Acceptance Criteria

- `bot_logic.py` is a compatibility shim under 300 lines.
- No project-owned Python file exceeds 300 lines.
- `from bot_logic import DoublesMvpBot` still works.
- `test_bot.py --preflight` behavior is unchanged.
- Existing tests pass.
- New import contract and file-size tests pass.
- Debug output remains available through `--debug`.
