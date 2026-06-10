# Code-AI prompt — build & push Band Risk-Review (Band of Agents Hackathon, Track 3)

Paste this into Claude Code / Cursor **on Ryon's machine** (it has GitHub auth + can
run the Band SDK). You are taking an existing, tested offline scaffold and turning it
into a real multi-agent system that collaborates through the **Band** platform, then
publishing it. Band is publicly usable today (app.band.ai) — you do **not** need a
hackathon code to build; partner promo codes (AI/ML API, Featherless) are only for
optional partner credits at the June 12 kickoff.

---

## 0. Get the code

You have a git bundle `band-risk-review.bundle` (full history, one clean initial
commit). Clone it, then create the GitHub repo and push:

```bash
git clone band-risk-review.bundle band-risk-review
cd band-risk-review
git remote remove origin 2>/dev/null || true
# create the public repo and push (use gh if available):
gh repo create ryonzhang/band-risk-review --public --source=. --remote=origin --push
# or: git remote add origin git@github.com:ryonzhang/band-risk-review.git && git push -u origin main
```

If a stray, corrupted `.git/` folder shipped inside the source folder, delete it before
cloning the bundle (it was created on a restricted filesystem and is not the real repo).

**Confirm the push, then continue with the build below as normal commits.**

## 1. What already works (do NOT rewrite)

- `risk_core.py` — deterministic risk + calibration math (Brier/ECE, fractional Kelly,
  HHI concentration, drawdown). Pure functions. **The LLM must never compute these.**
- `band_bus.py` — the collaboration seam: a `Bus` protocol + `LocalBandBus` (offline
  in-memory stand-in for a Band room).
- `agents.py` — the four agents: `DataAgent`, `RiskAgent`, `CalibrationAgent`,
  `ReviewerAgent`. Each has one job and posts a structured message for the next.
- `run_demo.py` / `test_workflow.py` — 16/16 passing; four scenarios produce
  APPROVED / ABSTAIN(conflict) / ABSTAIN(no-data) / ESCALATE.
- `architecture_band.png`, `cover_band.png`, `logo_band.png` — brand assets.

Keep `LocalBandBus`, the risk math, and the decision thresholds intact. Your job is the
Band integration *around* them.

## 2. Wire the real Band SDK  (docs: https://docs.band.ai)

1. **Account + agents.** Create a free Band account at https://app.band.ai. Create
   **four Remote Agents** (Data, Risk, Calibration, Reviewer). Copy each agent's
   API key + UUID. Put them in `agent_config.yaml` (already gitignored) and `.env`
   (`THENVOI_REST_URL=https://app.band.ai/`,
   `THENVOI_WS_URL=wss://app.band.ai/api/v1/socket/websocket`).
2. **Install:** `uv init` (or use the repo) then
   `uv add "band-sdk[anthropic]"` (or `[claude-sdk]` / `[google-adk]` — pick one and
   note it in the README).
3. **Add `RealBandBus` in `band_bus.py`** implementing the SAME `Bus` protocol as
   `LocalBandBus` (`post`, `latest`, `history`) over a Band chat room. `Message`
   (sender, kind, payload) stays the on-the-wire schema. Do not modify `LocalBandBus`.
4. **Register the four agents as Band agents** and run the workflow as a real
   collaboration in a Band room: `Data → Risk → Calibration → Reviewer`, with each
   agent handing the turn to the next. The Reviewer must be able to end the chain by
   **ESCALATING** (hand to a human/queue) instead of auto-approving. This agent-to-agent
   handoff *through Band* is the judged feature — not a wrapper around one agent.
5. **MongoDB Atlas via MCP** for `DataAgent`: replace the in-memory `seed_data` reads
   with calls to the MongoDB MCP server against `portfolio` and `market` collections.
   Add `seed_atlas.py` loading the same data shape. The Data Agent must still emit the
   identical `evidence` packet — nothing downstream changes.
6. **LLM narration layer.** Use a model ONLY to (a) parse the user's free-text question
   into `{symbol, intent}` and (b) turn the Reviewer's structured decision into a plain
   answer + audit trail. **Point this at AI/ML API** (unified endpoint) so the project
   qualifies for the "Best Use of AI/ML API" partner prize ($1,000 cash + $1,000
   credits); fall back to Anthropic if AI/ML API credits aren't active yet. The model
   must never produce a risk number — those come only from `risk_core.py`.

## 3. Keep it honest & tested

- `test_workflow.py` must still pass against `LocalBandBus` (offline, no creds).
- Add a guarded smoke test that runs one review through `RealBandBus` and skips when
  Band credentials are absent (so CI stays green).
- Update `README.md` with the real Band setup steps and keep the architecture diagram.

## 4. Deliverables to print at the end

- Confirmation the public repo `ryonzhang/band-risk-review` is pushed (MIT).
- A checklist: Band room created · 4 agents registered · MongoDB MCP returns real data ·
  the four demo asks reproduce APPROVED / ABSTAIN×2 / ESCALATE · full message trace is
  retrievable from the Band room · `test_workflow.py` green.
- The repo URL.

## Hard constraints

- **3+ agents genuinely collaborating through Band** (the core judging criterion).
- Original work, MIT-licensed (Band rule). Don't touch the risk math or decision
  thresholds — if Band's API forces a signature change, adapt the bus, not the logic.

## Still needed from Ryon (human)

- Demo video + slide presentation walking the four scenarios and the audit trail.
- A hosted demo URL if the track requires one.
- Enroll on lablab.ai and (optionally) grab the AI/ML API promo code at the June 12
  kickoff to activate partner credits.

<!-- end of BUILD_AND_PUSH_PROMPT -->
