from types import SimpleNamespace


def test_should_debug_respects_turn_limit():
    from draftleaguebot import debug

    assert debug.should_debug(True, 3, SimpleNamespace(turn=3)) is True
    assert debug.should_debug(True, 3, SimpleNamespace(turn=4)) is False
    assert debug.should_debug(False, 3, SimpleNamespace(turn=1)) is False


def test_log_final_orders_prints_messages(capsys):
    from draftleaguebot import debug

    debug.log_final_orders([SimpleNamespace(message="/move 1"), SimpleNamespace(message="/move 2")])

    assert capsys.readouterr().out == "[AI DEBUG] final_orders=['/move 1', '/move 2']\n"
