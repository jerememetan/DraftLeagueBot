# Bot Logic Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the 1,950-line `bot_logic.py` into a maintainable package where every project-owned Python file is under 300 lines and current bot behavior is preserved.

**Architecture:** Keep `DoublesMvpBot` as the public bot class, but move helper responsibilities into focused modules under `draftleaguebot/`. Keep root `bot_logic.py` as a compatibility shim so the existing CLI import remains stable.

**Tech Stack:** Python 3.12, poke-env, pytest, PowerShell on Windows.

---

## File Structure

- Create: `draftleaguebot/__init__.py` for package exports.
- Create: `draftleaguebot/bot.py` for `DoublesMvpBot` and `choose_move`.
- Create: `draftleaguebot/debug.py` for debug gates and log formatting.
- Create: `draftleaguebot/orders.py` for battle slot and order construction.
- Create: `draftleaguebot/scoring/__init__.py` for scoring package exports.
- Create: `draftleaguebot/scoring/move_scorer.py` for score dispatch.
- Create: `draftleaguebot/scoring/damage.py` for damaging move scoring.
- Create: `draftleaguebot/scoring/status.py` for status/support scoring.
- Create: `draftleaguebot/scoring/doubles.py` for doubles partner scoring.
- Create: `draftleaguebot/scoring/setup.py` for setup and boost scoring.
- Create: `draftleaguebot/scoring/speed_control.py` for Tailwind, Trick Room, and speed-control scoring.
- Create: `draftleaguebot/mechanics/__init__.py` for mechanics package exports.
- Create: `draftleaguebot/mechanics/damage_calc.py` for damage estimation.
- Create: `draftleaguebot/mechanics/targets.py` for candidate targets and partner checks.
- Create: `draftleaguebot/mechanics/pokemon_state.py` for HP, speed, stats, boosts, and alive counts.
- Create: `draftleaguebot/mechanics/effects.py` for weather, side conditions, type effectiveness, immunities, and move facts.
- Modify: `bot_logic.py` into a compatibility shim.
- Add: `tests/test_import_contract.py`.
- Add: `tests/test_file_size_limits.py`.

## Task 1: Add Import Contract Tests

**Files:**

- Create: `tests/test_import_contract.py`

- [x] **Step 1: Write the failing import contract test**

```python
def test_legacy_bot_logic_import_matches_package_export():
    from bot_logic import DoublesMvpBot as LegacyBot
    from draftleaguebot import DoublesMvpBot as PackageBot
    from draftleaguebot.bot import DoublesMvpBot as ModuleBot

    assert LegacyBot is PackageBot
    assert PackageBot is ModuleBot
```

- [x] **Step 2: Run the test to verify it fails before the package exists**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_import_contract.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'draftleaguebot'`.

- [x] **Step 3: Create the package skeleton**

Create `draftleaguebot/__init__.py`:

```python
from draftleaguebot.bot import DoublesMvpBot

__all__ = ["DoublesMvpBot"]
```

Create `draftleaguebot/bot.py` with a temporary re-export:

```python
from bot_logic import DoublesMvpBot

__all__ = ["DoublesMvpBot"]
```

- [x] **Step 4: Run the import contract test**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_import_contract.py -v
```

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add draftleaguebot tests/test_import_contract.py
git commit -m "test: add bot import contract"
```

## Task 2: Add File Size Limit Test

**Files:**

- Create: `tests/test_file_size_limits.py`

- [x] **Step 1: Write the failing file-size test**

```python
from pathlib import Path


MAX_PYTHON_FILE_LINES = 300
EXCLUDED_PARTS = {".git", ".pytest_cache", ".venv", "__pycache__"}


def project_python_files():
    root = Path(__file__).resolve().parents[1]
    for path in root.rglob("*.py"):
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        yield path


def test_project_python_files_stay_under_300_lines():
    oversized = []
    for path in project_python_files():
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_PYTHON_FILE_LINES:
            oversized.append(f"{path.relative_to(path.parents[1])}: {line_count}")

    assert oversized == []
```

- [x] **Step 2: Run the test to verify it catches `bot_logic.py`**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_file_size_limits.py -v
```

Expected: FAIL and list `bot_logic.py` as oversized.

- [x] **Step 3: Commit the guardrail test**

```powershell
git add tests/test_file_size_limits.py
git commit -m "test: enforce python file size limit"
```

## Task 3: Move Debug Helpers

**Files:**

- Create: `draftleaguebot/debug.py`
- Modify: `bot_logic.py`

