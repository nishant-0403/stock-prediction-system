# Minimal ML model service (stub). Replace with real model loading/training.
from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np

app = FastAPI(title='ML Model Service')

class MLRequest(BaseModel):
    symbol: str
    period: str = '1d'
    interval: str = '1m'

@app.post('/predict')
def predict(req: MLRequest):
    # Dummy predictor: returns a simple moving-average-based 'prediction' and a signal
    # In production, load your model and apply to features.
    dummy_price = 100.0 + (hash(req.symbol) % 10)
    prediction = dummy_price + np.random.randn() * 0.5
    signal = 'BUY' if prediction > dummy_price else 'SELL'
    return {'symbol': req.symbol, 'prediction': float(prediction), 'signal': signal}
