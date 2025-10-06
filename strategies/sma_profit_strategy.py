import pandas as pd

from strategies.base import StrategyBase

# -----------------------------
# SMA Crossover Strategy
# -----------------------------
class SimpleMovingAverageProfitStrategy(StrategyBase):
    """
    Simple moving average crossover strategy using the original base class interface.
    Buys when short MA crosses above long MA.
    Sells when short MA crosses below long MA, only if in profit.
    """

    def __init__(self, short_window=5, long_window=20, initial_capital=10000):
        self.short_window = short_window
        self.long_window = long_window
        self.capital = float(initial_capital)
        self.position = 0
        self.entry_price = 0
        self.trade_log = []

    # -----------------------------
    # 1️⃣ Generate Signals
    # -----------------------------
    def generate_signals(self, historical_data: pd.DataFrame):
        df = historical_data.copy()
        df['short_ma'] = df['close'].rolling(self.short_window).mean()
        df['long_ma'] = df['close'].rolling(self.long_window).mean()
        df['signal'] = None

        # Buy signal: short MA crosses above long MA
        df.loc[(df['short_ma'] > df['long_ma']) &
               (df['short_ma'].shift(1) <= df['long_ma'].shift(1)), 'signal'] = 'buy'

        # Sell signal: short MA crosses below long MA
        df.loc[(df['short_ma'] < df['long_ma']) &
               (df['short_ma'].shift(1) >= df['long_ma'].shift(1)), 'signal'] = 'sell'

        return df[['timestamp', 'close', 'signal']]

    # -----------------------------
    # 2️⃣ Handle Order
    # -----------------------------
    def handle_order(self, current_price, signal, timestamp):
        if signal == 'buy' and self.position == 0:
            self.position = 1
            self.entry_price = current_price
            self.capital -= current_price
            self.trade_log.append({'time': timestamp, 'side': 'buy', 'price': current_price})

        elif signal == 'sell' and self.position > 0:
            if current_price > self.entry_price:  # only exit if profitable
                self.position = 0
                self.capital += current_price
                self.entry_price = 0
                self.trade_log.append({'time': timestamp, 'side': 'sell', 'price': current_price})

    # -----------------------------
    # 3️⃣ Backtest
    # -----------------------------
    def backtest(self, historical_data: pd.DataFrame):
        historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'], utc=True)
        signals = self.generate_signals(historical_data)

        equity_curve = []
        for i, row in signals.iterrows():
            # Skip rows with NaN close price
            if pd.isna(row['close']):
                continue

            self.handle_order(row['close'], row['signal'], row['timestamp'])
            current_equity = self.capital + (self.position * row['close'])
            equity_curve.append({'time': row['timestamp'], 'equity': current_equity})

        equity_df = pd.DataFrame(equity_curve)
        return self.trade_log, equity_df

class SimpleMovingAverageProfitStrategy1(StrategyBase):

    """
    Simple moving average crossover strategy.
    Buys when short MA crosses above long MA.
    Sells only when in profit.
    Can work on 15-min, 1-hour, or 1-day bars.
    """
    def __init__(self, short_window=5, long_window=20):
        self.short_window = short_window
        self.long_window = long_window
        self.position = None  # 'long' or None
        self.entry_price = None
        self.trades = []

    def generate_signals(self, historical_data: pd.DataFrame):
        """
        historical_data: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        Returns: DataFrame with signals: 'buy', 'sell', or None
        """
        df = historical_data.copy()
        df['short_ma'] = df['close'].rolling(self.short_window).mean()
        df['long_ma'] = df['close'].rolling(self.long_window).mean()
        df['signal'] = None

        # Buy signal
        df.loc[(df['short_ma'] > df['long_ma']) &
               (df['short_ma'].shift(1) <= df['long_ma'].shift(1)), 'signal'] = 'buy'

        # Sell signal: only if we are in profit
        df['profit_check'] = df['close'] > self.entry_price if self.entry_price else False
        df.loc[(df['short_ma'] < df['long_ma']) & df['profit_check'], 'signal'] = 'sell'

        return df[['timestamp', 'close', 'signal']]

    def handle_order(self, current_price, signal):
        """
        Execute trades based on signals.
        """
        if signal == 'buy' and self.position is None:
            self.position = 'long'
            self.entry_price = current_price
            self.trades.append({'type': 'buy', 'price': current_price})
            # print(f"Bought at {current_price}")

        elif signal == 'sell' and self.position == 'long' and current_price > self.entry_price:
            self.position = None
            self.trades.append({'type': 'sell', 'price': current_price})
            # print(f"Sold at {current_price} for profit")
            self.entry_price = None

    def backtest(self, historical_data: pd.DataFrame):
        df_signals = self.generate_signals(historical_data)
        for _, row in df_signals.iterrows():
            self.handle_order(row['close'], row['signal'])
        return self.trades