# Self-Hit Partner Boost Combos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add conservative doubles scoring for intentional partner hits that activate Stamina, Water Compaction, and existing Weakness Policy / Fling synergy.

**Architecture:** Add a focused `draftleaguebot/scoring/self_hit.py` module and call it from `draftleaguebot/scoring/doubles.py`. Reuse existing context helpers for partner lookup, damage estimation, boost checks, move lookup, physical/special attack detection, and KO detection.

**Tech Stack:** Python 3.12, pytest, poke-env battle objects, existing DraftLeagueBot scoring modules.

---

## File Structure

- Create: `draftleaguebot/scoring/self_hit.py`
  - Owns Stamina, Water Compaction, and shared self-hit safety logic.
- Modify: `draftleaguebot/scoring/doubles.py`
  - Calls `self_hit.self_hit_partner_boost_bonus(...)` from `apply_doubles_damage_bonuses`.
  - Keeps existing Weakness Policy and Fling functions intact.
- Test: `tests/test_self_hit_scoring_module.py`
  - Unit tests expected-first against `self_hit.py`.
- Test: `tests/test_doubles_scoring_module.py`
  - Small routing regression test for `apply_doubles_damage_bonuses`.

## Existing Helpers To Reuse

- `context._get_partner(battle, attacker)`
- `context._estimate_damage(battle, attacker, move, target, use_max_roll=True)`
- `context._estimated_kill(target, damage)`
- `context._get_boost(partner, "def")`
- `context._has_move_id(partner, "bodypress")`
- `context._has_move_id(partner, "storedpower")`
- `context._has_move_id(partner, "powertrip")`
For physical board pressure, use visible stats instead of revealed move
categories. This matters in draft league because turn 1 may not have reliable
opponent move information yet.

## Multi-Hit Scoring Policy

- Fixed-hit moves use their real hit count.
- Variable 2-5 hit moves use `5` hits when the attacker has Skill Link or Loaded Dice.
- Normal variable 2-5 hit moves use a controlled 2-5 RNG roll for scoring.
- Tests inject a fixed roll into `expected_hit_count(...)` so assertions stay deterministic.
- Beat Up is treated as `1` hit for the first implementation because its hit count depends on remaining healthy party members.
- Future follow-up: make Beat Up team-aware by counting healthy remaining party members.
- Triple Axel, Triple Kick, and Population Bomb are treated as `1` hit for this first implementation because they need accuracy-aware scoring before they can safely receive full combo value.

### Task 1: Add Safety Gate Tests

**Files:**
- Create: `tests/test_self_hit_scoring_module.py`

- [x] **Step 1: Write failing safety tests**

```python
from types import SimpleNamespace


def make_context(partner, damage):
    return SimpleNamespace(
        _get_partner=lambda _battle, _attacker: partner,
        _estimate_damage=lambda _battle, _attacker, _move, _target, use_max_roll=False: damage,
        _estimated_kill=lambda target, amount: amount >= getattr(target, "current_hp", 100),
        _get_boost=lambda pokemon, stat: getattr(pokemon, "boosts", {}).get(stat, 0),
        _has_move_id=lambda pokemon, move_id: move_id in getattr(pokemon, "moves", {}),
        _has_physical_move=lambda pokemon: False,
        _has_special_move=lambda pokemon: True,
    )


def test_self_hit_rejects_partner_ko():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=20,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = make_context(partner, damage=20)
    battle = SimpleNamespace(opponent_active_pokemon=[])
    move = SimpleNamespace(id="pinmissile", type="Bug")
    expected = -20

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner
    )

    assert result == expected


def test_self_hit_rejects_damage_at_25_percent_of_partner_max_hp():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = make_context(partner, damage=25)
    battle = SimpleNamespace(opponent_active_pokemon=[])
    move = SimpleNamespace(id="pinmissile", type="Bug")
    expected = -20

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner
    )

    assert result == expected


def test_self_hit_penalizes_damage_at_15_percent_of_partner_max_hp():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = make_context(partner, damage=15)
    battle = SimpleNamespace(opponent_active_pokemon=[])
    move = SimpleNamespace(id="pinmissile", type="Bug")
    expected = -6

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner
    )

    assert result == expected
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_self_hit_scoring_module.py -v
```

Expected: FAIL with import error for `draftleaguebot.scoring.self_hit`.

- [x] **Step 3: Implement minimal safety module**

Create `draftleaguebot/scoring/self_hit.py`:

