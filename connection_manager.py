from fastapi import WebSocket, WebSocketDisconnect
from content import Content
from five_crowns import Game
from loguru import logger


class ConnectionManager:
    def __init__(self, game: Game) -> None:
        self.active_connections = {}
        self.game = game

    async def connect(self, user_id: str, websocket: WebSocket):
        message = {"message_txt": ""}
        await websocket.accept()
        self.active_connections[user_id] = websocket
        # Notify current clients of new login
        await self.broadcast(message, game=self.game, message_type="login")

    async def disconnect(self, user_id: str, websocket: WebSocket | None = None):
        # Remove connection safely without raising if it was already removed
        removed = self.active_connections.pop(user_id, None)
        if removed:
            logger.debug(f"Disconnected {user_id}")
        else:
            logger.debug(f"Attempted to disconnect {user_id} but no active connection was found")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        # Send a message and let the caller handle any exceptions so we can centralize cleanup in broadcast
        await websocket.send_text(message)

    async def broadcast(self, message: dict, game: Game, message_type: str = "all"):
        # Iterate over a snapshot so we can remove dead connections safely
        dead = []
        for user_id, websocket in list(self.active_connections.items()):
            self.game.user_id = user_id
            content = Content(self.game, user_id)
            try:
                if message_type in ("all", "alert"):
                    table = content.show_game_alert()
                    await self.send_personal_message(table, websocket)
                    table = content.show_player_alert(user_id)
                    await self.send_personal_message(table, websocket)

                if message_type in ("all", "table"):
                    table = content.show_table()
                    await self.send_personal_message(table, websocket)
                    if game.top_discard():
                        table = content.show_discard()
                        await self.send_personal_message(table, websocket)

                table = content.show_out_cards()
                await self.send_personal_message(table, websocket)

                if message_type in ("all", "score"):
                    table = content.show_score_card()
                    await self.send_personal_message(table, websocket)

                if message_type in ("all", "turn"):
                    table = content.show_turn()
                    await self.send_personal_message(table, websocket)

                if message_type in ("all", "action"):
                    table = content.show_actions()
                    await self.send_personal_message(table, websocket)

                if message_type == "login":
                    table = content.show_logins()
                    await self.send_personal_message(table, websocket)

            except WebSocketDisconnect:
                logger.warning(f"WebSocketDisconnect for {user_id}")
                dead.append(user_id)
            except Exception as e:
                # Any send error should cause the connection to be removed so it doesn't hang the server
                logger.error(f"Error broadcasting to {user_id}: {e}")
                dead.append(user_id)

        if dead:
            # remove dead connections
            for uid in dead:
                self.active_connections.pop(uid, None)

            # Notify remaining users that someone disconnected (best effort)
            try:
                notice = {"message_txt": f"{', '.join(dead)} has disconnected"}
                for uid, ws in list(self.active_connections.items()):
                    try:
                        await ws.send_text(notice["message_txt"])
                    except Exception as e:
                        logger.error(f"Failed to notify {uid} about disconnect: {e}")
                        self.active_connections.pop(uid, None)
            except Exception as e:
                logger.error(f"Failed to send disconnect notice: {e}")
