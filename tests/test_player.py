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

def test_score_hand(player):
    player.hand=[Card("heart",5),Card("heart",6),Card("heart",7)]
    score=player.score_hand(3).get("score")
    assert score==0
    player.hand=[Card("heart",5),Card("heart",3),Card("heart",4)]
    score=player.score_hand(3).get("score")
    assert score==0
    player.hand=[Card("heart",7),Card("joker",99),Card("club",3)]
    score=player.score_hand(3).get("score")
    assert score==0
    player.hand=[Card("heart",13),Card("heart",3),Card("heart",4)]
    score=player.score_hand(3)
    assert score.get("score")==20
    player.hand=[Card("joker",99),Card("heart",3),Card("heart",4)]
    score=player.score_hand(3)
    assert score.get("score")==0
    player.hand=[Card("spade",5),Card("heart",3),Card("spade",4)]
    score=player.score_hand(3)
    assert score.get("score")==0
    player.hand=[Card("spade",6),Card("heart",4),Card("spade",3),Card("spade",5)]
    score=player.score_hand(4)
    assert score.get("score")==0
    player.hand=[Card("diamond",5),Card("club",5),Card("star",5),Card("spade",5)]
    score=player.score_hand(4)
    assert score.get("score")==0
    player.hand=[Card("diamond",4),Card("club",6),Card("star",6),Card("joker",99)]
    score=player.score_hand(4)
    assert score.get("score")==0
    player.hand=[Card("joker",99),Card("spade",11),Card("spade",10),Card("heart",4)]
    score=player.score_hand(4)
    assert score.get("score")==0
