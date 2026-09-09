from datetime import datetime, timezone
import httpx
from .config import settings

SOLANA = "solana"

def _f(v, default=0.0):
    try: return float(v or default)
    except (TypeError, ValueError): return default

def _i(v, default=0):
    try: return int(v or default)
    except (TypeError, ValueError): return default

async def _get(client, path, **params):
    r = await client.get(settings.dex_base_url + path, params=params)
    r.raise_for_status()
    return r.json()

async def discover_token_addresses(client):
    addresses = []
    seen = set()
    for path in ("/token-boosts/top/v1", "/token-profiles/latest/v1"):
        try:
            data = await _get(client, path)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict): continue
            if item.get("chainId") != SOLANA: continue
            addr = item.get("tokenAddress")
            if addr and addr not in seen:
                seen.add(addr); addresses.append(addr)
            if len(addresses) >= settings.discovery_limit: return addresses
    return addresses

async def fetch_pairs():
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        addresses = await discover_token_addresses(client)
        if not addresses: return []
        # Official API permits up to 30 comma-separated token addresses per request.
        try:
            data = await _get(client, f"/tokens/v1/{SOLANA}/{','.join(addresses[:30])}")
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        out = []
        for p in data:
            if not isinstance(p, dict): continue
            if p.get("chainId") != SOLANA: continue
            base = p.get("baseToken") or {}
            addr = base.get("address")
            if not addr: continue
            # Only score the deepest-liquidity Solana pair per token later.
            ch = p.get("priceChange") or {}
            tx = (p.get("txns") or {}).get("h24") or {}
            liq = (p.get("liquidity") or {}).get("usd") or 0
            created = p.get("pairCreatedAt")
            created_at = datetime.fromtimestamp(created/1000, tz=timezone.utc).isoformat() if created else ""
            out.append({
                "token_address": addr,
                "symbol": str(base.get("symbol") or "?")[:100],
                "name": str(base.get("name") or "Unknown")[:200],
                "pair_address": str(p.get("pairAddress") or ""),
                "dex": str(p.get("dexId") or "")[:100],
                "created_at": created_at,
                "liquidity": _f(liq),
                "market_cap": _f(p.get("marketCap") or p.get("fdv")),
                "volume_24h": _f((p.get("volume") or {}).get("h24")),
                "price_usd": _f(p.get("priceUsd")),
                "price_change_5m": _f(ch.get("m5")),
                "price_change_1h": _f(ch.get("h1")),
                "price_change_6h": _f(ch.get("h6")),
                "price_change_24h": _f(ch.get("h24")),
                "txns_24h": _i(tx.get("buys")) + _i(tx.get("sells")),
                "buys_24h": _i(tx.get("buys")),
                "sells_24h": _i(tx.get("sells")),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "boosts_active": _i((p.get("boosts") or {}).get("active")),
                "image_url": str((p.get("info") or {}).get("imageUrl") or ""),
                "source_url": str(p.get("url") or ""),
            })
        # One best-liquidity pair per token.
        best = {}
        for p in out:
            if p["token_address"] not in best or p["liquidity"] > best[p["token_address"]]["liquidity"]:
                best[p["token_address"]] = p
        return list(best.values())
