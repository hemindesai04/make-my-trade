import pandas as pd
import numpy as np

from strategies.base import StrategyBase

class SMAStrategy(StrategyBase):
    def __init__(self, sma_period=200, balance_investment_pct=80, profit_threshold=0.20):
        """
        Initialize SMA strategy with parameters.

        Args:
            sma_period (int): Period for Simple Moving Average calculation
            balance_investment_pct (float): Percentage of balance to invest
            profit_threshold (float): Minimum profit threshold to sell (default 20%)
        """
        super().__init__()
        self.sma_period = sma_period
        self.balance_investment_pct = balance_investment_pct / 100
        self.profit_threshold = profit_threshold
        self.entry_prices = {}

    def generate_signals(self, historical_data: pd.DataFrame):
        """
        Generate buy/sell signals based on SMA crossover strategy.

        A buy signal is generated when the low price crosses above the SMA.
        A sell signal is generated when the high price crosses below the SMA.

        Args:
            historical_data (pd.DataFrame): DataFrame with OHLC data

        Returns:
            pd.DataFrame: DataFrame with signals (1 for buy, -1 for sell, 0 for hold)
        """
        # Create a copy of the data and ensure we have numeric data
        data = historical_data.copy()

        # Convert price columns to numeric, replacing any invalid values with NaN
        for col in ['open', 'high', 'low', 'close']:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            else:
                raise ValueError(f"Required column {col} not found in data")

        # Calculate SMA with proper handling of NaN values
        data['SMA'] = data['close'].rolling(window=self.sma_period, min_periods=1).mean()

        # Initialize signals column
        data['signal'] = 0

        # Calculate conditions separately for clarity
        price_above_sma = data['low'] > data['SMA']
        price_was_below_sma = data['low'].shift(1) < data['SMA'].shift(1)
        price_below_sma = data['high'] < data['SMA']

        # Generate signals using numpy where to avoid ambiguous boolean operations
        data['signal'] = np.where(
            price_above_sma & price_was_below_sma,
            1,  # Buy signal
            np.where(
                price_below_sma,
                -1,  # Sell signal
                0   # Hold
            )
        )

        return data

    def handle_order(self, current_price, signals, balance=None):
        """
        Handle order execution based on signals and available balance.

        Args:
            current_price (float): Current asset price
            signals (pd.DataFrame): DataFrame with trading signals
            balance (float, optional): Available balance for trading

        Returns:
            dict: Order details including type, volume, and price
        """
        if balance is None:
            balance = 10000  # Default balance if none provided

        # Get the latest signal
        latest_signal = signals['signal'].iloc[-1]

        if latest_signal == 0:
            return None

        # Calculate order size based on balance percentage
        if latest_signal == 1:  # Buy signal
            # Calculate volume based on balance investment percentage
            usd_to_invest = balance * self.balance_investment_pct
            volume = usd_to_invest / current_price
            return {
                'type': 'buy',
                'volume': volume,
                'price': current_price
            }
        elif latest_signal == -1:  # Sell signal
            # For sell, we assume we're selling entire position
            # The actual position size should be tracked externally
            return {
                'type': 'sell',
                'volume': None,  # This should be filled with actual position size
                'price': current_price
            }

        return None

    def backtest(self, historical_data: pd.DataFrame):
        """
        Run backtest simulation for the strategy.

        Args:
            historical_data (pd.DataFrame): OHLC data for backtesting

        Returns:
            tuple: (trades DataFrame, equity DataFrame)
        """
        # Ensure we have timestamp column and proper datetime index
        data = historical_data.copy()

        if 'timestamp' in data.columns:
            data.set_index('timestamp', inplace=True)

        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index, utc=True)

        # Sort index to ensure proper time series analysis
        data = data.sort_index()

        # Generate signals
        signals = self.generate_signals(data)

        # Initialize tracking variables
        position = 0
        balance = 10000  # Starting balance
        entry_price = None
        trades = []
        equity_curve = []

        # Iterate through the signals using iterrows for better datetime handling
        for timestamp, row in signals.iterrows():
            current_price = float(row['close'])  # Ensure price is a float
            current_signal = int(row['signal'])  # Convert signal to integer

            # Track equity at each point
            current_equity = balance
            if position > 0:
                current_equity = balance + (position * current_price)
            equity_curve.append({
                'timestamp': timestamp,
                'equity': current_equity
            })

            # Process signals
            if current_signal == 1 and position == 0:  # Buy signal and no position
                # Calculate volume based on current balance
                volume = (balance * self.balance_investment_pct) / current_price
                position = volume
                entry_price = current_price
                cost = volume * current_price
                balance -= cost
                trades.append({
                    'timestamp': timestamp,
                    'type': 'buy',
                    'price': current_price,
                    'volume': volume,
                    'cost': cost,
                    'balance': balance
                })

            elif position > 0 and current_signal == -1:  # Have position and sell signal
                profit_pct = (current_price - entry_price) / entry_price

                # Sell if minimum profit threshold is met
                if profit_pct >= self.profit_threshold:
                    revenue = position * current_price
                    realized_profit = revenue - (position * entry_price)
                    balance += revenue
                    trades.append({
                        'timestamp': timestamp,
                        'type': 'sell',
                        'price': current_price,
                        'volume': position,
                        'revenue': revenue,
                        'profit': realized_profit,
                        'profit_pct': profit_pct,
                        'balance': balance
                    })
                    position = 0
                    entry_price = None

        # Create trades DataFrame
        trades_df = pd.DataFrame(trades)
        if len(trades_df) > 0:
            trades_df.set_index('timestamp', inplace=True)

        # Create equity curve DataFrame
        equity_df = pd.DataFrame(equity_curve)
        if len(equity_df) > 0:
            equity_df.set_index('timestamp', inplace=True)

        metrics = self._calculate_metrics(trades_df, equity_df['equity'].pct_change().dropna())

        return metrics

    def _calculate_metrics(self, trades_df, daily_returns):
        """Calculate performance metrics"""
        if len(trades_df) == 0:
            return {
                'final_capital': 10000,
                'cagr': 0,
                'sharpe': 0,
                'max_drawdown': 0,
                'avg_trades_per_day': 0,
                'avg_trades_per_month': 0
            }

        # Final capital is the last balance
        final_capital = trades_df['balance'].iloc[-1]

        # Calculate CAGR
        years = (trades_df.index[-1] - trades_df.index[0]).days / 365.25
        cagr = (final_capital / 10000) ** (1/years) - 1 if years > 0 else 0

        # Calculate Sharpe Ratio (assuming risk-free rate of 0.02)
        rf = 0.02
        if len(daily_returns) > 0:
            avg_daily_return = np.mean(daily_returns)
            daily_std = np.std(daily_returns)
            sharpe = ((avg_daily_return - rf/252) / (daily_std + 1e-10)) * np.sqrt(252)
        else:
            sharpe = 0

        # Calculate Maximum Drawdown
        peak = trades_df['balance'].expanding(min_periods=1).max()
        drawdown = (trades_df['balance'] - peak) / peak
        max_drawdown = drawdown.min()

        # Calculate average trades per day/month
        total_days = (trades_df.index[-1] - trades_df.index[0]).days
        total_months = total_days / 30.44  # average month length
        num_trades = len(trades_df)

        avg_trades_per_day = num_trades / total_days if total_days > 0 else 0
        avg_trades_per_month = num_trades / total_months if total_months > 0 else 0

        return {
            'final_capital': final_capital,
            'cagr': cagr,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'avg_trades_per_day': avg_trades_per_day,
            'avg_trades_per_month': avg_trades_per_month
        }