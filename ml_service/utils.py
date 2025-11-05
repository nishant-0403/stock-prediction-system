import numpy as np
import pandas as pd

def build_features_for_symbol(df: pd.DataFrame) -> np.ndarray:
    """
    Given a dataframe from yfinance with a 'Close' column indexed by date,
    produce a numpy array of feature vectors. Each row corresponds to features
    for a day t used to predict day t+1 close in training.
    
    Features used:
    - last close
    - pct change (close / prev_close - 1)
    - 3-day MA
    - 7-day MA
    - 14-day MA
    - 7-day volatility (std of returns)
    - momentum (close - close_7)
    
    Returns numpy array of shape (n_samples, n_features).
    """
    if df is None or df.empty:
        return np.array([])

    df = df.copy()
    # ensure Close exists
    if "Close" not in df.columns:
        raise ValueError("Input df must contain 'Close' column")

    df["close"] = df["Close"]
    df["prev_close"] = df["close"].shift(1)
    df["pct_change"] = df["close"] / df["prev_close"] - 1
    df["ma_3"] = df["close"].rolling(window=3).mean()
    df["ma_7"] = df["close"].rolling(window=7).mean()
    df["ma_14"] = df["close"].rolling(window=14).mean()
    df["vol_7"] = df["pct_change"].rolling(window=7).std()
    df["mom_7"] = df["close"] - df["close"].shift(7)

    feat_cols = ["close", "pct_change", "ma_3", "ma_7", "ma_14", "vol_7", "mom_7"]
    X = df[feat_cols].dropna().values

    return X

