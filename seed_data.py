"""
seed_data.py — sample portfolio + market snapshot.

In the real build this lives in MongoDB Atlas and the DataAgent reads it via
the MongoDB MCP server. Here it's a plain dict so the workflow runs offline.
Signals are normalized to roughly [-1, 1].
"""

STORE = {
    "portfolio": [
        {"symbol": "BTC", "weight": 0.50, "annual_vol": 0.65},
        {"symbol": "ETH", "weight": 0.30, "annual_vol": 0.75},
        {"symbol": "SOL", "weight": 0.20, "annual_vol": 1.05},
    ],
    "market": {
        # clean, confident bullish setup
        "BTC": {
            "annual_vol": 0.65,
            "signals": {"momentum": 0.6, "funding": -0.1, "oi_trend": 0.4,
                        "social_heat": 0.2, "fear_greed": 0.5},
        },
        # conflicting signals -> should shrink toward 0.5 / abstain
        "ETH": {
            "annual_vol": 0.75,
            "signals": {"momentum": 0.5, "funding": 0.6, "oi_trend": -0.1,
                        "social_heat": 0.9, "fear_greed": -0.2},
        },
        # high vol -> drawdown gate should trip on a fresh add
        "SOL": {
            "annual_vol": 1.05,
            "signals": {"momentum": 0.8, "funding": -0.2, "oi_trend": 0.6,
                        "social_heat": 0.3, "fear_greed": 0.6},
        },
        # DOGE intentionally absent from market -> DataAgent reports no data
    },
}
