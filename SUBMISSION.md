# Band of Agents — submission package (Track 3: Regulated & High-Stakes)

Paste these into the lablab.ai submission form when it opens at kickoff.

---

## Project title
**Band Risk-Review — a separation-of-duties risk desk for AI**

## Short description (one line)
Four specialized agents collaborate through Band to review high-stakes financial
decisions — proposing, calibrating, and independently approving or escalating, with
a full audit trail.

## Long description

**The problem.** Most "AI finance agents" are a single model answering every question
with the same confident voice. Regulated finance doesn't work that way. It runs on
*separation of duties*: the desk that proposes a trade is never the desk that approves
it, and risk numbers come from a deterministic system, not a person's gut. A single
LLM collapses all of that into one over-confident actor — exactly the failure mode that
makes AI hard to trust in high-stakes workflows.

**What it is.** Band Risk-Review is a band of four specialized agents that collaborate
through Band to review a portfolio decision the way a real risk desk would:

1. **Risk-Data** — gathers the evidence (portfolio holdings + market signals from
   MongoDB Atlas via MCP) and hands off the packet. Never invents numbers.
2. **Risk-Quant** — computes deterministic portfolio risk: volatility-weighted risk
   shares, HHI concentration, and a parametric drawdown bound.
3. **Risk-Calibration** — turns fused signals into a *calibrated* probability with an
   explicit confidence, sizes the position by fractional Kelly, and **abstains** when
   confidence is below floor or signals conflict.
4. **Risk-Reviewer** — an *independent* compliance gate that can veto. It checks the
   proposal against policy limits and returns APPROVED, APPROVED_WITH_CONDITIONS (trim),
   ESCALATE (to a human risk officer), or ABSTAIN_UPHELD.

**How Band is the collaboration layer.** The four agents live in a shared Band chat room
and coordinate by @mention handoff — `User → @Risk-Data → @Risk-Quant →
@Risk-Calibration → @Risk-Reviewer → User`. Band routes each message only to the
@mentioned agent, isolating context, and records every message, tool call, tool result,
and handoff in the room. That conversation history *is* the regulator-grade audit trail —
which is the whole point of Track 3. Band isn't a wrapper or a final notification here;
it is the coordination substrate the workflow runs on.

**Honesty by construction.** All risk math lives in a deterministic core (Brier/ECE
calibration scoring, fractional Kelly, HHI, drawdown). The agents *call* it as tools; the
LLMs only narrate and decide handoffs — they never produce a risk number themselves. This
is the anti-hallucination guarantee that matters in regulated finance.

**Demonstrated behaviour (four asks, four honest outcomes):**
- "Add to BTC?" → **APPROVED**, sized ~11% (clean signals, within drawdown gate)
- "ETH looks hot on socials?" → **ABSTAIN** (funding vs momentum conflict)
- "DOGE position?" → **ABSTAIN** (no data on the asset)
- "Add more SOL?" → **ESCALATE** (drawdown contribution exceeds the 6% gate → human review)

**Built by** Ruiyang Zhang — passed all three CFA Program exams; calibration, Kelly
sizing, and risk methodology are my professional domain. github.com/ryonzhang · ruiyang.co

## Technology & category tags
Band, Multi-Agent, Agent-to-Agent, MCP, MongoDB Atlas, Anthropic Claude, AI/ML API,
Python, RegTech, Compliance, Risk Management, Fintech, Calibration, Track 3

## Links
- GitHub: https://github.com/ryonzhang/band-risk-review
- Cover image: cover_band.png
- Architecture: architecture_band.png

---

## 2-minute demo video script

**[0:00–0:15] Hook.** "Most AI finance assistants are one model answering everything
with the same false confidence. Real risk desks don't work that way — they separate who
proposes a trade from who approves it. Band Risk-Review puts that on Band."

**[0:15–0:35] The band.** Show the architecture image. "Four agents in one Band room:
Data gathers evidence, Quant computes risk, Calibration produces a calibrated probability
and sizes it, and an independent Reviewer approves, trims, or escalates. They hand off by
@mention — Band is the coordination layer, and every step is recorded as the audit trail."

**[0:35–1:05] Demo 1 — a clean approve.** In the Band room, type
"@Risk-Data Should I add to my BTC position?" Let the handoff play live: watch each agent
@mention the next, show a tool call (e.g. compute_portfolio_risk), and the Reviewer's
**APPROVED** with a sized position. Point at the message trace: "This is the audit trail."

**[1:05–1:35] Demo 2 & 3 — honesty.** Ask the ETH question → Reviewer returns **ABSTAIN**
("funding and momentum conflict, confidence below floor"). Ask DOGE → **ABSTAIN** ("no
data"). "It refuses to give a confident call it can't back — by design."

**[1:35–1:55] Demo 4 — escalation.** Ask the SOL question → **ESCALATE** ("drawdown
contribution exceeds the gate — routed to a human risk officer"). "The reviewer is
independent and can veto. That's separation of duties, enforced by agents collaborating
through Band."

**[1:55–2:00] Close.** "Band Risk-Review — a regulated risk desk, as a band of agents.
Open source