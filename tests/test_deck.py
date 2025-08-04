def test_init(deck):
    assert len(deck.cards) == 15  # 5 roles, each with 3 copies
    assert deck.cards.count("duke") == 3
    assert deck.cards.count("assassin") == 3
    assert deck.cards.count("ambassador") == 3
    assert deck.cards.count("captain") == 3
    assert deck.cards.count("contessa") == 3


def test_shuffle(deck):
    original_order = deck.cards[:]
    deck.shuffle()
    assert deck.cards != original_order  # Cards should be shuffled


def test_draw(deck):
    num_cards_before_draw = len(deck.cards)
    drawn_card = deck.draw()
    assert len(deck.cards) == num_cards_before_draw - 1  # One card should be drawn
    assert drawn_card in ["duke", "assassin", "ambassador", "captain", "contessa"]


def test_repr(deck):
    assert repr(deck) == " ".join(deck.cards)


def test_return_to_deck(deck):
    cardname = "contessa"
    deck_length = len(deck.cards)
    deck.return_to_deck(cardname)
    assert len(deck.cards) == deck_length + 1
