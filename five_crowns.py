import random
import actions
from loguru import logger
from enum import Enum
from collections import defaultdict
import itertools
from functools import lru_cache


KEEP_CARDS = False
NUM_OF_ROUNDS = 11
CARD_VALUES = {n: n for n in range(3, 11)}
CARD_VALUES.update({11: 11, 12: 12, 13: 13, 99: 50})  # A=15, Joker=50
CARD_ORDER = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,]


class ActionStatus(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class GameStatus(Enum):
    NOT_STARTED = "Not started"
    WAITING = "Waiting"
    STARTED = "Started"
    IN_PROGRESS = "In progress"
    GAME_OVER = "Game_Over"


class SUIT(Enum):
    HEART = "heart"
    SPADE = "spade"
    CLUB = "club"
    DIAMOND = "diamond"
    STAR = "star"
    JOKER = "joker"


class No_Card(Exception):
    pass


class Card:
    def __init__(self, suit: SUIT, rank: int) -> None:
        self.suit = suit
        self.rank = rank

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __lt__(self,other):
        return self.rank<other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))

    @property
    def suit_html(self):
        match self.suit:
            case SUIT.HEART:
                return "♥"
            case SUIT.SPADE:
                return "♠"
            case SUIT.DIAMOND:
                return "♦"
            case SUIT.CLUB:
                return "♣"
            case SUIT.STAR:
                return "★"
            case SUIT.JOKER:
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
            for suit in SUIT:
                if suit == SUIT.JOKER:
                    continue
                for rank in range(3, 14):
                    self.cards.append(Card(suit, rank))
            self.cards.append(Card(SUIT.JOKER, 99))
            self.cards.append(Card(SUIT.JOKER, 99))
            self.cards.append(Card(SUIT.JOKER, 99))

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card:
        return self.cards.pop(0)

    def cards_remaining(self):
        return len(self.cards)

    def __repr__(self) -> str:
        return " ".join(
            [str(self.card.rank) + self.card.suit.value for self.card in self.cards]
        )


