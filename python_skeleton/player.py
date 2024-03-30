"""
Sophisticated example pokerbot, written in Python.
"""

import random
import itertools
from typing import Optional
from collections import defaultdict

from skeleton.actions import Action, CallAction, CheckAction, FoldAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

class Player(Bot):
    """
    A sophisticated pokerbot.
    """

    def __init__(self) -> None:
        """
        Called when a new game starts. Called exactly once.
        """
        self.log = []
        self.opponent_model = defaultdict(lambda: 0.5)  # Initialize opponent model with default value of 0.5

    def handle_new_round(self, game_state: GameState, round_state: RoundState, active: int) -> None:
        """
        Called when a new round starts.
        """
        self.log = []
        self.log.append("================================")
        self.log.append("new round")

    def handle_round_over(self, game_state: GameState, terminal_state: TerminalState, active: int, is_match_over: bool) -> Optional[str]:
        """
        Called when a round ends.
        """
        self.update_opponent_model(terminal_state)
        self.log.append("game over")
        self.log.append("================================\n")
        return self.log

    def get_action(self, observation: dict) -> Action:
        """
        Where the magic happens - your code should implement this function.
        """
        my_contribution = STARTING_STACK - observation["my_stack"]
        opp_contribution = STARTING_STACK - observation["opp_stack"]
        continue_cost = observation["opp_pip"] - observation["my_pip"]

        self.log.append("My cards: " + str(observation["my_cards"]))
        self.log.append("Board cards: " + str(observation["board_cards"]))
        self.log.append("My stack: " + str(observation["my_stack"]))
        self.log.append("My contribution: " + str(my_contribution))
        self.log.append("My bankroll: " + str(observation["my_bankroll"]))

        # Estimate hand strength using Monte Carlo simulations
        hand_strength = self.monte_carlo_hand_strength(observation["my_cards"], observation["board_cards"])

        # Implement pot odds and pot equity considerations
        pot_odds = continue_cost / (continue_cost + opp_contribution + observation["opp_pip"])
        pot_equity = hand_strength

        # Opponent modeling and exploitation
        opponent_action_probability = self.opponent_model[observation["board_cards"]]

        if pot_equity > pot_odds:
            # Call or raise if pot odds are favorable
            if RaiseAction in observation["legal_actions"] and random.random() < (1 - opponent_action_probability):
                min_cost = observation["min_raise"] - observation["my_pip"]
                max_cost = observation["max_raise"] - observation["my_pip"]
                raise_amount = self.calculate_raise_amount(min_cost, max_cost, pot_odds, pot_equity)
                return RaiseAction(raise_amount)
            else:
                return CallAction()
        else:
            # Fold if pot odds are not favorable
            return FoldAction()

        # Implement bluffing and semi-bluffing strategies
        if RaiseAction in observation["legal_actions"] and random.random() < (opponent_action_probability * 0.3):
            min_cost = observation["min_raise"] - observation["my_pip"]
            max_cost = observation["max_raise"] - observation["my_pip"]
            raise_amount = self.calculate_raise_amount(min_cost, max_cost, pot_odds, pot_equity, bluff=True)
            return RaiseAction(raise_amount)

        if CheckAction in observation["legal_actions"]:
            return CheckAction()
        return CallAction()

    def monte_carlo_hand_strength(self, my_cards: list, board_cards: list) -> float:
        """
        Estimate the strength of the hand using Monte Carlo simulations.
        """
        # Convert card strings to numerical values
        value_map = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
        my_values = [value_map[card[0]] for card in my_cards]
        board_values = [value_map[card[0]] for card in board_cards]

        # Generate all possible remaining cards
        deck = list(range(2, 15)) * 4
        for value in my_values + board_values:
            deck.remove(value)

        # Perform Monte Carlo simulations
        win_count = 0
        num_simulations = 10000
        for _ in range(num_simulations):
            # Generate a random opponent hand
            opponent_hand = random.sample(deck, 2)
            remaining_cards = [card for card in deck if card not in opponent_hand]

            # Simulate the remaining community cards
            community_cards = board_values + random.sample(remaining_cards, 5 - len(board_values))

            # Evaluate the hands
            my_hand_rank = self.evaluate_hand(my_values, community_cards)
            opponent_hand_rank = self.evaluate_hand(opponent_hand, community_cards)

            if my_hand_rank > opponent_hand_rank:
                win_count += 1

        # Normalize the win count to get the hand strength
        hand_strength = win_count / num_simulations
        return hand_strength

    def calculate_raise_amount(self, min_cost: int, max_cost: int, pot_odds: float, pot_equity: float, bluff: bool = False) -> int:
        """
        Calculate the optimal raise amount based on pot odds, pot equity, and game theory principles.
        """
        if bluff:
            # For bluffs, raise a moderate amount to balance the risk and reward
            raise_amount = (min_cost + max_cost) // 2
        else:
            # For value bets, raise an amount that maximizes the expected value
            expected_value = pot_equity * (pot_odds / (1 - pot_odds))
            raise_amount = int(max_cost * expected_value)
            raise_amount = max(min_cost, min(max_cost, raise_amount))
        return raise_amount

    def update_opponent_model(self, terminal_state: TerminalState):
        """
        Update the opponent model based on the terminal state of the round.
        """
        previous_state = terminal_state.previous_state
        board_cards = previous_state.board_cards
        opp_hand = previous_state.hands[1]

        if opp_hand:
            # Opponent's hand was revealed
            opp_hand_strength = self.evaluate_hand(opp_hand, board_cards)
            action_probability = self.opponent_model[board_cards]

            # Update the opponent model using a simple linear update rule
            update_factor = 0.1
            self.opponent_model[board_cards] = (1 - update_factor) * action_probability + update_factor * opp_hand_strength

    @staticmethod
    def evaluate_hand(hand: list, community_cards: list) -> int:
        """
        Evaluate the strength of a hand using a simple hand ranking system.
        """
        # Combine the hand and community cards
        all_cards = hand + community_cards

        # Check for straight flush
        suits = [card % 4 for card in all_cards]
        values = [card // 4 for card in all_cards]
        for suit in range(4):
            suit_values = [value for value, s in zip(values, suits) if s == suit]
            if len(suit_values) >= 5:
                straight_flush = sorted(suit_values, reverse=True)[:5]
                if straight_flush == list(range(straight_flush[0], straight_flush[0] - 5, -1)):
                    return 8 + straight_flush[0]

        # Check for four of a kind
        value_counts = [values.count(value) for value in range(2, 15)]
        if 4 in value_counts:
            return 7 + value_counts.index(4) * 2

        # Check for full house
        if 3 in value_counts and 2 in value_counts:
            return 6 + value_counts.index(3) * 2 + value_counts.index(2)

        # Check for flush
        for suit in range(4):
            suit_values = [value for value, s in zip(values, suits) if s == suit]
            if len(suit_values) >= 5:
                flush = sorted(suit_values, reverse=True)[:5]
                return 5 + flush[0]

        # Check for straight
        straight_values = sorted(list(set(values)), reverse=True)
        for i in range(len(straight_values) - 4):
            straight = straight_values[i:i+5]
            if straight == list(range(straight[0], straight[0] - 5, -1)):
                return 4 + straight[0]

        # Check for three of a kind
        if 3 in value_counts:
            return 3 + value_counts.index(3) * 2

        # Check for two pairs
        pairs = [value for value, count in zip(range(2, 15), value_counts) if count >= 2]
        if len(pairs) >= 2:
            pairs.sort(reverse=True)
            return 2 + pairs[0] * 2 + pairs[1]

        # Check for one pair
        if 2 in value_counts:
            pair_value = value_counts.index(2) * 2
            kickers = [value for value in values if value != pair_value]
            kickers.sort(reverse=True)
            return 1 + pair_value * 2 + kickers[0]

        # High card
        values.sort(reverse=True)
        return values[0]

if __name__ == '__main__':
    run_bot(Player(), parse_args())
