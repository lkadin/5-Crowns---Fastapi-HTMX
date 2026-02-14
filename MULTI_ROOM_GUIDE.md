# Multi-Room Capabilities Implementation

This document describes the multi-room feature added to the 5 Crowns FastAPI HTMX application.

## Overview

The application has been enhanced to support multiple simultaneous game rooms. Previously, there was only one global game instance. Now, players can create new rooms and join existing ones, allowing multiple independent games to run concurrently on the same server.

## Architecture

### New Components

#### 1. **RoomManager** (`room_manager.py`)
The `RoomManager` class manages all active game rooms:
- **`create_room(room_name: str, max_players: int)`** - Creates a new game room
- **`get_room(room_id: str)`** - Retrieves a room by ID
- **`delete_room(room_id: str)`** - Deletes an empty room
- **`list_rooms(joinable_only: bool)`** - Lists all rooms (optionally filtered)
- **`add_user_to_room(user_id: str, room_id: str)`** - Maps a user to a room
- **`get_user_room(user_id: str)`** - Gets the room a user is in
- **`remove_user_from_room(user_id: str)`** - Removes a user from their room
- **`get_or_create_default_room()`** - Gets or creates a default room for backward compatibility

#### 2. **Room** (`room_manager.py`)
The `Room` class encapsulates a single game:
- Each room has its own `Game` instance
- Each room has its own `ConnectionManager` instance
- Room metadata includes name, player count, max players, and game status

### Modified Components

#### 1. **app.py** - Refactored Routes
All routes have been updated to work with multiple rooms:

- **`GET /`** - Room selection page showing available rooms and option to create new ones
- **`POST /create_room`** - Creates a new room
- **`GET /room/{room_id}`** - Login page for a specific room
- **`GET /room/{room_id}/reset`** - Reset a specific room
- **`GET /room/{room_id}/restart`** - Restart a specific room
- **`POST /web/{room_id}/{user_id}/`** - User login in a specific room
- **`POST /web/{room_id}/{user_id}/{action_name}`** - User action in a specific room
- **`GET /score_card_detail/{room_id}`** - Score card details for a specific room
- **`POST /manual_sort/{room_id}`** - Card sorting in a specific room
- **`WebSocket /ws/{room_id}/{user_id}`** - WebSocket connection for a specific room

#### 2. **Templates** - Updated for Multi-Room

All templates have been updated to include `room_id` in their requests:

- **`room_select.html`** (NEW) - Room listing and creation interface
- **`error.html`** (NEW) - Generic error page
- **`login.html`** - Updated form action to include `room_id`
- **`htmx_user_generic.html`** - Updated WebSocket connection to include `room_id`
- **`actions.html`** - Updated POST requests to include `room_id`
- **`top_discard.html`** - Updated POST requests to include `room_id`
- **`score_card.html`** - Updated GET request to include `room_id`
- **`table.html`** - Updated fetch call to include `room_id`

## Usage

### For Users

1. **Home Page**: Visit `/` to see the room selection page
2. **Create a Room**: Enter a room name and click "Create Room"
3. **Join a Room**: Click "Join Game" next to an available room
4. **Play**: Log in with a username and play the game as normal

### For Developers

#### Creating a Room Programmatically

```python
# Create a new room
room = room_manager.create_room("My Game Room", max_players=7)

# The room is immediately available and players can join
```

#### Getting a Room

```python
room = room_manager.get_room(room_id)
if room:
    # Access the game and manager
    game = room.game
    manager = room.manager
```

#### User-to-Room Mapping

```python
# Map a user to a room
room_manager.add_user_to_room(user_id, room_id)

# Get the room a user is in
room = room_manager.get_user_room(user_id)

# Remove a user from their room
room_manager.remove_user_from_room(user_id)
```

#### Listing Rooms

```python
# Get all joinable rooms
available_rooms = room_manager.list_rooms(joinable_only=True)

# Get all rooms (including in-progress games)
all_rooms = room_manager.list_rooms(joinable_only=False)
```

## Backward Compatibility

For backward compatibility, the application maintains:
- A default room that is created on startup
- Global `game` and `manager` variables pointing to the default room
- These can still be used if needed, though all new functionality uses the `room_manager`

## Data Structure

### Room Information Dictionary
```python
{
    "room_id": "uuid-string",
    "room_name": "My Game",
    "player_count": 3,
    "max_players": 7,
    "game_status": "Waiting",  # or "In progress", "Game_Over", etc.
    "can_join": True  # False if full or game in progress
}
```

## WebSocket Connection

WebSocket connections are now room-aware:
- Old (legacy): `ws://localhost:8000/ws/{user_id}`
- New (multi-room): `ws://localhost:8000/ws/{room_id}/{user_id}`

The WebSocket endpoint automatically validates the room exists before accepting connections.

## Error Handling

- **Room Not Found**: Returns 404 status and displays error page
- **Room Full**: Displays "no_more_players.html"
- **Game In Progress**: Displays "game_started.html"
- **Invalid WebSocket Connection**: Closes connection with code 4004

## Future Enhancements

Potential improvements to consider:
1. Persistent room storage (database)
2. Room password protection
3. Spectator mode
4. Room statistics and leaderboards
5. Automatic room cleanup after game ends
6. Maximum concurrent rooms limit
7. Room search and filtering
8. Chat during games
9. Tournament mode with multiple rounds
10. Replay functionality

## Migration Notes

If you have existing code using the global `game` and `manager` variables:
- They still exist and point to a default room
- New code should use the `room_manager` for full functionality
- The global variables will eventually be deprecated

## Testing

When testing the multi-room functionality:
1. Open multiple browser tabs/windows
2. Create different rooms in each
3. Join the same room in multiple tabs/windows
4. Verify that games in different rooms operate independently
5. Test WebSocket connections with `room_id` parameter

## Security Considerations

- Room IDs are UUIDs (cryptographically secure)
- No authentication is currently implemented (users can join any room)
- For production, consider adding:
  - Room password/authentication
  - User authentication
  - Rate limiting on room creation
  - Room access control lists

## Performance Notes

- Each room maintains its own game state and connections
- Multiple concurrent games may impact server performance
- Memory usage scales with number of active rooms and players
- Consider database persistence for production deployments
