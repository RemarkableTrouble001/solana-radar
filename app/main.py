import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from .config import settings
from .db import init_db, top_signals, token_history, stats
from .service import service, poller
from .backtest import run_backtest

BASE_DIR = Path(__file__).resolve().parents[1]

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(poller())
    app.state.poller_task = task
    try:
        yield
    finally:
        task.cancel()
        try: await task
        except asyncio.CancelledError: pass

app = FastAPI(title="Solana Radar V1", version="1.1.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status":"ok","service":"solana-radar-v1","last_error":service.last_error,"last_processed":service.last_processed}

@app.get("/api/status")
def status():
    return stats()

@app.post("/api/refresh")
async def refresh():
    try:
        result = await service.refresh()
        return {"status":"ok", **result}
    except Exception as exc:
        service.last_error = str(exc)
        raise HTTPException(status_code=502, detail="refresh failed")

@app.get("/api/radar")
def radar(limit: int = Query(25, ge=1, le=100)):
    return [dict(x) for x in top_signals(limit)]

@app.get("/api/backtest")
def backtest(threshold: float = Query(70, ge=0, le=100), horizon_minutes: int = Query(60, ge=1, le=10080)):
    return run_backtest(threshold, horizon_minutes)

@app.get("/api/tokens/{token_address}/history")
def history(token_address: str, limit: int = Query(100, ge=1, le=500)):
    return [dict(x) for x in token_history(token_address, limit)]

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
