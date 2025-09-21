from collections import defaultdict
import itertools
from functools import lru_cache
# from five_crowns import Card

# point values
CARD_VALUES = {n: n for n in range(3, 11)}
CARD_VALUES.update({11: 11, 12: 12, 13: 13, 1: 15, 99: 50})  # A=15, Joker=50

CARD_ORDER = [3,4,5,6,7,8,9,10,11,12,13,1]  # Ace high

def score_hand_optimal(hand, round_num):
    """
    hand: list[Card]
    round_num: int (3..13 or 1 for Ace)

    Returns dict with books, runs, assigned wilds, remaining, score.
    """

    wild_rank = round_num  # e.g. round 8 → 8 is wild

    # build card dicts
    cards = []
    for idx, c in enumerate(hand):
        is_joker = (c.rank == 99 or c.suit == "joker")
        is_round_wild = (c.rank == wild_rank)
        is_wild = is_joker or is_round_wild
        cards.append({
            "id": idx,
            "card": c,
            "rank": c.rank,
            "suit": c.suit,
            "is_joker": is_joker,
            "is_round_wild": is_round_wild,
            "is_wild": is_wild,
        })

    n = len(cards)
    wild_ids = [c["id"] for c in cards if c["is_wild"]]
    # normal_ids = [c["id"] for c in cards if not c["is_wild"]]

    normals_by_rank = defaultdict(list)
    normals_by_suit_rank = defaultdict(lambda: defaultdict(list))
    for c in cards:
        if not c["is_wild"]:
            normals_by_rank[c["rank"]].append(c["id"])
            normals_by_suit_rank[c["suit"]][c["rank"]].append(c["id"])

    groups = []
    seen = set()

    def register_group(group_type, ids_tuple, assigned_map):
        ids_tuple = tuple(sorted(ids_tuple))
        key = (group_type, ids_tuple, tuple(sorted(assigned_map.items())))
        if key in seen:
            return
        seen.add(key)
        value = sum(CARD_VALUES[cards[i]["rank"]] for i in ids_tuple)
        groups.append({
            "type": group_type,
            "ids": ids_tuple,
            "assigned": dict(assigned_map),
            "value": value
        })

    # --- Books (3–5 of same rank) ---
    for rank in CARD_ORDER:
        normals = normals_by_rank.get(rank, [])
        max_size = min(5, len(normals) + len(wild_ids))
        for size in range(3, max_size+1):
            min_normals = max(0, size - len(wild_ids))
            max_normals = min(len(normals), size)
            for k in range(min_normals, max_normals+1):
                for normals_subset in itertools.combinations(normals, k):
                    wild_needed = size - k
                    for wild_subset in itertools.combinations(wild_ids, wild_needed):
                        ids = tuple(sorted(normals_subset + wild_subset))
                        assigned = {wid: (rank, None) for wid in wild_subset}
                        register_group("book", ids, assigned)

    # --- Runs (length ≥3) ---
    suits_to_try = ["heart", "spade", "diamond", "club","star"]
    for suit in suits_to_try:
        rank_map = normals_by_suit_rank.get(suit, {})
        for start in range(len(CARD_ORDER)):
            for L in range(3, len(CARD_ORDER)-start+1):
                seq = CARD_ORDER[start:start+L]
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
                                rec(pos+1, used_normals, used_wilds | {wid}, ids_list + [wid], new_assigned)
                        else:
                            if opt in used_normals:
                                continue
                            rec(pos+1, used_normals | {opt}, used_wilds, ids_list + [opt], assigned_map)
                rec(0, frozenset(), frozenset(), [], {})

    # runs of only wilds
    if len(wild_ids) >= 3:
        for suit in suits_to_try:
            for start in range(len(CARD_ORDER)):
                for L in range(3, min(len(CARD_ORDER)-start, len(wild_ids))+1):
                    seq = CARD_ORDER[start:start+L]
                    for wild_subset in itertools.combinations(wild_ids, L):
                        assigned = {wid: (seq[i], suit) for i, wid in enumerate(wild_subset)}
                        register_group("run", tuple(sorted(wild_subset)), assigned)

    # --- DP to select disjoint groups ---
    for g in groups:
        mask = 0
        for i in g["ids"]:
            mask |= (1 << i)
        g["mask"] = mask

    @lru_cache(None)
    def dp(mask):
        best_val = 0
        best_choice = None
        for gi, g in enumerate(groups):
            if (mask & g["mask"]) == 0:
                new_mask = mask | g["mask"]
                val_next, _ = dp(new_mask)
                val_with = g["value"] + val_next
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
    for g in chosen_groups:
        card_list = [cards[i]["card"] for i in g["ids"]]
        if g["type"] == "book":
            books_out.append(card_list)
        else:
            runs_out.append(card_list)
        for wid, (as_rank, as_suit) in g["assigned"].items():
            if cards[wid]["is_wild"]:
                assigned_wilds_out.append({
                    "card": cards[wid]["card"],
                    "assigned_rank": as_rank,
                    "assigned_suit": as_suit,
                    "used_for": g["type"]
                })

    remaining_ids = [i for i in range(n) if not (mask & (1 << i))]
    remaining = [cards[i]["card"] for i in remaining_ids]
    score = sum(CARD_VALUES[cards[i]["rank"]] for i in remaining_ids)

    return {
        "books": books_out,
        "runs": runs_out,
        "assigned_wilds": assigned_wilds_out,
        "remaining": remaining,
        "score": score
    }
# score_hand_optimal([Card("heart",5),Card("heart",6),Card("heart",7)], 3)