# Band setup — get the four agents live (do this on your machine)

This is the only part that can't be pre-built: it needs your Band account + keys.
Follow top to bottom; ~20–30 min. Fail-fast at step 4 before wiring all four.

## 1. Accounts & install
- Create a free Band account: https://app.band.ai
- Install: `uv init` (Python 3.11+), then `uv add "band-sdk[anthropic]"`
- Copy `.env.example` → `.env` and add your `ANTHROPIC_API_KEY` (or AI/ML API key).

## 2. Create the four agents in Band
In Band → **Agents** → **New Agent** → type **External Agent**. Create four, naming
them EXACTLY (the @mention routing depends on the names):
- `Risk-Data`
- `Risk-Quant`
- `Risk-Calibration`
- `Risk-Reviewer`

For each, on creation copy the **API Key** (shown once) and the **Agent UUID**
(agent settings, bottom-right).

## 3. Fill credentials
Copy `agent_config.example.yaml` → `agent_config.yaml` and paste each agent's
`agent_id` (UUID) + `api_key`. Both `.env` and `agent_config.yaml` are gitignored —
never commit them.

## 4. Fail-fast connection test (do this BEFORE step 5)
```
uv run python band_connect_test.py
```
Expect `Connected as: Risk-Data` and `Band connection verified.` If this fails,
fix credentials/endpoints before going further — don't wire all four until this passes.

## 5. Run the four agents
Each agent is its own long-running process. Open four terminals (or use a process
manager / `&`):
```
uv run python band_agents.py data
uv run python band_agents.py quant
uv run python band_agents.py calibration
uv run python band_agents.py reviewer
```
Each should log `<name> connected to Band.`

## 6. Drive the collaboration in a chat room
In Band → **Chats** → **+** new room → add all four agents as participants → post:
```
@Risk-Data Should I add to my BTC position?
```
You'll watch the handoff in the room: Data → @Risk-Quant → @Risk-Calibration →
@Risk-Reviewer → you, ending in a verdict (APPROVED / ABSTAIN / ESCALATE). The full
message + tool-call trace in the room is your audit trail — this is what to record
for the demo video.

Try all four demo asks:
- "Should I add to my BTC position?"  → APPROVED, sized
- "ETH looks hot on socials — should I add?"  → ABSTAIN (conflicting signals)
- "Thinking about a DOGE position?"  → ABSTAIN (no data)
- "Add more SOL here?"  → ESCALATE (drawdown gate)

## 7. Wire MongoDB (optional polish, strengthens Track 3)
Replace the Data agent's seeded evidence with live reads from MongoDB Atlas via the
MongoDB MCP server (`portfolio` + `market` collections). Keep the same evidence shape.

## Notes
- The offline scaffold (`run_demo.py`, `test_workflow.py`, `LocalBandBus`) still works
  with no creds and proves the logic — keep it for CI and as a fallback in the demo.
- Confirm the Anthropic adapter class/constructor against
  https://docs.band.ai/integrations/sdks/tutorials/anthropic ; the rest follows the
  documented Agent.create / agent.run flow exactly.

<!-- end of SETUP_BAND -->
