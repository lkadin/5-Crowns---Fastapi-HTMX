import random
import actions
from collections import defaultdict
from itertools import combinations

KEEP_CARDS = False


class No_Card(Exception):
    pass


class Card:
    def __init__(self, suit: str, rank: int) -> None:
        self.suit = suit
        self.rank = rank

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))

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
        if self.rank == 99:
            return "Joker"
        if self.rank == 11:
            return "J"
        if self.rank == 12:
            return "Q"
        if self.rank == 13:
            return "K"
        return self.rank


class Deck:
    def __init__(self) -> None:
        self.cards: list[Card] = []
        for _ in range(2):
            for suit in ["heart", "spade", "club", "diamond", "star"]:
                for rank in range(3, 14):
                    self.cards.append(Card(suit, rank))
            self.cards.append(Card("joker", 99))
            self.cards.append(Card("joker", 99))

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card:
        return self.cards.pop(0)

    def return_to_deck(self, card: Card):
        self.cards.append(card)

    def __repr__(self) -> str:
        return " ".join(
            [str(self.card.rank) + self.card.suit for self.card in self.cards]
        )


class Player:
    def __init__(self, id: str, name: str | None) -> None:
        self.id = id
        self.name = name
        self.hand: list[Card] = []
        self.player_alert = ""
        self.last_turn_played = False
        self.score = 0

    def reset(self):
        self.hand: list[Card] = []
        self.player_alert = ""
        self.last_turn_played = False

    def get_index(self, card_to_index: Card) -> int:
        for index, card in enumerate(self.hand):
            if card == card_to_index:
                return index
        raise No_Card("Card to discard not found in hand")

    def draw(self, deck: Deck) -> None:
        self.hand.append((deck.draw()))

    def discard(self, card: Card, deck: Deck, game=None) -> None:
        index = self.get_index(card)
        self.hand.pop(index)
        deck.return_to_deck(card)
        if game is not None:
            game.discard_pile.append(card)

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

    def score_hand(self, round_num: int) -> dict:
        wild_rank = round_num
        wilds = [card for card in self.hand if card.rank == wild_rank or card.rank == 99]
        normals = [card for card in self.hand if card not in wilds]
        # best_score = float('inf')
        best_score =9999
        best_solution = {"books":[],"runs":[],"remaining":self.hand,"score":best_score}
        def is_consecutive(run):
            idxs = [card.rank for card in run]
            return all(b == a + 1 for a, b in zip(idxs, idxs[1:]))

        def possible_books(cards, wilds):
            result = []
            rank_groups = defaultdict(list)
            for card in cards:
                rank_groups[card.rank].append(card)
            for rank, group in rank_groups.items():
                if len(group)+wilds >= 3:
                    result.append((group, 3 - len(group)))
            return result

        def possible_runs(cards, wilds):
            result = []
            suit_groups = defaultdict(list)
            for card in cards:
                suit_groups[card.suit].append(card)
            for suit, group in suit_groups.items():
                group = sorted(group, key=lambda card: card.rank)
                for r in range(3, len(group)+wilds+1):
                    for combo in combinations(group, min(len(group),r)):
                        combo = sorted(combo, key=lambda card: card.rank)
                        needed = 0
                        for a,b in zip(combo, combo[1:]):
                            gap = b.rank - a.rank - 1
                            needed += gap
                        if len(combo)+needed <= r and needed <= wilds:
                            result.append((combo, needed))
            return result

        def backtrack(cards, wilds, groups):
            nonlocal best_score, best_solution
            # If no cards left or all wilds used
            rem_score = sum( card.rank for card in cards) + wilds*50
            if rem_score >= best_score:
                return

            # Try books
            for group, need in possible_books(cards, wilds):
                if need <= wilds:
                    new_cards = [card for card in cards if card not in group]
                    backtrack(new_cards, wilds-need, groups+[("book", group+["wild"]*need)])

            # Try runs
            for group, need in possible_runs(cards, wilds):
                if need <= wilds:
                    new_cards = [card for card in cards if card not in group]
                    backtrack(new_cards, wilds-need, groups+[("run", group+["wild"]*need)])

            # If nothing more formed, score leftover
            leftover = cards[:]
            total = sum(card.rank for card in leftover) + wilds*50
            if total < best_score:
                best_score = total
                books = [g for t,g in groups if t=="book"]
                runs = [g for t,g in groups if t=="run"]
                best_solution = {"books":books,"runs":runs,"remaining":leftover+["wild"]*wilds,"score":total}

        backtrack(normals, len(wilds), [])
        self.score=best_solution.get('score')
        return best_solution


    def __repr__(self) -> str:
        return f"{self.id}-{self.hand} "


