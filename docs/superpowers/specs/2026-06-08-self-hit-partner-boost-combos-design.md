# Self-Hit Partner Boost Combos Design

## Goal
Add conservative doubles scoring for intentional partner hits that activate useful partner abilities or items: Weakness Policy, Stamina, Water Compaction, and positive berry Fling.

## Scope
- Applies only to damaging moves scored against the active partner.
- Preserves existing Fling and priority Weakness Policy behavior.
- Adds new scoring for Stamina and Water Compaction self-hit lines.
- Adds small synergy bonuses for Body Press, Stored Power, and Power Trip.
- Does not implement new switching logic or multi-turn planning.

## Current Codebase Patterns
- `draftleaguebot/mechanics/targets.py` already allows selected partner-targeting moves through `ALLY_TARGET_MOVE_IDS`.
- `draftleaguebot/scoring/damage.py` already calls `doubles.apply_doubles_damage_bonuses(...)` for damaging moves.
- `draftleaguebot/scoring/doubles.py` already owns partner interaction scoring for Weakness Policy, Fling, Coaching, and Earthquake partner checks.
- Existing helpers should be reused through the bot context:
  - `context._get_partner(battle, attacker)`
  - `context._estimate_damage(battle, attacker, move, target, use_max_roll=True)`
  - `context._estimated_kill(target, damage)`
  - `context._get_boost(partner, "def")`
  - `context._has_move_id(partner, "bodypress")`
  - `context._is_super_effective_on_target(move, partner)`

Opponent board pressure should use stat profile, not revealed move categories.
Draft-league first turns may not expose moves yet, but Pokemon stats are usually
available. Treat an opponent as physical pressure if its Attack is meaningfully
higher than its Special Attack.

## Architecture
Create `draftleaguebot/scoring/self_hit.py` for self-hit combo scoring. Keep `doubles.py` as the integration point by importing this module inside `apply_doubles_damage_bonuses`.

This keeps `doubles.py` focused and avoids growing it into another large file. The new module will expose one public entry point:

```python
def self_hit_partner_boost_bonus(context, battle, attacker, move, target):
    ...
```

## Scoring Rules
Safety gates apply before positive self-hit scoring:

- If target is not the active partner: `0`
- If estimated max-roll damage would KO partner: `-20`
- If estimated max-roll damage is at least 25% of partner max HP: `-20`
- If estimated max-roll damage is at least 15% of partner max HP: `-6`
- If the boosted stat is already `+6`: `-20`
- If the boosted stat is already `+4` or higher: `-6`
Weakness Policy:

- If hitting partner super-effectively and partner has Weakness Policy: `+12`
- If partner can act this turn and is an offensive attacker: `+1`
- If partner has Stored Power or Power Trip: `+1`
- If partner is already heavily boosted in Atk or SpA: reduce by `4`

Stamina:

- If a safe weak hit activates partner Stamina: `+3`
- For multi-hit moves, add `+1` per extra expected hit, capped at `+7` total
- If one opposing active Pokemon is a physical attacker: `+1`
- If two opposing active Pokemon are physical attackers: `+4`
- If partner has Body Press: `+1`

Water Compaction:

- If a safe Water-type hit activates partner Water Compaction: `+5`
- For multi-hit Water moves, add `+2` per extra expected hit, capped at `+9` total
- If one opposing active Pokemon is a physical attacker: `+1`
- If two opposing active Pokemon are physical attackers: `+4`
- If partner has Body Press: `+1`

Multi-hit estimation:

- Fixed-hit moves use their real hit count.
- Variable 2-5 hit moves use `5` hits if the attacker has Skill Link or Loaded Dice.
- Otherwise, variable 2-5 hit moves use a controlled 2-5 roll for scoring, with the roll injectable in tests.
- Beat Up is not treated as a normal multi-hit move because its hit count depends on remaining healthy party members. First implementation should score Beat Up as `1` hit until party-aware counting is added.
- Triple Axel, Triple Kick, and Population Bomb should use their own fixed upper-bound categories only after accuracy-aware scoring is added. First implementation should not give them full multi-hit combo value.

Positive berry Fling:

- Existing Salac Fling behavior remains:
  - Salac + partner Weakness Policy + super-effective: `+12`
  - Salac without WP or not super-effective: `+9`
- New Stamina / Water Compaction helper must not stack a second full Fling bonus on top of existing Fling speed logic.

## Expected Behavior
Against two special attackers, Light Screen should usually beat Stamina self-hit scoring because Stamina's board-pressure bonus only applies to physical attackers.

Against two physical attackers, safe Stamina or Water Compaction activation can compete with screens or setup, especially when partner has Body Press.

Fast OHKOs should normally beat self-hit setup through normal move scoring because these combo bonuses are intentionally modest.

## Testing
Tests should be written expected-first:

- assert unsafe partner damage returns `-20`
- assert medium partner damage returns `-6`
- assert safe Stamina one-hit score
- assert safe Stamina multi-hit score and cap
- assert two physical opponents add the larger board-pressure bonus
- assert two special opponents do not add physical board-pressure bonus
- assert Body Press adds only `+1`
- assert Water Compaction uses Water-type requirement
- assert existing Fling WP scores are preserved
