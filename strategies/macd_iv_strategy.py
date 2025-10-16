from strategies.base import StrategyBase


class MACDVolatilityStrategy(StrategyBase):
    def generate_signals(self, df):
        # Calculate MACD
        fast = df["close"].ewm(span=12).mean()
        slow = df["close"].ewm(span=26).mean()
        macd = fast - slow
        signal = macd.ewm(span=9).mean()
        df["macd_cross"] = (macd > signal).astype(int)

        # ATR for volatility filter
        df["atr"] = df["high"].rolling(14).max() - df["low"].rolling(14).min()

        # Trend filter with SMAs
        df["sma_50"] = df["close"].rolling(window=50).mean()
        df["sma_20"] = df["close"].rolling(window=20).mean()

        # Buy/Sell rules
        df["buy"] = (
            (df["macd_cross"] == 1)
            & (df["close"] > df["sma_20"])
            & (df["sma_20"] > df["sma_50"])
            & (df["atr"] > df["atr"].rolling(50).median())
        )
        df["sell"] = (
            (df["macd_cross"] == 0)
            & (df["close"] < df["sma_20"])
            & (df["sma_20"] < df["sma_50"])
            & (df["atr"] > df["atr"].rolling(50).median())
        )

        return df[["buy", "sell"]]

    def handle_order(self, current_price, signals, trailing_stop_pct=0.05, tp_pct=0.10):
        # Manage open position with trailing stop and take profit
        pass  # implement order management logic

    def backtest(self, historical_data):
        return super().backtest(historical_data)
