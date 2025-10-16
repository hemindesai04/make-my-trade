import pandas as pd
from strategies.base import StrategyBase


class FilteredDonchianStrategy(StrategyBase):
    """
    Donchian channel breakout strategy with:
      - Volatility filter (ATR-based)
      - Trend filter (SMA)
      - Momentum filter (short SMA)
    Positions sized based on risk and ATR.
    Only one position per direction is allowed at a time.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        initial_capital: float = 100_000,
        risk_per_trade: float = 0.005,
        stop_atr_mult: float = 2.0,
        max_notional_per_position: float = 0.10,
        min_notional: float = 10.0,
        donchian_entry: int = 20,
        donchian_exit: int = 10,
        atr_period: int = 14,
        atr_mult_entry: float = 1.5,
        sma_trend: int = 200,
        sma_mom: int = 50,
    ):
        self.data = df.copy()
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.stop_atr_mult = stop_atr_mult
        self.max_notional_per_position = max_notional_per_position
        self.min_notional = min_notional

        self.donchian_entry = donchian_entry
        self.donchian_exit = donchian_exit
        self.atr_period = atr_period
        self.atr_mult_entry = atr_mult_entry
        self.sma_trend = sma_trend
        self.sma_mom = sma_mom

        self.positions = []
        self.equity_curve = []
        self.trade_log = []

    # ------------------------
    # Signal Generation
    # ------------------------
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        assert {"high", "low", "close"}.issubset(df.columns), "Data must contain high, low, close"

        # Donchian channels using previous bars only
        df["donchian_high_entry"] = df["high"].shift(1).rolling(self.donchian_entry).max()
        df["donchian_low_exit"] = df["low"].shift(1).rolling(self.donchian_exit).min()

        # ATR calculation
        tr = pd.concat(
            [df["high"] - df["low"], (df["high"] - df["close"].shift(1)).abs(), (df["low"] - df["close"].shift(1)).abs()],
            axis=1,
        ).max(axis=1)
        df["atr"] = tr.rolling(self.atr_period, min_periods=1).mean()

        # Volatility filter
        df["today_range"] = df["high"] - df["low"]
        df["atr_median50"] = df["atr"].rolling(50, min_periods=1).median()
        df["vol_ok"] = df["today_range"] > (self.atr_mult_entry * df["atr_median50"])

        # Trend filter
        df[f"sma_trend"] = df["close"].rolling(self.sma_trend, min_periods=1).mean()
        df["trend_ok"] = df["close"] > df[f"sma_trend"]

        # Momentum filter
        df[f"sma_mom"] = df["close"].rolling(self.sma_mom, min_periods=1).mean()
        df["mom_ok"] = df["close"] > df[f"sma_mom"]

        # Signals
        df["buy"] = (df["close"] > df["donchian_high_entry"]) & df["vol_ok"] & df["trend_ok"] & df["mom_ok"]
        df["sell"] = df["close"] < df["donchian_low_exit"]

        return df[["buy", "sell", "atr", "donchian_high_entry", "donchian_low_exit"]]

    # ------------------------
    # Order Execution
    # ------------------------
    def handle_order(self, current_price, row):
        signal = 1 if row["buy"] else (-1 if row["sell"] else 0)
        atr = row["atr"]

        if signal == 0 or pd.isna(atr) or atr == 0:
            return

        # Prevent multiple positions in the same direction
        if signal == 1 and any(p["side"] == 1 and not p["closed"] for p in self.positions):
            return
        if signal == -1 and any(p["side"] == -1 and not p["closed"] for p in self.positions):
            return

        stop_distance = self.stop_atr_mult * atr
        stop_price = current_price - stop_distance if signal == 1 else current_price + stop_distance

        dollar_risk = self.capital * self.risk_per_trade
        size = dollar_risk / stop_distance
        notional = size * current_price

        if notional < self.min_notional:
            return
        if notional > self.capital * self.max_notional_per_position:
            size = (self.capital * self.max_notional_per_position) / current_price

        pos = {
            "side": signal,
            "entry_price": current_price,
            "stop_price": stop_price,
            "size": size,
            "closed": False,
            "entry_time": row.name,
        }
        self.positions.append(pos)

        # Log trade
        self.trade_log.append(
            {
                "time": row.name,
                "side": "long" if signal == 1 else "short",
                "price": current_price,
                "size": size,
                "stop_price": stop_price,
                "capital": self.capital,
            }
        )

    # ------------------------
    # Backtest
    # ------------------------
    def backtest(self, historical_data: pd.DataFrame):
        df_signals = self.generate_signals(historical_data)

        for idx, row in df_signals.iterrows():
            price = historical_data.loc[idx, "close"]

            # Check stops
            for pos in self.positions:
                if pos["closed"]:
                    continue
                if pos["side"] == 1 and historical_data.loc[idx, "low"] <= pos["stop_price"]:
                    pnl = (pos["stop_price"] - pos["entry_price"]) * pos["size"]
                    self.capital += pnl
                    pos["closed"] = True
                elif pos["side"] == -1 and historical_data.loc[idx, "high"] >= pos["stop_price"]:
                    pnl = (pos["entry_price"] - pos["stop_price"]) * pos["size"]
                    self.capital += pnl
                    pos["closed"] = True

            # Handle new signals
            self.handle_order(price, row)

            # Track equity
            unrealized = sum(
                (price - p["entry_price"]) * p["size"] if p["side"] == 1 else (p["entry_price"] - price) * p["size"]
                for p in self.positions
                if not p["closed"]
            )
            self.equity_curve.append({"time": idx, "equity": self.capital + unrealized})

        return {"capital": self.capital, "trade_log": self.trade_log, "equity_curve": self.equity_curve}
