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
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Regular Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ML_MODEL_URL = os.getenv("ML_MODEL_URL", "http://localhost:8001/predict")

class PredictRequest(BaseModel):
    symbol: str
    history_days: int = 60

class WatchlistRemoveRequest(BaseModel):
    user_id: int
    stock_id: int

class WatchlistAdd(BaseModel):
    symbol: str
    user_id: int

class WatchlistGet(BaseModel):
    user_id: int

class LoginRequest(BaseModel):
    email: str
    password: str

class ThresholdGet(BaseModel):
    user_id: int



def update_stock_price(db, stock_id, symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if not data.empty:
            price = float(data["Close"].iloc[-1])
            db.execute(
                text("UPDATE Stock SET current_price = :p, last_updated = NOW() WHERE stock_id = :id"),
                {"p": price, "id": stock_id}
            )
            db.commit()
            return price
    except Exception as e:
        print("Price update error:", e)
    return None


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
def register_user(req: UserCreate, db: Session = Depends(get_db)):
    connection = db.connection().connection
    cursor = connection.cursor()

    # 1. Insert user
    sql = """
        INSERT INTO User (name, email, password, telegram_id)
        VALUES (%s, %s, %s, %s)
    """
    values = (req.name, req.email, req.password, req.telegram_id)
    cursor.execute(sql, values)
    user_id = cursor.lastrowid

    # 2. Create empty watchlist for this user
    cursor.execute("INSERT INTO Watchlist (user_id) VALUES (%s)", (user_id,))

    connection.commit()
    cursor.close()

    # 3. Return the same structure as /login
    return {
        "message": "User registered successfully",
        "user_id": user_id,
        "name": req.name,
        "email": req.email
    }

@app.post('/login')
def login(req: LoginRequest, db: Session = Depends(get_db)):

    # Fetch name, email, and password for validation and frontend display
    user = db.execute(
        text("SELECT name, email, user_id, password FROM User WHERE email = :email"),
        {"email": req.email}
    ).fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # user = (name, email, user_id, password)
    name, email, user_id, stored_password = user

    if stored_password != req.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    # Return everything the frontend needs
    return {
        "message": "Login successful",
        "user_id": user_id,
        "name": name,
        "email": email
    }


@app.post("/watchlist/add")
def add_to_watchlist(data: WatchlistAdd, session=Depends(get_db)):
    symbol = data.symbol
    user_id = data.user_id

    if not user_id or not symbol:
        raise HTTPException(status_code=400, detail="user_id and symbol are required")

    db = SessionLocal()
    try:
        # 1) Check / Insert stock dynamically if needed
        stock = db.execute(
            text("SELECT stock_id FROM Stock WHERE company_name = :sym"),
            {"sym": symbol}
        ).fetchone()

        if not stock:
            import yfinance as yf
            data_yf = yf.Ticker(symbol).info
            current_price = data_yf.get("currentPrice")
            if not current_price:
                raise HTTPException(status_code=400, detail="Invalid stock symbol")

            db.execute(text("""
                INSERT INTO Stock (company_name, current_price, last_updated)
                VALUES (:name, :price, NOW())
            """), {"name": symbol, "price": current_price})
            db.commit()
            stock = db.execute(
                text("SELECT stock_id FROM Stock WHERE company_name = :sym"),
                {"sym": symbol}
            ).fetchone()

        stock_id = stock[0]

        # 2) Get this user’s watchlist
        wl = db.execute(
            text("SELECT watchlist_id FROM Watchlist WHERE user_id = :uid"),
            {"uid": user_id}
        ).fetchone()
        wid = wl[0]

        # 3) Add to watchlist
        db.execute(text("""
            INSERT IGNORE INTO Watchlist_Stock (watchlist_id, stock_id, date_added)
            VALUES (:wid, :sid, NOW())
        """), {"wid": wid, "sid": stock_id})
        db.commit()

        # 4) Call ML model — use the configured ML_MODEL_URL
        try:
            ml_payload = {"symbol": symbol.upper(), "history_days": 60}
            ml_response = requests.post(ML_MODEL_URL, json=ml_payload, timeout=10)
            ml_response.raise_for_status()
            ml_data = ml_response.json()
            predicted_price = ml_data.get("predicted_price")
        except Exception as e:
            print("ML error while adding to watchlist:", e)
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


@app.post("/watchlist")
def get_watchlist(data: WatchlistGet):
    user_id = data.user_id
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                "SELECT s.stock_id, s.company_name, s.current_price, ws.date_added "
                "FROM Stock s "
                "JOIN Watchlist_Stock ws ON s.stock_id = ws.stock_id "
                "JOIN Watchlist w ON w.watchlist_id = ws.watchlist_id "
                "WHERE w.user_id = :uid"
            ),
            {"uid": user_id}
        ).fetchall()

        watchlist = []
        for row in rows:
            r = row._mapping
            symbol = r["company_name"]
            stock_id = r["stock_id"]

	    # update price before sending
            new_price = update_stock_price(db, stock_id, symbol)
            price = new_price if new_price else float(r["current_price"])

            watchlist.append({
        	"stock_id": stock_id,
        	"symbol": symbol,
        	"name": symbol,
        	"current_price": price,
        	"change_percent": 0.0,
            })
        return watchlist
    finally:
        db.close()


