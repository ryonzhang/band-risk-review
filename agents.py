"""
agents.py — the four collaborating agents.

Each agent has ONE job, reads structured input off the Band bus, does
deterministic work (risk_core), and posts its result back for the next agent.
This separation is the point: the Reviewer is an INDEPENDENT agent that can
veto or escalate — the regulated-workflow story for Track 3.

In the real Band build, each class becomes a registered Band agent; `act()`
is what runs when the agent is handed the turn. The LLM (Gemini/your model
of choice) is used only to NARRATE the structured payloads into plain language
and to parse the user's question into a structured intent — never to compute
the risk numbers.
"""
from __future__ import annotations
from typing import Any, Dict, List

from band_bus import Bus, Message
from risk_core import (
    Holding, PolicyLimits,
    fractional_kelly, risk_contribution, herfindahl,
    max_drawdown_estimate, logistic,
)


# --------------------------------------------------------------------------- #
# 1. DATA AGENT — gathers the evidence packet (MongoDB MCP in the real build)  #
# --------------------------------------------------------------------------- #
class DataAgent:
    role = "data"

    def __init__(self, bus: Bus, store: Dict[str, Any]):
        self.bus = bus
        self.store = store  # in real build: MongoDB Atlas via MCP tool

    def act(self, request: Dict[str, Any]) -> None:
        symbol = request["symbol"]
        portfolio = self.store["portfolio"]
        market = self.store["market"]
        packet = {
            "request": request,
            "holdings": portfolio,
            "subject": market.get(symbol),
            "have_subject_data": symbol in market,
            "signals": market.get(symbol, {}).get("signals", {}),
        }
        self.bus.post(Message(self.role, "evidence", packet))


# --------------------------------------------------------------------------- #
# 2. RISK AGENT — deterministic portfolio risk metrics                        #
# --------------------------------------------------------------------------- #
class RiskAgent:
    role = "risk"

    def __init__(self, bus: Bus):
        self.bus = bus

    def act(self) -> None:
        ev = self.bus.latest("evidence").payload
        holdings = [Holding(h["symbol"], h["weight"], h["annual_vol"])
                    for h in ev["holdings"]]
        shares = risk_contribution(holdings)
        hhi = herfindahl(shares)
        top_symbol = max(shares, key=shares.get) if shares else None
        subject = ev.get("subject") or {}
        subj_vol = subject.get("annual_vol", 0.0)
        dd = max_drawdown_estimate(subj_vol) if subj_vol else None
        self.bus.post(Message(self.role, "risk", {
            "risk_shares": shares,
            "hhi": hhi,
            "top_risk_symbol": top_symbol,
            "top_risk_share": shares.get(top_symbol) if top_symbol else None,
            "subject_drawdown_est": dd,
        }))


# --------------------------------------------------------------------------- #
# 3. CALIBRATION AGENT — calibrated probability, confidence, sized rec        #
# --------------------------------------------------------------------------- #
class CalibrationAgent:
    role = "calibration"

    def __init__(self, bus: Bus, limits: PolicyLimits):
        self.bus = bus
        self.limits = limits

    def _calibrated_prob(self, signals: Dict[str, float]):
        """
        Map fused signals -> calibrated probability via a fixed logit model.
        (In production this is the walk-forward-fit, Brier-validated model.)
        Returns (prob_up, confidence) where confidence = |prob - 0.5| * 2.
        Conflicting signals shrink toward 0.5 (honest uncertainty).
        """
        if not signals:
            return 0.5, 0.0
        w = {"momentum": 1.1, "funding": -0.8, "oi_trend": 0.5,
             "social_heat": -0.4, "fear_greed": 0.6}
        z = sum(w.get(k, 0.0) * float(v) for k, v in signals.items())
        disagree = abs(signals.get("momentum", 0) - (-signals.get("funding", 0)))
        z *= max(0.2, 1.0 - 0.3 * disagree)
        p = logistic(z)
        return p, abs(p - 0.5) * 2.0

    def act(self) -> None:
        ev = self.bus.latest("evidence").payload
        signals = ev.get("signals", {})
        have_data = ev.get("have_subject_data", False)

        if not have_data or not signals:
            self.bus.post(Message(self.role, "calibration", {
                "abstain": True,
                "reason": "insufficient or missing data for the subject asset",
                "prob_up": None, "confidence": 0.0, "size": 0.0,
            }))
            return

        prob, conf = self._calibrated_prob(signals)
        if conf < self.limits.min_confidence:
            self.bus.post(Message(self.role, "calibration", {
                "abstain": True,
                "reason": f"confidence {conf:.2f} below floor; edge not earned",
                "prob_up": round(prob, 4), "confidence": round(conf, 4), "size": 0.0,
            }))
            return

        size = fractional_kelly(prob, payoff_ratio=1.0,
                                fraction=0.25, cap=self.limits.max_position)
        self.bus.post(Message(self.role, "calibration", {
            "abstain": False,
            "prob_up": round(prob, 4),
            "confidence": round(conf, 4),
            "proposed_size": round(size, 4),
            "basis": list(signals.keys()),
        }))


# --------------------------------------------------------------------------- #
# 4. REVIEWER AGENT — independent compliance gate; approve / trim / escalate  #
# --------------------------------------------------------------------------- #
class ReviewerAgent:
    role = "reviewer"

    def __init__(self, bus: Bus, limits: PolicyLimits):
        self.bus = bus
        self.limits = limits

    def act(self) -> None:
        cal = self.bus.latest("calibration").payload
        risk = self.bus.latest("risk").payload
        L = self.limits
        breaches: List[str] = []
        actions: List[str] = []

        if cal.get("abstain"):
            self.bus.post(Message(self.role, "decision", {
                "verdict": "ABSTAIN_UPHELD",
                "rationale": cal.get("reason", "calibration abstained"),
                "final_size": 0.0,
                "breaches": [], "escalate": False,
            }))
            return

        size = cal.get("proposed_size", 0.0)
        if size > L.max_position:
            breaches.append(f"position {size:.2f} > cap {L.max_position:.2f}")
            actions.append(f"trim to {L.max_position:.2f}")
            size = L.max_position
        if (risk.get("top_risk_share") or 0) > L.max_risk_concentration:
            breaches.append(
                f"{risk['top_risk_symbol']} holds "
                f"{risk['top_risk_share']:.0%} of risk > "
                f"{L.max_risk_concentration:.0%} limit")
            actions.append("flag concentration; require diversification before add")
        dd = risk.get("subject_drawdown_est")
        if dd is not None:
            contribution = size * dd
            if contribution > L.max_dd_contribution:
                breaches.append(
                    f"drawdown contribution {contribution:.0%} of NAV "
                    f"(size {size:.0%} x {dd:.0%} move) > "
                    f"{L.max_dd_contribution:.0%} gate")
                actions.append("escalate to human risk officer")

        escalate = any("escalate" in a for a in actions)
        verdict = ("ESCALATE" if escalate else
                   "APPROVED_WITH_CONDITIONS" if breaches else "APPROVED")
        self.bus.post(Message(self.role, "decision", {
            "verdict": verdict,
            "final_size": round(size, 4),
            "breaches": breaches,
            "actions": actions,
            "escalate": escalate,
        }))

# end of agents.py
