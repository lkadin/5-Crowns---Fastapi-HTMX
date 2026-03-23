from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect, Response, Form
import json
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
# from connection_manager import ConnectionManager
from room_manager import RoomManager
from five_crowns import  Action, GameStatus, ActionStatus
import traceback
from loguru import logger
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os

# from starlette.middleware.base import BaseHTTPMiddleware

templates = Jinja2Templates(directory="templates")

app = FastAPI()

# Add this after app = FastAPI() and before other middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "kadinenterprises.com",
        "*.kadinenterprises.com",
        "testserver",
    ],
)


# If using a proxy, also add an HTTP middleware that validates/proxies scheme headers
# and rewrites redirect responses. Using the decorator avoids type-check issues with
# add_middleware for custom BaseHTTPMiddleware subclasses.
@app.middleware("http")
async def https_redirect_middleware(request, call_next):
    # Only enforce HTTPS in production, not on localhost
    if os.getenv("ENV") == "production":
        # Trust the proxy's scheme header
        if request.headers.get("x-forwarded-proto") == "https":
            request.scope["scheme"] = "https"

        response = await call_next(request)

        # If response is a redirect, ensure it uses HTTPS
        if response.status_code in (301, 302, 307, 308):
            location = response.headers.get("location")
            if location and location.startswith("http://"):
                response.headers["location"] = location.replace(
                    "http://", "https://", 1
                )

        return response

    # Development: just pass through
    return await call_next(request)


app.mount("/static", StaticFiles(directory="static"), name="static")

MAXPLAYERS = 7

# Initialize the room manager
room_manager = RoomManager(default_max_players=MAXPLAYERS)

# Legacy support: create a default room for backward compatibility
default_room = room_manager.create_room("Default Game")
game = default_room.game
manager = default_room.manager


@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    """Show room selection or login screen."""
    # Get list of available rooms
    available_rooms = room_manager.list_rooms(joinable_only=True)
    
    return templates.TemplateResponse(
        request,
        "room_select.html",
        {"available_rooms": available_rooms},
    )


@app.post("/create_room", response_class=HTMLResponse)
async def create_room(request: Request, room_name: str = Form(...)):
    """Create a new game room."""
    new_room = room_manager.create_room(room_name)
    return RedirectResponse(f"/room/{new_room.room_id}", status_code=303)


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def room_login(request: Request, room_id: str):
    """Login screen for a specific room."""
    room = room_manager.get_room(room_id)
    
    if not room:
        return templates.TemplateResponse(
            request, "error.html", {"error": "Room not found"}
        )
    
    if room.is_full():
        return templates.TemplateResponse(request, "no_more_players.html")
    
    if room.game.game_status != GameStatus.WAITING:
        return templates.TemplateResponse(request, "game_started.html")

    user_id = room.game.next_user_id()
    return templates.TemplateResponse(
        request,
        "login.html",
        {"user_id": user_id, "room_id": room_id},
    )


@app.get("/room/{room_id}/reset", response_class=HTMLResponse)
async def reset_room(request: Request, room_id: str):
    """Reset a specific room."""
    room = room_manager.get_room(room_id)
    if not room:
        return RedirectResponse("/")
    
    room.game.reset()
    room.manager.active_connections = {}
    room.game.wait()
    return RedirectResponse(f"/room/{room_id}")


@app.get("/room/{room_id}/restart", response_class=HTMLResponse)
async def restart_room(request: Request, room_id: str):
    """Restart a specific room."""
    room = room_manager.get_room(room_id)
    if not room:
        return RedirectResponse("/")
    
    room.game.start_game()
    return templates.TemplateResponse(request, "restart.html", {"room_id": room_id})


@app.get("/hidden_checkbox", response_class=HTMLResponse)
async def hidden_checkbox(request: Request):
    return templates.TemplateResponse(request, "hidden_checkbox.html")


