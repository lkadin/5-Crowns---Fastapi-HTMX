import pytest
from five_crowns import Card


def test_init(player):
    assert player.id == "1"
    assert player.hand == []


def test_draw(player, deck):
    player.draw(deck)
    assert player.hand[0].value == "duke"


def test_discard(player, deck):
    player.hand = [Card("contessa"), Card("contessa"), Card("assassin"), Card("duke")]
    player.discard(["duke", "contessa"], deck)
    assert len(player.hand) == 2


# def test_play_card(player):
#     player.hand = [Card("contessa"), Card("duke")]
#     played_card = player.play_card()
#     assert played_card.value == "duke"
#     assert player.hand[0].value == "contessa"


def test_get_index(player):
    player.hand = [Card("contessa"), Card("duke")]
    cardname = "contessa"
    assert player.get_index(cardname) == 0
    cardname = "duke"
    assert player.get_index(cardname) == 1
    cardname = None
    with pytest.raises(Exception):
        player.get_index(cardname)




def test_repr(player):
    player.hand = ["contessa", "duke"]
    assert repr(player) == "1-['contessa', 'duke'] "