```python
def self_hit_partner_boost_bonus(context, battle, attacker, move, target):
    """Score intentional partner hits that activate beneficial partner effects."""
    partner = context._get_partner(battle, attacker)
    if partner is None or target is not partner:
        return 0
    boosted_stat = boosted_stat_for_partner_combo(partner, move)
    if boosted_stat is None:
        return 0
    safety = self_hit_safety_score(context, battle, attacker, move, partner, boosted_stat)
    if safety != 0:
        return safety
    return 0


def boosted_stat_for_partner_combo(partner, move):
    """Return the stat boosted by the partner self-hit combo, if supported."""
    ability = normalize_id(getattr(partner, "ability", None))
    if ability == "stamina":
        return "def"
    if ability == "watercompaction" and move_is_water_type(move):
        return "def"
    return None


def self_hit_safety_score(context, battle, attacker, move, partner, boosted_stat):
    """Return a hard safety score or 0 when positive scoring may continue."""
    damage = context._estimate_damage(battle, attacker, move, partner, use_max_roll=True)
    if context._estimated_kill(partner, damage):
        return -20
    max_hp = max(getattr(partner, "max_hp", 100) or 100, 1)
    damage_ratio = damage / max_hp
    if damage_ratio >= 0.25:
        return -20
    if damage_ratio >= 0.15:
        return -6
    boost = context._get_boost(partner, boosted_stat)
    if boost >= 6:
        return -20
    if boost >= 4:
        return -6
    return 0


def move_is_water_type(move):
    """Return whether a move's type is Water across string/enum shapes."""
    move_type = getattr(move, "type", None)
    value = getattr(move_type, "name", None) or getattr(move_type, "value", None) or move_type
    return str(value).lower() == "water"


def normalize_id(value):
    """Normalize poke-env ids, item ids, and ability ids for scoring checks."""
    if value is None:
        return None
    return str(value).replace(" ", "").replace("-", "").lower()
```

- [x] **Step 4: Run tests to verify safety passes**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_self_hit_scoring_module.py -v
```

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add draftleaguebot/scoring/self_hit.py tests/test_self_hit_scoring_module.py
git commit -m "feat: add self-hit combo safety scoring"
```

### Task 2: Add Stamina Scoring

**Files:**
- Modify: `tests/test_self_hit_scoring_module.py`
- Modify: `draftleaguebot/scoring/self_hit.py`

- [x] **Step 1: Add failing Stamina expected-score tests**

Append:

```python
def test_stamina_scores_safe_single_hit():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = make_context(partner, damage=5)
    battle = SimpleNamespace(opponent_active_pokemon=[])
    move = SimpleNamespace(id="tackle", type="Normal")
    expected = 3

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner
    )

    assert result == expected


def test_stamina_adds_multi_hit_body_press_and_two_physical_stat_pressure():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="stamina",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={"bodypress": SimpleNamespace()},
    )
    physical_1 = SimpleNamespace(moves={}, stats={"atk": 150, "spa": 90})
    physical_2 = SimpleNamespace(moves={}, stats={"atk": 130, "spa": 80})
    context = make_context(partner, damage=5)
    battle = SimpleNamespace(opponent_active_pokemon=[physical_1, physical_2])
    move = SimpleNamespace(id="pinmissile", type="Bug")
    expected = 10

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner, hit_roll=lambda: 5
    )

    assert result == expected


def test_variable_multi_hit_forces_five_hits_with_skill_link():
    from draftleaguebot.scoring import self_hit

    attacker = SimpleNamespace(ability="skilllink", item=None)
    move = SimpleNamespace(id="pinmissile")
    expected = 5

    result = self_hit.expected_hit_count(move, attacker, hit_roll=lambda: 2)

    assert result == expected


def test_beat_up_is_not_treated_as_generic_multi_hit():
    from draftleaguebot.scoring import self_hit

    attacker = SimpleNamespace(ability=None, item=None)
    move = SimpleNamespace(id="beatup")
    expected = 1

    result = self_hit.expected_hit_count(move, attacker, hit_roll=lambda: 5)

    assert result == expected


def test_physical_pressure_uses_attack_stat_when_moves_unknown():
    from draftleaguebot.scoring import self_hit

    context = make_context(partner=SimpleNamespace(), damage=0)
    opponent = SimpleNamespace(moves={}, stats={"atk": 140, "spa": 100})
    battle = SimpleNamespace(opponent_active_pokemon=[opponent])
    expected = 1

    result = self_hit.physical_pressure_bonus(context, battle)

    assert result == expected


def test_physical_pressure_uses_attack_stat_over_revealed_move_category():
    from draftleaguebot.scoring import self_hit

    context = make_context(partner=SimpleNamespace(), damage=0)
    opponent = SimpleNamespace(moves={}, stats={"atk": 140, "spa": 100})
    battle = SimpleNamespace(opponent_active_pokemon=[opponent])
    context._has_physical_move = lambda _pokemon: False
    context._has_special_move = lambda _pokemon: True
    expected = 1

    result = self_hit.physical_pressure_bonus(context, battle)

    assert result == expected
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_self_hit_scoring_module.py -v
```

