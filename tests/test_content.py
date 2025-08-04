def test_show_hand(content, game_ready):
    player = game_ready.player("1")
    assert len(content.show_hand(player)) >= 100
    assert """<div class=""" in content.show_hand(player)


def test_show_table(content):
    assert len(content.show_table()) >= 100
    assert """<div hx-swap-oob="innerHTML:#table">""" in content.show_table()


def test_show_turn(content):
    assert """<div id="turn""" in content.show_turn()


def test_show_alert(content):
    assert len(content.show_game_alert()) > 10



def test_show_actions(content):
    assert len(content.show_actions()) > 10
