from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
import json
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from connection_manager import ConnectionManager
from five_crowns import Game, Action
import traceback
from loguru import logger

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

MAXPLAYERS = 7


def setup_game():
    game = Game()
    manager = ConnectionManager(game)
    game.wait()
    return game, manager


game, manager = setup_game()


@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    if len(game.players) >= MAXPLAYERS:
        return templates.TemplateResponse(request, "no_more_players.html")
    if game.game_status != "Waiting":
        return templates.TemplateResponse(request, "game_started.html")

    user_id = game.next_user_id()
    return templates.TemplateResponse(request, "login.html", {"user_id": user_id})


@app.get("/reset", response_class=HTMLResponse)
async def reset(request: Request):
    user_id = game.next_user_id()
    game.reset()
    manager.active_connections = {}
    game.wait()
    return templates.TemplateResponse(request, "reset.html", {"user_id": user_id})


@app.get("/restart", response_class=HTMLResponse)
async def restart(request: Request):
    game.restart()
    return templates.TemplateResponse(request, "restart.html")


@app.get("/hidden_checkbox", response_class=HTMLResponse)
async def hidden_checkbox(request: Request):
    return templates.TemplateResponse(request, "hidden_checkbox.html")

@app.get("/score_card_detail", response_class=HTMLResponse)
async def score_card_detail(request: Request):
    #set up list of lists to represent score_card_detail
    player_names=[player.name for player in game.players.values()]
    round_scores= list(game.score_card.values())[:game.round_number]
    return templates.TemplateResponse(request, "score_card_detail.html",{"score_card_detail":round_scores,"player_names":player_names})


@app.get("/web/{user_id}/{action_name}", response_class=HTMLResponse)
async def get_action_name(request: Request, user_id: str, action_name: str):
    logger.debug(user_id, action_name)
    message = {"message_txt": action_name}
    await process_message(user_id, message)  # type: ignore
    # await bc(user_id, message)


@app.get("/web/{user_id}/", response_class=HTMLResponse)
async def read_item(request: Request, user_id: str, user_name: str):
    def refresh():
        if game.players.get(user_id):
            if game.players[user_id].name == user_name:
                return True

    def already_in_game(
        user_id, user_name
    ):  # if user is logged in with a different ID return True
        for player in game.players:
            if (game.players[player].name) == user_name and game.players[
                player
            ].id != user_id:
                return True

    def already_logged_in(user_id, user_name):  # websocket (user_id) already in use
        if manager.active_connections.get(user_id) and not already_in_game(
            user_id, user_name
        ):
            return True

    def game_started():
        if game.game_status != "Waiting":
            return True

    if refresh():
        logger.debug("refresh")
        # Re-render the main template with current actions after refresh
        player = {"name": "", "coins": 0}
        return templates.TemplateResponse(request, "htmx_user_generic.html", {
            "user_id": user_id,
            "user_name": user_name,
            "actions": game.actions,
            "game_status": game.game_status,
            "turn": game.whose_turn_name(),
            "suffix": game.get_suffix(),
            "player_names": [],
            "player": player,
        })

    elif already_logged_in(user_id, user_name):
        return templates.TemplateResponse(request, "id_already_in_game.html")

    elif already_in_game(user_id, user_name):
        return templates.TemplateResponse(request, "player_already_in_game.html")

    elif game_started():
        # Show initial deal (player hands) on game_started.html
        from content import Content
        content = Content(game, user_id)
        table_html = content.show_table()
        return templates.TemplateResponse(request, "game_started.html", {"table_html": table_html})

    game.add_player(user_id, user_name)  # Try to add the player to the game
    player = {"name": "", "coins": 0}
    return templates.TemplateResponse(request, "htmx_user_generic.html", {
        "user_id": user_id,
        "user_name": user_name,
        "actions": game.actions,
        "game_status": game.game_status,
        "turn": game.whose_turn_name(),
        "suffix": game.get_suffix(),
        "player_names": [],
        "player": player,
        "top_discard":game.top_discard(),
    })


async def bc(user_id, message, message_type="all"):
    await manager.broadcast(
        f" {game.players[user_id].name}: {message['message_txt']}",
        game,
        message_type,
    )


@app.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data:
                message = json.loads(data)
                await process_message(user_id, message)  # type: ignore

    except WebSocketDisconnect as e:
        if e.code == 1001:  # type: ignore
            message = f"{user_id} has disconnected"
            logger.warning(f"{user_id} has disconnected")
            await manager.disconnect(user_id, websocket)
            await manager.broadcast(message, game)
        else:
            logger.error(f"Exception = {e}")
            logger.error(traceback.format_exc())


async def process_message(user_id, message):
    if message.get("action") == "sort_cards":
        game.sort_cards(user_id, message.get("order", []))
    else:
        if message.get("message_txt") and not game.exchange_in_progress:
            game.set_current_action(message.get("message_txt"), user_id)
        else:
            message["message_txt"] = ""
        if "Pick_from" in game.current_action.name :
            message["message_txt"] = game.current_action.name

        if game.exchange_in_progress:
            card_to_exchange = message.get("cardnames")
            if isinstance(card_to_exchange, str):
                game.card_to_exchange = game.get_card_object_from_cardname(card_to_exchange) # type: ignore
        game.process_action(message["message_txt"], user_id)
        await bc(user_id, message)
        if game.game_over():
            game.process_action(Action("No_action",  "disabled", ), user_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
