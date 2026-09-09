import sqlite3
from pathlib import Path
from .config import settings

DB = Path(settings.db_path)
DB.parent.mkdir(parents=True, exist_ok=True)

def conn():
    c = sqlite3.connect(DB, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS tokens (
          token_address TEXT PRIMARY KEY, symbol TEXT, name TEXT, pair_address TEXT,
          dex TEXT, created_at TEXT, liquidity REAL, market_cap REAL, volume_24h REAL,
          price_usd REAL, price_change_5m REAL, price_change_1h REAL, price_change_6h REAL,
          price_change_24h REAL, txns_24h INTEGER, buys_24h INTEGER, sells_24h INTEGER,
          updated_at TEXT, boosts_active INTEGER DEFAULT 0, image_url TEXT DEFAULT '', source_url TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS observations (
          id INTEGER PRIMARY KEY AUTOINCREMENT, observed_at TEXT NOT NULL, token_address TEXT NOT NULL,
          price_usd REAL, liquidity REAL, market_cap REAL, volume_24h REAL,
          price_change_1h REAL, price_change_24h REAL, txns_24h INTEGER, buys_24h INTEGER, sells_24h INTEGER,
          opportunity_score REAL, risk_score REAL,
          FOREIGN KEY(token_address) REFERENCES tokens(token_address)
        );
        CREATE TABLE IF NOT EXISTS signals (
          id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, token_address TEXT NOT NULL,
          pair_address TEXT NOT NULL DEFAULT '', bucket TEXT NOT NULL,
          opportunity_score REAL, risk_score REAL, momentum REAL, volume_anomaly REAL,
          trading_activity REAL, holder_growth REAL, buy_pressure REAL, liquidity_quality REAL,
          market_environment REAL, security_score REAL, entry_price REAL, explanation TEXT,
          UNIQUE(token_address, pair_address, bucket),
          FOREIGN KEY(token_address) REFERENCES tokens(token_address)
        );
        CREATE INDEX IF NOT EXISTS idx_signals_opp ON signals(opportunity_score DESC);
        CREATE INDEX IF NOT EXISTS idx_signals_token_time ON signals(token_address, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_observations_token_time ON observations(token_address, observed_at DESC);
        """)
        # Lightweight migration for databases created by V1.
        cols = {r[1] for r in c.execute("PRAGMA table_info(tokens)").fetchall()}
        for name, ddl in [("boosts_active", "INTEGER DEFAULT 0"), ("image_url", "TEXT DEFAULT ''"), ("source_url", "TEXT DEFAULT ''")]:
            if name not in cols: c.execute(f"ALTER TABLE tokens ADD COLUMN {name} {ddl}")

def upsert_token(p):
    cols = ["token_address","symbol","name","pair_address","dex","created_at","liquidity","market_cap","volume_24h","price_usd","price_change_5m","price_change_1h","price_change_6h","price_change_24h","txns_24h","buys_24h","sells_24h","updated_at","boosts_active","image_url","source_url"]
    vals = [p.get(k) for k in cols]
    with conn() as c:
        c.execute(f"INSERT INTO tokens ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)}) ON CONFLICT(token_address) DO UPDATE SET " + ','.join(f"{x}=excluded.{x}" for x in cols[1:]), vals)

def add_observation(p, opp, risk):
    with conn() as c:
        c.execute("""INSERT INTO observations(observed_at,token_address,price_usd,liquidity,market_cap,volume_24h,price_change_1h,price_change_24h,txns_24h,buys_24h,sells_24h,opportunity_score,risk_score) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (p["updated_at"],p["token_address"],p["price_usd"],p["liquidity"],p["market_cap"],p["volume_24h"],p["price_change_1h"],p["price_change_24h"],p["txns_24h"],p["buys_24h"],p["sells_24h"],opp,risk))

def add_signal(p, opp, risk, parts, explanation):
    # Minute bucket preserves historical signals while preventing duplicate writes from concurrent refreshes.
    bucket = p["updated_at"][:16].replace(":", "")
    with conn() as c:
        cur = c.execute("""INSERT OR IGNORE INTO signals(timestamp,token_address,pair_address,bucket,opportunity_score,risk_score,momentum,volume_anomaly,trading_activity,holder_growth,buy_pressure,liquidity_quality,market_environment,security_score,entry_price,explanation)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (p["updated_at"],p["token_address"],p.get("pair_address", ""),bucket,opp,risk,parts["momentum"],parts["volume_anomaly"],parts["trading_activity"],parts["holder_growth"],parts["buy_pressure"],parts["liquidity_quality"],parts["market_environment"],parts["security_score"],p["price_usd"],"; ".join(explanation)))
        return cur.rowcount == 1

def top_signals(limit=25):
    with conn() as c:
        return c.execute("""SELECT s.*,t.symbol,t.name,t.price_usd,t.liquidity,t.volume_24h,t.market_cap,t.image_url,t.source_url,t.price_change_1h,t.price_change_24h
        FROM signals s JOIN tokens t ON t.token_address=s.token_address
        ORDER BY s.opportunity_score DESC, s.risk_score ASC, s.timestamp DESC LIMIT ?""", (limit,)).fetchall()

def token_history(address, limit=100):
    with conn() as c:
        return c.execute("SELECT * FROM observations WHERE token_address=? ORDER BY observed_at DESC LIMIT ?", (address,limit)).fetchall()

def stats():
    with conn() as c:
        return {
            "tokens": c.execute("SELECT COUNT(*) FROM tokens").fetchone()[0],
            "observations": c.execute("SELECT COUNT(*) FROM observations").fetchone()[0],
            "signals": c.execute("SELECT COUNT(*) FROM signals").fetchone()[0],
            "last_update": (c.execute("SELECT MAX(updated_at) FROM tokens").fetchone()[0]),
        }
