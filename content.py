from jinja2 import Environment, FileSystemLoader

file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)
turn_template = env.get_template("turn.html")
actions_template = env.get_template("actions.html")
player_alert_template = env.get_template("player_alerts.html")
game_alert_template = env.get_template("game_alerts.html")
card_template = env.get_template("draw_card.html")


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
        self.display_cards = [card for card in player.hand]

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
        player = self.game.player(self.user_id)
        self.show_player(player)
        for player in self.players.values():
            if player.id == self.user_id:
                continue
            self.show_player(player)
        return self.table

    def show_player(self, player):
        self.table += self.show_hand(player)

    def show_turn(self):
        suffix = self.game.get_suffix()
        output = turn_template.render(turn=self.game.whose_turn_name(), suffix=suffix)
        return output

    def show_actions(self):
        print("show action")
        output = actions_template.render(
            actions=self.game.actions, user_id=self.game.user_id
        )
        print (f"{self.game.actions=}")
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
