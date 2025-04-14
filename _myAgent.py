from examples.players.random_player import RandomPlayer
from pypokerengine.players import BasePokerPlayer
from time import sleep, time
import pprint
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import numpy as np
from _evaluation import my_hand_unit, my_hand_card, check_flush, check_straight, check_fourKind_fullHouse, check_threeKind
import random as rand

# clubs (♣), spades (♠), diamonds (♦), hearts (♥)
hole_card = ['D4', 'C4']
community_card = ['H4', 'C5', 'C6']


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

    # ignore two pair, one pair, high card
    utility += np.array([0, 0.7, 0.3])
    return utility

# record start time and end time
start_time = time()
eval_hand(hole_card, community_card)
end_time = time()
print("Time: ", end_time - start_time)

def reinf_learning():
  # Implement reinforcement learning here

  # return [W of call, W of raise, W of fold]
    return


class MyPlayer(BasePokerPlayer):

    def declare_action(self, valid_actions, hole_card, round_state):
        # make decision, minimax?
        start_time = time()
        eval = eval_hand(hole_card, round_state['community_card'])
        end_time = time()
        print("Time: ", end_time - start_time)
        print("Evaluation: ", eval)
        eval = eval / np.sum(eval)  # probability of raise, call, fold
        # generate number between 0 and 1
        random = rand.uniform(0, 1)

        print("Random number: ", random)

        # check if valid_actions has raise
        action = 0
        if len(valid_actions) == 3:
            if random <= eval[0]:
                action = valid_actions[2]["action"]
            elif random <= eval[0] + eval[1]:
                action = valid_actions[1]["action"]
            else:
                action = valid_actions[0]["action"]
        else:
            if random <= eval[0]+eval[1]:
                action = valid_actions[1]["action"]
            else:
                action = valid_actions[0]["action"]
        return action

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def setup_ai():
  return RandomPlayer()