Expected: FAIL because positive Stamina scoring returns 0.

- [x] **Step 3: Implement Stamina scoring helpers**

Update `draftleaguebot/scoring/self_hit.py`:

```python
import random


FIXED_HIT_COUNTS = {
    "bonemerang": 2,
    "doublehit": 2,
    "doubleironbash": 2,
    "doublekick": 2,
    "dragondarts": 2,
    "dualchop": 2,
    "dualwingbeat": 2,
    "geargrind": 2,
    "surgingstrikes": 3,
    "tachyoncutter": 2,
    "tripledive": 3,
    "twinbeam": 2,
    "twineedle": 2,
    "watershuriken": 3,
}

VARIABLE_TWO_TO_FIVE_HIT_MOVES = {
    "armthrust",
    "barrage",
    "bonerush",
    "bulletseed",
    "cometpunch",
    "doubleslap",
    "furyattack",
    "furyswipes",
    "iciclespear",
    "pinmissile",
    "rockblast",
    "scaleshot",
    "spikecannon",
    "tailslap",
}


def self_hit_partner_boost_bonus(context, battle, attacker, move, target, hit_roll=None):
    """Score intentional partner hits that activate beneficial partner effects."""
    partner = context._get_partner(battle, attacker)
    if partner is None or target is not partner:
        return 0
    combo = partner_combo_kind(partner, move)
    if combo is None:
        return 0
    safety = self_hit_safety_score(context, battle, attacker, move, partner, "def")
    if safety != 0:
        return safety
    if combo == "stamina":
        score = score_stamina_combo(context, battle, attacker, partner, move, hit_roll=hit_roll)
    else:
        score = 0
    return score


def partner_combo_kind(partner, move):
    """Return the supported self-hit combo kind for this partner and move."""
    ability = normalize_id(getattr(partner, "ability", None))
    if ability == "stamina":
        return "stamina"
    if ability == "watercompaction" and move_is_water_type(move):
        return "watercompaction"
    return None


def score_stamina_combo(context, battle, attacker, partner, move, hit_roll=None):
    """Score a safe Stamina activation against the current opponent board."""
    score = 3
    extra_hits = max(expected_hit_count(move, attacker, hit_roll=hit_roll) - 1, 0)
    score += min(extra_hits, 4)
    score += physical_pressure_bonus(context, battle)
    if context._has_move_id(partner, "bodypress"):
        score += 1
    return min(score, 10)


def expected_hit_count(move, attacker, hit_roll=None):
    """Return the hit count to use when scoring multi-hit self-hit combos."""
    move_id = normalize_id(getattr(move, "id", None))
    if move_id in FIXED_HIT_COUNTS:
        return FIXED_HIT_COUNTS[move_id]
    if move_id not in VARIABLE_TWO_TO_FIVE_HIT_MOVES:
        return 1
    if has_guaranteed_five_hit_modifier(attacker):
        return 5
    roll = random.randint(2, 5) if hit_roll is None else hit_roll()
    return max(2, min(int(roll), 5))


def has_guaranteed_five_hit_modifier(attacker):
    """Return whether attacker forces 2-5 hit moves to hit five times."""
    ability = normalize_id(getattr(attacker, "ability", None))
    item = normalize_id(getattr(attacker, "item", None))
    return ability == "skilllink" or item == "loadeddice"


def physical_pressure_bonus(context, battle):
    """Reward Defense boosts more when active opponents lean physical."""
    opponents = [p for p in getattr(battle, "opponent_active_pokemon", []) if p is not None]
    physical_count = sum(1 for opponent in opponents if attack_stat_leans_physical(opponent))
    if physical_count >= 2:
        return 4
    if physical_count == 1:
        return 1
    return 0


def attack_stat_leans_physical(opponent):
    """Return whether Attack is meaningfully higher than Special Attack."""
    stats = getattr(opponent, "stats", {}) or {}
    attack = stats.get("atk", 0) or 0
    special_attack = stats.get("spa", 0) or 0
    return attack >= special_attack * 1.1 and attack > 0


```

