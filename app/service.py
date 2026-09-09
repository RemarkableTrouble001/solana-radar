import asyncio
from .config import settings
from .db import upsert_token, add_observation, add_signal
from .ingest import fetch_pairs
from .onchain import enrich_pairs
from .scoring import score_pair

class RadarService:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.last_error = None
        self.last_processed = 0

    async def refresh(self):
        async with self.lock:
            pairs = await fetch_pairs()
            if settings.onchain_enrichment:
                try:
                    pairs = await enrich_pairs(pairs)
                except Exception:
                    pass
            processed = 0
            signals_added = 0
            for p in sorted(pairs, key=lambda x: (x.get("liquidity",0), x.get("volume_24h",0)), reverse=True)[:settings.max_tokens]:
                if p.get("liquidity",0) < settings.min_liquidity_usd or p.get("volume_24h",0) < settings.min_volume_24h_usd:
                    continue
                opp, risk, parts, explanation = score_pair(p)
                upsert_token(p)
                add_observation(p, opp, risk)
                if add_signal(p, opp, risk, parts, explanation): signals_added += 1
                processed += 1
            self.last_processed = processed
            self.last_error = None
            return {"processed": processed, "signals_added": signals_added}

service = RadarService()

async def poller():
    while True:
        try:
            await service.refresh()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            service.last_error = str(exc)
            print(f"poll error: {exc}")
        await asyncio.sleep(settings.poll_seconds)
