# Make My Trade
'Make My Trade' is a stock/crypto trading framework and flow to,
1. collect data for stocks and crypto from different data providers
2. implement strategies to generate buy/sell/hold signals
3. backtest strategies using the data collected
4. automate trades using brokers

## How to run 'Make My Trade'
### Running a Backtest

1. Install venv and dependencies (including dev): `uv sync --all-groups`
2. Source the newly created venv: `source .venv/bin/activate`
3. Edit `main.py` to select your strategy and data source.
4. Place your data in `datasets/` by using an existing data fetcher or a new one
5. Instantiate an existing strategy or a new one in `main.py` and call backtest
6. Run: `uv run main.py` to execute the strategy

## Developer Guide:

### Dependencies and Tech Stack
1. Python Version - 3.13 (as mentioned in .python-version)
2. UV for dependency and project management

### Adding a New Strategy

1. Inherit from `StrategyBase` in `strategies/base.py`.
2. Implement `generate_signals`, `handle_order`, and `backtest`.
3. Register your strategy in `main.py`.

### Adding a Data Fetcher

1. Inherit from `DataFetcherBase` in `data/fetchers/base_fetcher.py`.
2. Implement `get_historical_data`.
3. Register in `DataFetcherFactory`.

### Adding a Broker

1. Inherit from `BrokerBase` in `broker/base_broker.py`.
2. Implement `place_order`.
3. Register in `BrokerFactory`.

### Data Caching
- Data is cached in `datasets/cache/` to avoid repeated downloads.
- The key of the cache is a hash of 'symbol', 'start_date', 'end_date' and 'timeframe'