Keep `self_hit_safety_score`, `move_is_water_type`, and `normalize_id` from Task 1.

- [x] **Step 4: Run Stamina tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_self_hit_scoring_module.py -v
```

Expected: PASS.

- [x] **Step 5: Commit**

```powershell
git add draftleaguebot/scoring/self_hit.py tests/test_self_hit_scoring_module.py
git commit -m "feat: score stamina partner self-hit combos"
```

### Task 3: Add Water Compaction Scoring

**Files:**
- Modify: `tests/test_self_hit_scoring_module.py`
- Modify: `draftleaguebot/scoring/self_hit.py`

- [x] **Step 1: Add failing Water Compaction tests**

Append:

```python
def test_water_compaction_requires_water_type_move():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="watercompaction",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = make_context(partner, damage=5)
    battle = SimpleNamespace(opponent_active_pokemon=[])
    move = SimpleNamespace(id="pinmissile", type="Bug")
    expected = 0

    result = self_hit.self_hit_partner_boost_bonus(
        context,
        battle,
        attacker=SimpleNamespace(),
        move=move,
        target=partner,
        hit_roll=lambda: 3,
    )

    assert result == expected


def test_water_compaction_scores_safe_multi_hit_water_move():
    from draftleaguebot.scoring import self_hit

    partner = SimpleNamespace(
        ability="watercompaction",
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={"bodypress": SimpleNamespace()},
    )
    physical_1 = SimpleNamespace(moves={}, stats={"atk": 150, "spa": 90})
    physical_2 = SimpleNamespace(moves={}, stats={"atk": 130, "spa": 80})
    context = make_context(partner, damage=5)
    battle = SimpleNamespace(opponent_active_pokemon=[physical_1, physical_2])
    move = SimpleNamespace(id="watershuriken", type="Water")
    expected = 12

    result = self_hit.self_hit_partner_boost_bonus(
        context, battle, attacker=SimpleNamespace(), move=move, target=partner
    )

    assert result == expected
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_self_hit_scoring_module.py -v
```

Expected: FAIL because Water Compaction positive scoring is not implemented.

- [x] **Step 3: Implement Water Compaction scoring**

Update `self_hit_partner_boost_bonus` branch:

```python
    if combo == "stamina":
        score = score_stamina_combo(context, battle, partner, move)
    elif combo == "watercompaction":
        score = score_water_compaction_combo(context, battle, attacker, partner, move, hit_roll=hit_roll)
    else:
        score = 0
```

Add:

```python
def score_water_compaction_combo(context, battle, attacker, partner, move, hit_roll=None):
    """Score a safe Water Compaction activation against the current board."""
    score = 5
    extra_hits = max(expected_hit_count(move, attacker, hit_roll=hit_roll) - 1, 0)
    score += min(extra_hits * 2, 4)
    score += physical_pressure_bonus(context, battle)
    if context._has_move_id(partner, "bodypress"):
        score += 1
    return min(score, 12)
```

- [x] **Step 4: Run Water Compaction tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_self_hit_scoring_module.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add draftleaguebot/scoring/self_hit.py tests/test_self_hit_scoring_module.py
git commit -m "feat: score water compaction partner self-hit combos"
```

### Task 4: Wire Self-Hit Scoring Into Doubles Bonuses

**Files:**
- Modify: `draftleaguebot/scoring/doubles.py`
- Modify: `tests/test_doubles_scoring_module.py`

- [ ] **Step 1: Add failing routing test**

Append to `tests/test_doubles_scoring_module.py`:

```python
def test_apply_doubles_damage_bonuses_routes_stamina_partner_self_hit():
    from draftleaguebot.scoring import doubles

    partner = SimpleNamespace(
        ability="stamina",
        item=None,
        current_hp=100,
        max_hp=100,
        boosts={"def": 0},
        moves={},
    )
    context = SimpleNamespace(
        _get_partner=lambda _battle, _attacker: partner,
        _estimate_damage=lambda _battle, _attacker, _move, _target, use_max_roll=False: 5,
        _estimated_kill=lambda _target, _damage: False,
        _get_boost=lambda pokemon, stat: pokemon.boosts.get(stat, 0),
        _has_move_id=lambda pokemon, move_id: move_id in getattr(pokemon, "moves", {}),
        _has_physical_move=lambda _pokemon: False,
        _has_special_move=lambda _pokemon: True,
        _is_super_effective_on_target=lambda _move, _target: False,
    )
    battle = SimpleNamespace(opponent_active_pokemon=[])
    expected = 3

    result = doubles.apply_doubles_damage_bonuses(
        context,
        battle=battle,
        attacker=SimpleNamespace(moves={}),
        move=SimpleNamespace(id="pinmissile", type="Bug"),
        target=partner,
    )

    assert result == expected
```

