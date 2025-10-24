# Stock Prediction System

Architecture: dashboard frontend ↔ regular backend (FastAPI) ↔ Yahoo (yfinance) & MySQL.
Notifications module sends signals to users via Telegram Bot API. ML model is a separate microservice that receives real-time data and returns predictions.

This repository is a skeleton meant to match the architecture you provided. It contains:
- `backend/` - FastAPI-based regular backend + notifications module
- `ml_model/` - simple ML microservice (stub) exposing a /predict REST endpoint
- `frontend/` - dashboard skeleton / notes
- `docker-compose.yml` - local orchestration (backend, ml_model, mysql)
- `architecture.jpeg` - add your architecture image here (already provided separately)

## How to use (quick)
1. Copy `.env.example` -> `.env` and set `MYSQL_ROOT_PASSWORD`, `TELEGRAM_BOT_TOKEN`, etc.
2. `docker compose up --build` to bring up mysql, backend and ml_model (development).
3. Backend exposes REST endpoints on port 8000; ml_model on port 8001.

## Important notes
- This is a starter skeleton. You should replace the stub logic with real DB models, ML code, authentication, and production-grade config.
- See `backend/` and `ml_model/` folders for runnable examples.
