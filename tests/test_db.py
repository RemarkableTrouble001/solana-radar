import tempfile
from pathlib import Path
from app import db

def sample(tmp):
    db.DB=Path(tmp)/"test.db"; db.DB.parent.mkdir(parents=True,exist_ok=True); db.init_db()
    return {"token_address":"A","symbol":"X","name":"X","pair_address":"P","dex":"dex","created_at":"","liquidity":10000,"market_cap":100000,"volume_24h":20000,"price_usd":1,"price_change_5m":1,"price_change_1h":2,"price_change_6h":3,"price_change_24h":4,"txns_24h":20,"buys_24h":12,"sells_24h":8,"updated_at":"2026-09-08T09:23:00+00:00","boosts_active":0,"image_url":"","source_url":""}

def test_signal_deduplication(tmp_path):
    p=sample(tmp_path); db.upsert_token(p)
    parts={k:50 for k in ["momentum","volume_anomaly","trading_activity","holder_growth","buy_pressure","liquidity_quality","market_environment","security_score"]}
    assert db.add_signal(p,60,40,parts,["test"]) is True
    assert db.add_signal(p,60,40,parts,["test"]) is False
    assert len(db.top_signals())==1

def test_top_signals_includes_price_change(tmp_path):
    # Regression: top_signals() must surface price_change_1h/24h from the tokens
    # table so the dashboard doesn't render 0% for every row.
    p=sample(tmp_path); db.upsert_token(p)
    parts={k:50 for k in ["momentum","volume_anomaly","trading_activity","holder_growth","buy_pressure","liquidity_quality","market_environment","security_score"]}
    db.add_signal(p,60,40,parts,["test"])
    row=dict(db.top_signals()[0])
    assert row["price_change_1h"]==p["price_change_1h"]
    assert row["price_change_24h"]==p["price_change_24h"]
