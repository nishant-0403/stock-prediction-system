from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import yfinance as yf
import numpy as np
import joblib
from utils import build_features_for_symbol
from typing import Optional

app = FastAPI(title="ML Stock Service (RandomForest)")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

class PredictRequest(BaseModel):
    symbol: str
    history_days: Optional[int] = 60  # how many days of history to fetch for feature creation

def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Run train_model.py first.")
    model = joblib.load(MODEL_PATH)
    return model

@app.get("/health")
def health():
    return {"status": "ml-service-ok"}

@app.post("/predict")
def predict(req: PredictRequest):
    symbol = req.symbol.upper().strip()
    if not symbol:
        raise HTTPException(status_code=400, detail="Missing 'symbol' in request")

    # 1) Download historical data
    try:
        period_days = max(30, req.history_days)
        data = yf.download(symbol, period=f"{period_days}d", interval="1d", progress=False)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error fetching historical data: {e}")

    if data is None or data.empty or "Close" not in data:
        raise HTTPException(status_code=404, detail=f"No historical data found for symbol '{symbol}'")

    # 2) Build features (features as used by train_model.py)
    X = build_features_for_symbol(data)
    if X is None or len(X) == 0:
        raise HTTPException(status_code=500, detail="Failed to build features from downloaded data")

    # Use the last available row for prediction (most recent features)
    X_last = X[-1].reshape(1, -1)

    # 3) Load model
    try:
        model = load_model()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model: {e}")

    # 4) Predict
    try:
        pred = model.predict(X_last)[0]
        # estimate a simple "confidence" based on spread of tree predictions (for RandomForest)
        try:
            # some regressors (RandomForest) have estimators_
            if hasattr(model, "estimators_"):
                tree_preds = np.array([t.predict(X_last)[0] for t in model.estimators_])
                std = float(np.std(tree_preds))
                mean = float(np.mean(tree_preds))
                # confidence: 1 - normalized std (clamped 0..1). heuristic only.
                conf = 1.0 - (std / (abs(mean) + 1e-8))
                conf = max(0.0, min(1.0, conf))
            else:
                conf = 0.5
        except Exception:
            conf = 0.5

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")

    return {
        "symbol": symbol,
        "predicted_price": float(pred),
        "confidence": float(conf),
        "model": getattr(model, "__class__", type(model)).__name__
    }