class Action:
    def __init__(
        self,
        name: str,
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
        self.NUM_OF_ROUNDS = 11
        self.round_number = 1
        self.game_alert = f"Round {self.round_number}"
        self.players: dict[str, Player] = {}
        self.game_status: str = "Not started"
        self.actions: list[Action] = []
        self.current_action: Action = Action("No_action", "disabled")
        self.current_player_index: int = 0
        self.game_alert: str = ""
        self.user_id: str = ""
        self.last_user_id_assigned = 0
        self.exchange_in_progress: bool = False
        self.card_to_exchange: Card | None = None
        self.keep_cards = KEEP_CARDS
        self.discard_pile: list[Card] | None = []
        self.last_turn_in_round: int = 0
        self.round_over: bool = False
        self.out_cards: list[Card] | None = []
        self.out_cards_player_id: str = ""

    def initial_deal(self) -> None:
        for _ in range(self.round_number + 2):
            for player in self.players.values():
                player.draw(self.deck)
        # Add one card to discard pile after initial deal
        self.discard_pile.append(self.deck.draw())  # type: ignore

    def top_discard(self):
        if self.discard_pile:
            return self.discard_pile[-1]
        return None

    def add_player(self, player_id: str, player_name: str) -> bool:
        if player_name in [player.name for player in self.players.values()]:
            return False
        self.players[player_id] = Player(player_id, player_name)
        return True

    def next_turn(self) -> None:
        self.next_player()
        self.clear_all_player_alerts()
        if not self.last_turn_in_round:
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
                "disabled",
            ),
            (
                "Pick_from_deck",
                "disabled",
            ),
            (
                "Pick_from_discard",
                "disabled",
            ),
            (
                "Go_out",
                "disabled",
            ),
            (
                "Next_round",
                "disabled",
            ),
        ]:
            self.actions.append(
                Action(
                    name,
                    self.action_status,
                    actions.actions_text.get(name, "NOT FOUND"),
                )
            )
        if self.game_status == "Waiting":
            self.enable_one_action("Start")

        if self.game_status == "In progress":
            self.disable_one_action("Start")

    def enable_one_action(self, action_name):
        for self.action in self.actions:
            if self.action.name == action_name:
                self.action.action_status = "enabled"

    def disable_one_action(self, action_name):
        for self.action in self.actions:
            if self.action.name == action_name:
                self.action.action_status = "disabled"

    def enable_all_actions(self):
        for self.action in self.actions:
            if self.action.name not in (
                "Start",
                "Restart",
                "Pick_from_discard",
                "Pick_from_deck",
            ):
                self.action.action_status = "enabled"

    def action_from_action_name(self, action_name: str) -> Action:
        default_action = Action(
            "No_action",
            "disabled",
        )
        for action in self.actions:
            if action.name == action_name:
                return action
        return default_action

    def exchange(self, user_id):
        self.user_id = user_id

        if not self.card_to_exchange and self.exchange_in_progress:
            self.player(self.user_id).set_player_alert("You didn't pick any cards")
            return

        if not self.card_to_exchange:
            self.player(self.user_id).save_cards()
            if self.current_action.name == "Pick_from_deck":
                self.player(self.user_id).draw(self.deck)
            if self.current_action.name == "Pick_from_discard":
                self.player(self.user_id).hand.append(self.discard_pile.pop())  # type: ignore
            self.exchange_in_progress = True

        if self.card_to_exchange:
            self.player(self.user_id).discard(self.card_to_exchange, self.deck, self)
            self.card_to_exchange = None
            self.exchange_in_progress = False
            if self.last_turn_in_round:
                self.players[self.user_id].last_turn_played = True
            else:
                self.next_turn()

    def wait(self):
        self.game_status = "Waiting"
        self.add_all_actions()

    def start(self):
        self.game_status = "In progress"
        self.deck = Deck()
        self.deck.shuffle()
        self.add_all_actions()
        self.enable_all_actions()
        self.initial_deal()
        self.current_player_index = random.randint(0, len(self.players) - 1)

    def restart(self):
        for player in self.players.values():
            player.reset()
            self.clear_all_player_alerts
            self.clear_game_alerts()
            self.out_cards = []
            self.out_cards_player_id = ""
            self.over = False
            self.actions.pop()  # remove restart action
        self.start()

    def your_turn(self) -> bool:
        whose_turn = self.whose_turn_name()
        name = self.players[self.user_id].name
        return whose_turn == name

    def process_action(self, action: Action, user_id: str):
        print(f"processing {action=} {user_id=} {self.current_action=}")
        if self.game_over():
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
            self.game_alert = f"Round - {self.round_number}"
            return
        if not self.your_turn():
            return

        if (
            "Pick_from" in action.name
            and not self.players[self.user_id].last_turn_played
            and not self.out_cards_player_id == self.current_action_player_id
        ):
            self.exchange(self.user_id)

        if self.game_status == "Waiting":
            return
        if action.name == "Go_out":
            self.go_out()
            return
        if action.name == "Next_round":
            self.next_round()

    def go_out(self):
        # validate cards and return if not valid
        if (
            self.players[str(self.current_action_player_id)]
            .score_hand(self.round_number+2)
            .get("score")
            and not self.last_turn_in_round
        ):
            self.game_alert = f"You don't have the correct score to go out - {self.players[str(self.current_action_player_id)]
            .score_hand(self.round_number+2)
            .get("score")}"
            return

        # allow for one more hand per person
        self.last_turn_in_round += 1
        self.game_alert = f"{self.whose_turn_name()} went out-LAST TURN of round!!!"
        self.out_cards = self.players[str(self.current_action_player_id)].hand
        self.out_cards_player_id = self.current_action_player_id
        if self.last_turn_in_round != len(self.players):
            # if not self.next_round() :
            self.next_turn()

        if self.round_number > self.NUM_OF_ROUNDS:
            self.game_alert = "Game Over"
            self.game_over()

    def next_round(self):
        if self.last_turn_in_round == len(self.players):
            ##show last players out cards
            self.round_over = True
            self.game_alert = "Round Over"
            self.round_number += 1
            self.last_turn_in_round = 0
            self.out_cards = []
            self.restart()
            return True

    def player_id(self, name) -> str:
        for i, player in enumerate(self.players):
            if self.players[player].name == name:
                return self.players[player].id
        return ""

    def player(self, user_id) -> Player:
        try:
            return self.players[user_id]
        except KeyError:
            return None  # type: ignore

    def set_game_status(self, game_status: str):
        self.game_status = game_status

    def get_game_status(self):
        return self.game_status

    def game_over(self):
        self.over = False
        return self.over

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

    def get_card_object_from_cardname(self, cardname: str):
        print(cardname)
        suit = cardname.split("-")[0]
        rank = int(cardname.split("-")[1])
        return Card(suit, rank)


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
