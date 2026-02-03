from collections import defaultdict
from itertools import combinations

CARD_ORDER = ["3","4","5","6","7","8","9","10","J","Q","K","A"]
CARD_VALUES = {
    "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 11, "Q": 12, "K": 13, "A": 15, "★": 50
}

def is_consecutive(run):
    idxs = [CARD_ORDER.index(c[0]) for c in run]
    return all(b == a+1 for a,b in zip(idxs, idxs[1:]))

def possible_books(cards, wilds):
    result = []
    rank_groups = defaultdict(list)
    for c in cards:
        rank_groups[c[0]].append(c)
    for rank, group in rank_groups.items():
        if len(group)+wilds >= 3:
            result.append((group, 3 - len(group)))
    return result

def possible_runs(cards, wilds):
    result = []
    suit_groups = defaultdict(list)
    for c in cards:
        suit_groups[c[1]].append(c)
    for suit, group in suit_groups.items():
        group = sorted(group, key=lambda c: CARD_ORDER.index(c[0]))
        for r in range(3, len(group)+wilds+1):
            for combo in combinations(group, min(len(group),r)):
                combo = sorted(combo, key=lambda c: CARD_ORDER.index(c[0]))
                needed = 0
                for a,b in zip(combo, combo[1:]):
                    gap = CARD_ORDER.index(b[0]) - CARD_ORDER.index(a[0]) - 1
                    needed += gap
                if len(combo)+needed <= r and needed <= wilds:
                    result.append((list(combo), needed))
    return result

def score_hand(hand, round_num):
    # Determine wild cards
    wild_rank = CARD_ORDER[round_num-3]
    wild_cards = [c for c in hand if c[0] == "★" or c[0] == wild_rank]
    normal_cards = [c for c in hand if c not in wild_cards]
    wild_count = len(wild_cards)

    best_score = float('inf')
    best_solution = {"books":[],"runs":[],"remaining":hand,"score":best_score}

    def backtrack(cards, wilds, groups):
        nonlocal best_score, best_solution
        # If no cards left or all wilds used
        rem_score = sum(CARD_VALUES[c[0]] for c in cards) + wilds*50
        if rem_score >= best_score:
            return

        # Try books
        for group, need in possible_books(cards, wilds):
            if need <= wilds:
                new_cards = [c for c in cards if c not in group]
                backtrack(new_cards, wilds-need, groups+[("book", group+["wild"]*need)])

        # Try runs
        for group, need in possible_runs(cards, wilds):
            if need <= wilds:
                new_cards = [c for c in cards if c not in group]
                backtrack(new_cards, wilds-need, groups+[("run", group+["wild"]*need)])

        # If nothing more formed, score leftover
        leftover = cards[:]
        total = sum(CARD_VALUES[c[0]] for c in leftover) + wilds*50
        if total < best_score:
            best_score = total
            books = [g for t,g in groups if t=="book"]
            runs = [g for t,g in groups if t=="run"]
            best_solution = {"books":books,"runs":runs,"remaining":leftover+["wild"]*wilds,"score":total}

    backtrack(normal_cards, wild_count, [])
    return best_solution
