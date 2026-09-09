
### `DEPLOYMENT.md`
```markdown
# Deployment Guide

Solana Radar V1.1 is a plain FastAPI + SQLite app with no external services
required (no Postgres, no Redis, no message queue). It needs Python 3.11+
and outbound HTTPS access to `api.dexscreener.com` (and, optionally, a
Solana RPC endpoint if `ONCHAIN_ENRICHMENT=true`).

## 1. Install dependencies

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
