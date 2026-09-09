from dataclasses import dataclass
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    poll_seconds: int = int(os.getenv("POLL_SECONDS", "60"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "30"))
    min_liquidity_usd: float = float(os.getenv("MIN_LIQUIDITY_USD", "5000"))
    min_volume_24h_usd: float = float(os.getenv("MIN_VOLUME_24H_USD", "5000"))
    db_path: Path = Path(os.getenv("RADAR_DB", str(BASE_DIR / "data" / "radar.db")))
    discovery_limit: int = int(os.getenv("DISCOVERY_LIMIT", "30"))
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "20"))
    dex_base_url: str = os.getenv("DEX_BASE_URL", "https://api.dexscreener.com")
    onchain_enrichment: bool = os.getenv("ONCHAIN_ENRICHMENT", "false").lower() == "true"

settings = Settings()