- [x] **Step 1: Create debug helper functions**

Create `draftleaguebot/debug.py`:

```python
def should_debug(enabled, debug_turns, battle):
    if not enabled:
        return False
    turn = getattr(battle, "turn", None)
    if turn is None:
        return True
    return turn <= debug_turns


def log_decision(battle, slot_index, attacker, scored):
    turn = getattr(battle, "turn", "?")
    attacker_name = getattr(attacker, "name", "?")
    sorted_scored = sorted(scored, key=lambda item: item[0], reverse=True)
    top_moves = sorted_scored[:3]
    top_str = " | ".join(
        f"{getattr(move, 'id', '?')}->{getattr(target, 'name', '?')} ({score:.2f})"
        for score, move, target in top_moves
    )
    print(
        f"[AI DEBUG] turn={turn} slot={slot_index} attacker={attacker_name} "
        f"top_candidates=[{top_str}]"
    )


def log_final_orders(orders):
    messages = [order.message for order in orders]
    print(f"[AI DEBUG] final_orders={messages}")
```

- [x] **Step 2: Update `bot_logic.py` debug methods to delegate**

Replace `_should_debug`, `_log_decision`, and `_log_final_orders` bodies with:

```python
from draftleaguebot import debug as debug_helpers


def _should_debug(self, battle):
    return debug_helpers.should_debug(self._debug, self._debug_turns, battle)


def _log_decision(self, battle, slot_index, attacker, scored, best_move, best_target):
    debug_helpers.log_decision(battle, slot_index, attacker, scored)


def _log_final_orders(self, orders):
    debug_helpers.log_final_orders(orders)
```

- [x] **Step 3: Run focused tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_import_contract.py -v
```

Expected: PASS.

- [x] **Step 4: Commit**

```powershell
git add bot_logic.py draftleaguebot/debug.py
git commit -m "refactor: extract bot debug helpers"
```

## Task 4: Move Order Helpers

**Files:**

- Create: `draftleaguebot/orders.py`
- Modify: `bot_logic.py`

- [x] **Step 1: Move order and slot helpers into `orders.py`**

Create functions equivalent to these current methods:

```python
get_active_slots(battle)
fallback_order_for_slot(create_order, battle, slot_index)
move_target_position(battle, attacker, move, target)
opponent_position(battle, target)
ally_positions(battle, attacker)
```

Keep all `DoubleBattle` and `Target` imports inside `draftleaguebot/orders.py`.

- [x] **Step 2: Replace methods in `bot_logic.py` with wrappers**

```python
from draftleaguebot import orders


def _get_active_slots(self, battle):
    return orders.get_active_slots(battle)


def _fallback_order_for_slot(self, battle, slot_index):
    return orders.fallback_order_for_slot(self.create_order, battle, slot_index)


def _move_target_position(self, battle, attacker, move, target):
    return orders.move_target_position(
        battle,
        attacker,
        move,
        target,
        ally_target_allowed=self._ally_target_allowed,
        is_partner=self._is_partner,
    )
```

- [x] **Step 3: Run existing tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest
```

Expected: PASS except `tests/test_file_size_limits.py`, which is allowed to fail until the final shim task.

- [x] **Step 4: Commit**

```powershell
git add bot_logic.py draftleaguebot/orders.py
git commit -m "refactor: extract double battle order helpers"
```

## Task 5: Move Target Mechanics

**Files:**

- Create: `draftleaguebot/mechanics/__init__.py`
- Create: `draftleaguebot/mechanics/targets.py`
- Modify: `bot_logic.py`

- [x] **Step 1: Move target helper functions**

Move these methods to `draftleaguebot/mechanics/targets.py` as plain functions:

```python
candidate_targets(battle, attacker, move, opponents)
move_allows_foe(move_target)
move_allows_ally(move_target, move)
ally_target_allowed(move)
move_targets_self_or_side(move_target, move)
is_partner(battle, attacker, target)
get_partner(battle, attacker)
```

Pass `setup_move_ids` into `move_targets_self_or_side` if the function needs the setup move set.

- [] **Step 2: Add wrapper methods in `bot_logic.py`**

Keep method names stable and delegate to `targets.py`:

```python
from draftleaguebot.mechanics import targets


def _candidate_targets(self, battle, attacker, move, opponents):
    return targets.candidate_targets(
        battle,
        attacker,
        move,
        opponents,
        setup_move_ids=self._setup_move_ids(),
    )
```

