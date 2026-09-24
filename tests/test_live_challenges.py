"""Verify the live challenge entry point without connecting to Showdown."""

import asyncio
import sys

import test_bot
from poke_env import ShowdownServerConfiguration


def test_public_national_dex_mode_uses_selected_team_and_accepts_repeated_challenges(
    monkeypatch,
):
    calls = []

    class FakeBot:
        def __init__(self, **kwargs):
            calls.append(("init", kwargs))

        async def accept_challenges(self, opponent, count):
            calls.append(("accept", opponent, count))
            if len([call for call in calls if call[0] == "accept"]) == 2:
                raise KeyboardInterrupt

    monkeypatch.setattr(test_bot, "SmartAggroBot", FakeBot)
    monkeypatch.setattr(test_bot, "list_available_challengers", lambda: ["TESTER"])
    monkeypatch.setattr(
        test_bot, "load_random_team_from_challenger",
        lambda trainer, team_file=None: calls.append(("team", trainer, team_file)) or "team",
    )
    monkeypatch.setattr("builtins.input", lambda _: "TESTER")
    monkeypatch.setenv("PS_BOT_USERNAME", "GymBot")
    monkeypatch.setenv("PS_BOT_PASSWORD", "dummy-password")
    monkeypatch.setattr(
        sys, "argv",
        ["test_bot.py", "--server", "showdown", "--format-profile", "national-dex-doubles",
         "--team-file", "gym.txt", "--max-challenges", "0"],
    )

    try:
        asyncio.run(test_bot.main())
    except KeyboardInterrupt:
        pass

    assert ("team", "TESTER", "gym.txt") in calls
    init = next(call[1] for call in calls if call[0] == "init")
    assert init["server_configuration"] == ShowdownServerConfiguration
    assert init["account_configuration"].username == "GymBot"
    assert init["battle_format"] == "gen9nationaldexdoubles"
    assert [call for call in calls if call[0] == "accept"] == [
        ("accept", None, 1), ("accept", None, 1)
    ]
