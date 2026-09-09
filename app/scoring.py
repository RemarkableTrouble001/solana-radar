from math import isfinite

OPPORTUNITY_WEIGHTS = {
    "momentum": 0.25,
    "volume_anomaly": 0.20,
    "trading_activity": 0.15,
    "holder_growth": 0.15,
    "buy_pressure": 0.10,
    "liquidity_quality": 0.10,
    "market_environment": 0.05,
}
RISK_WEIGHTS = {
    "liquidity_risk": 0.25,
    "volatility_risk": 0.20,
    "concentration_risk": 0.20,
    "security_risk": 0.20,
    "wallet_risk": 0.10,
    "market_risk": 0.05,
}

def clamp(x: float) -> float:
    if not isfinite(x):
        return 0.0
    return max(0.0, min(100.0, float(x)))

def _num(p, key, default=0.0):
    try:
        x = float(p.get(key, default) or default)
        return x if isfinite(x) else default
    except (TypeError, ValueError):
        return default

def score_pair(p: dict):
    ch1 = _num(p, "price_change_1h")
    ch24 = _num(p, "price_change_24h")
    vol = max(0.0, _num(p, "volume_24h"))
    liq = max(0.0, _num(p, "liquidity"))
    buys = max(0, int(_num(p, "buys_24h")))
    sells = max(0, int(_num(p, "sells_24h")))
    txns = buys + sells

    momentum = clamp(50 + ch1 * 5 + ch24 * 1.5)
    volume_anomaly = clamp(25 + (vol / max(liq, 1.0)) * 25)
    trading_activity = clamp(txns / 20)
    # Explicit V1/V2 data-coverage placeholder until holder history is connected.
    holder_growth = clamp(_num(p, "holder_growth", 50.0))
    buy_pressure = clamp(50 + (buys - sells) / max(txns, 1) * 50)
    liquidity_quality = clamp(liq / 1000)
    market_environment = clamp(_num(p, "market_environment", 50.0))

    opportunity = sum([
        momentum * OPPORTUNITY_WEIGHTS["momentum"],
        volume_anomaly * OPPORTUNITY_WEIGHTS["volume_anomaly"],
        trading_activity * OPPORTUNITY_WEIGHTS["trading_activity"],
        holder_growth * OPPORTUNITY_WEIGHTS["holder_growth"],
        buy_pressure * OPPORTUNITY_WEIGHTS["buy_pressure"],
        liquidity_quality * OPPORTUNITY_WEIGHTS["liquidity_quality"],
        market_environment * OPPORTUNITY_WEIGHTS["market_environment"],
    ])

    volatility_risk = clamp(abs(ch1) * 5 + abs(ch24) * 1.5)
    liquidity_risk = 100 - liquidity_quality
    concentration_risk = clamp(_num(p, "concentration_risk", 50.0))
    security_risk = clamp(_num(p, "security_risk", 50.0))
    wallet_risk = clamp(_num(p, "wallet_risk", 50.0))
    market_risk = clamp(_num(p, "market_risk", 50.0))
    risk = sum([
        liquidity_risk * RISK_WEIGHTS["liquidity_risk"],
        volatility_risk * RISK_WEIGHTS["volatility_risk"],
        concentration_risk * RISK_WEIGHTS["concentration_risk"],
        security_risk * RISK_WEIGHTS["security_risk"],
        wallet_risk * RISK_WEIGHTS["wallet_risk"],
        market_risk * RISK_WEIGHTS["market_risk"],
    ])
    parts = {
        "momentum": round(momentum, 2), "volume_anomaly": round(volume_anomaly, 2),
        "trading_activity": round(trading_activity, 2), "holder_growth": round(holder_growth, 2),
        "buy_pressure": round(buy_pressure, 2), "liquidity_quality": round(liquidity_quality, 2),
        "market_environment": round(market_environment, 2), "security_score": round(100-security_risk, 2),
        "volatility_risk": round(volatility_risk, 2), "liquidity_risk": round(liquidity_risk, 2),
        "concentration_risk": round(concentration_risk, 2), "wallet_risk": round(wallet_risk, 2),
        "market_risk": round(market_risk, 2),
    }
    explanation = []
    if momentum >= 70: explanation.append("strong short-term momentum")
    if volume_anomaly >= 70: explanation.append("elevated volume relative to liquidity")
    if buy_pressure >= 65: explanation.append("buy pressure is positive")
    if liquidity_quality >= 70: explanation.append("liquidity quality is strong")
    if risk >= 65: explanation.append("risk is elevated")
    if not explanation: explanation.append("mixed signals; more history is needed")
    return round(clamp(opportunity), 2), round(clamp(risk), 2), parts, explanation
