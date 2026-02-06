from five_crowns import SUIT
def test_init(card):
    assert card.suit == SUIT.SPADE
    assert card.rank == 3