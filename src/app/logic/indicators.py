import pandas as pd
import numpy as np

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.ewm(alpha=1/period, adjust=False).mean()

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to DataFrame.
    Expects: open, high, low, close, volume on index or columns.
    Modifies df in place.
    """
    if df.empty:
        return df

    # EMA
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # RSI
    df['rsi'] = calculate_rsi(df['close'], 14)
    
    # ATR
    df['atr'] = calculate_atr(df, 14)
    
    # Volume MA
    df['vol_ma20'] = df['volume'].rolling(window=20).mean()
    
    # Bollinger Bands (20, 2)
    periods = 20
    std_dev = 2
    df['bb_mid'] = df['close'].rolling(window=periods).mean()
    df['bb_std'] = df['close'].rolling(window=periods).std()
    df['bb_upper'] = df['bb_mid'] + (df['bb_std'] * std_dev)
    df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * std_dev)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
    
    # Pivots (Recent High/Low within 20 periods)
    # Using simple rolling max/min for basic pivot detection or identifying breakout levels
    df['high_20'] = df['high'].rolling(window=20).max()
    df['low_20'] = df['low'].rolling(window=20).min()
    
    return df
