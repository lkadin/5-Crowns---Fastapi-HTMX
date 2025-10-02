from jinja2 import Environment, FileSystemLoader

file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)
turn_template = env.get_template("turn.html")
actions_template = env.get_template("actions.html")
player_alert_template = env.get_template("player_alerts.html")
game_alert_template = env.get_template("game_alerts.html")
card_template = env.get_template("draw_card.html")
top_discard_template = env.get_template("top_discard.html")
out_cards_template = env.get_template("out_cards.html")


class Content:
    def __init__(self, game, user_id: str) -> None:
        self.game = game
        self.players = self.game.players
        self.user_id = user_id
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
        output = card_template.render(
            cards=self.display_cards,
            checkbox_required=self.checkbox_required,
            discard_prompt=self.discard_prompt,
            player=player,
            keep_discard=keep_discard,
        )
        return output

    def show_table(self):
        self.table = """
            <div hx-swap-oob="innerHTML:#table">
            """
        # Only show cards for the current user_id
        player = self.game.player(self.user_id)
        self.show_player(player)
        # self.show_discard()
        # Show discard pile for all sessions
        return self.table

    def show_discard(self):
        discard_html = """
            <div hx-swap-oob="innerHTML:#discard">
            """
        top_card = self.game.top_discard()
        player = self.game.player(self.user_id)
        if top_card:
            # Render discard using the same card template
            discard_html += top_discard_template.render(
                top_discard=top_card,
                checkbox_required=True,
                discard_prompt=False,
                player=player,
                keep_discard="discard",
            )
            return discard_html

    def show_out_cards(self):
        score=0
        out_player_name = ""
        if self.game.out_cards_player_id:
            player = self.game.player(self.game.out_cards_player_id)
            if player:
                out_player_name = player.name
                score=player.score
                
        output = out_cards_template.render(
            cards=self.game.out_cards,
            out_player_name=out_player_name,
            out_player_score=score,
        )
        return output

    def show_score_card(self):
        # score_card=self.game.total_score_card()
        score_card=''
        return score_card

    def show_player(self, player):
        self.table += self.show_hand(player)

    def show_turn(self):
        suffix = self.game.get_suffix()
        output = turn_template.render(turn=self.game.whose_turn_name(), suffix=suffix)
        return output

    def show_actions(self):
        output = actions_template.render(
            actions=self.game.actions, user_id=self.game.user_id
        )
        return output

    def show_game_alert(self):
        output = game_alert_template.render(game_alert=self.game.game_alert)
        return output

    def show_player_alert(self, user_id):
        try:
            output = player_alert_template.render(
                player_alert=self.game.player(user_id).player_alert
            )
        except AttributeError:
            output = player_alert_template.render(player_alert="")
        return output
