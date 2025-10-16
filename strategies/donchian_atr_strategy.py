import pandas as pd

from strategies.base import StrategyBase


class DonchianATRStrategy(StrategyBase):
    """
    Donchian breakout + ATR volatility filter + momentum confirmation.
    - Long entries when price breaks above the N_up Donchian high
    - Exit when price breaks below the N_dn Donchian low OR hit stop/tp
    - ATR filter ensures breakout has some volatility (avoids micro-churn)
    - Optional SMA trend filter to avoid counter-trend entries
    """

    def __init__(
        self,
        donchian_entry=55,  # slow channel for entries (e.g., 55-period)
        donchian_exit=20,  # fast channel for exits (e.g., 20-period)
        atr_period=21,  # ATR lookback (21)
        atr_mult_entry=1.0,  # require today's range > atr_mult_entry * ATR median to consider entry
        sma_trend=200,  # optional long-term trend filter (set None to disable)
        sma_mom: int = 10,
    ):
        self.donchian_entry = donchian_entry
        self.donchian_exit = donchian_exit
        self.atr_period = atr_period
        self.atr_mult_entry = atr_mult_entry
        self.sma_trend = sma_trend
        self.sma_mom = sma_mom

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Ensure OHLC exists
        assert {"high", "low", "close"}.issubset(df.columns), "Data must contain high, low, close"

        # Donchian channels
        df["donchian_high_entry"] = df["high"].rolling(window=self.donchian_entry, min_periods=1).max()
        df["donchian_low_exit"] = df["low"].rolling(window=self.donchian_exit, min_periods=1).min()

        # ATR (classic)
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift(1)).abs()
        low_close = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = tr.rolling(window=self.atr_period, min_periods=1).mean()

        # Volatility filter (today range vs recent median ATR)
        df["today_range"] = df["high"] - df["low"]
        df["atr_median50"] = df["atr"].rolling(window=50, min_periods=1).median()
        df["vol_ok"] = df["today_range"] > (self.atr_mult_entry * df["atr_median50"])

        # Long-term trend filter
        if self.sma_trend is not None:
            df[f"sma_{self.sma_trend}"] = df["close"].rolling(window=self.sma_trend, min_periods=1).mean()
            df["trend_long"] = df["close"] > df[f"sma_{self.sma_trend}"]
        else:
            df["trend_long"] = True

        # Momentum confirmation (short sma)
        df[f"sma_{self.sma_mom}"] = df["close"].rolling(window=self.sma_mom, min_periods=1).mean()
        df["mom_ok"] = df["close"] > df[f"sma_{self.sma_mom}"]

        # Signals
        df["buy"] = (df["close"] > df["donchian_high_entry"]) & df["vol_ok"] & df["trend_long"] & df["mom_ok"]
        df["sell"] = df["close"] < df["donchian_low_exit"]

        # Cast to bool
        df["buy"] = df["buy"].fillna(False).astype(bool)
        df["sell"] = df["sell"].fillna(False).astype(bool)

        return df[["buy", "sell", "atr", "donchian_high_entry", "donchian_low_exit"]]

    def handle_order(self, current_price, signals):
        return super().handle_order(current_price, signals)
