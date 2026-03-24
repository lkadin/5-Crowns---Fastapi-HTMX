# from fastapi import WebSocket, WebSocketDisconnect
from five_crowns import Game, GameStatus
from connection_manager import ConnectionManager
from loguru import logger
import uuid


class Room:
    """Represents a single game room with its own game instance and connections."""
    
    def __init__(self, room_id: str, room_name: str = "", max_players: int = 7, creator_email: str = ""):
        self.room_id = room_id
        self.room_name = room_name or f"Room {room_id[:8]}"
        self.game = Game()
        self.manager = ConnectionManager(self.game, room_id, self.room_name)
        self.max_players = max_players
        self.created_at = None
        self.creator_email = creator_email
        self.game.wait()
    
    def is_full(self) -> bool:
        """Check if room has reached max players."""
        return len(self.game.players) >= self.max_players
    
    def can_join(self) -> bool:
        """Check if a player can join the room."""
        return (
            not self.is_full() and
            self.game.game_status == GameStatus.WAITING
        )
    
    def get_info(self) -> dict:
        """Get room information."""
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "player_count": len(self.game.players),
            "max_players": self.max_players,
            "game_status": self.game.game_status.value,
            "can_join": self.can_join(),
        }


class RoomManager:
    """Manages multiple game rooms."""
    
    def __init__(self, default_max_players: int = 7):
        self.rooms: dict[str, Room] = {}
        self.default_max_players = default_max_players
        self.user_to_room: dict[str, str] = {}  # Maps user_id to room_id
    
    def create_room(self, room_name: str = "", max_players: int | None = None, creator_email: str = "") -> Room:
        """Create a new room."""
        room_id = str(uuid.uuid4())
        max_p = max_players or self.default_max_players
        room = Room(room_id, room_name, max_p, creator_email)
        self.rooms[room_id] = room
        logger.info(f"Created room {room_id} ({room_name})")
        return room
    
    def get_room(self, room_id: str) -> Room | None:
        """Get a room by ID."""
        return self.rooms.get(room_id)
    
    def delete_room(self, room_id: str) -> bool:
        """Delete a room (typically when empty or game ends)."""
        if room_id in self.rooms:
            # Remove all user mappings for this room
            users_in_room = [uid for uid, rid in self.user_to_room.items() if rid == room_id]
            for user_id in users_in_room:
                del self.user_to_room[user_id]
            
            del self.rooms[room_id]
            logger.info(f"Deleted room {room_id}")
            return True
        return False
    
    def list_rooms(self, joinable_only: bool = True) -> list[dict]:
        """List all rooms (optionally only joinable ones)."""
        rooms_list = []
        for room in self.rooms.values():
            if joinable_only and not room.can_join():
                continue
            rooms_list.append(room.get_info())
        return rooms_list
    
    def add_user_to_room(self, user_id: str, room_id: str) -> bool:
        """Map a user to a room."""
        if room_id not in self.rooms:
            return False
        
        # If user is already in another room, remove them from it
        if user_id in self.user_to_room:
            old_room_id = self.user_to_room[user_id]
            # Optionally clean up empty rooms
            if old_room_id in self.rooms and len(self.rooms[old_room_id].game.players) == 0:
                self.delete_room(old_room_id)
        
        self.user_to_room[user_id] = room_id
        logger.info(f"User {user_id} joined room {room_id}")
        return True
    
    def get_user_room(self, user_id: str) -> Room | None:
        """Get the room a user is in."""
        room_id = self.user_to_room.get(user_id)
        if room_id:
            return self.rooms.get(room_id)
        return None
    
    def remove_user_from_room(self, user_id: str) -> bool:
        """Remove a user from their room."""
        if user_id not in self.user_to_room:
            return False
        
        room_id = self.user_to_room[user_id]
        del self.user_to_room[user_id]
        
        # Clean up empty rooms
        if room_id in self.rooms and len(self.rooms[room_id].game.players) == 0:
            self.delete_room(room_id)
        
        logger.info(f"User {user_id} removed from room {room_id}")
        return True
    
    def get_or_create_default_room(self) -> Room:
        """Get or create a default room for backward compatibility."""
        # Look for an existing joinable default room
        for room in self.rooms.values():
            if room.room_name.startswith("Lobby") and room.can_join():
                return room
        
        # Create a new default room
        room = self.create_room("Lobby")
        return room
