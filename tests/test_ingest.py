import asyncio
from app import ingest


class FakeResp:
    def __init__(self, data, ok=True):
        self._data = data
        self._ok = ok

    def raise_for_status(self):
        if not self._ok:
            raise RuntimeError("simulated HTTP failure")

    def json(self):
        return self._data


class FakeClient:
    def __init__(self, responses):
        # responses: dict mapping a substring of the request path -> FakeResp
        self._responses = responses

    async def get(self, url, params=None):
        for key, resp in self._responses.items():
            if key in url:
                return resp
        return FakeResp([])


def test_discover_token_addresses_ignores_non_list_response():
    # Regression: the API returning a dict (e.g. an error object) instead of
    # a list must not be iterated as token records.
    client = FakeClient({
        "/token-boosts/top/v1": FakeResp({"error": "rate limited"}),
        "/token-profiles/latest/v1": FakeResp([{"chainId": "solana", "tokenAddress": "MINT1"}]),
    })
    addresses = asyncio.run(ingest.discover_token_addresses(client))
    assert addresses == ["MINT1"]


def test_fetch_pairs_survives_tokens_endpoint_failure(monkeypatch):
    # Regression: a failing/erroring tokens-endpoint request must not crash
    # the whole refresh cycle; it should degrade to an empty result.
    async def fake_discover(client):
        return ["MINT1"]

    async def fake_get(client, path, **params):
        if path.startswith("/tokens/v1/"):
            raise RuntimeError("simulated network failure")
        return []

    monkeypatch.setattr(ingest, "discover_token_addresses", fake_discover)
    monkeypatch.setattr(ingest, "_get", fake_get)
    pairs = asyncio.run(ingest.fetch_pairs())
    assert pairs == []


def test_fetch_pairs_skips_malformed_pair_and_keeps_valid_ones(monkeypatch):
    # Regression: a malformed/non-dict pair item must be skipped, not abort
    # processing of the valid pairs around it.
    async def fake_discover(client):
        return ["MINT1", "MINT2"]

    good_pair = {
        "chainId": "solana",
        "baseToken": {"address": "MINT1", "symbol": "FOO", "name": "Foo"},
        "priceChange": {"m5": 1, "h1": 2, "h6": 3, "h24": 4},
        "txns": {"h24": {"buys": 5, "sells": 3}},
        "liquidity": {"usd": 12000},
        "marketCap": 500000,
        "volume": {"h24": 30000},
        "priceUsd": "0.01",
        "pairCreatedAt": 1700000000000,
        "pairAddress": "PAIR1",
        "dexId": "raydium",
        "boosts": {"active": 0},
        "info": {"imageUrl": ""},
        "url": "https://dexscreener.com/x",
    }

    async def fake_get(client, path, **params):
        if path.startswith("/tokens/v1/"):
            return [good_pair, {"chainId": "solana"}, "not-a-dict-at-all"]
        return []

    monkeypatch.setattr(ingest, "discover_token_addresses", fake_discover)
    monkeypatch.setattr(ingest, "_get", fake_get)
    pairs = asyncio.run(ingest.fetch_pairs())
    assert len(pairs) == 1
    assert pairs[0]["token_address"] == "MINT1"