- [ ] **Step 2: Run routing test to verify it fails**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_doubles_scoring_module.py::test_apply_doubles_damage_bonuses_routes_stamina_partner_self_hit -v
```

Expected: FAIL because `apply_doubles_damage_bonuses` does not call `self_hit`.

- [ ] **Step 3: Wire module into `doubles.py`**

Modify `draftleaguebot/scoring/doubles.py`:

```python
from draftleaguebot.scoring import self_hit
```

In `apply_doubles_damage_bonuses`, after existing move-specific bonus checks:

```python
    bonus += self_hit.self_hit_partner_boost_bonus(context, battle, attacker, move, target)
```

Keep the existing Fling branch in place. The self-hit module should return `0` for Salac-only Fling unless Stamina or Water Compaction also applies.

- [ ] **Step 4: Run routing and existing doubles tests**

Run:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_doubles_scoring_module.py tests/test_doubles_specific.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add draftleaguebot/scoring/doubles.py tests/test_doubles_scoring_module.py
git commit -m "feat: route self-hit partner boost scoring"
```

### Task 5: Final Verification

**Files:**
- Read: `AI_LOGIC_DOUBLES_MVP.txt`
- Run: test suite

- [ ] **Step 1: Run targeted scoring tests**

```powershell
.venv/Scripts/python.exe -m pytest tests/test_self_hit_scoring_module.py tests/test_doubles_scoring_module.py tests/test_damage_scoring_module.py -v
```

Expected: PASS.

- [ ] **Step 2: Run file size check**

```powershell
Get-ChildItem -Recurse -Filter *.py |
  Where-Object { $_.FullName -notmatch '\\.venv|\\.git|__pycache__|\\.pytest_cache' } |
  ForEach-Object {
    $lines = (Get-Content $_.FullName).Count
    if ($lines -gt 300) { "$($_.FullName): $lines" }
  }
```

Expected: No output.

- [ ] **Step 3: Run full tests in two batches if one-shot pytest is slow**

```powershell
.venv/Scripts/python.exe -m pytest tests/test_bot_logic_regression.py tests/test_damage_calc.py tests/test_damage_estimation.py tests/test_damage_scoring_module.py tests/test_damaging_move_scoring.py tests/test_debug_helpers.py tests/test_doubles_scoring_module.py tests/test_doubles_specific.py tests/test_effects.py tests/test_file_size_limits.py tests/test_import_contract.py -v

.venv/Scripts/python.exe -m pytest tests/test_move_scorer.py tests/test_orders.py tests/test_pokemon_state.py tests/test_setup_and_utility.py tests/test_setup_scoring_module.py tests/test_speed_control_scoring_module.py tests/test_status_move_scoring.py tests/test_status_scoring_module.py tests/test_targets.py tests/test_terrain_and_weather_moves.py tests/test_terrain_status_moves.py tests/test_threat_and_speed.py tests/test_weatherball.py tests/test_self_hit_scoring_module.py -v
```

Expected: PASS.

- [ ] **Step 4: Confirm docs match implementation scope**

Read `AI_LOGIC_DOUBLES_MVP.txt` and verify `Remaining / Not Yet Implemented` is updated after implementation. If the listed self-hit combo rules are implemented, change the remaining note to:

```text
Remaining / Not Yet Implemented
- None currently listed.
```

- [ ] **Step 5: Commit**

```powershell
git add draftleaguebot/scoring/self_hit.py draftleaguebot/scoring/doubles.py tests AI_LOGIC_DOUBLES_MVP.txt
git commit -m "feat: score partner self-hit boost combos"
```

## Self-Review

- Spec coverage: Covers safety gates, Stamina, Water Compaction, physical board pressure, Body Press synergy, and existing Fling preservation.
- Placeholder scan: No open placeholders.
- Type consistency: Functions consistently use `context`, `battle`, `attacker`, `move`, and `target`, matching existing scoring modules.
