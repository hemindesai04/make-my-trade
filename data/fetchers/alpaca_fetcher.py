from data.base_data_fetcher import DataFetcherBase, CryptoTicker, DataTimeFrame
from data.data_cache import DataCache
from utilities.logging import setup_logging

from datetime import datetime
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.historical import StockHistoricalDataClient
import pandas as pd
import logging
import os
from dotenv import load_dotenv


class AlpacaFetcher(DataFetcherBase):
    def __init__(self):
        # No keys required for crypto data
        load_dotenv()  # Load environment variables from .env file
        api_key = os.getenv("ALPACA_API_KEY")
        api_secret = os.getenv("ALPACA_API_SECRET")
        self.crypto_client = CryptoHistoricalDataClient()
        self.stock_client = StockHistoricalDataClient(api_key, api_secret)
        self.logger = setup_logging("AlpacaFetcher", logging.DEBUG)

    def get_historical_crypto_data(
        self, start_date: datetime, end_date: datetime, ticker: CryptoTicker, **kwargs
    ) -> pd.DataFrame:
        try:
            # Get timeframe from kwargs or use default
            timeframe: TimeFrame = self._get_alpaca_time_frame(kwargs.get("timeframe", DataTimeFrame.Day))

            self.logger.debug(f"Fetching data for {ticker.value} from {start_date} to {end_date} with timeframe {timeframe}")

            # Check cache first
            self.logger.debug("Checking cache for existing data")
            cached_data = DataCache.get(
                symbol=ticker.value,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                timeframe=str(timeframe),
            )

            if cached_data is not None:
                self.logger.info(f"Retrieved cached data for {ticker.value}")
                self.logger.debug(f"Cached data shape: {cached_data.shape}")
                return cached_data

            self.logger.info(f"No cached data found for {ticker.value}, fetching from Alpaca")

            # Creating request object if not in cache
            request_params = CryptoBarsRequest(
                symbol_or_symbols=[ticker.value], timeframe=timeframe, start=start_date, end=end_date
            )

            # Retrieve bars for the crypto in a DataFrame
            self.logger.debug("Sending request to Alpaca API")
            crypto_bars = self.crypto_client.get_crypto_bars(request_params).df
            self.logger.info(f"Successfully retrieved {len(crypto_bars)} bars from Alpaca")

            # Reset index to add 'timestamp' column to the dataframe
            crypto_bars = crypto_bars.reset_index()
            self.logger.debug("Reset index to add timestamp column")

            # Convert timezone
            crypto_bars["timestamp"] = crypto_bars["timestamp"].dt.tz_convert("US/Pacific")  # convert to desired TZ
            self.logger.debug("Converted timestamps to US/Pacific timezone")

            # Cache the data before returning
            self.logger.debug("Caching the retrieved data")
            DataCache.set(
                symbol=ticker.value,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                timeframe=str(timeframe),
                df=crypto_bars,
            )
            self.logger.info(f"Successfully cached data for {ticker.value}")

            return crypto_bars

        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker.value}: {str(e)}", exc_info=True)
            raise

    def get_historical_stocks_data(self, start_date: datetime, end_date: datetime, ticker: str, **kwargs) -> pd.DataFrame:
        """
        Fetch historical stock data from Alpaca.

        Args:
            start_date (datetime): Start date for the data
            end_date (datetime): End date for the data
            ticker (str): Stock ticker symbol
            **kwargs: Additional arguments including timeframe

        Returns:
            pd.DataFrame: Historical stock data
        """
        try:
            # Get timeframe from kwargs or use default
            timeframe: TimeFrame = self._get_alpaca_time_frame(kwargs.get("timeframe", DataTimeFrame.Day))

            self.logger.debug(f"Fetching stock data for {ticker} from {start_date} to {end_date} with timeframe {timeframe}")

            # Check cache first
            self.logger.debug("Checking cache for existing stock data")
            cached_data = DataCache.get(
                symbol=ticker,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                timeframe=str(timeframe),
            )

            if cached_data is not None:
                self.logger.info(f"Retrieved cached stock data for {ticker}")
                self.logger.debug(f"Cached data shape: {cached_data.shape}")
                return cached_data

            self.logger.info(f"No cached data found for {ticker}, fetching from Alpaca")

            # Creating request object
            request_params = StockBarsRequest(
                symbol_or_symbols=[ticker],
                timeframe=timeframe,
                start=start_date,
                end=end_date,
                adjustment="all",  # Include all adjustments (splits, dividends)
            )

            # Retrieve bars for the stock in a DataFrame
            self.logger.debug("Sending request to Alpaca API")
            stock_bars = self.stock_client.get_stock_bars(request_params).df
            self.logger.info(f"Successfully retrieved {len(stock_bars)} bars from Alpaca")

            # Reset index to add 'timestamp' column to the dataframe
            stock_bars = stock_bars.reset_index()
            self.logger.debug("Reset index to add timestamp column")

            # Convert timezone
            stock_bars["timestamp"] = stock_bars["timestamp"].dt.tz_convert("US/Pacific")  # convert to desired TZ
            self.logger.debug("Converted timestamps to US/Pacific timezone")

            # Cache the data before returning
            self.logger.debug("Caching the retrieved stock data")
            DataCache.set(
                symbol=ticker,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                timeframe=str(timeframe),
                df=stock_bars,
            )
            self.logger.info(f"Successfully cached stock data for {ticker}")

            return stock_bars

        except Exception as e:
            self.logger.error(f"Error fetching stock data for {ticker}: {str(e)}", exc_info=True)
            raise

    def _get_alpaca_time_frame(self, timeframe: DataTimeFrame) -> TimeFrame:
        if timeframe == DataTimeFrame.Day:
            return TimeFrame.Day
        elif timeframe == DataTimeFrame.Hour:
            return TimeFrame.Hour
        elif timeframe == DataTimeFrame.Minute:
            return TimeFrame.Minute
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
