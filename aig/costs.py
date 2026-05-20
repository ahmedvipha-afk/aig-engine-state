"""
Realistic cost & slippage model (Layer B item 3).

Round-trip cost applied to every simulated trade as a fraction of entry price.
Bigger for UAE (low liquidity) and crypto (wide spreads) than US.
"""

from config import MARKET_COSTS


def round_trip_cost_frac(market: str) -> float:
    c = MARKET_COSTS.get(market, MARKET_COSTS["US"])
    # commission both sides + spread crossed + slippage both sides, in bps -> frac
    bps = 2 * c["commission_bps"] + c["spread_bps"] + 2 * c["slippage_bps"]
    return bps / 10_000.0