@app.get("/score_card_detail/{room_id}", response_class=HTMLResponse)
async def score_card_detail(request: Request, room_id: str):
    """Get score card details for a specific room."""
    room = room_manager.get_room(room_id)
    if not room:
        return templates.TemplateResponse(
            request, "error.html", {"error": "Room not found"}
        )
    
    # set up list of lists to represent score_card_detail
    player_names = [player.name for player in room.game.players.values()]
    round_scores = list(room.game.score_card.values())[: room.game.round_number - 2]
    score_card_total = room.game.total_score_card()
    return templates.TemplateResponse(
        request,
        "score_card_detail.html",
        {
            "score_card_detail": round_scores,
            "player_names": player_names,
            "score_card_total": score_card_total,
        },
    )


@app.post("/web/{room_id}/{user_id}/{action_name}", response_class=HTMLResponse)
async def get_action_name(request: Request, room_id: str, user_id: str, action_name: str):
    """Handle user action in a specific room."""
    room = room_manager.get_room(room_id)
    if not room:
        return Response(status_code=404, content="Room not found")
    
    logger.debug(f"Room {room_id}, user {user_id}, action {action_name}")
    message = {"message_txt": action_name}
    await process_message(room_id, user_id, message)  # type: ignore


@app.post("/web/{room_id}/{user_id}/", response_class=HTMLResponse)
async def user_login(request: Request, room_id: str, user_id: str, user_name: str = Form(...)):
    """Handle user login in a specific room."""
    room = room_manager.get_room(room_id)
    if not room:
        return templates.TemplateResponse(
            request, "error.html", {"error": "Room not found"}
        )
    
    def refresh():
        if room.game.players.get(user_id):
            if room.game.players[user_id].name == user_name:
                return True

    def already_in_game(
        user_id, user_name
    ):  # if user is logged in with a different ID return True
        for player in room.game.players:
            if (room.game.players[player].name) == user_name and room.game.players[
                player
            ].id != user_id:
                return True

    def already_logged_in(user_id, user_name):  # websocket (user_id) already in use
        if room.manager.active_connections.get(user_id) and not already_in_game(
            user_id, user_name
        ):
            return True

    def game_started():
        if room.game.game_status != GameStatus.WAITING:
            return True

    if refresh():
        logger.debug("refresh")
        # Re-render the main template with current actions after refresh
        player = {"name": "", "coins": 0}
        return templates.TemplateResponse(
            request,
            "htmx_user_generic.html",
            {
                "user_id": user_id,
                "user_name": user_name,
                "room_id": room_id,
                "actions": room.game.actions,
                "game_status": room.game.game_status,
                "turn": room.game.whose_turn_name(),
                "dealer": room.game.whose_dealer_name(),
                "suffix": room.game.get_suffix(),
                "player_names": [],
                "player": player,
            },
        )

    elif already_logged_in(user_id, user_name):
        return templates.TemplateResponse(request, "id_already_in_game.html")

    elif already_in_game(user_id, user_name):
        return templates.TemplateResponse(request, "player_already_in_game.html")

    elif game_started():
        # Show initial deal (player hands) on game_started.html
        from content import Content

        content = Content(room.game, user_id, room_id, room.room_name)
        table_html = content.show_table()
        return templates.TemplateResponse(
            request, "game_started.html", {"table_html": table_html}
        )

    room.game.add_player(user_id, user_name)  # Try to add the player to the game
    # Map user to room
    room_manager.add_user_to_room(user_id, room_id)
    
    player = {"name": "", "coins": 0}
    return templates.TemplateResponse(
        request,
        "htmx_user_generic.html",
        {
            "user_id": user_id,
            "user_name": user_name,
            "room_id": room_id,
            "actions": room.game.actions,
            "game_status": room.game.game_status,
            "turn": room.game.whose_turn_name(),
            "dealer": room.game.whose_dealer_name(),
            "suffix": room.game.get_suffix(),
            "player_names": [],
            "player": player,
            "top_discard": room.game.top_discard(),
        },
    )


