# Draft League Bot

## Requirements
- Local Pokemon Showdown server
- Python 3.12+ with a virtual environment

## Setup
1) Start the local Showdown server:

```bash
node pokemon-showdown
```

2) In `config/config.js`, set:

```js
exports.noguestsecurity = true
```

## Run the Bot
From the DraftLeagueBot folder:

```bash
".venv/Scripts/python.exe" test_bot.py
```

### Debug Mode
Enable debug logs and use a specific team file when `--debug` is set:

```bash
".venv/Scripts/python.exe" test_bot.py --debug --team-file team5.txt
```

### Preflight Check
Loads the team and exits (no battle):

```bash
".venv/Scripts/python.exe" test_bot.py --preflight
```

## Team Selection
- You will be prompted to choose a trainer folder (e.g., `TESTER`).
- With `--debug`, `--team-file` can point to a team filename in that folder or a full path.
- Without `--debug`, team selection remains random.

## AI Battle Logic
The bot uses custom doubles-only scoring rules derived from `AI_LOGIC.txt`.
See `AI_LOGIC_DOUBLES_MVP.txt` for the current implemented logic and remaining work.

## Unit Testings
The 
