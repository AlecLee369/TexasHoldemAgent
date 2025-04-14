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
# hole_card = ['D4', 'C4']
# community_card = ['H4', 'C5', 'C6']

class Group13Player(BasePokerPlayer):
    # Opens and loads the weights file for training
    #file = open('weights.json', 'r') 
    global weights
    weights = np.array([10, 5, 0.1])
    # Initialize list to store actions 
    global actions
    actions = []
    
    def declare_action(self, valid_actions, hole_card, round_state):
        # Global weights
        # Copy the value of weights
        W = weights.copy()
        print('declare_action weights', W)
        # Record the start time 
        start_time = time()
        # Evaluate stregth of hand 
        eval = eval_hand(hole_card, round_state['community_card'])
        end_time = time()
        #print("Time: ", end_time - start_time)

        # Calculate the probability of raise, call, and fold 
        eval = eval / np.sum(eval)  # probability of raise, call, fold
        W = (W / np.sum(W)) * eval
        eval = W / np.sum(W)  # probability of raise, call, fold combined with evaluation
        #print('decision', eval)

        # Generate number between 0 and 1 
        random = rand.uniform(0, 1)

        #print("Random number: ", random)

        # Check if valid_actions has raise
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
        # Return chosen action based on criteria above 
        return action 

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def collect_bet(self, action_histories):
        # Initialize my_bet and opponent_bet
        my_bet = 0
        opponent_bet = 0
        # Get preflop actions 
        preflop = action_histories['preflop']
        my_preflop_amount = 0
        opponent_preflop_amount = 0

        # Determine bet amounts 
        for act in preflop:
            if act['uuid'] == self.uuid:
                if act['action'] != 'FOLD':
                    my_preflop_amount = act['amount']
            else:
                if act['action'] != 'FOLD':
                    opponent_preflop_amount = act['amount']
        # Iterates over action histories 
        for act in action_histories:
            # Initialize amount and opponent ammount to 0 
            amount = 0
            opponent_amount = 0
            for item in action_histories[act]:
                # Check last two actions
                if item['uuid'] == self.uuid:
                    if item['action'] != 'FOLD':
                        amount = item['amount']
                else:
                    if item['action'] != 'FOLD':
                        opponent_amount = item['amount']
            # Add bet amounts 
            my_bet += amount
            opponent_bet += opponent_amount
        # Return bet amounts and preflop amounts for myself and oponent 
        return my_bet, opponent_bet, my_preflop_amount, opponent_preflop_amount

    def receive_round_result_message(self, winners, hand_info, round_state):
        # Access and initialize weights 
        global weights
        #W = weights.copy()
        action_weights = np.array([0, 0, 0])
        # Get action histories 
        all_actions = round_state["action_histories"]
        # pprint.pprint(all_actions)
        # print(self.uuid)
        # pprint.pprint(self.collect_bet(all_actions))
        # Iterates over all actions in current round 
        for flops in all_actions:
            #print(flops)
            # Count number of times each action occured 
            for item in all_actions[flops]:
                if item['uuid'] == self.uuid:
                    if item['action'] == 'RAISE':
                        action_weights[0] += 1
                    if item['action'] == 'CALL':
                        action_weights[1] += 1
                    if item['action'] == 'FOLD':
                        action_weights[2] += 1
        # Check if player has one the round 
        has_won = winners[0]['uuid'] == self.uuid
        # Collect bet ammounts 
        my_bet, opponent_bet, my_preflop_amount, opponent_preflop_amount = self.collect_bet(all_actions)
        #print("my_bet: ", my_bet, "opponent_bet: ", opponent_bet, "my_preflop_amount: ", my_preflop_amount, "opponent_preflop_amount: ", opponent_preflop_amount)
        # Update weights based on actions 
        if np.sum(action_weights) > 0:  # handle opponent fold in preflop
            action_weights = action_weights / np.sum(action_weights)  # percentage of raise, call, fold
            # eplison = np.sqrt(np.log(3) / round_state['round_count']) 
            eplison = 0.1
            if has_won:
                opponent_bet = opponent_bet / opponent_preflop_amount
                weights = weights * np.exp(eplison * action_weights * opponent_bet)
            else:
                my_bet = my_bet / my_preflop_amount
                weights = weights * np.exp(eplison * action_weights * (-my_bet))

            # action_weights = action_weights / max(np.sum(action_weights), 0.01)
            # if(action_weights[2] == 0):
            #     if has_won:
            #         weights = weights * (np.exp(action_weights * 0.001))
            #         weights = weights / np.sum(weights)
            # else:
            #     if(np.sum(action_weights) > 2):
            #         weights = (weights * (np.exp(action_weights * 0.001)))
            #         weights = weights / np.sum(weights)
            # Update JSON file for training
            # print('weight_update', weights)
            # file = open('weights.json', 'w+')
            # data = { "w": [float(weights[0]), float(weights[1]), float(weights[2])] }
            # print('data', data)
            # json.dump(data, file)
        pass

def setup_ai():
  return RandomPlayer()
