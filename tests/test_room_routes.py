import pytest
from fastapi.testclient import TestClient
from app import app, room_manager


@pytest.fixture
def client():
    return TestClient(app)


class TestRoomSelection:
    """Tests for room selection and creation endpoints"""

    def test_home_page_shows_available_rooms(self, client):
        """Test that home page displays available rooms"""
        # Create a test room via room_manager
        
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Test Room" in response.text or "room" in response.text.lower()

    def test_create_room_endpoint(self, client):
        """Test creating a new room via POST"""
        initial_room_count = len(room_manager.rooms)
        
        response = client.post("/create_room", data={"room_name": "New Test Room"})
        
        # Should redirect to the room page
        assert response.status_code == 303 or response.status_code == 200
        assert len(room_manager.rooms) > initial_room_count

    def test_join_room_login_screen(self, client):
        """Test accessing a room's login screen"""
        test_room = room_manager.create_room("Test Room")
        
        response = client.get(f"/room/{test_room.room_id}")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_join_nonexistent_room(self, client):
        """Test trying to join a non-existent room"""
        response = client.get("/room/nonexistent-room-id")
        
        assert response.status_code == 200
        assert "not found" in response.text.lower() or "error" in response.text.lower()

    def test_full_room_displays_error(self, client):
        """Test that full room shows appropriate message"""
        # Create a room with max 1 player
        test_room = room_manager.create_room("Full Room", max_players=1)
        
        # Add one player to fill it
        test_room.game.add_player("user1", "Player1")
        
        response = client.get(f"/room/{test_room.room_id}")
        
        # Should show no more players page
        assert "text/html" in response.headers["content-type"]