- [x] **Step 3: Run tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest
```

Expected: PASS except the known file-size failure.

- [x] **Step 4: Commit**

```powershell
git add bot_logic.py draftleaguebot/mechanics
git commit -m "refactor: extract targeting mechanics"
```

## Task 6: Move Pokemon State Helpers

**Files:**

- Create: `draftleaguebot/mechanics/pokemon_state.py`
- Modify: `bot_logic.py`

- [x] **Step 1: Move state helper functions**

Move HP, speed, boost, stat, and alive-count helpers to `pokemon_state.py`:

```python
get_target_current_hp(target)
get_target_max_hp(target)
safe_speed(pokemon)
is_faster(attacker, defender)
stat(pokemon, key)
get_boost(pokemon, stat_name)
has_positive_boost(pokemon)
active_list(active)
count_alive(team)
alive_counts(battle)
is_last_mon(battle)
both_last_mon(battle)
opponent_has_multiple_alive(battle)
```

- [x] **Step 2: Keep wrappers in `bot_logic.py`**

Each original method should delegate to `pokemon_state.py` so existing scoring methods keep working during the incremental extraction.

- [x] **Step 3: Run tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest
```

Expected: PASS except the known file-size failure.

- [x] **Step 4: Commit**

```powershell
git add bot_logic.py draftleaguebot/mechanics/pokemon_state.py
git commit -m "refactor: extract pokemon state helpers"
```

## Task 7: Move Effect and Move Fact Helpers

**Files:**

- Create: `draftleaguebot/mechanics/effects.py`
- Modify: `bot_logic.py`

- [x] **Step 1: Move battle effect helpers**

Move weather, condition, type, immunity, and move category helpers to `effects.py`, including:

```python
is_damaging(move)
has_stab(attacker, move)
is_high_crit(move)
is_super_effective(battle, move, target)
is_not_very_effective(battle, move, target)
is_super_effective_on_target(move, target)
resisted_penalty(battle, move, target, scale=10)
is_immune_to_move(battle, move, target)
has_any_type(pokemon, types)
is_sun_active(battle)
is_rain_active(battle)
side_condition_active(battle, condition)
ally_side_condition_active(battle, condition)
is_trick_room_active(battle)
```

- [x] **Step 2: Keep wrappers in `bot_logic.py`**

Delegate each original method to `effects.py`.

- [x] **Step 3: Run tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest
```

Expected: PASS except the known file-size failure.

- [x] **Step 4: Commit**

```powershell
git add bot_logic.py draftleaguebot/mechanics/effects.py
git commit -m "refactor: extract battle effect helpers"
```

## Task 8: Move Damage Calculation

**Files:**

- Create: `draftleaguebot/mechanics/damage_calc.py`
- Modify: `bot_logic.py`

- [x] **Step 1: Move damage calculation helpers**

Move these methods into `damage_calc.py`:

```python
estimate_damage(battle, attacker, move, target, use_max_roll=False, debug=False)
resolve_identifier_side(battle, pokemon)
hydrate_damage_stats(pokemon)
damage_roll_factor()
get_offense_defense_stats(attacker, target, move)
```

Import `calculate_damage`, `compute_raw_stats`, and `GenData` only in `damage_calc.py`.

- [x] **Step 2: Preserve debug behavior**

Pass `debug=self._should_debug(battle)` from the wrapper method:

```python
def _estimate_damage(self, battle, attacker, move, target, use_max_roll=False):
    return damage_calc.estimate_damage(
        battle,
        attacker,
        move,
        target,
        use_max_roll=use_max_roll,
        debug=self._should_debug(battle),
    )
```

- [x] **Step 3: Run tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest
```

Expected: PASS except the known file-size failure.

- [x] **Step 4: Commit**

```powershell
git add bot_logic.py draftleaguebot/mechanics/damage_calc.py
git commit -m "refactor: extract damage calculation"
```

## Task 9: Move Scoring Modules Incrementally

**Files:**

- Create: `draftleaguebot/scoring/__init__.py`
- Create: `draftleaguebot/scoring/move_scorer.py`
- Create: `draftleaguebot/scoring/damage.py`
- Create: `draftleaguebot/scoring/status.py`
- Create: `draftleaguebot/scoring/doubles.py`
- Create: `draftleaguebot/scoring/setup.py`
- Create: `draftleaguebot/scoring/speed_control.py`
- Modify: `bot_logic.py`

- [x] **Step 1: Create scoring package marker files**

