import pytest
from five_crowns import Card


def test_init(player):
    assert player.id == "1"
    assert player.hand == []


def test_draw(player, deck):
    player.draw(deck)
    assert player.hand[0].suit == "heart"
    assert player.hand[0].rank ==  3


def test_discard(player, deck):
    player.hand = [Card("heart",3), Card("spade",13), Card("joker",99), Card("star",7)]
    player.discard(player.hand[0], deck)
    assert len(player.hand) == 3


# def test_play_card(player):
#     player.hand = [Card("contessa"), Card("duke")]
#     played_card = player.play_card()
#     assert played_card.value == "duke"
#     assert player.hand[0].value == "contessa"


def test_get_index(player):
    player.hand = [Card("spade",3), Card("star",5)]
    card = Card("spade",3)
    assert player.get_index(card) == 0
    card = Card("star",5)
    assert player.get_index(card) == 1
    card = None
    with pytest.raises(Exception):
        player.get_index(card)




def test_repr(player):
    player.hand = ["contessa", "duke"]
    assert repr(player) == "1-['contessa', 'duke'] "

def test_player_alert_set_and_clear(player):
    # Test initial state
    assert player.player_alert == ""
    
    # Test setting an alert
    test_message = "It's your turn!"
    player.set_player_alert(test_message)
    assert player.player_alert == test_message
    
    # Test clearing the alert
    player.clear_player_alert()
    assert player.player_alert == ""
    
    # Test setting empty alert is same as clearing
    player.set_player_alert("")
    assert player.player_alert == ""
    
    # Test setting None alert is same as clearing
    player.set_player_alert(None)
    assert player.player_alert == ""

def test_player_alert_multiple_messages(player):
    # Test setting multiple messages in sequence
    messages = [
        "First alert",
        "Second alert",
        "Third alert"
    ]
    
    for message in messages:
        player.set_player_alert(message)
        assert player.player_alert == message
