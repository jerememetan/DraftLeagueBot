# Bot Logic Refactor Flow Analysis

## User Flows

1. Developer runs the bot through the current CLI.

- Entry point: `test_bot.py`.
- Happy path: `test_bot.py` imports `DoublesMvpBot`, prompts for battle format and trainer, loads a team, instantiates the bot, and accepts challenges.
- Terminal state: bot is ready, or preflight exits after successful instantiation.
- Required preservation: `from bot_logic import DoublesMvpBot` must keep working.

2. Developer debugs a battle decision.

- Entry point: `test_bot.py --debug`.
- Happy path: debug mode reaches `DoublesMvpBot.choose_move`, scoring logs show top candidates, damage logs show calculation details, final order logs show selected orders.
- Terminal state: developer can locate decision flow in `bot.py`, scoring flow in `scoring/`, and mechanics in `mechanics/`.
- Required preservation: debug output remains available and recognizable.

3. Developer edits one category of battle logic.

- Entry point: project files under `draftleaguebot/`.
- Happy path: developer navigates to the relevant module, changes a focused rule, runs tests, and keeps every file under 300 lines.
- Terminal state: tests pass and file-size guard remains green.

4. Test runner validates maintainability.

- Entry point: `python -m pytest`.
- Happy path: import contract test verifies public imports, file-size test verifies every project Python file stays under 300 lines, existing tests validate behavior.
- Terminal state: passing suite blocks regression back into a giant file.

## Gaps

### Critical

No critical gaps block implementation. The spec and plan preserve the existing CLI import and make the 300-line rule testable.

### Important

1. The plan allows temporary wrappers that may keep `DoublesMvpBot` larger than desired until Task 10.

Why it matters: if implementation stops midway, the repo may still fail the file-size test.

Default assumption: intermediate commits may fail only `tests/test_file_size_limits.py`; all behavior tests should pass after each task.

2. The plan uses the current bot instance as `context` during scoring extraction.

Why it matters: this preserves behavior, but it can keep coupling alive after the first refactor.

Default assumption: this is acceptable for the first behavior-preserving pass. A later cleanup can replace `context` with explicit collaborators.

### Minor

1. The final exact distribution of scoring helper methods may need small adjustments to keep each module under 300 lines.

Why it matters: `status.py` and `damage.py` are likely to become the largest files.

Default assumption: split dense categories further by behavior if needed, for example `status_conditions.py` or `damage_special_cases.py`, while keeping the same package organization.

## Questions

1. Should intermediate commits be allowed to fail only the file-size test until the final shim task?

Stakes: strict green-at-every-commit would require delaying the file-size test or doing a larger, riskier extraction in one pass.

Default assumption: yes, intermediate commits may have the known file-size failure while behavior tests stay green.

2. Should `test_bot.py` keep importing from `bot_logic`, or should it move to `from draftleaguebot import DoublesMvpBot` after the shim is in place?

Stakes: keeping the old import proves compatibility; using the new import advertises the preferred path.

Default assumption: keep `test_bot.py` unchanged for the first refactor and rely on tests to prove both paths work.

3. Should the first implementation pass keep compatibility wrappers inside `DoublesMvpBot`, or immediately convert scoring modules to explicit function dependencies?

Stakes: wrappers are less pure but safer; explicit dependencies are cleaner but raise behavior-change risk.

Default assumption: keep wrappers for the first pass, then simplify after the full suite is green.

## Recommended Next Steps

1. Approve the spec and plan as a behavior-preserving refactor.
2. During implementation, treat `tests/test_file_size_limits.py` as an expected failure until Task 10.
3. After Task 10 passes, do a second review for leftover wrappers and decide whether to simplify the scoring context.
