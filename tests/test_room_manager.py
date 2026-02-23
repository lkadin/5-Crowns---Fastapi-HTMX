from room_manager import Room, RoomManager
from five_crowns import GameStatus


class TestRoom:
    """Tests for the Room class"""

    def test_room_initialization(self):
        """Test that a room is properly initialized"""
        room = Room("test-room-id", "Test Room", max_players=7)
        assert room.room_id == "test-room-id"
        assert room.room_name == "Test Room"
        assert room.max_players == 7
        assert len(room.game.players) == 0
        assert room.game.game_status == GameStatus.WAITING

    def test_room_default_name(self):
        """Test that room gets a default name if not provided"""
        room = Room("abc123", max_players=7)
        assert "Room abc123" in room.room_name or room.room_name.startswith("Room")

    def test_is_full_empty_room(self):
        """Test is_full returns False for empty room"""
        room = Room("test-room-id", "Test Room")
        assert room.is_full() is False

    def test_is_full_with_players(self):
        """Test is_full when room has players"""
        room = Room("test-room-id", "Test Room", max_players=3)
        room.game.add_player("1", "Player1")
        assert room.is_full() is False
        room.game.add_player("2", "Player2")
        assert room.is_full() is False
        room.game.add_player("3", "Player3")
        assert room.is_full() is True

    def test_can_join_empty_waiting_room(self):
        """Test can_join returns True for empty waiting room"""
        room = Room("test-room-id", "Test Room")
        assert room.can_join() is True

    def test_can_join_full_room(self):
        """Test can_join returns False for full room"""
        room = Room("test-room-id", "Test Room", max_players=2)
        room.game.add_player("1", "Player1")
        room.game.add_player("2", "Player2")
        assert room.can_join() is False

    def test_can_join_in_progress_game(self):
        """Test can_join returns False when game is in progress"""
        room = Room("test-room-id", "Test Room")
        room.game.add_player("1", "Player1")
        room.game.add_player("2", "Player2")
        room.game.start_game()
        assert room.can_join() is False

    def test_get_info(self):
        """Test get_info returns correct room information"""
        room = Room("test-room-id", "Test Room", max_players=7)
        room.game.add_player("1", "Player1")
        info = room.get_info()
        
        assert info["room_id"] == "test-room-id"
        assert info["room_name"] == "Test Room"
        assert info["player_count"] == 1
        assert info["max_players"] == 7
        assert info["game_status"] == GameStatus.WAITING.value
        assert info["can_join"] is True


