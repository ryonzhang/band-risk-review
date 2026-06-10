"""
run_demo.py — drive the four agents through the Band room.

Usage:  python run_demo.py

Each scenario posts a request, then hands the turn down the chain:
    Data -> Risk -> Calibration -> Reviewer
and prints the full collaboration transcript plus the reviewed decision.
This is the demo path for the video: three asks, three honest outcomes.
"""
from __future__ import annotations
from band_bus import LocalBandBus, Message
from agents import DataAgent, RiskAgent, CalibrationAgent, ReviewerAgent
from risk_core import PolicyLimits
from seed_data import STORE


def run_review(symbol: str, question: str) -> dict:
    bus = LocalBandBus()
    limits = PolicyLimits()
    data = DataAgent(bus, STORE)
    risk = RiskAgent(bus)
    calib = CalibrationAgent(bus, limits)
    review = ReviewerAgent(bus, limits)

    bus.post(Message("user", "request", {"symbol": symbol, "question": question}))
    data.act({"symbol": symbol, "question": question})  # Data -> evidence
    risk.act()                                           # Risk -> risk
    calib.act()                                          # Calibration -> calibration
    review.act()                                         # Reviewer -> decision

    decision = bus.latest("decision").payload
    return {"bus": bus, "decision": decision}


SCENARIOS = [
    ("BTC", "Should I add to my BTC position?"),
    ("ETH", "ETH looks hot on socials — should I add?"),
    ("DOGE", "Thinking about a DOGE position. Thoughts?"),
    ("SOL", "Add more SOL here?"),
]


def main() -> None:
    for symbol, q in SCENARIOS:
        print("=" * 74)
        print(f"USER ({symbol}): {q}")
        print("-" * 74)
        out = run_review(symbol, q)
        print(out["bus"].transcript())
        d = out["decision"]
        print("-" * 74)
        print(f"REVIEWER VERDICT: {d['verdict']}   final_size={d['final_size']}")
        if d.get("breaches"):
            print("  breaches:", "; ".join(d["breaches"]))
        if d.get("actions"):
            print("  actions :", "; ".join(d["actions"]))
        if d.get("rationale"):
            print("  rationale:", d["rationale"])
        print()


if __name__ == "__main__":
    main()
