
import pandas as pd

from strategies.base import StrategyBase


class EMAcrossoverStrategy(StrategyBase):
    """
    Simple EMA crossover strategy.
    Buy when short EMA crosses above long EMA which shows uptrend.
    Sell when short EMA crosses below long EMA which shows downtrend.
    """
    def __init__(self, short_ema: int = 8, long_ema: int = 21):
        self.short_ema = short_ema
        self.long_ema = long_ema

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Compute EMAs
        df["ema_short"] = df["close"].ewm(span=self.short_ema, adjust=False).mean()
        df["ema_long"] = df["close"].ewm(span=self.long_ema, adjust=False).mean()

        # ATR for sizing (no stop-loss used)
        df["high_low"] = df["high"] - df["low"]
        df["high_close_prev"] = (df["high"] - df["close"].shift(1)).abs()
        df["low_close_prev"] = (df["low"] - df["close"].shift(1)).abs()
        df["tr"] = df[["high_low", "high_close_prev", "low_close_prev"]].max(axis=1)
        df["atr"] = df["tr"].rolling(14).mean()

        # Buy when short EMA crosses above long EMA
        df["buy"] = (df["ema_short"] > df["ema_long"]) & (df["ema_short"].shift(1) <= df["ema_long"].shift(1))

        # Sell only if in profit
        df["sell"] = False  # backtester logic will sell only if price > entry

        df["buy"] = df["buy"].fillna(False)
        df["sell"] = df["sell"].fillna(False)

        return df[["buy", "sell", "ema_short", "ema_long", "atr"]]

    def handle_order(self, current_price, signals):
        return super().handle_order(current_price, signals)

