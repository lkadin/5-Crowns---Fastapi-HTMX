# Multi-Room API Reference

## HTTP Routes

### Room Management

#### `GET /`
**Description:** Display room selection and creation page  
**Returns:** HTML page with list of available rooms  
**Parameters:** None  
**Example:** `GET http://localhost:8000/`

#### `POST /create_room`
**Description:** Create a new game room  
**Parameters:** 
- `room_name` (form data, required) - Name for the new room  
**Returns:** Redirect to `/room/{room_id}`  
**Example:** `POST http://localhost:8000/create_room` with body `room_name=My Game`

#### `GET /room/{room_id}`
**Description:** Display login page for a specific room  
**Parameters:**
- `room_id` (path, required) - UUID of the room  
**Returns:** Login form or error if room not found/full  
**Status Codes:**
- `200` - Success, show login form
- `404` - Room not found (shows error page)  
**Example:** `GET http://localhost:8000/room/550e8400-e29b-41d4-a716-446655440000`

#### `GET /room/{room_id}/reset`
**Description:** Reset a room (clear players and game state)  
**Parameters:**
- `room_id` (path, required) - UUID of the room  
**Returns:** Redirect to `/room/{room_id}`  
**Example:** `GET http://localhost:8000/room/550e8400-e29b-41d4-a716-446655440000/reset`

#### `GET /room/{room_id}/restart`
**Description:** Restart a room after game ends  
**Parameters:**
- `room_id` (path, required) - UUID of the room  
**Returns:** Restart confirmation page  
**Example:** `GET http://localhost:8000/room/550e8400-e29b-41d4-a716-446655440000/restart`

### User Management

#### `POST /web/{room_id}/{user_id}/`
**Description:** User login to a specific room  
**Parameters:**
- `room_id` (path, required) - UUID of the room
- `user_id` (path, required) - User's ID
- `user_name` (form data, required) - Player's name  
**Returns:** Game page or error  
**Status Codes:**
- `200` - Success, user logged in
- `404` - Room not found  
**Example:** `POST http://localhost:8000/web/550e8400-e29b-41d4-a716-446655440000/user123/` with body `user_name=Alice`

#### `POST /web/{room_id}/{user_id}/{action_name}`
**Description:** Process a player action in a room  
**Parameters:**
- `room_id` (path, required) - UUID of the room
- `user_id` (path, required) - User's ID
- `action_name` (path, required) - Action name (e.g., "Draw", "Discard")  
**Returns:** Updated game state  
**Status Codes:**
- `200` - Success
- `404` - Room not found  
**Example:** `POST http://localhost:8000/web/550e8400-e29b-41d4-a716-446655440000/user123/Draw`

### Game State

#### `GET /score_card_detail/{room_id}`
**Description:** Get detailed score card for a room  
**Parameters:**
- `room_id` (path, required) - UUID of the room  
**Returns:** HTML table with score details  
**Status Codes:**
- `200` - Success
- `404` - Room not found  
**Example:** `GET http://localhost:8000/score_card_detail/550e8400-e29b-41d4-a716-446655440000`

#### `POST /manual_sort/{room_id}`
**Description:** Handle manual card sorting  
**Parameters:**
- `room_id` (path, required) - UUID of the room
- Body (JSON):
  ```json
  {
    "user_id": "user123",
    "newOrder": [...],
    "old_index": 2,
    "new_index": 5
  }
  ```
**Returns:** `{"status": "success"}`  
**Status Codes:**
- `200` - Success
- `400` - Missing required data
- `404` - Room not found
- `500` - Server error  
**Example:** 
```
POST http://localhost:8000/manual_sort/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "user_id": "user123",
  "newOrder": ["card1", "card2", ...],
  "old_index": 2,
  "new_index": 5
}
```

### WebSocket

#### `WebSocket /ws/{room_id}/{user_id}`
**Description:** WebSocket connection for real-time game updates  
**Connection String:** `ws://localhost:8000/ws/{room_id}/{user_id}`  
**Message Format (JSON):**
```json
{
  "message_txt": "action_name",
  "action": "optional_action_type"
}
```
**Returns:** Real-time game updates sent to all players in the room  
**Connection Codes:**
- `1001` - Normal disconnect
- `4004` - Room not found  
**Example:**
```javascript
const socket = new WebSocket(
  'ws://localhost:8000/ws/550e8400-e29b-41d4-a716-446655440000/user123'
);

socket.onmessage = (event) => {
  console.log('Game update:', event.data);
};
```

### Utility

#### `GET /hidden_checkbox`
**Description:** Utility endpoint  
**Returns:** HTML content  
**Example:** `GET http://localhost:8000/hidden_checkbox`

## Error Responses

### 404 Not Found
Returned when room doesn't exist.
```html
Error: Room not found
```

### 400 Bad Request
Returned when required parameters are missing.
```
Missing user_id or newOrder
```

### 500 Internal Server Error
Returned on server errors.
```
Error message details
```

## Data Models

### Room Information
```python
{
    "room_id": "550e8400-e29b-41d4-a716-446655440000",
    "room_name": "My Game Room",
    "player_count": 3,
    "max_players": 7,
    "game_status": "Waiting",  # or "In progress", "Game_Over"
    "can_join": True
}
```

### Player Object
```python
{
    "id": "user_id",
    "name": "Player Name",
    "total_score": 45,
    "hand": [...]  # List of Card objects
}
```

## Common Use Cases

### Join a Game
1. `GET /` - See available rooms
2. `POST /create_room` or select existing room
3. `GET /room/{room_id}` - Go to login page
4. `POST /web/{room_id}/{user_id}/` - Log in
5. `WebSocket /ws/{room_id}/{user_id}` - Connect for real-time updates

### Play the Game
1. User makes action: `POST /web/{room_id}/{user_id}/ActionName`
2. Server updates game state
3. WebSocket sends update to all players
4. UI updates with new state

### Sort Cards
1. User drags cards in UI
2. `POST /manual_sort/{room_id}` - Send new order
3. Server updates player's hand
4. WebSocket notifies all players

## Rate Limiting Recommendations

For production, consider implementing:
- Max 10 room creations per IP per hour
- Max 100 messages per user per minute
- Max 1000 active rooms per server
- Connection timeouts after 30 minutes inactivity

## Security Notes

- Room IDs are UUIDs (cryptographically random)
- No built-in authentication (add if needed)
- WebSocket connections not encrypted (use WSS in production)
- Consider CORS headers for cross-origin requests
- Implement rate limiting to prevent abuse
