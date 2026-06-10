"""
test_workflow.py — prove the math and the multi-agent handoff.
Run: python test_workflow.py   (no pytest required)
"""
from risk_core import (
    fractional_kelly, risk_contribution, herfindahl, Holding,
    brier_score, expected_calibration_error, max_drawdown_estimate, logistic,
)
from run_demo import run_review

PASS, FAIL = 0, 0

def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  PASS  {name}")
    else:
        FAIL += 1; print(f"  FAIL  {name}")


print("risk_core:")
check("kelly monotonic in prob", fractional_kelly(0.7) > fractional_kelly(0.55))
check("kelly capped at limit", fractional_kelly(0.99, fraction=1.0, cap=0.20) == 0.20)
check("kelly zero at p<=0.5", fractional_kelly(0.5) == 0.0)
check("logistic in (0,1)", 0 < logistic(-5) < logistic(5) < 1)
H = [Holding("A", 0.9, 1.0), Holding("B", 0.1, 1.0)]
shares = risk_contribution(H)
check("risk shares sum to 1", abs(sum(shares.values()) - 1.0) < 1e-9)
check("dominant holding gets most risk", shares["A"] > shares["B"])
check("hhi higher when concentrated",
      herfindahl({"A": 0.9, "B": 0.1}) > herfindahl({"A": 0.5, "B": 0.5}))
probs = [0.0, 1.0, 0.0, 1.0]; out = [0, 1, 0, 1]
check("brier 0 on perfect forecasts", brier_score(probs, out) == 0.0)
check("ece 0 on perfect forecasts", expected_calibration_error(probs, out) == 0.0)
check("drawdown estimate positive", max_drawdown_estimate(0.65) > 0)

print("workflow (4 agents through the bus):")
btc = run_review("BTC", "add?")["decision"]
check("BTC approved (not abstain/escalate)",
      btc["verdict"].startswith("APPROVED") and not btc["escalate"])
check("BTC final size within cap", 0 < btc["final_size"] <= 0.20)
eth = run_review("ETH", "add?")["decision"]
check("ETH abstains on conflicting signals", eth["verdict"] == "ABSTAIN_UPHELD")
doge = run_review("DOGE", "add?")["decision"]
check("DOGE abstains on missing data", doge["verdict"] == "ABSTAIN_UPHELD")
sol = run_review("SOL", "add?")["decision"]
check("SOL escalates on drawdown gate", sol["escalate"] is True)
check("every run ends in a reviewer decision",
      all(run_review(s, "x")["decision"].get("verdict")
          for s in ("BTC", "ETH", "DOGE", "SOL")))

print("-" * 50)
print(f"{PASS} passed, {FAIL} failed")
raise SystemExit(1 if FAIL else 0)
# end of test_workflow.py
