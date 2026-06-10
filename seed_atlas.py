"""
seed_atlas.py — load the sample portfolio + market snapshot into MongoDB Atlas.

This is the real-build counterpart to seed_data.py: it writes the SAME data
shape into Atlas so the DataAgent can read it via the MongoDB MCP server at the
June 12 kickoff. Nothing downstream changes — the DataAgent still emits the
identical `evidence` packet.

Collections written to the `MONGODB_DB` database:
  - portfolio : one document per holding  {symbol, weight, annual_vol}
  - market    : one document per asset     {symbol, annual_vol, signals{...}}

DOGE is intentionally absent from `market` so the "no data" abstention still
reproduces against Atlas.

Run:  python seed_atlas.py
Requires:  MONGODB_URI (and optional MONGODB_DB) in .env
"""
from __future__ import annotations

import os
import sys

from seed_data import STORE

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MONGODB_URI = os.environ.get("MONGODB_URI", "")
MONGODB_DB = os.environ.get("MONGODB_DB", "band_risk_review")


def _market_docs() -> list[dict]:
    """Flatten the market dict into one document per symbol (symbol as a field)."""
    docs = []
    for symbol, data in STORE["market"].items():
        doc = {"symbol": symbol}
        doc.update(data)
        docs.append(doc)
    return docs


def main() -> None:
    if not MONGODB_URI:
        sys.exit("MONGODB_URI is not set. Copy .env.example to .env and fill it in.")

    from pymongo import MongoClient

    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    db.portfolio.drop()
    db.market.drop()

    db.portfolio.insert_many([dict(h) for h in STORE["portfolio"]])
    db.market.insert_many(_market_docs())

    db.portfolio.create_index("symbol", unique=True)
    db.market.create_index("symbol", unique=True)

    n_port = db.portfolio.count_documents({})
    n_mkt = db.market.count_documents({})
    print(f"Seeded '{MONGODB_DB}':")
    print(f"  portfolio: {n_port} holdings")
    print(f"  market:    {n_mkt} assets ({', '.join(sorted(STORE['market']))})")
    print("  (DOGE deliberately absent from market -> 'no data' abstention holds.)")
    client.close()


if __name__ == "__main__":
    main()
