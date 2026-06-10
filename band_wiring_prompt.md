# Code-AI build prompt — wire Band Risk-Review into the real Band SDK

Paste this into Claude Code / Cursor **at or after the June 12 kickoff**, once you
have your Band account and the SDK/API access codes (shared on the kickoff stream).
You are extending an existing, working repo — do **not** rewrite the agent logic.

## Context for you, the code AI

The repo `band-risk-review/` already contains four working agents that collaborate
through a `Bus` abstraction and a deterministic risk core. It runs end-to-end
offline today via `LocalBandBus` and passes `test_workflow.py` (16/16). Your job is
to make the same four agents collaborate through a **real Band room**, plus connect
the **MongoDB Atlas MCP server** as the Data Agent's source — without changing the
risk math or the decision logic.

## Tasks

1. **Read the Band SDK docs first** (link given at kickoff). Identify the real
   primitives for: creating/joining a room, registering an agent, handing the turn
   to the next agent, and posting/reading structured messages. Map them to the four
   methods our agents already use: `post(Message)`, `latest(kind)`, `history(kind)`.

2. **Add `RealBandBus` in `band_bus.py`** implementing the same `Bus` protocol as
   `LocalBandBus`. It wraps the Band room: `post()` publishes a message to the room;
   `latest()/history()` read the room's message log. Keep `Message` (sender, kind,
   payload) as the on-the-wire schema. **Do not modify `LocalBandBus`** — keep it as
   the offline test double.

3. **Register the four agents as Band agents.** Each of `DataAgent`, `RiskAgent`,
   `CalibrationAgent`, `ReviewerAgent` becomes a Band-registered agent whose turn
   handler calls its existing `act()`. Preserve the handoff order:
   `Data → Risk → Calibration → Reviewer`. The Reviewer must remain able to ESCALATE
   (i.e. end the chain by handing to a human/queue rather than auto-approving).

4. **Wire MongoDB Atlas via the MCP server** in `DataAgent`. Replace the in-memory
   `self.store` reads with calls to the MongoDB MCP tool against a `portfolio`
   collection and a `market` collection. Add a `seed_atlas.py` that loads the same
   data shape currently in `seed_data.py` (free-tier Atlas). The Data Agent must
   still post the identical `evidence` packet shape — nothing downstream changes.

5. **Add an LLM narration layer (your model of choice — e.g. Gemini or Claude).**
   Use it ONLY to (a) parse the user's free-text question into `{symbol, intent}`
   for the Data Agent, and (b) turn the Reviewer's structured decision into a plain
   plain-English answer with the audit trail. The LLM must **never compute risk
   numbers** — those come only from `risk_core.py`. Keep that boundary explicit in
   the system prompts.

6. **Keep tests green.** `test_workflow.py` must still pass against `LocalBandBus`.
   Add a thin smoke test that runs one review through `RealBandBus` (guarded so CI
   skips it when Band credentials are absent).

7. **Deliverables to print at the end:**
   - public GitHub repo `ryonzhang/band-risk-review` (MIT)
   - README updated with the real Band setup steps + the `architecture_band.png`
   - a checklist confirming: room created, 4 agents registered, MongoDB MCP returns
     real data, the four demo asks reproduce APPROVED / ABSTAIN×2 / ESCALATE, and the
     full message trace is retrievable from the room.

## Hard constraints

- 3+ agents must genuinely **collaborate through Band** (the judging criterion) —
  not one agent calling functions. The handoff and the shared room are the point.
- Original work, MIT-licensed (Band rule).
- Don't touch `risk_core.py`'s math or `agents.py`'s decision thresholds. If the
  Band API forces a signature change, adapt the bus, not the logic.

## Submission assets still needed (human)

- Demo video / slide presentation walking the four scenarios and the audit trail.
- Public demo URL if required by the track.

<!-- end of band_wiring_prompt -->
