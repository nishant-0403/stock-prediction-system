from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI(title="ML Service (Realtime Price)")

FINNHUB_API_KEY = os.getenv("FINNHUB_KEY", "d40hqn1r01qqo3qi4argd40hqn1r01qqo3qi4as0")
FINNHUB_URL = "https://finnhub.io/api/v1/quote"

@app.get("/health")
def health():
    return {"status": "ml-service-ok"}

@app.post("/predict")
def predict(req: dict):
    symbol = req.get("symbol")
    if not symbol:
        raise HTTPException(status_code=400, detail="Missing 'symbol' in request")

    r = requests.get(FINNHUB_URL, params={
        "symbol": symbol,
        "token": FINNHUB_API_KEY
    })

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Finnhub error: " + r.text)

    data = r.json()

    return {
        "symbol": symbol,
        "predicted_price": data.get("c"),
        "confidence": 1.0 
    }
