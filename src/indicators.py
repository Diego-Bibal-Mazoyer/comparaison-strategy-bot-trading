import pandas as pd

def EMA(df: pd.DataFrame, period: int) -> pd.Series:
    """
    Moyenne mobile exponentielle sur la série 'Close'.
    """
    return df['Close'].ewm(span=period, adjust=False).mean()

def RSI(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Relative Strength Index sur 'Close'.
    Achat si RSI > 55, vente si RSI < 45 selon notre stratégie.
    """
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(span=period, adjust=False).mean()
    ma_down = down.ewm(span=period, adjust=False).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

def ATR(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range sur le dataframe OHLCV.
    """
    high_low   = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close  = (df['Low']  - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

