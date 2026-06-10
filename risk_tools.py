"""
risk_tools.py — the deterministic core, exposed as agent tools.

These wrap risk_core.py so a Band agent's LLM can CALL them (never compute the
numbers itself). Framework-agnostic: each is a plain function with clear types
and a docstring, so it can be registered with any Band adapter
(Anthropic / LangGraph / etc.) via that adapter's tool mechanism.

The LLM decides WHEN to call a tool and how to narrate the result; the math is
always these functions. This is the anti-hallucination guarantee for Track 3.
"""
from __future__ import annotations
from typing import List, Dict, Any
from risk_core import (
    Holding, PolicyLimits,
    fractional_kelly, risk_contribution, herfindahl,
    max_drawdown_estimate, logistic,
)

LIMITS = PolicyLimits()


def compute_portfolio_risk(holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Given holdings [{symbol, weight, annual_vol}], return deterministic risk:
    per-symbol risk shares, HHI concentration, and the top risk contributor.
    """
    hs = [Holding(h["symbol"], float(h["weight"]), float(h["annual_vol"])) for h in holdings]
    shares = risk_contribution(hs)
    top = max(shares, key=shares.get) if shares else None
    return {
        "risk_shares": {k: round(v, 4) for k, v in shares.items()},
        "hhi": round(herfindahl(shares), 4),
        "top_risk_symbol": top,
        "top_risk_share": round(shares.get(top, 0.0), 4) if top else None,
    }


def drawdown_estimate(annual_vol: float, horizon_days: int = 21) -> Dict[str, float]:
    """Parametric 2-sigma drawdown bound over a horizon. A sanity gate, not a forecast."""
    return {"drawdown_estimate": round(max_drawdown_estimate(float(annual_vol), horizon_days), 4)}


def calibrated_probability(signals: Dict[str, float]) -> Dict[str, Any]:
    """
    Fuse signals -> calibrated probability of an up-move + confidence.
    Conflicting signals shrink toward 0.5 (honest uncertainty). Returns
    {prob_up, confidence, abstain, reason?}. abstain=True when confidence is
    below the policy floor or data is missing.
    """
    if not signals:
        return {"abstain": True, "reason": "no signals for subject asset",
                "prob_up": None, "confidence": 0.0}
    w = {"momentum": 1.1, "funding": -0.8, "oi_trend": 0.5, "social_heat": -0.4, "fear_greed": 0.6}
    z = sum(w.get(k, 0.0) * float(v) for k, v in signals.items())
    disagree = abs(signals.get("momentum", 0) - (-signals.get("funding", 0)))
    z *= max(0.2, 1.0 - 0.3 * disagree)
    p = logistic(z); conf = abs(p - 0.5) * 2.0
    if conf < LIMITS.min_confidence:
        return {"abstain": True, "reason": f"confidence {conf:.2f} below floor {LIMITS.min_confidence}",
                "prob_up": round(p, 4), "confidence": round(conf, 4)}
    return {"abstain": False, "prob_up": round(p, 4), "confidence": round(conf, 4)}


def size_position(prob_up: float) -> Dict[str, float]:
    """Fractional-Kelly position size (fraction of NAV), capped by policy."""
    return {"proposed_size": round(fractional_kelly(float(prob_up), 1.0, 0.25, LIMITS.max_position), 4)}


def review_decision(proposed_size: float, top_risk_share: float,
                    subject_drawdown_est: float, abstain: bool = False,
                    abstain_reason: str = "") -> Dict[str, Any]:
    """
    Independent compliance gate. Returns a verdict:
    APPROVED / APPROVED_WITH_CONDITIONS / ESCALATE / ABSTAIN_UPHELD,
    with the final size, any policy breaches, and required actions.
    """
    L = LIMITS
    if abstain:
        return {"verdict": "ABSTAIN_UPHELD", "final_size": 0.0,
                "rationale": abstain_reason or "calibration abstained",
                "breaches": [], "escalate": False}
    size = float(proposed_size); breaches: List[str] = []; actions: List[str] = []
    if size > L.max_position:
        breaches.append(f"position {size:.2f} > cap {L.max_position:.2f}")
        actions.append(f"trim to {L.max_position:.2f}"); size = L.max_position
    if top_risk_share is not None and float(top_risk_share) > L.max_risk_concentration:
        breaches.append(f"risk concentration {float(top_risk_share):.0%} > {L.max_risk_concentration:.0%}")
        actions.append("require diversification before add")
    if subject_drawdown_est is not None:
        contrib = size * float(subject_drawdown_est)
        if contrib > L.max_dd_contribution:
            breaches.append(f"drawdown contribution {contrib:.0%} of NAV > {L.max_dd_contribution:.0%} gate")
            actions.append("escalate to human risk officer")
    escalate = any("escalate" in a for a in actions)
    verdict = ("ESCALATE" if escalate else "APPROVED_WITH_CONDITIONS" if breaches else "APPROVED")
    return {"verdict": verdict, "final_size": round(size, 4),
            "breaches": breaches, "actions": actions, "escalate": escalate}

# end of risk_tools.py
