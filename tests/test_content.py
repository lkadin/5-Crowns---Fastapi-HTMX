def test_show_hand(content, game_ready):
    player = game_ready.player("1")
    game_ready.current_player_index = 0
    game_ready.exchange_in_progress = True
    game_ready.disable_one_action("Sort_cards")
    hand = content.show_hand(player)
    assert len(hand) >= 100
    assert 'class="sort-cards-action"' in hand
    assert 'class="action-button">Sort Cards</button>' in hand
    assert "<button hidden" not in hand
    assert hand.index('class="sort-cards-action"') < hand.index('id="listForSorting"')
    assert """<div class=""" in hand
    player = game_ready.player("2")
    game_ready.exchange_in_progress = True
    assert len(content.show_hand(player)) >= 100
    assert """<div class=""" in content.show_hand(player)


def test_sort_button_hidden_when_disabled_outside_discarding_mode(content, game_ready):
    game_ready.disable_one_action("Sort_cards")

    hand = content.show_hand(game_ready.player("1"))

    assert "<button hidden" in hand


def test_show_table(content):
    table = content.show_table()
    assert len(table) >= 100
    assert """<div hx-swap-oob="innerHTML:#table">""" in table
    assert table.index('id="listForSorting"') < table.index('id="scores"')
    assert table.index('id="scores"') < table.index("Room:")


def test_show_turn(content):
    assert """<div id="turn""" in content.show_turn()


def test_show_alert(content):
    assert len(content.show_game_alert()) > 10


def test_show_actions(content):
    actions = content.show_actions()
    assert len(actions) > 10
    assert 'id="Sort_cards"' not in actions


def test_show_discard(content):
    assert len(content.show_discard()) > 10


def test_show_out_cards(content):
    assert len(content.show_out_cards()) > 10


def test_show_score_card(content):
    assert len(content.show_score_card()) > 10


def test_show_player_alert(content):
    assert len(content.show_player_alert("1")) > 10
    assert len(content.show_player_alert("92")) > 10
