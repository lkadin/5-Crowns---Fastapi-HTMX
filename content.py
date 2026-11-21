from jinja2 import Environment, FileSystemLoader

file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)
turn_template = env.get_template("turn.html")
ding_template = env.get_template("ding.html")
actions_template = env.get_template("actions.html")
player_alert_template = env.get_template("player_alerts.html")
game_alert_template = env.get_template("game_alerts.html")
card_template = env.get_template("draw_card.html")
top_discard_template = env.get_template("top_discard.html")
out_cards_template = env.get_template("out_cards.html")
score_card_template = env.get_template("score_card.html")
logins_template = env.get_template("logins.html")


class Content:
    def __init__(self, game, user_id: str, room_id: str = "", room_name: str = "") -> None:
        self.game = game
        self.players = self.game.players
        self.user_id = user_id
        self.room_id = room_id
        self.room_name = room_name
        self.actions: str = ""

    def show_hand(self, player):
        self.checkbox_required = False
        self.discard_prompt = False

        # Always display all cards in player's hand
        self.display_cards = []
        for card_number, card in enumerate(player.hand):
            card.card_number = card_number
            self.display_cards.append(card)

        # Only enable checkboxes/discard prompt during exchange and user's turn
        if self.game.exchange_in_progress and self.game.your_turn():
            if player.name == self.players[self.user_id].name:
                self.discard_prompt = True
                self.checkbox_required = True

        keep_discard = "Keep" if self.game.keep_cards else "discard"
        sort_action = next(
            (action for action in self.game.actions if action.name == "Sort_cards"),
            None,
        )
        output = card_template.render(
            cards=self.display_cards,
            checkbox_required=self.checkbox_required,
            discard_prompt=self.discard_prompt,
            player=player,
            keep_discard=keep_discard,
            sort_action=sort_action,
            room_id=self.room_id,
            room_name=self.room_name,
            user_id=self.user_id,
        )
        return output

    def show_table(self)->str:
        self.table = """
            <div hx-swap-oob="innerHTML:#table">
            """
        # Only show cards for the current user_id
        player = self.game.player(self.user_id)
        self.show_player(player)
        self.table += """
            <div id="scores">""" + self._render_score_card() + """</div>
            <div style="padding: 10px; background-color: #f5f5f5; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #4CAF50;">
                <h6 style="margin: 0 0 5px 0; color: #666;">Room:</h6>
                <p style="margin: 0; font-weight: bold; color: #333;">""" + self.room_name + """</p>
                <h6 style="margin: 8px 0 5px 0; color: #666;">Wild:</h6>
                <p style="margin: 0; font-weight: bold; color: #333;">""" + str(self.game.round_wild()) + """</p>
            </div>
            </div>
            """
        return self.table

    def show_discard(self):
        discard_html = """
            <div hx-swap-oob="innerHTML:#discard">
            """
        top_card = self.game.top_discard()
        player = self.game.player(self.user_id)
        if top_card:
            discard_html += top_discard_template.render(
                top_discard=top_card,
                checkbox_required=True,
                discard_prompt=False,
                player=player,
                keep_discard="discard",
                room_id=self.room_id,
                room_name=self.room_name,
            )
            return discard_html

    def show_out_cards(self):
        score = 0
        out_player_name = ""
        cards = self.game.out_cards
        if self.game.out_cards_player_id:
            player = self.game.player(self.game.out_cards_player_id)
            if player:
                out_player_name = player.name
                score = player.score
                if cards is not None:
                    cards = player.get_sorted_hand(
                        self.game.round_number, sort_runs=True
                    )

        output = out_cards_template.render(
            cards=cards,
            out_player_name=out_player_name,
            out_player_score=score,
            room_id=self.room_id,
            room_name=self.room_name,
        )
        return output

    def _render_score_card(self):
        return score_card_template.render(
            players=self.game.players.values(),
            score_card_total=self.game.total_score_card(),
            show="visible",
            room_id=self.room_id,
            room_name=self.room_name,
        )

    def show_score_card(self):
        return (
            '<div hx-swap-oob="innerHTML:#scores">'
            + self._render_score_card()
            + "</div>"
        )

    def show_player(self, player):
        self.table += self.show_hand(player)
        self.table += f"<div id=player_id hidden>{player.id}</div>"

    def show_turn(self):
        suffix = self.game.get_suffix()
        output = turn_template.render(
            turn=self.game.whose_turn_name(),
            dealer=self.game.whose_dealer_name(),
            suffix=suffix,
            round_info=self.game.round_wild(),
            room_id=self.room_id,
            room_name=self.room_name,
        )
        return output

    def show_ding(self):
        output = ding_template.render(
            ding=self._should_play_ding(),
        )
        return output

    def _should_play_ding(self):
        return (
            self.game.ding
            and self.user_id == self.game.player_id_from_index(self.game.whose_turn())
        )

    def show_actions(self):
        output = actions_template.render(
            actions=self.game.actions, user_id=self.game.user_id, room_id=self.room_id, room_name=self.room_name
        )
        return output

    def show_game_alert(self):
        output = game_alert_template.render(game_alert=self.game.game_alert, room_id=self.room_id, room_name=self.room_name)
        return output

    def show_logins(self):
        player_names = [player.name for player in self.game.players.values()]
        output = logins_template.render(
            logins=player_names,
            current_player=self.game.whose_turn_name(),
        )
        return output

    def show_player_alert(self, user_id):
        try:
            output = player_alert_template.render(
                player_alert=self.game.player(user_id).player_alert,
                room_id=self.room_id,
                room_name=self.room_name,
            )
        except AttributeError:
            output = player_alert_template.render(player_alert="", room_id=self.room_id, room_name=self.room_name)
        return output