class Player:
    def __init__(self, id: str, name: str | None) -> None:
        self.id = id
        self.name = name
        self.hand: list[Card] = []
        self.player_alert = ""
        self.last_turn_played = False
        self.score = 0
        self.total_score = 0

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
        if game is not None:
            game.discard_pile.append(card)

    def set_player_alert(self, message) -> None:
        if message:
            self.player_alert = message
        else:
            self.clear_player_alert()

    def clear_player_alert(self) -> None:
        self.player_alert = ""

    def auto_sort_hand(self,round_num):
        score = self.score_hand_optimal( round_num)
        books=score['books']
        runs=score['runs']
        remaining=score["remaining"]
        sorted_hand:list[Card]=[]
        if books:
            for book in books:
                sorted_hand+=book
        if runs:
            for run in runs:
                sorted_hand+=run
        if remaining:
            sorted_hand+=sorted(remaining)  

        self.hand=sorted_hand
        pass

    def score_hand(self, round_num: int) -> dict:
        score = self.score_hand_optimal( round_num)
        self.score = score.get("score")
        return score

    def score_hand_optimal(self, round_num):
        """
        hand: list[Card]
        round_num: int (3..13)

        Returns dict with books, runs, assigned wilds, remaining, score.
        """

        wild_rank = round_num  # e.g. round 8 → 8 is wild

        # build card dicts
        cards = []
        for idx, card in enumerate(self.hand):
            is_joker = card.rank == 99 or card.suit == SUIT.JOKER
            is_round_wild = card.rank == wild_rank
            is_wild = is_joker or is_round_wild
            cards.append(
                {
                    "id": idx,
                    "card": card,
                    "rank": card.rank,
                    "suit": card.suit,
                    "is_joker": is_joker,
                    "is_round_wild": is_round_wild,
                    "is_wild": is_wild,
                }
            )

        card_length = len(cards)
        wild_ids = [card["id"] for card in cards if card["is_wild"]]

        normals_by_rank = defaultdict(list)
        normals_by_suit_rank = defaultdict(lambda: defaultdict(list))
        for card in cards:
            if not card["is_wild"]:
                normals_by_rank[card["rank"]].append(card["id"])
                normals_by_suit_rank[card["suit"]][card["rank"]].append(card["id"])

        groups = []
        seen = set()

        def register_group(group_type, ids_tuple, assigned_map):
            ids_tuple = tuple(sorted(ids_tuple))
            key = (group_type, ids_tuple, tuple(sorted(assigned_map.items())))
            if key in seen:
                return
            seen.add(key)
            value = sum(CARD_VALUES[cards[i]["rank"]] for i in ids_tuple)
            groups.append(
                {
                    "type": group_type,
                    "ids": ids_tuple,
                    "assigned": dict(assigned_map),
                    "value": value,
                }
            )

        # --- Books (3–5 of same rank) ---
        for rank in CARD_ORDER:
            normals = normals_by_rank.get(rank, [])
            max_size = min(5, len(normals) + len(wild_ids))
            for size in range(3, max_size + 1):
                min_normals = max(0, size - len(wild_ids))
                max_normals = min(len(normals), size)
                for k in range(min_normals, max_normals + 1):
                    for normals_subset in itertools.combinations(normals, k):
                        wild_needed = size - k
                        for wild_subset in itertools.combinations(
                            wild_ids, wild_needed
                        ):
                            ids = tuple(sorted(normals_subset + wild_subset))
                            assigned = {wid: (rank, None) for wid in wild_subset}
                            register_group("book", ids, assigned)

        # --- Runs (length ≥3) ---
        for suit in SUIT:
            rank_map = normals_by_suit_rank.get(suit, {})
            for start in range(len(CARD_ORDER)):
                for L in range(3, len(CARD_ORDER) - start + 1):
                    seq = CARD_ORDER[start : start + L]
                    # prune if impossible
                    if len(seq) > len(rank_map) + len(wild_ids):
                        continue
                    opts = []
                    for rank_label in seq:
                        normals_here = rank_map.get(rank_label, [])
                        opts.append([None] + normals_here)  # None = wild slot

                    seen_assign = set()

                    def rec(pos, used_normals, used_wilds, ids_list, assigned_map):
                        if len(used_wilds) > len(wild_ids):
                            return
                        if pos == L:
                            ids_tuple = tuple(sorted(ids_list))
                            key = (ids_tuple, tuple(sorted(assigned_map.items())))
                            if key in seen_assign:
                                return
                            seen_assign.add(key)
                            register_group("run", ids_tuple, assigned_map)
                            return
                        for opt in opts[pos]:
                            if opt is None:
                                for wid in wild_ids:
                                    if wid in used_wilds:
                                        continue
                                    new_assigned = dict(assigned_map)
                                    new_assigned[wid] = (seq[pos], suit)
                                    rec(
                                        pos + 1,
                                        used_normals,
                                        used_wilds | {wid},
                                        ids_list + [wid],
                                        new_assigned,
                                    )
                            else:
                                if opt in used_normals:
                                    continue
                                rec(
                                    pos + 1,
                                    used_normals | {opt},
                                    used_wilds,
                                    ids_list + [opt],
                                    assigned_map,
                                )

                    rec(0, frozenset(), frozenset(), [], {})

        # runs of only wilds
        if len(wild_ids) >= 3:
            for suit in SUIT:
                for start in range(len(CARD_ORDER)):
                    for L in range(3, min(len(CARD_ORDER) - start, len(wild_ids)) + 1):
                        seq = CARD_ORDER[start : start + L]
                        for wild_subset in itertools.combinations(wild_ids, L):
                            assigned = {
                                wid: (seq[i], suit) for i, wid in enumerate(wild_subset)
                            }
                            register_group("run", tuple(sorted(wild_subset)), assigned)

        # --- DP to select disjoint groups ---
        for group in groups:
            mask = 0
            for i in group["ids"]:
                mask |= 1 << i
            group["mask"] = mask

        @lru_cache(None)
        def dp(mask):
            best_val = 0
            best_choice = None
            for gi, group in enumerate(groups):
                if (mask & group["mask"]) == 0:
                    new_mask = mask | group["mask"]
                    val_next, _ = dp(new_mask)
                    val_with = group["value"] + val_next
                    if val_with > best_val:
                        best_val = val_with
                        best_choice = (gi, new_mask)
            return best_val, best_choice

        total_value_removed, choice = dp(0)
        chosen_groups = []
        mask = 0
        while choice is not None:
            gi, next_mask = choice
            chosen_groups.append(groups[gi])
            mask = next_mask
            _, choice = dp(mask)

        books_out, runs_out, assigned_wilds_out = [], [], []
        for group in chosen_groups:
            card_list = [cards[i]["card"] for i in group["ids"]]
            if group["type"] == "book":
                books_out.append(card_list)
            else:
                runs_out.append(card_list)
            for wid, (as_rank, as_suit) in group["assigned"].items():
                if cards[wid]["is_wild"]:
                    assigned_wilds_out.append(
                        {
                            "card": cards[wid]["card"],
                            "assigned_rank": as_rank,
                            "assigned_suit": as_suit,
                            "used_for": group["type"],
                        }
                    )

        remaining_ids = [i for i in range(card_length) if not (mask & (1 << i))]
        remaining = [cards[i]["card"] for i in remaining_ids]
        score = sum(CARD_VALUES[cards[i]["rank"]] for i in remaining_ids)

        return {
            "books": books_out,
            "runs": runs_out,
            "assigned_wilds": assigned_wilds_out,
            "remaining": remaining,
            "score": score,
        }


