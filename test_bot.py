import argparse
import asyncio
import random
from pathlib import Path

from poke_env import AccountConfiguration, LocalhostServerConfiguration

from bot_logic import DoublesMvpBot


def load_random_team_from_challenger(challenger_name):
    """Load a random team from a challenger's folder."""
    script_dir = Path(__file__).parent
    challenger_folder = script_dir / challenger_name
    
    if not challenger_folder.exists():
        print(f"❌ Challenger folder '{challenger_name}' does not exist!")
        return None
    
    team_files = list(challenger_folder.glob("*.txt"))
    
    if not team_files:
        print(f"❌ No .txt team files found in '{challenger_name}' folder")
        return None
    
    valid_teams = []
    for team_file in team_files:
        try:
            with open(team_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    valid_teams.append((team_file.name, content))
                else:
                    print(f"  ⚠️ Skipped empty file: {team_file.name}")
        except Exception as e:
            print(f"  ❌ Error reading {team_file.name}: {e}")
    
    if not valid_teams:
        print(f"❌ No valid teams found in '{challenger_name}' folder")
        return None
    
    selected_file, selected_team = random.choice(valid_teams)
    print(f"  ✅ Selected team: {selected_file} from {challenger_name}")
    
    return selected_team


def list_available_challengers():
    """List all available challenger folders"""
    script_dir = Path(__file__).parent
    challengers = [f.name for f in script_dir.iterdir() 
                   if f.is_dir() and not f.name.startswith('.') and not f.name.startswith('__')]
    return challengers



class SmartAggroBot(DoublesMvpBot):
    """Doubles MVP bot with custom scoring logic."""


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true", help="Run import/team checks only")
    parser.add_argument("--debug", action="store_true", help="Enable per-turn debug output")
    args = parser.parse_args()

    bot_account = AccountConfiguration("Bot_Opponent", None)
    
    available = list_available_challengers()
    
    if not available:
        print("❌ No challenger folders found!")
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
            selected_team = load_random_team_from_challenger(selected_trainer)
            if selected_team:
                break
        else:
            print(f"❌ '{selected_trainer}' not found. Please try again.")

    if args.preflight:
        print("✅ Preflight OK: team loaded and bot can be instantiated.")
        return
    
    # Create bot
    bot = SmartAggroBot(
        account_configuration=bot_account,
        server_configuration=LocalhostServerConfiguration,
        team=selected_team,
        battle_format="gen94v4doublesdraft",
        debug=args.debug,
        debug_turns=2
    )
    if args.debug:
        print("✅ Bot Ready. Debugging enabled.")
    else:
        print("✅ Bot Ready.")
    await bot.accept_challenges(None, 5)


if __name__ == "__main__":
    asyncio.run(main())