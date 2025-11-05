"""
train_model.py

Downloads historical data for a set of symbols, creates features and a training
dataset, trains a RandomForestRegressor to predict next-day Close price, and
saves the model to model.pkl.

Usage:
    python train_model.py

Notes:
- Training uses multiple symbols to get more samples. This is a simple baseline
  approach (not financial advice). For production you'd use more careful splits,
  leakage checks, and symbol-specific models.
"""
import joblib
import os
import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from utils import build_features_for_symbol

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

# You can extend this list with more liquid tickers
DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "UNH", "V"
]

def create_dataset(symbols, period="2y"):
    X_list = []
    y_list = []
    for sym in symbols:
        print(f"Downloading {sym} historical data...")
        try:
            df = yf.download(sym, period=period, interval="1d", progress=False)
        except Exception as e:
            print(f"  failed to download {sym}: {e}")
            continue

        if df is None or df.empty:
            print(f"  no data for {sym}")
            continue

        # build features
        X = build_features_for_symbol(df)
        if X is None or len(X) == 0:
            continue

        # target: next day's close. align by shifting -1
        closes = df["Close"].values
        # Because build_features_for_symbol dropped initial NaNs, compute matching y:
        # Reconstruct the dates used in X: build_features uses dropna, so find the index offset
        df2 = df.copy()
        df2["close"] = df2["Close"]
        df2["prev_close"] = df2["close"].shift(1)
        df2["pct_change"] = df2["close"] / df2["prev_close"] - 1
        df2["ma_3"] = df2["close"].rolling(window=3).mean()
        df2["ma_7"] = df2["close"].rolling(window=7).mean()
        df2["ma_14"] = df2["close"].rolling(window=14).mean()
        df2["vol_7"] = df2["pct_change"].rolling(window=7).std()
        df2["mom_7"] = df2["close"] - df2["close"].shift(7)
        feat_cols = ["close", "pct_change", "ma_3", "ma_7", "ma_14", "vol_7", "mom_7"]
        df_feats = df2[feat_cols].dropna()

        # y is next day's close. So shift -1 and drop last row
        y = df_feats["close"].shift(-1).dropna().values
        X_clean = df_feats[:-1].values  # drop last row because its y is missing

        if len(X_clean) != len(y):
            # safety
            minlen = min(len(X_clean), len(y))
            X_clean = X_clean[:minlen]
            y = y[:minlen]

        X_list.append(X_clean)
        y_list.append(y)

    if not X_list:
        raise RuntimeError("No data collected for any symbol.")

    X_all = np.vstack(X_list)
    y_all = np.hstack(y_list)
    return X_all, y_all

def train_and_save(symbols=DEFAULT_SYMBOLS, period="2y"):
    print("Preparing dataset...")
    X, y = create_dataset(symbols, period=period)
    print(f"Dataset prepared. Samples: {len(y)}, Features: {X.shape[1]}")

    # train / test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.12, random_state=42)

    # model
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    print("Training RandomForestRegressor...")
    model.fit(X_train, y_train)

    # eval
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    mse = mean_squared_error(y_test, preds)
    rmse = mse ** 0.5
    print(f"Eval -> MAE: {mae:.4f}, RMSE: {rmse:.4f}")

    # save
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_and_save()

