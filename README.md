# Band Risk-Review

**A multi-agent compliance workflow for high-stakes financial decisions — four specialized agents collaborating through Band.**

Submission for the **Band of Agents Hackathon** (lablab.ai), **Track 3 — Regulated & High-Stakes workflows**. Built by Ruiyang Zhang (passed all three CFA Program exams). MIT.

![architecture](architecture_band.png)

## The idea

Most "AI finance agents" are a single model answering every question with the same false confidence. Real regulated finance doesn't work that way — it runs on **separation of duties**: the desk that proposes a trade is not the desk that approves it, and risk numbers come from a deterministic system, not someone's gut.

Band Risk-Review encodes exactly that as a band of four agents, each with one job, collaborating through Band:

1. **Data Agent** — retrieves the portfolio + market snapshot (MongoDB Atlas via MCP in the real build) and posts a structured *evidence packet*. Never invents data.
2. **Risk Agent** — computes deterministic portfolio risk: volatility-weighted risk shares, HHI concentration, a parametric drawdown estimate.
3. **Calibration Agent** — turns fused signals into a **calibrated probability + explicit confidence**, sizes the position by **fractional Kelly**, and **abstains** when confidence is below floor or signals conflict.
4. **Reviewer Agent** — an *independent* compliance gate. It reads the proposal and the risk metrics, checks them against policy limits, and returns one of: **APPROVED**, **APPROVED_WITH_CONDITIONS** (trim), **ESCALATE** (to a human risk officer), or **ABSTAIN_UPHELD**. It can veto.

The differentiator for Track 3: the **Reviewer is a separate agent that can override the Calibration Agent**, and every step is an auditable message on the shared Band room — a regulator-friendly trace of who said what and why.

## Honest design choice: deterministic core

All risk math lives in `risk_core.py` (Brier/ECE, fractional Kelly, HHI, drawdown). The agents *call* it and the LLM only narrates the results. The model never produces a risk number out of its head — the anti-hallucination guarantee that matters in regulated finance.

## Run it (no network, no credentials)

```
python run_demo.py        # four scenarios through the four agents
python test_workflow.py   # 16/16 — math + multi-agent handoff
```

The demo shows the full range of honest behaviour:

| Ask | Outcome | Why |
|---|---|---|
| Add to BTC? | **APPROVED**, size 11.4% | clean signals, drawdown contribution within gate |
| Add ETH (hot on socials)? | **ABSTAIN** | funding vs momentum conflict → confidence below floor |
| Add DOGE? | **ABSTAIN** | no data on the asset |
| Add SOL? | **ESCALATE** | drawdown contribution 9% of NAV > 6% gate → human review |

## Live on Band (verified ✅)

This is **not** just a mock — the four agents have been run live as Band Remote
Agents, collaborating through a real Band room and powered by **Gemini**:

```
python band_agents.py data         # 4 processes (see SETUP_BAND.md for creds)
python band_agents.py quant
python band_agents.py calibration
python band_agents.py reviewer
# then in a Band room with all four added:  @Risk-Data Should I add to my BTC position?
python post_question.py "Should I add to my BTC position?"   # or drive it headlessly
python read_transcript.py reviewer                            # print the room's audit trail
```

Each agent (`band_agents.py`) is a custom Band `SimpleAdapter`: it calls **Gemini**
for intent parsing + narration and the deterministic **`risk_tools.py`** for every
number (the LLM never invents a risk figure). The handoff
`Data → Quant → Calibration → Reviewer → user` happens entirely through the shared
Band room via @mentions — that agent-to-agent collaboration is the judged feature.
A verified run of all four scenarios (APPROVED / ABSTAIN×2 / ESCALATE) is in
[`DEMO_TRANSCRIPT.md`](DEMO_TRANSCRIPT.md).

The offline `LocalBandBus` in `band_bus.py` remains as the credential-free test
double (`run_demo.py` / `test_workflow.py`).

## Files

**Offline scaffold (runs now, no creds — proves the logic):**

- `risk_core.py` — deterministic risk + calibration math (pure functions)
- `band_bus.py` — the collaboration layer (`Bus` protocol + `LocalBandBus`)
- `agents.py` — the four agents (mock-bus version)
- `seed_data.py` — sample portfolio + market snapshot
- `run_demo.py` — orchestrates the four scenarios
- `test_workflow.py` — tests (math + workflow), 16/16

**Live on Band (Gemini-powered — see `SETUP_BAND.md`):**

- `risk_tools.py` — the deterministic core exposed as agent tools
- `band_agents.py` — the four agents as Band Remote Agents (Gemini + @mention handoff)
- `post_question.py` — headlessly post a question into the room (drives the demo)
- `read_transcript.py` — print the room's audit trail
- `agent_config.example.yaml`, `.env.example` — config templates (gitignored when filled)
- `SETUP_BAND.md` — step-by-step to stand up the four agents
- `DEMO_TRANSCRIPT.md` — a verified live run of all four scenarios

Built by **Ruiyang Zhang** (passed all three CFA Program exams). MIT.