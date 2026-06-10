"""
test_real_band.py — guarded smoke test for the REAL Band room.

Runs one review (BTC) through RealBandBus end-to-end. It SKIPS cleanly (exit 0)
when Band credentials are absent, so CI stays green before the June 12 kickoff.
Once the room + agents exist and RealBandBus is wired, set the env vars below and
this becomes the live agent-to-agent verification.

Run:  python test_real_band.py
Activates only when these are all present:
    THENVOI_REST_URL, THENVOI_WS_URL, BAND_ROOM_ID, and agent_config.yaml
"""
from __future__ import annotations

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _creds_present() -> bool:
    have_urls = bool(os.environ.get("THENVOI_REST_URL")) and \
        bool(os.environ.get("THENVOI_WS_URL"))
    have_room = bool(os.environ.get("BAND_ROOM_ID"))
    have_config = os.path.exists("agent_config.yaml")
    return have_urls and have_room and have_config


def main() -> None:
    if not _creds_present():
        print("SKIP  test_real_band: Band credentials absent "
              "(set THENVOI_REST_URL, THENVOI_WS_URL, BAND_ROOM_ID + "
              "agent_config.yaml to enable). CI stays green.")
        sys.exit(0)

    # --- live path (enabled at the kickoff once RealBandBus is wired) -------- #
    from band_bus import RealBandBus, Message
    from agents import DataAgent, RiskAgent, CalibrationAgent, ReviewerAgent
    from risk_core import PolicyLimits

    config = _load_agent_config("agent_config.yaml")
    bus = RealBandBus(
        room_id=os.environ["BAND_ROOM_ID"],
        rest_url=os.environ["THENVOI_REST_URL"],
        ws_url=os.environ["THENVOI_WS_URL"],
        agent_config=config,
    )

    # The DataAgent reads from Atlas via MCP at kickoff; STORE is the fallback shape.
    from seed_data import STORE
    limits = PolicyLimits()
    DataAgent(bus, STORE), RiskAgent(bus), CalibrationAgent(bus, limits), \
        ReviewerAgent(bus, limits)

    bus.post(Message("user", "request", {"symbol": "BTC", "question": "add?"}))
    # At kickoff, hand the turn agent-to-agent through Band; for the smoke test we
    # just confirm a decision message lands back in the room.
    decision = bus.latest("decision")
    assert decision is not None, "no reviewer decision returned from the Band room"
    assert decision.payload.get("verdict"), "reviewer decision missing a verdict"
    print(f"PASS  live Band review returned verdict={decision.payload['verdict']}")


def _load_agent_config(path: str) -> dict:
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:  # pragma: no cover
        print(f"WARN  could not parse {path}: {exc}")
        return {}


if __name__ == "__main__":
    main()
