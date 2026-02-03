import asyncio
from poke_env import AccountConfiguration, LocalhostServerConfiguration
from poke_env.player import MaxBasePowerPlayer
import random
from pathlib import Path


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



class SmartAggroBot(MaxBasePowerPlayer):
    """For this Smart Aggro Bot, just need to code to work in a doubles scenario, note that original MaxBasePowerPlayer can handle all 
    states of double scenarios (Partner Died, Request to Switch when needed, etc)
    
    Current Flaws of the Bot: Only cares about highest base attacks, but does not account for type effectiveness.
    Does not like to set-up as well
    Does not go for pirority moves when defender is low on health
    Fake Out support
    
    Documentation: https://poke-env.readthedocs.io/en/stable/
    """
    
    def _should_mega_evolve(self, pokemon, battle): 
        return False
    
    def _should_z_move(self, pokemon, battle): 
        return False
    
    def _should_terastallize(self, pokemon, battle): 
        return False


async def main():
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
    
    # Create bot
    bot = SmartAggroBot(
        account_configuration=bot_account,
        server_configuration=LocalhostServerConfiguration,
        team=selected_team,
        battle_format="gen9vgc2025regj"
    )
    print("✅ Bot Ready. Debugging enabled.")
    await bot.accept_challenges(None, 5)


if __name__ == "__main__":
    asyncio.run(main())