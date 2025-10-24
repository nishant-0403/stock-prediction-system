# Small wrapper around yfinance for fetching recent data
import yfinance as yf

def fetch_ohlcv(ticker, period='1d', interval='1m'):
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval)
    # return records as dict for simplicity
    return df.reset_index().to_dict(orient='records')
