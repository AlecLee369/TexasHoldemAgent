from pypokerengine.api.game import setup_config, start_poker
from randomplayer import RandomPlayer
from raise_player import RaisedPlayer
from collections import defaultdict
from io import StringIO
import sys

#TODO:config the config as our wish
config = setup_config(max_round = 10, initial_stack = 10000, small_blind_amount = 10)

config.register_player(name="f1", algorithm = RandomPlayer())
config.register_player(name="FT2", algorithm = RaisedPlayer())

# Create output buffer using StringIO()
output_buffer = StringIO()
sys.stdout = output_buffer

game_result = start_poker(config, verbose=1)

# Restore standard output
sys.stdout = sys.__stdout__

# Get the game log from the string buffer
game_log = output_buffer.getvalue().split('\n')

"""
Parse Wins Function 
- log: A log of the wins from the game result 
Returns: Number of wins and rounds
"""
def parse_wins(log):
    wins = 0
    rounds = 0
    for line in log:
        # Extracts the number of wins by looking at "won the round"
        if "won the round" in line:
            # Counter for number of rounds
            rounds += 1
            # Extracts winner
            winner = line.split("[")[1].split("]")[0]
            winner = winner.strip("'[]")
            # If the winner is our player, then add the number of wins 
            if winner == "f1":            
                wins += 1
    # Returns the number of wins and the number of rounds
    return wins, rounds

# Gets wins and total number of wins using the parse_wins function 
wins, total_rounds = parse_wins(game_log)

# Prints Total Rounds, Wins, and the percentage of wins 
print("Total Rounds:", total_rounds)
print("Wins:", wins)
print("Percentage of Wins:", (wins/total_rounds) * 100, "%")
