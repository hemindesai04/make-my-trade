import os
from datetime import datetime
from pathlib import Path

import pandas as pd

def transform_to_15min_bars(filepath: Path, transformedFile: Path):
    # Load the CSV file
    df = pd.read_csv(filepath, parse_dates=['timestamp'])

    df_resampled = transform_df_to_15min_bars(df=df)

    # Save the resampled data to a new CSV file
    df_resampled.to_csv(transformedFile, index=False)

def transform_df_to_15min_bars(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure the timestamp column is in datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Set the timestamp column as the index
    df.set_index('timestamp', inplace=True)

    # Resample the data to 15-minute bars
    df_resampled = df.groupby('symbol').resample('15min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'trade_count': 'sum',
        'vwap': 'mean'  # or 'last' depending on your requirements
    })

    # Reset the index to include timestamp and symbol in the columns
    df_resampled.reset_index(inplace=True)

    return df_resampled
