from randomplayer import RandomPlayer
from pypokerengine.players import BasePokerPlayer
from time import sleep, time
import pprint
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import numpy as np
from _evaluation import eval_hand
import random as rand
import json
import math
from pypokerengine.utils.card_utils import HandEvaluator

# clubs (♣), spades (♠), diamonds (♦), hearts (♥)
#hole_card = ['D4', 'C4']
#community_card = ['H4', 'C5', 'C6']


class updated13Agent(BasePokerPlayer):
    file = open('weights.json', 'r')
    global weights
    weights = np.array(json.load(file)['w'])
    global actions
    actions = []
    # make decision based on the weights + evaluation of the hand
    # np.sum(W) = 1, np.sum(E) = 1, W = [W_raise, W_call, W_fold], E = [E_raise, E_call, E_fold]
    # model 1: P_raise = (W_raise + \alpha * E_raise) / sum of (W + \alpha * E), more randomness
    # if W = [0.98, 0.01, 0.01], E = [0.1, 0.8, 0.2], eval = [1.08, 0.81, 0.2] ==> [0.516, 0.386, 0.1]
    # model 2: P_raise = (W_raise * \alpha * E_raise) / sum of (W + \alpha * E), more deterministic
    # if W = [0.98, 0.01, 0.01], E = [0.1, 0.8, 0.2], eval = [0.098, 0.008, 0.002] ==> [0.9, 0.07, 0.03]
    def declare_action(self, valid_actions, hole_card, round_state):
        #global weights
        # copy the value of weights
        W = weights.copy()
        print('declare_action weights', W)
        start_time = time()
        eval = eval_hand(hole_card, round_state['community_card'])  # evaluation of the hand
        eval = eval / np.sum(eval)  # probability of raise, call, fold
        alpha = 1
        W = (W / np.sum(W)) + eval * alpha  # combine the evaluation with the weights we learned
        eval = W / np.sum(W)  # probability of raise, call, fold combined with evaluation
        end_time = time()
        #print('decision', eval)
        # print("Time: ", end_time - start_time)

        random = rand.uniform(0, 1)

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

    # return the amount of bet, initial bet in preflop for both players, and the amount of bet for each action
    def collect_bet(self, action_histories):
        my_bet = 0
        opponent_bet = 0
        preflop = action_histories['preflop']
        my_preflop_amount = 0
        opponent_preflop_amount = 0
        amount_each_action = np.array([0, 0, 0])
        # record the amount of bet in preflop for both players
        for act in preflop:
            if act['uuid'] == self.uuid:
                if act['action'] != 'FOLD':
                    my_preflop_amount = act['amount']
            else:
                if act['action'] != 'FOLD':
                    opponent_preflop_amount = act['amount']
        # record the amount of bet for each action for both players
        # record proportion of raise, call, fold of player's bet in amount_each_action
        for act in action_histories:
            amount = 0
            opponent_amount = 0
            check_action_name = 0
            for item in action_histories[act]:
                # check last two actions
                if item['uuid'] == self.uuid:
                    if item['action'] == 'FOLD':
                        check_action_name = 2
                    if item['action'] != 'FOLD':
                        amount = item['amount']
                        if item['action'] == 'RAISE':
                            check_action_name = 0
                        else:
                            check_action_name = 1
                else:
                    if item['action'] != 'FOLD':
                        opponent_amount = item['amount']
            amount_each_action[check_action_name] += amount
            my_bet += amount
            opponent_bet += opponent_amount
        return my_bet, opponent_bet, my_preflop_amount, opponent_preflop_amount, amount_each_action


    # update the weights based on the result of the round
    def receive_round_result_message(self, winners, hand_info, round_state):
        global weights
        #W = weights.copy()

        action_weights = np.array([0, 0, 0])
        all_actions = round_state["action_histories"]  # all actions in last round
        eplison = np.sqrt(np.log(3) / round_state['round_count']) / 2  # eplison for multiplicative weights update
        #pprint.pprint(round_state)
        # print(self.uuid)
        # pprint.pprint(self.collect_bet(all_actions))

        # record the times of raise, call, fold for the player in last round
        for flops in all_actions:
            #print(flops)
            for item in all_actions[flops]:
                if item['uuid'] == self.uuid:
                    if item['action'] == 'RAISE':
                        action_weights[0] += 1
                    if item['action'] == 'CALL':
                        action_weights[1] += 1
                    if item['action'] == 'FOLD':
                        action_weights[2] += 1

        has_won = winners[0]['uuid'] == self.uuid  # check if the player has won the round
        my_bet, opponent_bet, my_preflop_amount, opponent_preflop_amount, amount_each_action\
            = self.collect_bet(all_actions)

        if np.sum(action_weights) > 0:  # handle opponent fold immediately in preflop stage
            action_weights = action_weights / np.sum(action_weights)  # percentage of raise, call, fold times
            # reward actions based on how much the player has earned. i.e. call 20, raise 40, fold 0 ==> [0.33, 0.67, 0]
            # To prevent large reward increase weights too much, we divide the reward by the amount of bet in preflop
            # W = W * exp(eplison * reward percentage of each action * (reward / amount of bet in preflop))
            if has_won:
                opponent_bet = opponent_bet / opponent_preflop_amount
                # percentage mount of raise, call, fold
                amount_each_action = amount_each_action / np.sum(amount_each_action)

                weights = weights * np.exp(eplison * amount_each_action * opponent_bet)
            # if the player has lost the round, we punish the weights based on the amount of bet we lost
            # W = W * exp(eplison * reward percentage of each action * (lost / amount of bet in preflop))
            else:
                # handle fold case, this action is responsible for part of the lost
                fold_lost = my_bet * action_weights[2]
                amount_each_action = amount_each_action / np.sum(amount_each_action)
                amount_each_action = amount_each_action * (my_bet - fold_lost)
                amount_each_action[2] = fold_lost
                amount_each_action = amount_each_action / np.sum(amount_each_action)

                my_bet = my_bet / my_preflop_amount

                weights = weights * np.exp(eplison * amount_each_action * (-my_bet))
            #update the weights
            #print('weight_update', weights)
            file = open('weights.json', 'w+')
            data = { "w": [float(weights[0]), float(weights[1]), float(weights[2])] }
            print('data', data)
            json.dump(data, file)
        pass

def setup_ai():
  return RandomPlayer()