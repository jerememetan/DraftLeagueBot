# Draft League Bot

## Requirements
- Local Pokemon Showdown server -> download from https://github.com/smogon/pokemon-showdown (Open Source)
- Python 3.12+ with a virtual environment

## Setup
1) Start the local Showdown server:

```bash
node pokemon-showdown
```

2) In showdown-master, `config/config.js`, set:
(You will need to run node pokemon-showdown at least once to see config.js)
```js
exports.noguestsecurity = true
```

## Run the Bot (Basic Version)
From the DraftLeagueBot folder:
-> Prompts for either 4v4 doubles draft or reg M-A
-> Prompts for Trainers Name to select
-> Go to http://localhost:8000 , "Find a user" -> "Bot_Opponent" -> challenge

```bash
".venv/Scripts/python.exe" test_bot.py
```

### Debug Mode
Enable debug logs and use a specific team file when `--debug` is set:

```bash
".venv/Scripts/python.exe" test_bot.py --debug --team-file teamfilename.txt
```

### Battle Format
The bot now prompts you to choose a battle format interactively at startup.
Press Enter to use the default draft format, choose the Reg M-A profile, or enter a custom format id.

You can still force a format non-interactively:

```bash
".venv/Scripts/python.exe" test_bot.py --format-profile draft
".venv/Scripts/python.exe" test_bot.py --format-profile vgc-reg-ma
".venv/Scripts/python.exe" test_bot.py --battle-format gen9championsvgc2026regma
```

Skip the prompt and use the resolved default format:

```bash
".venv/Scripts/python.exe" test_bot.py --no-format-prompt
```

List the built-in profiles:

```bash
".venv/Scripts/python.exe" test_bot.py --list-formats
```

### Preflight Check
Loads the team and exits (no battle):

```bash
".venv/Scripts/python.exe" test_bot.py --preflight --no-format-prompt
```

## Team Selection
- You will be prompted to choose a trainer folder (e.g., `TESTER`).
- With `--debug`, `--team-file` can point to a team filename in that folder or a full path.
- Without `--debug`, team selection remains random.

## AI Battle Logic
The bot uses custom doubles-only scoring rules derived from `AI_LOGIC.txt`.
See `AI_LOGIC_DOUBLES_MVP.txt` for the current implemented logic and remaining work.

## Bot Package Layout
`DoublesMvpBot` is exported from `draftleaguebot` and `draftleaguebot.bot`.
The root `bot_logic.py` file remains as a compatibility shim, so older imports still work.

Core bot orchestration lives in `draftleaguebot/bot.py`, bot wrapper mixins live in
`draftleaguebot/bot_parts/`, battle mechanics live in `draftleaguebot/mechanics/`, and
move scoring lives in `draftleaguebot/scoring/`.

## Adding new trainers
Trainers can be added as new folders in /Trainers. To add teams in trainers, copy and paste your txt file of the pokepaste (refer to /Trainers/TESTER as reference)

