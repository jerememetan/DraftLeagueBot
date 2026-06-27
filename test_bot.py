import argparse
import asyncio
import random
from pathlib import Path

from poke_env import AccountConfiguration, LocalhostServerConfiguration

from bot_logic import DoublesMvpBot


FORMAT_PROFILES = {
    "draft": "gen94v4doublesdraft",
    "vgc-reg-mb": "gen9championsvgc2026regmb",
}


def prompt_for_battle_format():
    """Prompt the user to pick a battle format profile interactively."""
    options = list(FORMAT_PROFILES.items())
    print("\nSelect Battle Format:")
    for index, (profile_name, format_id) in enumerate(options, start=1):
        print(f" {index}) {profile_name} -> {format_id}")
    print(f" {len(options) + 1}) custom format id")

    while True:
        choice = input(f"Choose 1-{len(options) + 1} [1]: ").strip()
        if choice == "" or choice == "1":
            return FORMAT_PROFILES["draft"]
        if choice.isdigit():
            choice_index = int(choice)
            if 1 <= choice_index <= len(options):
                return options[choice_index - 1][1]
            if choice_index == len(options) + 1:
                custom_format = input("Enter custom battle format id: ").strip()
                if custom_format:
                    return custom_format
        print("[ERROR] Invalid format choice. Please try again.")


def load_random_team_from_challenger(challenger_name, team_file=None):
    """Load a random team from a challenger's folder or a specific team file."""
    script_dir = Path(__file__).parent / "Trainers"
    challenger_folder = script_dir / challenger_name
    if not challenger_folder.exists():
        print(f"[ERROR] Challenger folder '{challenger_name}' does not exist!")
        return None
    requested_team_file = team_file
    if requested_team_file:
        candidate = Path(team_file)
        if not candidate.is_file():
            candidate = challenger_folder / team_file
        team_files = [candidate] if candidate.is_file() else []
    else:
        team_files = list(challenger_folder.glob("*.txt"))
    if not team_files:
        print(f"[ERROR] No .txt team files found in '{challenger_name}' folder")
        return None
    valid_teams = []
    for team_file in team_files:
        try:
            with open(team_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    valid_teams.append((team_file.name, content))
                else:
                    print(f"  [WARN] Skipped empty file: {team_file.name}")
        except Exception as e:
            print(f"  [ERROR] Error reading {team_file.name}: {e}")
    if not valid_teams:
        print(f"[ERROR] No valid teams found in '{challenger_name}' folder")
        return None
    if requested_team_file:
        selected_file, selected_team = valid_teams[0]    
    else:
        selected_file, selected_team = random.choice(valid_teams)
    print(f"  [OK] Selected team: {selected_file} from {challenger_name}")
    return selected_team


def list_available_challengers():
    """List all available challenger folders"""
    script_dir = Path(__file__).parent / "Trainers"
    challengers = [f.name for f in script_dir.iterdir() 
                   if f.is_dir() and not f.name.startswith('.') and not f.name.startswith('__')]
    return challengers


def resolve_battle_format(format_profile=None, battle_format=None):
    """Resolve the Showdown battle format to use.

    A named profile keeps the common doubles ladders easy to switch between, while
    ``--battle-format`` lets you override with any custom Showdown format id.
    """
    if battle_format:
        return battle_format
    if format_profile:
        return FORMAT_PROFILES.get(format_profile, format_profile)
    return FORMAT_PROFILES["draft"]



class SmartAggroBot(DoublesMvpBot):
    """Doubles MVP bot with custom scoring logic."""


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true", help="Run import/team checks only")
    parser.add_argument("--debug", action="store_true", help="Enable per-turn debug output")
    parser.add_argument("--team-file", help="Use a specific team file (name or full path)")
    parser.add_argument(
        "--format-profile",
        choices=sorted(FORMAT_PROFILES),
        default="draft",
        help="Named doubles format preset to use",
    )
    parser.add_argument(
        "--battle-format",
        help="Override the Showdown battle format id directly",
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="Print supported format profiles and exit",
    )
    parser.add_argument(
        "--no-format-prompt",
        action="store_true",
        help="Skip the interactive format picker and use the resolved default",
    )
    args = parser.parse_args()

    if args.list_formats:
        print("Supported format profiles:")
        for profile_name, format_id in FORMAT_PROFILES.items():
            print(f" - {profile_name}: {format_id}")
        return

    bot_account = AccountConfiguration("Bot_Opponent", None)
    resolved_battle_format = resolve_battle_format(args.format_profile, args.battle_format)
    if not args.battle_format and not args.no_format_prompt:
        resolved_battle_format = prompt_for_battle_format()
    
    available = list_available_challengers()
    
    if not available:
        print("[ERROR] No challenger folders found!")
        return
    
    print("==================================== ")
    print("Current Available List of Trainers: ")
    print("==================================== ")
    for trainer in available:
        print(f" - {trainer}")

    while True:
        selected_trainer = input("\nSelect Trainer Folder (or 'quit' to exit): ").strip()
        
        if selected_trainer.lower() == 'quit':
            return
        
        if selected_trainer in available:
            team_file = args.team_file if args.debug else None
            selected_team = load_random_team_from_challenger(selected_trainer, team_file=team_file)
            if selected_team:
                break
        else:
            print(f"[ERROR] '{selected_trainer}' not found. Please try again.")

    if args.preflight:
        print(f"[OK] Preflight OK: team loaded and bot can be instantiated with '{resolved_battle_format}'.")
        return
    
    # Create bot
    bot = SmartAggroBot(
        account_configuration=bot_account,
        server_configuration=LocalhostServerConfiguration,
        team=selected_team,
        battle_format=resolved_battle_format,
        debug=args.debug,
        debug_turns=55
    )
    if args.debug:
        print(f"[OK] Bot Ready. Debugging enabled. Battle format: {resolved_battle_format}")
    else:
        print(f"[OK] Bot Ready. Battle format: {resolved_battle_format}")
    await bot.accept_challenges(None, 5)


if __name__ == "__main__":
    asyncio.run(main())
