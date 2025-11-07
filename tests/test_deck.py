def test_init(deck):
    assert len(deck.cards) == 116  # 5 roles, each with 3 copies
    assert sum(1 for card in deck.cards if "spade" in card.suit.lower())==22
    assert sum(1 for card in deck.cards if "heart" in card.suit.lower())==22
    assert sum(1 for card in deck.cards if "diamond" in card.suit.lower())==22
    assert sum(1 for card in deck.cards if "club" in card.suit.lower())==22
    assert sum(1 for card in deck.cards if "star" in card.suit.lower())==22
    assert sum(1 for card in deck.cards if "joker" in card.suit.lower())==6

def test_shuffle(deck):
    original_order = deck.cards[:]
    deck.shuffle()
    assert deck.cards != original_order  # Cards should be shuffled


def test_draw(deck):
    num_cards_before_draw = len(deck.cards)
    drawn_card = deck.draw()
    assert len(deck.cards) == num_cards_before_draw - 1  # One card should be drawn
    assert drawn_card.suit.lower() in ["spade", "heart", "club", "diamond", "star"]
    assert drawn_card.rank in range(3,14)


def test_repr(deck):
    assert (
        repr(deck)
        == "3heart 4heart 5heart 6heart 7heart 8heart 9heart 10heart 11heart 12heart 13heart 3spade 4spade 5spade 6spade 7spade 8spade 9spade 10spade 11spade 12spade 13spade 3club 4club 5club 6club 7club 8club 9club 10club 11club 12club 13club 3diamond 4diamond 5diamond 6diamond 7diamond 8diamond 9diamond 10diamond 11diamond 12diamond 13diamond 3star 4star 5star 6star 7star 8star 9star 10star 11star 12star 13star 99joker 99joker 99joker 3heart 4heart 5heart 6heart 7heart 8heart 9heart 10heart 11heart 12heart 13heart 3spade 4spade 5spade 6spade 7spade 8spade 9spade 10spade 11spade 12spade 13spade 3club 4club 5club 6club 7club 8club 9club 10club 11club 12club 13club 3diamond 4diamond 5diamond 6diamond 7diamond 8diamond 9diamond 10diamond 11diamond 12diamond 13diamond 3star 4star 5star 6star 7star 8star 9star 10star 11star 12star 13star 99joker 99joker 99joker"
    )


# def test_return_to_deck(deck):
#     cardname = "contessa"
#     deck_length = len(deck.cards)
#     deck.return_to_deck(cardname)
#     assert len(deck.cards) == deck_length + 1
