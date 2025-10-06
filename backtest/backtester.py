import logging
import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, strategy, data, initial_capital=10000):
        self.strategy = strategy
        self.data = data
        self.initial_capital = initial_capital

    def run(self):
        try:
            if hasattr(self.strategy, "backtest"):
                results = self.strategy.backtest(self.data)
            else:
                results = self._generic_backtest()
            logging.info("Backtest completed successfully.")
            return results
        except Exception as e:
            logging.error(f"Backtest failed: {e}")
            raise

    def _generic_backtest(self):
        # Implement generic backtest logic here
        pass