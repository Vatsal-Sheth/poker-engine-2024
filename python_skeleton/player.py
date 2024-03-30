"""
Simple example pokerbot, written in Python.
"""

import random
from typing import Optional

from skeleton.actions import Action, CallAction, CheckAction, FoldAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

class Player(Bot):
    """
    A pokerbot.
    """

    def __init__(self) -> None:
        """
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        """
        self.log = []
        pass

    def handle_new_round(self, game_state: GameState, round_state: RoundState, active: int) -> None:
        """
        Called when a new round starts. Called NUM_ROUNDS times.
        
        Args:
            game_state (GameState): The state of the game.
            round_state (RoundState): The state of the round.
            active (int): Your player's index.

        Returns:
            None
        """
        self.log = []
        self.log.append("================================")
        self.log.append("new round")
        pass

    def handle_round_over(self, game_state: GameState, terminal_state: TerminalState, active: int, is_match_over: bool) -> Optional[str]:
        """
        Called when a round ends. Called NUM_ROUNDS times.

        Args:
            game_state (GameState): The state of the game.
            terminal_state (TerminalState): The state of the round when it ended.
            active (int): Your player's index.

        Returns:
            Your logs.
        """
        self.log.append("game over")
        self.log.append("================================\n")

        return self.log

    def get_action(self, observation: dict) -> Action:
        """
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.
        """
        my_contribution = STARTING_STACK - observation["my_stack"]
        opp_contribution = STARTING_STACK - observation["opp_stack"]
        continue_cost = observation["opp_pip"] - observation["my_pip"]

        self.log.append("My cards: " + str(observation["my_cards"]))
        self.log.append("Board cards: " + str(observation["board_cards"]))
        self.log.append("My stack: " + str(observation["my_stack"]))
        self.log.append("My contribution: " + str(my_contribution))
        self.log.append("My bankroll: " + str(observation["my_bankroll"]))

        # Estimate the strength of your hand
        hand_strength = estimate_hand_strength(observation["my_cards"], observation["board_cards"])

        # Implement pot odds and pot equity considerations
        pot_odds = continue_cost / (continue_cost + opp_contribution + observation["opp_pip"])
        pot_equity = hand_strength

        if pot_equity > pot_odds:
            # Call or raise if pot odds are favorable
            if RaiseAction in observation["legal_actions"] and random.random() < 0.5:
                min_cost = observation["min_raise"] - observation["my_pip"]
                max_cost = observation["max_raise"] - observation["my_pip"]
                raise_amount = random.randint(min_cost, max_cost)
                return RaiseAction(raise_amount)
            else:
                return CallAction()
        else:
            # Fold if pot odds are not favorable
            return FoldAction()

        # Implement bluffing and semi-bluffing strategies
        if RaiseAction in observation["legal_actions"] and random.random() < 0.2:
            min_cost = observation["min_raise"] - observation["my_pip"]
            max_cost = observation["max_raise"] - observation["my_pip"]
            raise_amount = random.randint(min_cost, max_cost)
            return RaiseAction(raise_amount)

        if CheckAction in observation["legal_actions"]:
            return CheckAction()
        return CallAction()

    def estimate_hand_strength(self, my_cards: list, board_cards: list) -> float:
        """
        Estimate the strength of the hand based on the player's cards and the board cards.
        This is a simplified implementation and can be improved with more advanced techniques.
        """
        # Convert card strings to numerical values
        value_map = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
        my_values = [value_map[card[0]] for card in my_cards]
        board_values = [value_map[card[0]] for card in board_cards]

        # Calculate the hand strength based on the highest pair or high card
        all_values = my_values + board_values
        all_values.sort(reverse=True)
        strength = all_values[0] / 14.0  # Normalize the highest value to be between 0 and 1

        return strength

if __name__ == '__main__':
    run_bot(Player(), parse_args())
