from dataclasses import dataclass
from typing import Any

@dataclass
class PairData:
    token_address: str
    symbol: str
    name: str
    pair_address: str
    dex: str
    created_at: str
    liquidity: float
    market_cap: float
    volume_24h: float
    price_usd: float
    price_change_5m: float
    price_change_1h: float
    price_change_6h: float
    price_change_24h: float
    txns_24h: int
    buys_24h: int
    sells_24h: int
    updated_at: str
    boosts_active: int = 0
    image_url: str = ""
    source_url: str = ""

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()
