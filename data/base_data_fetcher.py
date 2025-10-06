from abc import ABC, abstractmethod
import pandas as pd
import enum
from datetime import datetime


class CryptoTicker(enum.Enum):
    BTC_USD = "BTC/USD"
    ETH_USD = "ETH/USD"
    SOL_USD = "SOL/USD"

class DataTimeFrame(enum.Enum):
    Day = "day"
    Hour = "hour"
    Minute = "min"

class DataFetcherBase(ABC):
    @abstractmethod
    def get_historical_data(self, start: datetime, end: datetime,
                            ticker: CryptoTicker, **kwargs) -> pd.DataFrame:
        pass

class DataFetcherFactory:
    @staticmethod
    def get_fetcher(client: str):
        if client == "alpaca":
            from data.fetchers.alpaca_fetcher import AlpacaFetcher
            return AlpacaFetcher()
        elif client == "kraken":
            from data.fetchers.kraken_fetcher import KrakenFetcher
            return KrakenFetcher()
        elif client == "polygon":
            from data.fetchers.polygon_fetcher import PolygonFetcher
            return PolygonFetcher()
        else:
            raise ValueError(f"Unknown data client: {client}")
