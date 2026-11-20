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
    # Create mock room with necessary attributes
    room_id = "test-room-id"
    room_mock = MagicMock()
    room_mock.room_id = room_id
    room_mock.game = game_mock
    room_mock.manager = manager_mock
    
    # Create a mock room_manager that returns our mock room
    mock_room_manager = MagicMock()
    mock_room_manager.get_room = MagicMock(return_value=room_mock)
    
    with patch("app.room_manager", mock_room_manager):
        await process_message(room_id, user_id, message)

        # Add assertions to validate the behavior of process_message
        # assert game_mock.set_current_action.called
        assert game_mock.process_action.called
        assert manager_mock.broadcast.called

        # game_mock.set_current_action.assert_called_with("Test message", user_id)


@pytest.mark.asyncio
async def test_sort_cards_during_discarding(
    user_id, game_mock, manager_mock
):
    room_id = "test-room-id"
    room_mock = MagicMock()
    room_mock.game = game_mock
    room_mock.manager = manager_mock
    game_mock.exchange_in_progress = True
    game_mock.current_action.name = "Pick_from_deck"
    game_mock.is_game_over.return_value = False

    mock_room_manager = MagicMock()
    mock_room_manager.get_room = MagicMock(return_value=room_mock)

    with patch("app.room_manager", mock_room_manager):
        await process_message(
            room_id, user_id, {"message_txt": "Sort_cards"}
        )
        await process_message(
            room_id, user_id, {"cardnames": "heart-1"}
        )

    game_mock.set_current_action.assert_not_called()
    assert game_mock.process_action.call_args_list[0].args == (
        "Sort_cards",
        user_id,
    )
    assert game_mock.process_action.call_args_list[1].args == (
        "Pick_from_deck",
        user_id,
    )
    assert manager_mock.broadcast.await_count == 2
