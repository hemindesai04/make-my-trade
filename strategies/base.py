from abc import ABC, abstractmethod

import pandas as pd


class StrategyBase(ABC):
    """
    Strategy class with functions to generate signals, execute trades and backtest the strategy.
    """
    @abstractmethod
    def generate_signals(self, historical_data: pd.DataFrame):
        """
        Function to generate buy/sell signals. DO NOT INCLUDE code related to allocation, risk-adjustments,
        and other order-specific information.
        """
        pass

    @abstractmethod
    def handle_order(self, current_price, signals):
        """
        Function to execute a trade based on the signals received. Include the logic to handle allocation,
        number of trades and other order-specific information.
        """
        pass

    @abstractmethod
    def backtest(self, historical_data: pd.DataFrame):
        # signals = self.generate_signals(historical_data)
        # ... backtest logic ...
        pass
