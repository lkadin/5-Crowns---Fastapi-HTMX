import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Assuming the process_message function is in a module named your_module
from app import process_message


@pytest.fixture
def game_mock():
    game = MagicMock()
    game.exchange_in_progress = False
    game.lose_influence_in_progress = False
    game.current_action = MagicMock(name="No_action")
    game.set_current_action = MagicMock()
    game.set_second_player_id = MagicMock()
    game.player_id = MagicMock(return_value="player_id_1")
    game.player_index_to_id = MagicMock(return_value="player_id_1")
    game.players = {"user_id_1": MagicMock(name="Player1")}
    game.whose_turn = MagicMock(return_value=0)
    game.check_coins = MagicMock()
    game.process_action = MagicMock()
    game.game_over = MagicMock(return_value=False)
    return game


@pytest.fixture
def manager_mock():
    manager = MagicMock()
    manager.broadcast = AsyncMock()
    return manager


@pytest.fixture
def websocket_mock():
    return AsyncMock()


@pytest.fixture
def user_id():
    return "user_id_1"


@pytest.fixture
def message():
    return {
        "message_txt": "Test message",
        "player": "player1",
        "cardnames": ["Duke", "Captain"],
    }


@pytest.mark.asyncio
async def test_process_message(
    websocket_mock, user_id, message, game_mock, manager_mock
):
    with patch("app.game", game_mock), patch("app.manager", manager_mock):
        await process_message(user_id, message)

        # Add assertions to validate the behavior of process_message
        # assert game_mock.set_current_action.called
        assert game_mock.process_action.called
        assert manager_mock.broadcast.called

        # game_mock.set_current_action.assert_called_with("Test message", user_id)
