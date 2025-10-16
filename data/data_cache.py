import os
import pandas as pd
import hashlib


class DataCache:
    """Simple file-based cache for historical data."""

    CACHE_DIR = "datasets/cache"

    @staticmethod
    def _cache_key(symbol: str, start: str, end: str, timeframe: str) -> str:
        """Generate a unique cache key based on start_date, end_date, timeframe and symbol
        parameters."""
        key = f"{symbol}_{start}_{end}_{timeframe}"
        return hashlib.md5(key.encode()).hexdigest() + ".csv"

    @classmethod
    def get(cls, symbol: str, start: str, end: str, timeframe: str):
        """Retrieve cached data if available."""
        os.makedirs(cls.CACHE_DIR, exist_ok=True)
        fname = cls._cache_key(symbol, start, end, timeframe)
        fpath = os.path.join(cls.CACHE_DIR, fname)
        if os.path.exists(fpath):
            return pd.read_csv(fpath)
        return None

    @classmethod
    def set(cls, symbol, start, end, timeframe, df):
        """Cache the DataFrame to a CSV file."""
        os.makedirs(cls.CACHE_DIR, exist_ok=True)
        fname = cls._cache_key(symbol, start, end, timeframe)
        fpath = os.path.join(cls.CACHE_DIR, fname)
        df.to_csv(fpath, index=False)