Create `draftleaguebot/scoring/__init__.py`:

```python
"""Scoring rules for DraftLeagueBot battle decisions."""
```

- [x] **Step 2: Move the top-level score dispatcher**

Move `_score_move` into `scoring/move_scorer.py` as `score_move(context, battle, attacker, move, target, opponents, attacker_moves)`.

Use `context` as the current bot instance during the first pass so helper calls still resolve while extraction continues.

- [x] **Step 3: Move damaging rules**

Move damage-specific methods from `bot_logic.py` to `scoring/damage.py`. Keep wrappers until all callers point to the module.

- [x] **Step 4: Move status rules**

Move status/support methods from `bot_logic.py` to `scoring/status.py`. Keep wrappers until all callers point to the module.

- [x] **Step 5: Move setup rules**

Move setup and boost-related scoring from `bot_logic.py` to `scoring/setup.py`.

- [x] **Step 6: Move doubles rules**

Move partner interaction scoring from `bot_logic.py` to `scoring/doubles.py`.

- [x] **Step 7: Move speed-control rules**

Move Tailwind, Trick Room, speed profile, and damaging speed-control scoring from `bot_logic.py` to `scoring/speed_control.py`.

- [x] **Step 8: Run tests after each scoring module move**

Run after each step above:

```powershell
.venv/Scripts/python.exe -m pytest
```

Expected: PASS except the known file-size failure.

- [x] **Step 9: Commit**

```powershell
git add bot_logic.py draftleaguebot/scoring
git commit -m "refactor: extract bot scoring modules"
```

## Task 10: Move `DoublesMvpBot` and Replace Root File with Shim

**Files:**

- Modify: `draftleaguebot/bot.py`
- Modify: `draftleaguebot/__init__.py`
- Modify: `bot_logic.py`

- [x] **Step 1: Move the final `DoublesMvpBot` class to `draftleaguebot/bot.py`**

`draftleaguebot/bot.py` should import `MaxBasePowerPlayer`, `DoubleBattleOrder`, `PassBattleOrder`, and the extracted helper modules. It should contain `DoublesMvpBot` with only orchestration and wrapper methods still needed by extracted scoring modules.

- [x] **Step 2: Replace `bot_logic.py` with the compatibility shim**

```python
from draftleaguebot.bot import DoublesMvpBot

__all__ = ["DoublesMvpBot"]
```

- [x] **Step 3: Confirm package export**

`draftleaguebot/__init__.py` should be:

```python
from draftleaguebot.bot import DoublesMvpBot

__all__ = ["DoublesMvpBot"]
```

- [x] **Step 4: Run import and file-size tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_import_contract.py tests/test_file_size_limits.py -v
```

Expected: PASS.

- [x] **Step 5: Run the full test suite**

Run:

```powershell
.venv/Scripts/python.exe -m pytest
```

Expected: PASS.

- [x] **Step 6: Commit**

```powershell
git add bot_logic.py draftleaguebot tests
git commit -m "refactor: move doubles bot into package"
```

## Task 11: Final Verification

**Files:**

- Read: `README.md`
- Read: `AI_LOGIC_DOUBLES_MVP.txt`
- Run: test suite

- [x] **Step 1: Run full tests**

```powershell
.venv/Scripts/python.exe -m pytest
```

Expected: PASS.

- [x] **Step 2: Run preflight if local dependencies are available**

```powershell
.venv/Scripts/python.exe test_bot.py --preflight --no-format-prompt
```

Expected: The script prompts for trainer selection and can instantiate the bot after a valid trainer is selected.

- [x] **Step 3: Check file sizes manually**

```powershell
Get-ChildItem -Recurse -Filter *.py |
  Where-Object { $_.FullName -notmatch '\\.venv|\\.git|__pycache__|\\.pytest_cache' } |
  ForEach-Object {
    $lines = (Get-Content $_.FullName).Count
    if ($lines -gt 300) { "$($_.FullName): $lines" }
  }
```

Expected: No output.

- [x] **Step 4: Commit final documentation note if README is updated**

If README gets an import-path note, commit it:

```powershell
git add README.md
git commit -m "docs: document bot package layout"
```

## Self-Review

- Spec coverage: The plan covers compatibility, file-size enforcement, package extraction, debugging preservation, testing, and final verification.
- Placeholder scan: The plan avoids open-ended placeholders and names concrete files, helpers, and commands.
- Type consistency: The public class remains `DoublesMvpBot`; the old import path and new package import path are both preserved.