@app.get("/watchlist/{user_id}")
def get_watchlist_get(user_id: int):
    """
    GET wrapper so the frontend can call /watchlist/{user_id}
    """
    return get_watchlist(WatchlistGet(user_id=user_id))


@app.post("/watchlist/remove")
def remove_from_watchlist(data: WatchlistRemoveRequest):
    # FIX: use Pydantic model attributes instead of dict.get
    user_id = data.user_id
    stock_id = data.stock_id

    if not user_id or not stock_id:
        raise HTTPException(status_code=400, detail="user_id and stock_id are required")

    db = SessionLocal()
    try:
        wl = db.execute(
            text("SELECT watchlist_id FROM Watchlist WHERE user_id = :uid"),
            {"uid": user_id}
        ).fetchone()
        if not wl:
            raise HTTPException(status_code=404, detail="No watchlist found for user.")

        wid = wl[0]

        db.execute(
            text("DELETE FROM Stock_Signal WHERE watchlist_id = :wid AND stock_id = :sid"),
            {"wid": wid, "sid": stock_id}
        )
        db.execute(
            text("DELETE FROM Threshold WHERE user_id = :uid AND stock_id = :sid"),
            {"uid": user_id, "sid": stock_id}
        )

        result = db.execute(
            text("DELETE FROM Watchlist_Stock WHERE watchlist_id = :wid AND stock_id = :sid"),
            {"wid": wid, "sid": stock_id}
        )

        db.commit()

        if result.rowcount == 0:
            return {"message": "Stock was not in watchlist."}

        count = db.execute(
            text("SELECT COUNT(*) FROM Watchlist_Stock WHERE stock_id = :sid"),
            {"sid": stock_id}
        ).scalar()

        if count == 0:
            db.execute(
                text("DELETE FROM Stock WHERE stock_id = :sid"),
                {"sid": stock_id}
            )
            db.commit()
            return {
                "message": "Stock removed from watchlist and deleted from database (no longer tracked by any user.)"
            }

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
        raise HTTPException(
            status_code=400,
            detail="user_id, stock_id, threshold_no are required"
        )

    if upper_limit is None and lower_limit is None:
        raise HTTPException(
            status_code=400,
            detail="At least one of upper_limit or lower_limit is required"
        )

    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO Threshold (user_id, stock_id, threshold_no, upper_limit, lower_limit)
            VALUES (:uid, :sid, :tno, :ul, :ll)
            ON DUPLICATE KEY UPDATE upper_limit = :ul, lower_limit = :ll
        """), {
            "uid": user_id,
            "sid": stock_id,
            "tno": threshold_no,
            "ul": upper_limit,
            "ll": lower_limit
        })

        db.commit()
        return {"message": "Threshold set successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/threshold")
def get_thresholds(data: ThresholdGet):
    user_id = data.user_id
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT stock_id, threshold_no, upper_limit, lower_limit
                FROM Threshold WHERE user_id = :uid
            """),
            {"uid": user_id}
        ).fetchall()

        return [dict(row._mapping) for row in result]
    finally:
        db.close()


@app.get("/threshold/{user_id}")
def get_thresholds_get(user_id: int):
    """
    GET wrapper so the frontend can call /threshold/{user_id}
    """
    return get_thresholds(ThresholdGet(user_id=user_id))


@app.get("/stocks/available")
def get_available_stocks():
    db = SessionLocal()
    try:
        rows = db.execute(
            text("SELECT stock_id, company_name, current_price FROM Stock")
        ).fetchall()

        stocks = []
        for row in rows:
            r = row._mapping
            stocks.append({
                "stock_id": r["stock_id"],
                "symbol": r["company_name"],
                "name": r["company_name"],   # again, you can later change this to a nicer display name
                "current_price": float(r["current_price"]),
                "change_percent": 0.0,       # placeholder
            })
        return stocks
    finally:
        db.close()


@app.get("/stocks/{stock_id}/check-threshold/{user_id}")
def check_threshold(stock_id: int, user_id: int):
    db = SessionLocal()
    try:
        # Get stock info
        stock_row = db.execute(
            text("SELECT company_name, current_price FROM Stock WHERE stock_id = :sid"),
            {"sid": stock_id}
        ).fetchone()

        if not stock_row:
            raise HTTPException(status_code=404, detail="Stock not found")

        symbol = stock_row[0]
        current_price = float(stock_row[1])

        # Get thresholds for this user & stock
        rows = db.execute(
            text("""
                SELECT threshold_no, upper_limit, lower_limit
                FROM Threshold
                WHERE user_id = :uid AND stock_id = :sid
            """),
            {"uid": user_id, "sid": stock_id}
        ).fetchall()

        breaches = []
        for row in rows:
            t = row._mapping
            upper = t["upper_limit"]
            lower = t["lower_limit"]

            if upper is not None and current_price > float(upper):
                breaches.append({
                    "symbol": symbol,
                    "type": "UPPER",
                    "limit": float(upper),
                    "current_price": current_price,
                    "threshold_no": t["threshold_no"],
                })

            if lower is not None and current_price < float(lower):
                breaches.append({
                    "symbol": symbol,
                    "type": "LOWER",
                    "limit": float(lower),
                    "current_price": current_price,
                    "threshold_no": t["threshold_no"],
                })

        return {"breaches": breaches}
    finally:
        db.close()

