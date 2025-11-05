from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends 
from pydantic import BaseModel
import requests
import os
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import UserCreate
import mysql.connector

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Regular Backend")

ML_MODEL_URL = os.getenv("ML_MODEL_URL", "http://localhost:8001/predict")

class PredictRequest(BaseModel):
    symbol: str
    period: str = "1d"
    interval: str = "1m"

class WatchlistAddRequest(BaseModel):
    user_id: int
    stock_id: int


@app.get('/health')
def health():
    return {"status": "ok"}

@app.post('/predict')
def predict(req: PredictRequest):
    payload = req.dict()
    try:
        r = requests.post(ML_MODEL_URL, json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    connection = db.connection().connection 
    cursor = connection.cursor()

    sql = "INSERT INTO User (name, email, password, telegram_id) VALUES (%s, %s, %s, %s)"
    values = (user.name, user.email, user.password, user.telegram_id)

    cursor.execute(sql, values)
    connection.commit()
    cursor.close()

    return {"message": "User registered successfully"}


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post('/login')
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(
        text("SELECT user_id, password FROM User WHERE email = :email"),
        {"email": req.email}
    ).fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user[1] != req.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    return {"message": "Login successful", "user_id": user[0]}

@app.post("/watchlist/add")
def add_to_watchlist(symbol: str, user_id: int, session=Depends(get_db)):

    if not user_id or not symbol:
        raise HTTPException(status_code=400, detail="user_id and symbol are required")

    db = SessionLocal()
    try:
        # 1) Check / Insert stock dynamically if needed
        stock = db.execute(text("SELECT stock_id FROM Stock WHERE company_name = :sym"), {"sym": symbol}).fetchone()

        if not stock:
            import yfinance as yf
            data = yf.Ticker(symbol).info
            current_price = data.get("currentPrice")
            if not current_price:
                raise HTTPException(status_code=400, detail="Invalid stock symbol")

            db.execute(text("""
                INSERT INTO Stock (company_name, current_price, last_updated)
                VALUES (:name, :price, NOW())
            """), {"name": symbol, "price": current_price})
            db.commit()
            stock = db.execute(text("SELECT stock_id FROM Stock WHERE company_name = :sym"), {"sym": symbol}).fetchone()

        stock_id = stock[0]

        # 2) Get this user’s watchlist
        wl = db.execute(text("SELECT watchlist_id FROM Watchlist WHERE user_id = :uid"),
                        {"uid": user_id}).fetchone()
        wid = wl[0]

        # 3) Add to watchlist
        db.execute(text("""
            INSERT IGNORE INTO Watchlist_Stock (watchlist_id, stock_id, date_added)
            VALUES (:wid, :sid, NOW())
        """), {"wid": wid, "sid": stock_id})
        db.commit()

        # 4) Call ML model — just return the result
        try:
            ml_payload = {"symbol": symbol.upper(), "period": "1d", "interval": "1m"}
            ml_response = requests.post("http://127.0.0.1:8001/predict", json=ml_payload)
            ml_data = ml_response.json()
            predicted_price = ml_data.get("predicted_price", None)
        except:
            predicted_price = None

        return {
            "message": "Stock added + ML prediction processed",
            "stock_id": stock_id,
            "predicted_price": predicted_price
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/watchlist/{user_id}")
def get_watchlist(user_id: int):
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT s.stock_id, s.company_name, s.current_price, ws.date_added "
                 "FROM Stock s "
                 "JOIN Watchlist_Stock ws ON s.stock_id = ws.stock_id "
                 "JOIN Watchlist w ON w.watchlist_id = ws.watchlist_id "
                 "WHERE w.user_id = :uid"),
            {"uid": user_id}
        ).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

@app.post("/watchlist/remove")
def remove_from_watchlist(data: dict):
    user_id = data.get("user_id")
    stock_id = data.get("stock_id")

    if not user_id or not stock_id:
        raise HTTPException(status_code=400, detail="user_id and stock_id are required")

    db = SessionLocal()
    try:
        wl = db.execute(text("SELECT watchlist_id FROM Watchlist WHERE user_id = :uid"),
                        {"uid": user_id}).fetchone()
        if not wl:
            raise HTTPException(status_code=404, detail="No watchlist found for user.")

        wid = wl[0]

        db.execute(text("DELETE FROM Stock_Signal WHERE watchlist_id = :wid AND stock_id = :sid"),
                   {"wid": wid, "sid": stock_id})
        db.execute(text("DELETE FROM Threshold WHERE user_id = :uid AND stock_id = :sid"),
                   {"uid": user_id, "sid": stock_id})

        result = db.execute(text("DELETE FROM Watchlist_Stock WHERE watchlist_id = :wid AND stock_id = :sid"),
                   {"wid": wid, "sid": stock_id})

        db.commit()

        if result.rowcount == 0:
            return {"message": "Stock was not in watchlist."}

        count = db.execute(text(
            "SELECT COUNT(*) FROM Watchlist_Stock WHERE stock_id = :sid"
        ), {"sid": stock_id}).scalar()

        if count == 0:
            db.execute(text("DELETE FROM Stock WHERE stock_id = :sid"), {"sid": stock_id})
            db.commit()
            return {"message": "Stock removed from watchlist and deleted from database (no longer tracked by any user.)"}

        return {"message": "Stock successfully removed from watchlist."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/threshold/set")
def set_threshold(data: dict):
    user_id = data.get("user_id")
    stock_id = data.get("stock_id")
    threshold_no = data.get("threshold_no")
    upper_limit = data.get("upper_limit")
    lower_limit = data.get("lower_limit")

    if not user_id or not stock_id or threshold_no is None:
        raise HTTPException(status_code=400, detail="user_id, stock_id, threshold_no are required")

    if upper_limit is None and lower_limit is None:
        raise HTTPException(status_code=400, detail="At least one of upper_limit or lower_limit is required")

    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO Threshold (user_id, stock_id, threshold_no, upper_limit, lower_limit)
            VALUES (:uid, :sid, :tno, :ul, :ll)
            ON DUPLICATE KEY UPDATE upper_limit = :ul, lower_limit = :ll
        """), {"uid": user_id, "sid": stock_id, "tno": threshold_no, "ul": upper_limit, "ll": lower_limit})

        db.commit()
        return {"message": "Threshold set successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/threshold/{user_id}")
def get_thresholds(user_id: int):
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT stock_id, threshold_no, upper_limit, lower_limit 
            FROM Threshold WHERE user_id = :uid
        """), {"uid": user_id}).fetchall()

        return [dict(row._mapping) for row in result]
    finally:
        db.close()
