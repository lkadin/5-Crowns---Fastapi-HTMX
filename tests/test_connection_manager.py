import pytest

from connection_manager import ConnectionManager
from five_crowns import Game


class DummyWebSocket:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.sent = []

    async def send_text(self, text):
        if self.should_fail:
            raise Exception("send failed")
        self.sent.append(text)

    async def accept(self):
        return None


class FakeContent:
    def __init__(self, game, user_id):
        pass

    def show_game_alert(self):
        return "game_alert"

    def show_player_alert(self, uid):
        return "player_alert"

    def show_table(self):
        return "table"

    def show_discard(self):
        return "discard"

    def show_out_cards(self):
        return "out"

    def show_score_card(self):
        return "score"

    def show_turn(self):
        return "turn"

    def show_actions(self):
        return "actions"

    def show_logins(self):
        return "logins"


@pytest.mark.asyncio
async def test_broadcast_removes_dead(monkeypatch):
    game = Game()
    manager = ConnectionManager(game)

    # Patch the Content used inside ConnectionManager
    monkeypatch.setattr("connection_manager.Content", FakeContent)

    manager.active_connections = {"good": DummyWebSocket(False), "bad": DummyWebSocket(True)}

    # No exception should bubble up; 'bad' should be removed
    await manager.broadcast({}, game, message_type="all")

    assert "bad" not in manager.active_connections
    assert "good" in manager.active_connections


@pytest.mark.asyncio
async def test_disconnect_no_error_if_missing():
    game = Game()
    manager = ConnectionManager(game)

    # Should not raise even if user is not connected
    await manager.disconnect("missing_user", None)