class Action:
    def __init__(
        self,
        name: str,
        action_status: ActionStatus,
        text: str = "",
    ) -> None:
        self.name = name
        self.action_status = action_status
        self.text = text

    def __repr__(self) -> str:
        return self.name


class Game:
    def __init__(self) -> None:
        self.round_number = 0
        self.players: dict[str, Player] = {}
        self.game_status: GameStatus = GameStatus.NOT_STARTED
        self.actions: list[Action] = []
        self.current_action: Action = Action("No_action", ActionStatus.DISABLED)
        self.current_player_index: int = 0
        self.current_dealer_index: int = 0
        self.game_alert: str = ""
        self.user_id: str = ""
        self.last_user_id_assigned = 0
        self.exchange_in_progress: bool = False
        self.card_to_exchange: Card | None = None
        self.keep_cards = KEEP_CARDS
        self.discard_pile: list[Card] = []
        self.last_turn_in_round: int = 0
        self.round_over: bool = False
        self.out_cards: list[Card] | None = []
        self.out_cards_player_id: str = ""
        self.score_card: dict[int, list[int]] = {}
        self.ding: bool = False

    def deal_cards(self) -> None:
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
        for round_number in range(1, NUM_OF_ROUNDS + 1):
            self.score_card[round_number] = [0 for player in self.players.values()]
        return True

    def next_turn(self) -> None:
        self.ding=True   #this is temporary
        self.next_player()
        self.clear_all_player_alerts()
        if not self.last_turn_in_round:
            self.clear_game_alerts()
        self.current_action = Action(
            "No_action",
            ActionStatus.DISABLED,
        )

    def next_player(self):
        self.current_player_index += 1
        if self.current_player_index >= len(self.players):
            self.current_player_index = 0
        self.current_player_id = str(
            self.player_id_from_index(self.current_player_index)
        )

    def next_dealer(self):
        self.current_dealer_index += 1
        if self.current_dealer_index >= len(self.players):
            self.current_dealer_index = 0

    def whose_turn(self) -> int:
        return self.current_player_index

    def whose_turn_name(self) -> str | None:
        if self.game_status == GameStatus.IN_PROGRESS:
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
                ActionStatus.DISABLED,
            ),
            (
                "Restart",
                ActionStatus.DISABLED,
            ),
            (
                "Pick_from_deck",
                ActionStatus.DISABLED,
            ),
            (
                "Pick_from_discard",
                ActionStatus.DISABLED,
            ),
            (
                "Go_out",
                ActionStatus.DISABLED,
            ),
            (
                "Next_round",
                ActionStatus.DISABLED,
            ),
            (
                "Sort_cards",
                ActionStatus.DISABLED,
            ),
        ]:
            self.actions.append(
                Action(
                    name,
                    self.action_status,
                    actions.actions_text.get(name, "NOT FOUND"),
                )
            )
        if self.game_status == GameStatus.WAITING:
            self.enable_one_action("Start")

        if self.game_status == GameStatus.IN_PROGRESS:
            self.disable_one_action("Start")

    def enable_one_action(self, action_name):
        for self.action in self.actions:
            if self.action.name == action_name:
                self.action.action_status = ActionStatus.ENABLED

    def disable_one_action(self, action_name):
        for self.action in self.actions:
            if self.action.name == action_name:
                self.action.action_status = ActionStatus.DISABLED

    def enable_all_actions(self):
        for self.action in self.actions:
            if self.action.name not in (
                "Start",
                "Restart",
                "Pick_from_discard",
                "Pick_from_deck",
                "Go_out",
                "Next_round",
            ):
                self.action.action_status = ActionStatus.ENABLED

    def action_from_action_name(self, action_name: str) -> Action:
        default_action = Action(
            "No_action",
            ActionStatus.DISABLED,
        )
        for action in self.actions:
            if action.name == action_name:
                return action
        return default_action

    def exchange(self, user_id):
        self.user_id = user_id

        if not self.card_to_exchange and self.exchange_in_progress:
            self.player(self.user_id).set_player_alert(
                "You didn't pick a card to discard"
            )
            return

        if not self.card_to_exchange:
            logger.warning(
                f"Cards remaining - {self.deck.cards_remaining()} Discard {len(self.discard_pile)})"
            )
            if self.current_action.name == "Pick_from_deck":
                self.player(self.user_id).draw(self.deck)
                if self.deck.cards_remaining() == 0:
                    self.deck.cards = self.discard_pile[:-1]
                    self.discard_pile = [self.discard_pile[-1]]
                    self.deck.shuffle()

            if self.current_action.name == "Pick_from_discard":
                self.player(self.user_id).hand.append(self.discard_pile.pop())  # type: ignore
            self.exchange_in_progress = True

        if self.card_to_exchange:
            self.player(self.user_id).discard(self.card_to_exchange, self.deck, self)
            self.card_to_exchange = None
            self.exchange_in_progress = False
            if self.last_turn_in_round:
                self.players[self.user_id].last_turn_played = True
                self.go_out()
            else:
                if (
                    not self.players[str(self.current_action_player_id)]
                    .score_hand(self.round_number + 2)
                    .get("score")
                ):
                    self.go_out()
                else:
                    self.next_turn()

    def wait(self)->None:
        self.set_game_status(GameStatus.WAITING)
        self.add_all_actions()

    def start_game(self)->None:
        self.round_number=0
        self.set_game_status(GameStatus.IN_PROGRESS)
        self.add_all_actions()
        self.enable_all_actions()
        self.current_player_index = random.randint(0, len(self.players) - 1)
        self.current_dealer_index = self.current_player_index
        self.start_round()

    def start_round(self)->None:
        self.round_over = True
        self.game_alert = "Round Over"
        self.last_turn_in_round = 0
        self.round_number += 1
        self.deck = Deck()
        self.deck.shuffle()

        for player in self.players.values():
            player.reset()
        self.deal_cards()
        self.clear_all_player_alerts()
        self.clear_game_alerts()
        self.out_cards = []
        self.out_cards_player_id = ""
        self.next_dealer()
        self.disable_one_action("Next_round")
        self.disable_one_action("Restart")
        if self.is_game_over():
            self.game_alert = "Game Over"
            self.disable_one_action("Next_round")
            self.enable_one_action("Restart")

    def your_turn(self) -> bool:
        whose_turn = self.whose_turn_name()
        name = self.players[self.user_id].name
        return whose_turn == name

    def process_action(self, action: Action, user_id: str):
        self.ding = False
        logger.debug(f"processing {action=} {user_id=} {self.current_action=}")
        self.user_id = user_id
        if not isinstance(action, Action):
            action = self.action_from_action_name(action)
        if action.name=="Sort_cards":
            self.players[self.user_id].auto_sort_hand(self.round_number)
            pass
        if action.name == "Restart":
            self.set_game_status(GameStatus.IN_PROGRESS)
            self.round_number = 1
            self.next_turn()
            self.start_game()
            return  # Can't do anything if block in progress
        if (
            action.name == "Start"
            and self.game_status == GameStatus.WAITING
            and len(self.players) > 1
        ):
            self.start_game()
            return
        if not self.your_turn():
            return

        if (
            "Pick_from" in action.name
            and not self.players[self.user_id].last_turn_played
            and not self.out_cards_player_id == self.current_action_player_id
        ):
            self.exchange(self.user_id)

        if self.game_status == GameStatus.WAITING:
            return
        if action.name == "Go_out":
            self.go_out()
            return
        if action.name == "Next_round":
            if self.is_next_round():
                self.start_round()

    def go_out(self):
        # validate cards and return if not valid  #TODO probably not necessary any more
        if (
            self.players[str(self.current_action_player_id)]
            .score_hand(self.round_number + 2)
            .get("score")
            and not self.last_turn_in_round
        ):
            self.game_alert = f"You don't have the correct score to go out - {self.players[str(self.current_action_player_id)].score_hand(self.round_number+2).get("score")}"
            return

        # allow for one more hand per person
        self.last_turn_in_round += 1
        self.game_alert = f"{self.whose_turn_name()} went out-LAST TURN of round!!!"
        self.out_cards = self.players[str(self.current_action_player_id)].hand
        self.out_cards_player_id = self.current_action_player_id
        if self.last_turn_in_round <= len(self.players):
            self.next_turn()

        if self.last_turn_in_round >= len(self.players):
            if self.is_game_over():
                self.enable_one_action("Restart")
            else:
                self.enable_one_action("Next_round")

        self.update_score_card()

    def is_next_round(self)->bool:  ######check for game_over
        if self.last_turn_in_round >= len(self.players):
            return True
        else:
            return False

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

    def set_game_status(self, game_status: GameStatus):
        self.game_status = game_status

    def get_game_status(self) ->GameStatus:
        return self.game_status

    def is_game_over(self)->bool:
        if self.round_number > NUM_OF_ROUNDS:
            self.set_game_status(GameStatus.GAME_OVER)
            return  True
        else:
            return False

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
        self.round_number = 1
        self.players: dict[str, Player] = {}
        self.set_game_status(GameStatus.NOT_STARTED)
        self.actions: list[Action] = []
        self.current_action: Action = Action(
            "No_action",
            ActionStatus.DISABLED,
        )
        self.current_action_player_id: str = ""
        self.current_player_index: int = 0
        self.current_dealer_index: int = 0
        self.game_alert: str = ""
        self.players_remaining = []
        self.user_id: str = ""
        self.last_user_id_assigned = 0
        self.exchange_in_progress: bool = False
        self.card_to_exchange: Card | None = None
        self.keep_cards = KEEP_CARDS
        self.discard_pile: list[Card]  = []
        self.last_turn_in_round: int = 0
        self.round_over: bool = False
        self.out_cards: list[Card] | None = []
        self.out_cards_player_id: str = ""
        self.score_card: dict[int, list[int]] = {}
        self.ding: bool = False

    def get_card_object_from_cardname(self, cardname: str):
        suit = SUIT(cardname.split("-")[0])
        rank = int(cardname.split("-")[1])
        return Card(suit, rank)

    def sort_cards(self, user_id: str, old_index: int, new_index: int):
        """Reorder cards in player's hand based on drag and drop action"""
        logger.debug(f"Sorting cards for user {user_id}")
        logger.debug(f"Moving card from index {old_index} to {new_index}")

        player = self.player(user_id)
        if not player:
            logger.error("Player not found")
            return

        if old_index == new_index:
            logger.debug("No movement needed - same position")
            return
        logger.debug(f"Old hand order: {[(c.suit, c.rank) for c in player.hand]}")

        # Get the card being moved
        card_to_move = player.hand.pop(old_index)

        # Insert it at the new position
        player.hand.insert(new_index, card_to_move)

        logger.debug(f"New hand order: {[(c.suit, c.rank) for c in player.hand]}")

    def update_score_card(self):
        self.score_card[self.round_number] = [
            player.score or 0 for player in self.players.values()
        ]
        self.total_score_card()

    def total_score_card(self):
        if not self.score_card:
            return
        score_card_total = []
        for player in self.players.values():
            player.total_score = -0
        for round in range(1, NUM_OF_ROUNDS + 1):
            for player_num, player in enumerate(self.players.values()):
                player.total_score += self.score_card[round][player_num]
        score_card_total = [player.total_score for player in self.players.values()]
        return score_card_total

    def round_wild(self):
        if self.is_game_over():  #######################################TODO
            return
        if self.round_number > 8:
            wild = ["Jack", "Queen", "King"][self.round_number - 9]
        else:
            wild = self.round_number + 2
        return f"{wild}'s are wild"


def main():
    ids = [("1", "Lee"), ("2", "Adina")]
    game = Game()
    for player_id, player_name in ids:
        game.players[player_id] = Player(player_id, player_name)
    game.wait()
    print(game.actions)
    game.start_game()
    print(game.actions)
    game.user_id = "1"
    print(game.whose_turn())
    print(game.player_id("1"))
    game.current_player_index = 1
    print(game.your_turn())
    print(game.whose_turn_name())


if __name__ == "__main__":
    main()
