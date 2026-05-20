def test_legacy_bot_logic_import_matches_package_export():
    from bot_logic import DoublesMvpBot as LegacyBot
    from draftleaguebot import DoublesMvpBot as PackageBot
    from draftleaguebot.bot import DoublesMvpBot as ModuleBot

    assert LegacyBot is PackageBot
    assert PackageBot is ModuleBot
