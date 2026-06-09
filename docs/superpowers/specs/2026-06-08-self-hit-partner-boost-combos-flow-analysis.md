# Self-Hit Partner Boost Combos Flow Analysis

## User Flows

1. **Safe Stamina setup**
   - Entry point: `choose_move` scores Jolteon's damaging move against candidate targets.
   - Decision points: move can target partner, partner has Stamina, damage is safe, opponents have physical pressure.
   - Happy path: scoring adds a small Stamina bonus that competes naturally with other move scores.
   - Terminal state: move-target candidate competes normally against opponent-target moves and status moves.

2. **Special attackers vs Light Screen**
   - Entry point: Jolteon can click Light Screen or hit Stamina partner.
   - Decision points: opponents have special moves but no physical moves.
   - Happy path: Light Screen gets its existing screen score; Stamina gets no physical-board bonus.
   - Terminal state: Light Screen usually wins unless Stamina has unusually strong safe synergy.

3. **Unsafe partner hit**
   - Entry point: a strong move can target partner.
   - Decision points: max-roll damage would KO or deal at least 25% of partner max HP.
   - Happy path: self-hit bonus returns `-20`, preventing accidental partner nukes.
   - Terminal state: candidate loses to normal opponent-targeting moves.

## Gaps

### Important

1. **Physical board pressure cannot rely only on revealed moves**
   - Missing: first-turn draft league board state may not expose opponent moves yet.
   - Why it matters: Stamina and Water Compaction would be under-scored into obvious physical attackers before moves are revealed.
   - Existing pattern: Pokemon objects expose `stats` even when moves are unknown.
   - Default: use Atk vs SpA. Count physical pressure when Attack is at least 10% higher than Special Attack.

1. **Multi-hit count needs move-specific handling**
   - Missing: the first draft treated Beat Up, fixed-hit moves, and 2-5 hit moves as one generic table.
   - Why it matters: fixed-hit moves should be exact, Skill Link / Loaded Dice should force 5 hits, and Beat Up depends on party state rather than the usual 2-5 distribution.
   - Existing pattern: current scoring allows RNG weights, but tests should inject deterministic rolls.
   - Default: use fixed counts where known, force 5 with Skill Link / Loaded Dice, use an injectable 2-5 roll for normal variable-hit moves, and treat Beat Up as 1 until party-aware counting exists.

2. **Water Compaction needs a reliable Water-type check**
   - Missing: the spec says Water-type hit, but move type shape may vary between tests and poke-env.
   - Why it matters: string and enum types both appear in tests/helpers.
   - Existing pattern: existing helpers read `move.type` directly in several modules.
   - Default: compare normalized lower-case type name/value to `"water"`.

### Minor

1. **Positive berry Fling list can stay narrow**
   - Missing: which berries count as useful positive Fling targets.
   - Default: keep current Salac behavior for the first implementation and only add infrastructure for future berry role matching.

## Questions

1. Should normal 2-5 hit moves use a controlled RNG roll instead of a fixed expected value?
   - Stakes: fixed expected values are easier to debug, but existing bot scoring already has some RNG and the user wants occasional variation.
   - Default: yes, use an injectable controlled roll; tests pass fixed rolls.

2. Should positive berry Fling remain Salac-only for now?
   - Stakes: adding many berry effects requires role matching and item-effect knowledge.
   - Default: yes, preserve existing Salac behavior first.

## Recommended Next Steps

1. Implement a small `self_hit.py` scoring module with deterministic helpers.
2. Add focused tests before implementation in `tests/test_self_hit_scoring_module.py`.
3. Wire the module through `doubles.apply_doubles_damage_bonuses`.
4. Keep existing Fling tests passing and add regression tests that Fling does not stack full bonuses twice.
