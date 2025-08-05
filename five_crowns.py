import random
import actions


class No_Card(Exception):
    pass


class Card:
    def __init__(self, suit:str,rank:int) -> None:
        self.suit = suit
        self.rank=rank

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    @property
    def suit_html(self):
        match self.suit:
            case "heart":
                return "♥"
            case "spade":
                return "♠"
            case "diamond":
                return "♦"
            case "club":
                return "♣"
            case "star":
                return "★"
            case "joker":
                return chr(127199)

    @property
    def rank_html(self):
        if self.rank==99:
            return 'Joker'
        return self.rank

class Deck:
    def __init__(self) -> None:
        self.cards = []
        for _ in range(2):
            for suit in ["heart", "spade", "club", "diamond", "star"]:
                for rank in range(3,14):
                    self.cards.append(Card(suit,rank))
            self.cards.append(Card('joker',99))
            self.cards.append(Card('joker',99))

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card:
        return self.cards.pop(0)

    def return_to_deck(self, cardname):
        self.cards.append(cardname)

    def __repr__(self) -> str:
        return " ".join([str(self.card.rank)+self.card.suit for self.card in self.cards])


class Player:
    def __init__(self, id: str, name: str | None) -> None:
        self.id = id
        self.name = name
        self.hand: list[Card] = []
        self.player_alert = ""

    def reset(self):
        self.hand: list[Card] = []
        self.player_alert = ""

    def get_index(self, card_to_index: Card) -> int:
        for index, card in enumerate(self.hand):
            if card == card_to_index :
                return index
        raise No_Card("Card to discard not found in hand")

    def draw(self, deck: Deck) -> None:
        self.hand.append((deck.draw()))

    def discard(self, cardnames: list[Card], deck: Deck) -> None:
        for cardname in cardnames:
            index = self.get_index(cardname)
            self.hand.pop(index)
            deck.return_to_deck(cardname)

    def set_player_alert(self, message) -> None:
        if message:
            self.player_alert = message
        else:
            self.clear_player_alert()

    def clear_player_alert(self) -> None:
        self.player_alert = ""

    def save_cards(self):
        self.cards_prior_to_exchange = self.hand.copy()

    def save_to_exchange(
        self, cards: list
    ) -> list:  # if FLAG is set, assume cards were to be saved and switch list to cards to be exchanged
        cardnames_to_exchange = []
        index_list = []
        for card in cards:
            for i, card in enumerate(self.hand):
                if i in index_list:
                    continue
                    index_list.append(i)
                    continue
                if card == card:
                    index_list.append(i)
                    break
        for i, card in enumerate(self.hand):
            if i not in index_list:
                cardnames_to_exchange.append(card)
        return cardnames_to_exchange

    def __repr__(self) -> str:
        return f"{self.id}-{self.hand} "


class Action:
    def __init__(
        self,
        name,
        action_status: str,
        text: str = "",
    ) -> None:
        self.name = name
        self.action_status = action_status
        self.text = text

    def __repr__(self) -> str:
        return self.name


