from datetime import datetime
from pathlib import Path
import logging

from data.base_data_fetcher import DataTimeFrame, CryptoTicker, DataFetcherFactory
from utilities.utils import transform_df_to_15min_bars
from utilities.logging import setup_logging


def run_strategy(symbol, data, logger):
    """Run SMA strategy on the given data and log results"""
    from strategies.sma_strategy import SMAStrategy
    from backtest.backtester import Backtester

    # Ensure we have OHLC columns
    required_columns = ['open', 'high', 'low', 'close']
    if not all(col in data.columns for col in required_columns):
        logger.error(f"Missing required OHLC columns in data for {symbol}")
        return None

    # Initialize strategy and backtester
    strategy = SMAStrategy(sma_period=200, balance_investment_pct=80, profit_threshold=0.20)
    backtester = Backtester(strategy=strategy, data=data)

    try:
        results = backtester.run()
        metrics = results

        logger.info(f"\n========== {symbol} Backtest Summary ==========")

        if metrics:
            if isinstance(metrics, dict):
                logger.info(f"Final Portfolio Value : ${metrics.get('final_capital', 0):,.2f}")
                logger.info(f"CAGR                  : {metrics.get('cagr', 0)*100:.2f}%")
                logger.info(f"Sharpe Ratio          : {metrics.get('sharpe', 0):.2f}")
                logger.info(f"Max Drawdown          : {metrics.get('max_drawdown', 0)*100:.2f}%")
                logger.info(f"Avg Trades / Day      : {metrics.get('avg_trades_per_day', 0):.2f}")
                logger.info(f"Avg Trades / Month    : {metrics.get('avg_trades_per_month', 0):.2f}")

        logger.info("==========================================\n")

        return metrics

    except Exception as e:
        logger.error(f"Error running strategy for {symbol}: {str(e)}")
        return None

def main():
    logger = setup_logging('AlpacaFetcher', logging.DEBUG)
    logger.info("Hello from make-my-trade!")

    # Initialize data fetcher
    alpaca_fetcher = DataFetcherFactory.get_fetcher("alpaca")

    # Fetch BTC data
    btc_df = alpaca_fetcher.get_historical_data(
        start_date=datetime(2015, 1, 1),
        end_date=datetime(2025, 12, 31),
        ticker=CryptoTicker.BTC_USD,
        timeframe=DataTimeFrame.Minute
    )
    logger.info(f"Retrieved {len(btc_df)} rows of BTC data")

    # Fetch ETH data
    eth_df = alpaca_fetcher.get_historical_data(
        start_date=datetime(2015, 1, 1),
        end_date=datetime(2025, 12, 31),
        ticker=CryptoTicker.ETH_USD,
        timeframe=DataTimeFrame.Minute
    )
    logger.info(f"Retrieved {len(eth_df)} rows of ETH data")

    # Run strategy for both symbols
    btc_results = run_strategy("BTC-USD", btc_df, logger)
    eth_results = run_strategy("ETH-USD", eth_df, logger)


    # df = from_csv("/Users/hemin/Projects/makemytrade/make-my-trade/data/crypto/eth_usd_mins_2015_2_2025.csv")
    # # strategy = FilteredDonchianStrategy(df)
    # strategy = SimpleMovingAverageProfitStrategy()
    # backtester = Backtester(strategy=strategy, data=df)
    # results = backtester.run()
    # print("Final capital:", results["metrics"]["final_capital"])
    # print("CAGR:", results["metrics"]["cagr"])
    # print("Sharpe ratio:", results["metrics"]["sharpe"])
    # print("Max drawdown:", results["metrics"]["max_drawdown"])
    # print("Avg trades/day:", results["metrics"]["avg_trades_per_day"])
    # print("Avg trades/month:", results["metrics"]["avg_trades_per_month"])
    # call to run a strategy
    # strat = DonchianATRStrategy()
    # strat = EMAcrossoverStrategy()
    # btc_df = from_csv(Path("/Users/hemin/Projects/makemytrade/make-my-trade/data/crypto/btc_usd_15mins_2015_2_2025.csv"))
    # btc_df.set_index('timestamp', inplace=True)
    # # df = strat.generate_signals(btc_df)

    # backtester = CryptoBacktester(
    #     strategy=strat,
    #     data=btc_df,  # your OHLC dataframe
    #     symbol="BTCUSDT",
    #     initial_cash=10000,
    #     fee_rate=0.001,
    #     target_risk_per_trade=100,
    #     stop_atr_mult=1.0,
    #     trail_atr_mult=2.0,
    #     take_profit_mult=3.0,
    #     max_entries_per_day=10  # increased for testing
    # )
    # results = backtester.run()
    # print("\n========== Backtest Summary ==========")
    # print(f"Final Portfolio Value : ${results['final_portfolio']:,.2f}")
    # print(f"CAGR                  : {results['cagr']*100:.2f}%")
    # print(f"Sharpe Ratio          : {results['sharpe_ratio']:.2f}")
    # print(f"Volatility (annual)   : {results['volatility']*100:.2f}%")
    # print(f"Max Drawdown          : {results['max_drawdown']*100:.2f}%")
    # print(f"Avg Trades / Day      : {results['avg_trades_per_day']:.2f}")
    # print(f"Avg Trades / Month    : {results['avg_trades_per_month']:.2f}")
    # print("======================================\n")

    # call to populate 1-min bars data of a symbol
    # eth_df = CryptoAlpacaClient().get_historical_data(datetime(2015, 9, 1), datetime(2025, 9, 23),
    #                                                   timeframe=TimeFrame.Minute, ticker=CryptoTicker.ETH_USD)
    # print(eth_df.columns)
    # eth_df = transform_df_to_15min_bars(eth_df)
    # write_csv(eth_df, Path("/Users/hemin/Projects/makemytrade/make-my-trade/data/crypto/eth_usd_mins_2015_2_2025.csv"))

    # print(btc_df)
    # call to transform 1-min bars to 15-min bars
    # transform_15min_bars(Path("/Users/hemin/Projects/makemytrade/make-my-trade/data/crypto/btc_usd_mins_2015_2_2025.csv"),
                        # Path("/Users/hemin/Projects/makemytrade/make-my-trade/data/crypto/btc_usd_15mins_2015_2_2025.csv"))


if __name__ == "__main__":
    main()
