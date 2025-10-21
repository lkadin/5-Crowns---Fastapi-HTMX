def test_init(card,deck):
    assert card.suit == "spade"
    assert card.rank == 3

    for card in deck.cards:
        assert card.suit in ["heart", "spade", "club", "diamond", "star","joker"]
