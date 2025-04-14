import numpy as np
from time import sleep, time
def my_hand_unit(my_hand):
    my_unit = np.array([0, 0, 0, 0])  # clubs (♣), spades (♠), diamonds (♦), hearts (♥)
    for card in my_hand:
        if card[0] == 'C':
            my_unit[0] += 1
        elif card[0] == 'S':
            my_unit[1] += 1
        elif card[0] == 'D':
            my_unit[2] += 1
        else:
            my_unit[3] += 1
    rest_unit = 13 - my_unit
    return my_unit, rest_unit


def my_hand_card(my_hand):
    my_card = np.zeros(13)
    for card in my_hand:
        if card[1] == 'A':
            my_card[12] += 1
        elif card[1] == 'T':
            my_card[8] += 1
        elif card[1] == 'J':
            my_card[9] += 1
        elif card[1] == 'Q':
            my_card[10] += 1
        elif card[1] == 'K':
            my_card[11] += 1
        else:
            my_card[int(card[1]) - 2] += 1
    rest_card = 4 - my_card
    return my_card, rest_card


def check_flush(my_unit, rest_unit, rest_community_card_num):
    max_unit = np.max(my_unit)
    max_unit_index = np.argmax(my_unit)

    if max_unit + rest_community_card_num > 5:
        if max_unit == 5:
            return np.array([1, 0, 0]), True
        if max_unit == 4:
            #p = rest_unit[max_unit_index] / np.sum(rest_unit)
            return np.array([0.7, 0.2, 0]), False
        # if max_unit == 3:
        #     # p = rest_unit[max_unit_index] / np.sum(rest_unit)
        #     # p_next = (rest_unit[max_unit_index]) / (np.sum(rest_unit) - 1)
        #     # p = p * p_next
        #     return np.array([0.2, 0.7, 0.1]), False
    return np.array([0.15, 0.7, 0.15]), False  # no flush
def check_straight(my_card, rest_card, rest_community_card_num):

    for i in range(0, 9):
        if np.sum(my_card[i:i + 5]) == 5:
            return np.array([1, 0, 0]), True
        if np.sum(my_card[i:i + 5]) == 4:
            if rest_community_card_num == 2:
                return np.array([0.7, 0.3, 0]), True
            if rest_community_card_num == 1:
                return np.array([0.5, 0.5, 0]), True
    return np.array([0.1, 0.7, 0.2]), False

def check_fourKind_fullHouse(my_card, rest_card, rest_community_card_num):
    max = np.max(my_card)
    max_index = np.argmax(my_card)
    if max == 4:  # Four of a kind
        return np.array([1, 0, 0]), True
    if max == 3 and 2 in my_card:  # Full house
        return np.array([0.8, 0.2, 0]), True
    # find index where 1 in my_card
    if max == 3:
        index = np.where(my_card == 1)[0]
        p = (np.sum(rest_card[index]) + rest_card[max_index]) / np.sum(rest_card)
        return np.array([p, 1 - p, 0]), True
    return np.array([0.1, 0.6, 0.3]), False


def check_threeKind(my_card, rest_card, rest_community_card_num):
    max = np.max(my_card)
    max_index = np.argmax(my_card)
    if max == 3:
        return np.array([0.7, 0.3, 0]), True
    if max == 2:
        index = np.where(my_card == 1)[0]
        p = rest_card[max_index] / np.sum(rest_card)
        return np.array([p, 1 - p, 0]), True
    return np.array([0.1, 0.5, 0.4]), False

def check_doublePair(my_card, rest_card, rest_community_card_num):
    two_pair = np.where(my_card == 2)[0]
    if len(two_pair) == 2:
        return np.array([0.4, 0.6, 0]), True
    return np.array([0, 0.5, 0.5]), False

# the function to evaluate the hand is based on the combination of hand and community cards,
# the intuition of this function is that three 2 are still better than any two pairs of cards, so consideration of the
# combination of the cards is more suitable in this case.
# This function is pyramidical structure, we first check the highest rank, then the second highest rank, and so on.
# For example, we check a royal flush or potential royal flush first. If we can get a royal flush or potential royal flush,
# we definitely will to raise bet, so we return a hardcode utility immediately. [P_raise > P_call, P_fold]
# otherwise, we store a conservative utility [P_raise < P_call ≈ P_fold] in accumulator utility, and continue to check the next rank.
# if we can't get any high rank or potential high rank, we return the accumulated utility at the end.
# this accumulated utility is the probability of raise, call, fold where [P_raise <<< P_call ≈ P_fold].

def eval_hand(hole_card, community_card):
    # Evaluate your best hand with the combination of hole and community cards
    # Return a number between 0 and 1
    # hole_card example ['D4', 'D7'], community_card example ['D3', 'C5', 'C6']

    my_hand = hole_card + community_card
    my_unit, rest_unit = my_hand_unit(my_hand)
    my_card, rest_card = my_hand_card(my_hand)
    rest_card_num = np.sum(rest_unit)
    rest_community_card_num = 5 - len(community_card)

    # rank: Royal flush, Straight flush, Four of a kind, Full house,
    # Flush, Straight, Three of a kind, Two pair, One pair, High card
    # check probability of getting a flush

    utility = np.array([0, 0, 0])

    flush_utility, flush = check_flush(my_unit, rest_unit, rest_community_card_num)
    straight_utility, straight = check_straight(my_card, rest_card, rest_community_card_num)
    if flush and straight:  # potential Royal flush and Straight flush
        #utility = flush_utility + straight_utility
        return np.array([1, 0, 0])
    utility = flush_utility + straight_utility  # no Royal flush or Straight flush

    four_full_utility, four_full = check_fourKind_fullHouse(my_card, rest_card, rest_community_card_num)
    if four_full:
        return four_full_utility
    utility += four_full_utility  # no four of a kind or full house
    if flush:
        return flush_utility
    if straight:
        return straight_utility

    # check Three of a kind
    three_kind_utility, three_kind = check_threeKind(my_card, rest_card, rest_community_card_num)
    if three_kind:
        return three_kind_utility
    utility += three_kind_utility  # no three of a kind
    doublePair_utility, doublePair = check_doublePair(my_card, rest_card, rest_community_card_num)
    if doublePair:
        return doublePair_utility
    # ignore two pair, one pair, high card, return accumulated utility
    utility += doublePair_utility
    return utility


hole_card = ['D4', 'C4']
community_card = ['H4', 'C5', 'C6']
# record start time and end time
start_time = time()
eval_hand(hole_card, community_card)
end_time = time()
print("Time: ", end_time - start_time)