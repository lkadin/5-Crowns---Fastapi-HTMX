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


def test_show_discard(content):
    assert len(content.show_discard()) > 10

def test_show_out_cards(content):
    assert len(content.show_out_cards()) > 10

def test_show_score_card(content):
    assert len(content.show_score_card()) > 10

def test_show_player_alert(content):
    assert len(content.show_player_alert("1")) > 10
    assert len(content.show_player_alert("92")) > 10