class TestRoomManager:
    """Tests for the RoomManager class"""

    def test_room_manager_initialization(self):
        """Test that RoomManager initializes correctly"""
        manager = RoomManager(default_max_players=5)
        assert len(manager.rooms) == 0
        assert len(manager.user_to_room) == 0
        assert manager.default_max_players == 5

    def test_create_room(self):
        """Test creating a new room"""
        manager = RoomManager()
        room = manager.create_room("My Room")
        
        assert room is not None
        assert room.room_name == "My Room"
        assert room.room_id in manager.rooms
        assert manager.rooms[room.room_id] == room

    def test_create_multiple_rooms(self):
        """Test creating multiple rooms"""
        manager = RoomManager()
        room1 = manager.create_room("Room 1")
        room2 = manager.create_room("Room 2")
        room3 = manager.create_room("Room 3")
        
        assert len(manager.rooms) == 3
        assert room1.room_id != room2.room_id != room3.room_id
        assert manager.rooms[room1.room_id] == room1
        assert manager.rooms[room2.room_id] == room2
        assert manager.rooms[room3.room_id] == room3

    def test_create_room_with_custom_max_players(self):
        """Test creating a room with custom max_players"""
        manager = RoomManager()
        room = manager.create_room("My Room", max_players=4)
        assert room.max_players == 4

    def test_get_room_existing(self):
        """Test retrieving an existing room"""
        manager = RoomManager()
        created_room = manager.create_room("My Room")
        retrieved_room = manager.get_room(created_room.room_id)
        
        assert retrieved_room is not None
        assert retrieved_room == created_room

    def test_get_room_nonexistent(self):
        """Test retrieving a non-existent room returns None"""
        manager = RoomManager()
        room = manager.get_room("nonexistent-id")
        assert room is None

    def test_delete_room_existing(self):
        """Test deleting an existing room"""
        manager = RoomManager()
        room = manager.create_room("My Room")
        room_id = room.room_id
        
        assert room_id in manager.rooms
        result = manager.delete_room(room_id)
        
        assert result is True
        assert room_id not in manager.rooms

    def test_delete_room_nonexistent(self):
        """Test deleting a non-existent room returns False"""
        manager = RoomManager()
        result = manager.delete_room("nonexistent-id")
        assert result is False

    def test_list_rooms_empty(self):
        """Test listing rooms when none exist"""
        manager = RoomManager()
        rooms = manager.list_rooms()
        assert rooms == []

    def test_list_rooms_joinable_only(self):
        """Test listing only joinable rooms"""
        manager = RoomManager()
        room1 = manager.create_room("Room 1")
        room2 = manager.create_room("Room 2", max_players=1)
        
        # Fill room2
        room2.game.add_player("1", "Player1")
        
        joinable = manager.list_rooms(joinable_only=True)
        all_rooms = manager.list_rooms(joinable_only=False)
        
        assert len(joinable) == 1
        assert len(all_rooms) == 2
        assert room1.get_info() in joinable
        assert room2.get_info() not in joinable

    def test_add_user_to_room(self):
        """Test adding a user to a room"""
        manager = RoomManager()
        room = manager.create_room("My Room")
        
        result = manager.add_user_to_room("user1", room.room_id)
        
        assert result is True
        assert manager.user_to_room["user1"] == room.room_id

    def test_add_user_to_nonexistent_room(self):
        """Test adding a user to a non-existent room returns False"""
        manager = RoomManager()
        result = manager.add_user_to_room("user1", "nonexistent-id")
        assert result is False

    def test_get_user_room(self):
        """Test getting the room a user is in"""
        manager = RoomManager()
        room = manager.create_room("My Room")
        manager.add_user_to_room("user1", room.room_id)
        
        user_room = manager.get_user_room("user1")
        assert user_room == room

    def test_get_user_room_not_in_room(self):
        """Test getting room for user not in any room"""
        manager = RoomManager()
        user_room = manager.get_user_room("user1")
        assert user_room is None

    def test_remove_user_from_room(self):
        """Test removing a user from a room"""
        manager = RoomManager()
        room = manager.create_room("My Room")
        manager.add_user_to_room("user1", room.room_id)
        
        assert "user1" in manager.user_to_room
        result = manager.remove_user_from_room("user1")
        
        assert result is True
        assert "user1" not in manager.user_to_room

    def test_remove_user_not_in_room(self):
        """Test removing a user who is not in any room"""
        manager = RoomManager()
        result = manager.remove_user_from_room("user1")
        assert result is False

    def test_user_switch_rooms(self):
        """Test a user switching from one room to another"""
        manager = RoomManager()
        room1 = manager.create_room("Room 1")
        room2 = manager.create_room("Room 2")
        
        # Add user to room1
        manager.add_user_to_room("user1", room1.room_id)
        assert manager.user_to_room["user1"] == room1.room_id
        
        # Switch user to room2
        manager.add_user_to_room("user1", room2.room_id)
        assert manager.user_to_room["user1"] == room2.room_id

    def test_get_or_create_default_room(self):
        """Test get_or_create_default_room"""
        manager = RoomManager()
        
        # First call should create a default room
        room1 = manager.get_or_create_default_room()
        assert room1 is not None
        assert "Lobby" in room1.room_name
        
        # Second call should return the same room if it's still joinable
        room2 = manager.get_or_create_default_room()
        assert room1.room_id == room2.room_id

    def test_get_or_create_default_room_when_full(self):
        """Test get_or_create_default_room creates new room when existing is full"""
        manager = RoomManager()
        room1 = manager.get_or_create_default_room()
        
        # Fill the room
        for i in range(room1.max_players):
            room1.game.add_player(str(i), f"Player{i}")
        
        # Should create a new room since the first one is full
        room2 = manager.get_or_create_default_room()
        assert room2.room_id != room1.room_id
        assert len(manager.rooms) == 2


class TestMultiRoomIsolation:
    """Tests to verify that games in different rooms don't interfere with each other"""

    def test_games_in_different_rooms_are_independent(self):
        """Test that games in different rooms have independent game state"""
        manager = RoomManager()
        room1 = manager.create_room("Room 1")
        room2 = manager.create_room("Room 2")
        
        # Add players to room1
        room1.game.add_player("user1", "Player1")
        room1.game.add_player("user2", "Player2")
        
        # Add different players to room2
        room2.game.add_player("user3", "Player3")
        room2.game.add_player("user4", "Player4")
        
        # Verify players are isolated
        assert len(room1.game.players) == 2
        assert len(room2.game.players) == 2
        assert "user1" in room1.game.players
        assert "user1" not in room2.game.players
        assert "user3" not in room1.game.players
        assert "user3" in room2.game.players

    def test_game_start_in_one_room_doesnt_affect_another(self):
        """Test that starting a game in one room doesn't affect another"""
        manager = RoomManager()
        room1 = manager.create_room("Room 1")
        room2 = manager.create_room("Room 2")
        
        # Add players and start game in room1
        room1.game.add_player("1", "Player1")
        room1.game.add_player("2", "Player2")
        room1.game.start_game()
        
        # Add players to room2 but don't start
        room2.game.add_player("3", "Player3")
        room2.game.add_player("4", "Player4")
        
        # Verify room2 is still waiting
        assert room1.game.game_status == GameStatus.IN_PROGRESS
        assert room2.game.game_status == GameStatus.WAITING
        assert room2.can_join() is True

    def test_separate_connection_managers_per_room(self):
        """Test that each room has its own ConnectionManager"""
        manager = RoomManager()
        room1 = manager.create_room("Room 1")
        room2 = manager.create_room("Room 2")
        
        assert room1.manager is not room2.manager
        assert room1.manager.room_id == room1.room_id
        assert room2.manager.room_id == room2.room_id
