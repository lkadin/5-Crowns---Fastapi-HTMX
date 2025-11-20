import pytest
from five_crowns import Card,SUIT


def test_init(player):
    assert player.id == "1"
    assert player.hand == []


def test_draw(player, deck):
    player.draw(deck)
    assert player.hand[0].suit == SUIT.HEART
    assert player.hand[0].rank ==  3


def test_discard(player, deck):
    player.hand = [Card(SUIT.HEART,3), Card(SUIT.SPADE,13), Card(SUIT.JOKER,99), Card(SUIT.STAR,7)]
    player.discard(player.hand[0], deck)
    assert len(player.hand) == 3


def test_get_index(player):
    player.hand = [Card(SUIT.SPADE,3), Card(SUIT.STAR,5)]
    card = Card(SUIT.SPADE,3)
    assert player.get_index(card) == 0
    card = Card(SUIT.STAR,5)
    assert player.get_index(card) == 1
    card = None
    with pytest.raises(Exception):
        player.get_index(card)


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
    player.hand=[Card(SUIT.HEART,5),Card(SUIT.HEART,6),Card(SUIT.HEART,7)]
    score=player.score_hand(3).get("score")
    assert score==0
    player.hand=[Card(SUIT.HEART,5),Card(SUIT.HEART,3),Card(SUIT.HEART,4)]
    score=player.score_hand(3).get("score")
    assert score==0
    player.hand=[Card(SUIT.HEART,7),Card(SUIT.JOKER,99),Card(SUIT.CLUB,3)]
    score=player.score_hand(3).get("score")
    assert score==0
    player.hand=[Card(SUIT.HEART,13),Card(SUIT.HEART,3),Card(SUIT.HEART,4)]
    score=player.score_hand(3)
    assert score.get("score")==20
    player.hand=[Card(SUIT.JOKER,99),Card(SUIT.HEART,3),Card(SUIT.HEART,4)]
    score=player.score_hand(3)
    assert score.get("score")==0
    player.hand=[Card(SUIT.SPADE,5),Card(SUIT.HEART,3),Card(SUIT.SPADE,4)]
    score=player.score_hand(3)
    assert score.get("score")==0
    player.hand=[Card(SUIT.SPADE,6),Card(SUIT.HEART,4),Card(SUIT.SPADE,3),Card(SUIT.SPADE,5)]
    score=player.score_hand(4)
    assert score.get("score")==0
    player.hand=[Card(SUIT.DIAMOND,5),Card(SUIT.CLUB,5),Card(SUIT.STAR,5),Card(SUIT.SPADE,5)]
    score=player.score_hand(4)
    assert score.get("score")==0
    player.hand=[Card(SUIT.DIAMOND,4),Card(SUIT.CLUB,6),Card(SUIT.STAR,6),Card(SUIT.JOKER,99)]
    score=player.score_hand(4)
    assert score.get("score")==0
    player.hand=[Card(SUIT.JOKER,99),Card(SUIT.SPADE,11),Card(SUIT.SPADE,10),Card(SUIT.HEART,4)]
    score=player.score_hand(4)
    assert score.get("score")==0
    player.hand=[Card(SUIT.STAR,7),Card(SUIT.HEART,7),Card(SUIT.HEART,7),Card(SUIT.SPADE,3)]
    score=player.score_hand(4)
    assert score.get("score")==3

def test_auto_sort_hand(player):
    player.hand=[Card(SUIT.STAR,7),Card(SUIT.SPADE,3),Card(SUIT.HEART,7),Card(SUIT.HEART,7)]
    player.auto_sort_hand(4)
    assert player.hand[0] == Card(SUIT.STAR, 7)
    assert player.hand[1] == Card(SUIT.HEART, 7)
    assert player.hand[2] == Card(SUIT.HEART, 7)
    assert player.hand[3] == Card(SUIT.SPADE, 3)