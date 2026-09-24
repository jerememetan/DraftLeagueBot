# Draft League Bot

## Requirements
- Local Pokemon Showdown server -> download from https://github.com/smogon/pokemon-showdown (Open Source)
- Python 3.12+ with a virtual environment
- Python packages: `pip install poke-env` (tested with poke-env 0.16.1)

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

### Live National Dex Doubles gym challenges

Use a registered account on the **public Pokemon Showdown server**. Set its
credentials in your terminal; do not put the password in a team file or commit it.
Alternatively, create the ignored `.env` file in the repository root:

```dotenv
PS_BOT_USERNAME=YourBotUsername
PS_BOT_PASSWORD=YourBotPassword
```

Shell environment variables take precedence over values in `.env`.
For example, in PowerShell:

```powershell
$env:PS_BOT_USERNAME = "YourBotUsername"
$env:PS_BOT_PASSWORD = "YourBotPassword"
```

Start the bot using the team you want it to play. Choose the trainer folder when
prompted. `--team-file` accepts a filename in that folder or a full path.

For the **online challenge version**, run this command from the repository root:

```powershell
python test_bot.py --server showdown `
  --format-profile national-dex-doubles `
  --team-file AV.txt `
  --max-challenges 0 `
  --no-format-prompt `
  --debug
```

Other players can challenge your bot account to **[Gen 9] National Dex Doubles**.
The bot accepts challenges matching `gen9nationaldexdoubles` and plays them with
the existing scoring logic. `--max-challenges 0` keeps it available for another
match after each battle until you stop it with Ctrl+C. The default is five
matches. If your league uses a custom format, pass its exact Showdown format ID
with `--battle-format` instead. Test the team on the public server before the
event: its legality and any custom rules are checked by Showdown when you
accept a challenge.

The default `--server local` preserves the local server workflow. A public
account password is required only for `--server showdown`.

### Preflight Check
Loads the team and exits (no battle):

```bash
".venv/Scripts/python.exe" test_bot.py --preflight --no-format-prompt
```

## Team Selection
- You will be prompted to choose a trainer folder (e.g., `TESTER`).
- `--team-file` selects a specific team in that folder or a full path, with or without `--debug`.
- Without `--team-file`, one team is picked at random at startup and used for that run.

## AI Battle Logic
The bot uses custom doubles-only scoring rules derived from `AI_LOGIC.txt`.
See `AI_LOGIC_DOUBLES_MVP.txt` for the current implemented logic and remaining work.

For Mega Evolution, Z-Moves, and Terastallization, the bot reads the live
Showdown request for each active slot. It Mega Evolves the first eligible active
Pokemon. It uses an eligible attacking Z-Move when the selected move gains power,
or offensively Terastallizes when the selected attack matches its Tera type.
Each action is limited to one Pokemon per turn and respects whether it was
already used in that battle. Status Z-Moves and defensive Tera decisions are
not part of the current scoring policy.

## Bot Package Layout
`DoublesMvpBot` is exported from `draftleaguebot` and `draftleaguebot.bot`.
The root `bot_logic.py` file remains as a compatibility shim, so older imports still work.

Core bot orchestration lives in `draftleaguebot/bot.py`, bot wrapper mixins live in
`draftleaguebot/bot_parts/`, battle mechanics live in `draftleaguebot/mechanics/`, and
move scoring lives in `draftleaguebot/scoring/`.

## Adding new trainers
Trainers can be added as new folders in /Trainers. To add teams in trainers, copy and paste your txt file of the pokepaste (refer to /Trainers/TESTER as reference)