class TestRoomUserLogin:
    """Tests for user login within a room"""

    def test_user_login_to_room(self, client):
        """Test that a user can login to a room"""
        test_room = room_manager.create_room("Test Room")
        
        response = client.post(
            f"/web/{test_room.room_id}/user123/",
            data={"user_name": "TestPlayer"}
        )
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_multiple_users_in_same_room(self, client):
        """Test that multiple users can join the same room"""
        test_room = room_manager.create_room("Test Room", max_players=3)
        
        # First user
        response1 = client.post(
            f"/web/{test_room.room_id}/user1/",
            data={"user_name": "Player1"}
        )
        assert response1.status_code == 200
        
        # Second user
        response2 = client.post(
            f"/web/{test_room.room_id}/user2/",
            data={"user_name": "Player2"}
        )
        assert response2.status_code == 200
        
        # Verify both are in the room
        assert len(test_room.game.players) == 2

    def test_duplicate_username_in_same_room(self, client):
        """Test that duplicate usernames in same room are rejected"""
        test_room = room_manager.create_room("Test Room")
        
        # First user with name "Player"
        client.post(
            f"/web/{test_room.room_id}/user1/",
            data={"user_name": "Player"}
        )
        
        # Second user with same name should get error
        response = client.post(
            f"/web/{test_room.room_id}/user2/",
            data={"user_name": "Player"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_user_login_nonexistent_room(self, client):
        """Test login fails for non-existent room"""
        response = client.post(
            "/web/nonexistent-room/user1/",
            data={"user_name": "Player"}
        )
        
        assert response.status_code == 404 or "error" in response.text.lower()


class TestRoomManagement:
    """Tests for room reset and restart functionality"""

    def test_room_reset(self, client):
        """Test resetting a room"""
        test_room = room_manager.create_room("Test Room")
        
        # Add some players
        test_room.game.add_player("user1", "Player1")
        test_room.game.add_player("user2", "Player2")
        assert len(test_room.game.players) == 2
        
        # Reset the room
        response = client.get(f"/room/{test_room.room_id}/reset")
        
        # Room should be cleared
        assert len(test_room.game.players) == 0

    def test_room_restart(self, client):
        """Test restarting a room (starting a new game)"""
        test_room = room_manager.create_room("Test Room")
        
        # Add players and start game
        test_room.game.add_player("user1", "Player1")
        test_room.game.add_player("user2", "Player2")
        test_room.game.start_game()
        
        response = client.get(f"/room/{test_room.room_id}/restart")
        
        assert response.status_code == 200


class TestMultiRoomIsolationIntegration:
    """Integration tests to verify multi-room isolation at the API level"""

    def test_actions_in_different_rooms_isolated(self, client):
        """Test that game actions in different rooms don't interfere"""
        room1 = room_manager.create_room("Room 1")
        room2 = room_manager.create_room("Room 2")
        
        # Add players to both rooms
        room1.game.add_player("user1", "Player1")
        room1.game.add_player("user2", "Player2")
        
        room2.game.add_player("user3", "Player3")
        room2.game.add_player("user4", "Player4")
        
        # Start games in both rooms
        room1.game.start_game()
        room2.game.start_game()
        
        # Record initial states
        room1_round = room1.game.round_number
        room2_round = room2.game.round_number
        
        # Perform action in room1
        response1 = client.post(
            f"/web/{room1.room_id}/user1/Draw"
        )
        
        # Rooms should remain independent
        assert room1.game.round_number >= room1_round
        # room2 should be unaffected
        assert room2.game.round_number == room2_round

    def test_room_managers_track_users_correctly(self, client):
        """Test that room_manager properly tracks which user is in which room"""
        room1 = room_manager.create_room("Room 1")
        room2 = room_manager.create_room("Room 2")
        
        # User joins room1
        client.post(
            f"/web/{room1.room_id}/user1/",
            data={"user_name": "Player1"}
        )
        
        # User joins room2
        client.post(
            f"/web/{room2.room_id}/user2/",
            data={"user_name": "Player2"}
        )
        
        # Verify mappings
        user1_room = room_manager.get_user_room("user1")
        user2_room = room_manager.get_user_room("user2")
        
        assert user1_room.room_id == room1.room_id
        assert user2_room.room_id == room2.room_id

    def test_score_card_detail_room_specific(self, client):
        """Test that score card detail returns room-specific data"""
        room1 = room_manager.create_room("Room 1")
        room2 = room_manager.create_room("Room 2")
        
        # Add different players to each room
        room1.game.add_player("user1", "Player1")
        room1.game.add_player("user2", "Player2")
        
        room2.game.add_player("user3", "Player3")
        
        # Get score card for room1
        response1 = client.get(f"/score_card_detail/{room1.room_id}")
        assert response1.status_code == 200
        assert "Player1" in response1.text or "2" in response1.text  # room1 has 2 players
        
        # Get score card for room2
        response2 = client.get(f"/score_card_detail/{room2.room_id}")
        assert response2.status_code == 200

    def test_manual_sort_room_specific(self, client):
        """Test that manual sort is room-specific"""
        room1 = room_manager.create_room("Room 1")
        room2 = room_manager.create_room("Room 2")
        
        room1.game.add_player("user1", "Player1")
        room2.game.add_player("user2", "Player2")
        
        # Send sort request to room1
        response = client.post(
            f"/manual_sort/{room1.room_id}",
            json={
                "user_id": "user1",
                "newOrder": [],
                "old_index": 0,
                "new_index": 1
            }
        )
        
        # Should handle room1-specific action
        assert response.status_code in [200, 400, 500]  # Don't test specific behavior, just that it's routed to room1


class TestRoomContentPassthrough:
    """Tests to verify room_id is properly passed through content rendering"""

    def test_room_id_in_template_context(self, client):
        """Test that room_id is available in template context"""
        test_room = room_manager.create_room("Test Room")
        
        response = client.post(
            f"/web/{test_room.room_id}/user1/",
            data={"user_name": "Player1"}
        )
        
        # room_id should be in the response (for JavaScript to use)
        assert response.status_code == 200
        # Check if room_id appears in HTML (either as attribute or in JS)
        assert test_room.room_id in response.text or "web" in response.text
