import httpx
from .config import settings

RPC_URL = "https://api.mainnet-beta.solana.com"

async def _rpc(client, method, params):
    r = await client.post(RPC_URL, json={"jsonrpc":"2.0","id":1,"method":method,"params":params})
    r.raise_for_status()
    data = r.json()
    if data.get("error"): raise RuntimeError(data["error"].get("message", "RPC error"))
    return data.get("result")

async def enrich_token(client, mint: str):
    """Best-effort, keyless Solana RPC enrichment.
    This is intentionally conservative: largest-account concentration is a proxy,
    not a complete holder-owner graph.
    """
    try:
        supply = await _rpc(client, "getTokenSupply", [mint, {"commitment":"confirmed"}])
        largest = await _rpc(client, "getTokenLargestAccounts", [mint, {"commitment":"confirmed"}])
        account = await _rpc(client, "getAccountInfo", [mint, {"encoding":"jsonParsed","commitment":"confirmed"}])
        amount = float(((supply or {}).get("value") or {}).get("uiAmount") or 0)
        rows = (largest or {}).get("value") or []
        top_sum = sum(float(x.get("uiAmount") or 0) for x in rows[:10])
        concentration = min(100.0, (top_sum / amount * 100.0) if amount > 0 else 50.0)
        concentration_risk = min(100.0, concentration)
        holders_proxy = len(rows)
        parsed = (((account or {}).get("value") or {}).get("data") or {}).get("parsed") or {}
        info = parsed.get("info") or {}
        mint_authority = info.get("mintAuthority")
        freeze_authority = info.get("freezeAuthority")
        security_risk = 30.0
        if mint_authority: security_risk += 20.0
        if freeze_authority: security_risk += 30.0
        return {
            "holder_growth": 50.0,
            "holder_count_proxy": holders_proxy,
            "concentration_risk": round(concentration_risk, 2),
            "security_risk": round(min(100.0, security_risk), 2),
            "mint_authority_present": bool(mint_authority),
            "freeze_authority_present": bool(freeze_authority),
        }
    except Exception:
        return {}

async def enrich_pairs(pairs):
    if not pairs: return pairs
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        for p in pairs:
            extra = await enrich_token(client, p["token_address"])
            p.update(extra)
    return pairs
