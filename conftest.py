import pytest
from five_crowns import Card
from five_crowns import Deck
from five_crowns import Player
from five_crowns import Game
from five_crowns import Action
from content import Content


@pytest.fixture
def player():
    return Player("1", "Lee")


@pytest.fixture
def action():
    return Action("Start",  "enabled",)


@pytest.fixture
def card():
    return Card("spade",3)


@pytest.fixture
def deck():
    return Deck()


@pytest.fixture
def game():
    return Game()


@pytest.fixture
def ids():
    # ids = [("1", "Lee"), ("2", "Adina"), ("3", "Joey"), ("9", "Jamie")]
    ids = [("1", "Lee"), ("2", "Adina")]
    return ids


@pytest.fixture
def game_ready(game, ids):
    game.deck = Deck()
    for player_id, player_name in ids:
        game.players[player_id] = Player(player_id, player_name)
    game.start()
    game.user_id = "1"
    return game


@pytest.fixture
def content(game_ready):
    return Content(game_ready, "1")
