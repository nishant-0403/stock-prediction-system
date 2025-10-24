# FastAPI-based regular backend (skeleton)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

app = FastAPI(title="Regular Backend")

ML_MODEL_URL = os.getenv("ML_MODEL_URL", "http://localhost:8001/predict")

class PredictRequest(BaseModel):
    symbol: str
    period: str = "1d"
    interval: str = "1m"

@app.get('/health')
def health():
    return {"status": "ok"}

@app.post('/api/predict')
def predict(req: PredictRequest):
    # In the real system, gather real-time data (yfinance), format features and call ML model service.
    payload = req.dict()
    try:
        r = requests.post(ML_MODEL_URL, json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
