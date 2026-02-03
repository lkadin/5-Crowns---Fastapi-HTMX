from five_crowns import SUIT
def test_init(card):
    assert card.suit == SUIT.SPADE
    assert card.rank == 3

    for card in deck.cards:
        assert card.suit in ["heart", "spade", "club", "diamond", "star","joker"]