class Game:
    def __init__(self) -> None:
        self.NUM_OF_ROUNDS=11
        self.round_number=1
        self.game_alert=f"Round {self.round_number}"
        self.players: dict[str, Player] = {}
        self.game_status: str = "Not started"
        self.actions: list[Action] = []
        self.current_player_index: int = 0
        self.game_alert: str = ""
        self.user_id: str = ""
        self.last_user_id_assigned = 0

    def initial_deal(self) -> None:
        for _ in range(self.round_number+2):
            for player in self.players.values():
                player.draw(self.deck)

    def add_player(self, player_id: str, player_name: str) -> bool:
        if player_name in [player.name for player in self.players.values()]:
            return False
        self.players[player_id] = Player(player_id, player_name)
        return True

    def next_turn(self) -> None:
        self.next_player()
        self.clear_all_player_alerts()
        self.clear_game_alerts()
        self.current_action = Action(
            "No_action",
            "disabled",
        )

    def next_player(self):
        self.current_player_index += 1
        if self.current_player_index >= len(self.players):
            self.current_player_index = 0
        self.current_player_id = str(
            self.player_id_from_index(self.current_player_index)
        )

        self.current_player_id = str(
            self.player_id_from_index(self.current_player_index)
        )

    def whose_turn(self) -> int:
        return self.current_player_index

    def whose_turn_name(self) -> str | None:
        if self.game_status == "In progress":
            for i, player in enumerate(self.players):
                if i == self.current_player_index:
                    return self.players[player].name
        else:
            return ""

    def player_index_to_id(self, index: int) -> str:
        for i, player in enumerate(self.players):
            if i == self.current_player_index:
                return self.players[player].id
        else:
            return ""

    def add_all_actions(self):
        self.actions = []
        for (
            name,
            self.action_status,
        ) in [
            (
                "Start",
                "enabled",
            ),
        ]:
            self.actions.append(
                Action(
                    name,
                    self.action_status,
                    actions.actions_text.get(name, ""),
                )
            )

    def enable_all_actions(self):
        for self.action in self.actions:
            if self.action.name not in ("Start", "Restart"):
                self.action.action_status = "enabled"

    def wait(self):
        self.game_status = "Waiting"
        self.add_all_actions()

    def start(self):
        self.game_status = "In progress"
        self.deck = Deck()
        self.deck.shuffle()
        self.add_all_actions()
        self.initial_deal()
        self.current_player_index = random.randint(0, len(self.players) - 1)

    def restart(self):
        for player in self.players.values():
            player.reset()
            self.clear_all_player_alerts
            self.clear_game_alerts()
            self.over = False
            self.actions.pop()  # remove restart action
        self.start()

    def your_turn(self) -> bool:
        whose_turn = self.whose_turn_name()
        name = self.players[self.user_id].name
        return whose_turn == name

    def process_action(self, action: Action, user_id: str):
        print(f"processing {action=} {user_id=}")
        if self.game_over():
            self.game_alert = f"Round - {self.round_number}"
            self.set_game_status("Game Over")
        self.user_id = user_id
        if not isinstance(action, Action):
            action = self.action_from_action_name(action)
        if action.name == "Restart":
            self.restart()
            return  # Can't do anything if block in progress
        if (
            action.name == "Start"
            and self.game_status == "Waiting"
            and len(self.players) > 1
        ):
            self.start()
            return

        if not self.your_turn():
            return


    def player(self, user_id) -> Player:
        try:
            return self.players[user_id]
        except KeyError:
            return None  # type: ignore

    def player_id(self, name) -> str:
        for i, player in enumerate(self.players):
            if self.players[player].name == name:
                return self.players[player].id
        return ""

    def set_game_status(self, game_status: str):
        self.game_status = game_status

    def get_game_status(self):
        return self.game_status

    def game_over(self):
        self.over = False
        return self.over

    def action_from_action_name(self, action_name: str) -> Action:
        default_action = Action(
            "No_action",
            "disabled",
        )
        for action in self.actions:
            if action.name == action_name:
                return action
        return default_action

    def set_current_action(self, action_name: str, user_id: str):
        self.user_id = user_id
        self.current_action = self.action_from_action_name(action_name)
        self.current_action_player_id = user_id

    def get_current_action(self):
        return self.current_action

    def clear_all_player_alerts(self):
        for player in self.players.values():
            player.clear_player_alert()

    def clear_game_alerts(self):
        self.game_alert = ""

    def player_id_from_index(self, index: int) -> str:
        for i, player in enumerate(self.players):
            if i == index:
                return self.players[player].id
        return ""

    def next_user_id(self):
        self.last_user_id_assigned += 1
        return self.last_user_id_assigned

    def get_suffix(self):
        suffix = ""
        if self.whose_turn_name() != "":
            suffix = "'s turn"
        return suffix

    def reset(self):
        self.players: dict[str, Player] = {}
        self.NUM_OF_CARDS: int = self.round_number
        self.game_status: str = "Not started"
        self.actions: list[Action] = []
        self.current_action: Action = Action(
            "No_action",
            "disabled",
        )
        self.current_action_player_id: str = ""
        self.current_player_index: int = 0
        self.game_alert: str = ""
        self.players_remaining = []
        self.user_id: str = ""
        self.last_user_id_assigned = 0


def main():
    ids = [("1", "Lee"), ("2", "Adina")]
    game = Game()
    for player_id, player_name in ids:
        game.players[player_id] = Player(player_id, player_name)
    game.wait()
    print(game.actions)
    game.start()
    print(game.actions)
    game.user_id = "1"
    print(game.whose_turn())
    print(game.player_id("1"))
    game.current_player_index = 1
    print(game.your_turn())
    print(game.whose_turn_name())


if __name__ == "__main__":
    main()
