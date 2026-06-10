"""
risk_core.py — deterministic risk + calibration math.

This is the honest, testable core. The LLM never invents these numbers;
the agents call these functions and narrate the results. Reused from
Calibrated Conviction / Calibrated Copilot (CFA/ASA methodology).

No network, no LLM, no randomness. Pure functions.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import math


# ----------------------------- calibration ---------------------------------

def logistic(x: float) -> float:
    """Numerically stable logistic."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def brier_score(probs: List[float], outcomes: List[int]) -> float:
    """Mean squared error of probabilistic forecasts. Lower is better."""
    if not probs:
        return float("nan")
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs)


def expected_calibration_error(probs: List[float], outcomes: List[int],
                               bins: int = 10) -> float:
    """ECE: weighted gap between confidence and accuracy across bins."""
    if not probs:
        return float("nan")
    n = len(probs)
    buckets: List[Tuple[float, int]] = [(p, o) for p, o in zip(probs, outcomes)]
    ece = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        members = [(p, o) for (p, o) in buckets
                   if (p >= lo and p < hi) or (b == bins - 1 and p == 1.0)]
        if not members:
            continue
        conf = sum(p for p, _ in members) / len(members)
        acc = sum(o for _, o in members) / len(members)
        ece += (len(members) / n) * abs(conf - acc)
    return ece


# ----------------------------- sizing ---------------------------------------

def fractional_kelly(prob_up: float, payoff_ratio: float = 1.0,
                     fraction: float = 0.25, cap: float = 0.20) -> float:
    """
    Position size as a fraction of capital.

    prob_up:       calibrated probability the trade wins (0..1)
    payoff_ratio:  win/loss payoff (b in Kelly f* = (bp - q)/b)
    fraction:      Kelly fraction (we use 1/4 Kelly — survival over greed)
    cap:           hard cap on any single position
    """
    p = max(0.0, min(1.0, prob_up))
    q = 1.0 - p
    b = max(1e-9, payoff_ratio)
    kelly = (b * p - q) / b
    sized = max(0.0, kelly) * fraction
    return min(sized, cap)


# ----------------------------- concentration --------------------------------

@dataclass
class Holding:
    symbol: str
    weight: float          # portfolio weight (fraction of NAV)
    annual_vol: float      # annualized volatility estimate


def risk_contribution(holdings: List[Holding]) -> Dict[str, float]:
    """
    Volatility-weighted risk share per holding (assumes ~zero cross-corr for a
    transparent first-order view: risk_i = w_i * vol_i, normalized).
    Returns each symbol's share of total risk (sums to 1.0).
    """
    raw = {h.symbol: h.weight * h.annual_vol for h in holdings}
    total = sum(raw.values())
    if total <= 0:
        return {k: 0.0 for k in raw}
    return {k: v / total for k, v in raw.items()}


def herfindahl(shares: Dict[str, float]) -> float:
    """HHI of risk shares: 1/N (diversified) .. 1.0 (one position is all risk)."""
    return sum(s * s for s in shares.values())


def max_drawdown_estimate(annual_vol: float, horizon_days: int = 21,
                          z: float = 2.0) -> float:
    """
    Rough parametric drawdown proxy: z-sigma move over the horizon.
    Not a forecast — a sanity bound for the reviewer's gate.
    """
    daily = annual_vol / math.sqrt(252)
    return z * daily * math.sqrt(horizon_days)


# ----------------------------- policy gate ----------------------------------

@dataclass
class PolicyLimits:
    max_position: float = 0.20            # no single new position > 20% NAV
    max_risk_concentration: float = 0.45  # no symbol > 45% of total risk
    max_dd_contribution: float = 0.06     # escalate if a new add's drawdown
                                          # contribution to NAV exceeds 6%
    min_confidence: float = 0.30          # confidence floor; below -> abstain

# The ReviewerAgent emits decisions as plain dicts on the bus, so no extra
# result class is needed here.
# end of risk_core.py