@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_chat(websocket: WebSocket, room_id: str, user_id: str):
    """WebSocket connection for a specific room."""
    room = room_manager.get_room(room_id)
    if not room:
        await websocket.close(code=4004, reason="Room not found")
        return
    
    await room.manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data:
                message = json.loads(data)
                await process_message(room_id, user_id, message)  # type: ignore

    except WebSocketDisconnect as e:
        # Normal client disconnect
        if getattr(e, "code", None) == 1001:
            message = {"message_txt": f"{user_id} has disconnected"}
            logger.warning(f"{user_id} has disconnected from room {room_id}")
            await room.manager.disconnect(user_id, websocket)
            await room.manager.broadcast(message, room.game, message_type="all")
        else:
            logger.error(f"WebSocketDisconnect exception = {e}")
            logger.error(traceback.format_exc())
    except Exception as e:
        # Treat any other exception as a disconnect to ensure we clean up correctly
        logger.warning(f"Websocket exception for {user_id} in room {room_id}: {e}")
        message = {"message_txt": f"{user_id} has disconnected"}
        try:
            await room.manager.disconnect(user_id, websocket)
        except Exception:
            pass
        try:
            await room.manager.broadcast(message, room.game, message_type="all")
        except Exception:
            logger.exception("Failed to broadcast disconnect message")


async def process_message(room_id: str, user_id: str, message: dict):
    """Process a message from a user in a specific room."""
    room = room_manager.get_room(room_id)
    if not room:
        logger.error(f"Room {room_id} not found")
        return
    
    logger.debug(
        f"Processing message for user {user_id} in room {room_id}: {message}"
    )
    
    if message.get("action") == "sort_cards":
        room.game.sort_cards(
            user_id, message.get("old_index", ""), message.get("new_index", "")
        )
        await room.manager.broadcast(message, room.game, message_type="all")
    else:
        if message.get("message_txt") and not room.game.exchange_in_progress:
            room.game.set_current_action(message.get("message_txt",""), user_id)
        else:
            message["message_txt"] = ""
        if "Pick_from" in room.game.current_action.name:
            message["message_txt"] = room.game.current_action.name

        if room.game.exchange_in_progress:
            card_to_exchange = message.get("cardnames")
            if isinstance(card_to_exchange, str):
                room.game.card_to_exchange = room.game.get_card_object_from_cardname(card_to_exchange)  # type: ignore
        room.game.process_action(message["message_txt"], user_id)
        await room.manager.broadcast(message, room.game, message_type="all")
        if room.game.is_game_over():
            room.game.process_action(
                Action(
                    "No_action",
                    ActionStatus.DISABLED,
                ),
                user_id,
            )


@app.post("/manual_sort/{room_id}")
async def manual_sort_endpoint(request: Request, room_id: str):
    """Handle manual card sorting in a specific room."""
    room = room_manager.get_room(room_id)
    if not room:
        return Response(status_code=404, content="Room not found")
    
    try:
        data = await request.json()
        logger.debug(f"Received manual sort request for room {room_id}: {data}")

        user_id = data.get("user_id")
        new_order = data.get("newOrder", [])
        old_index = data.get("old_index")
        new_index = data.get("new_index")

        if not user_id or not new_order:
            logger.error(f"Missing data - user_id: {user_id}, new_order: {new_order}")
            return Response(status_code=400, content="Missing user_id or newOrder")

        room.game.sort_cards(user_id, old_index, new_index)
        message = {}
        message["message_txt"] = ""
        ding = room.game.ding
        room.game.ding = False  # Don't ding during manual sort
        await room.manager.broadcast(message, room.game, message_type="all")
        room.game.ding = ding
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error in manual_sort for room {room_id}: {str(e)}")
        return Response(status_code=500, content=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
