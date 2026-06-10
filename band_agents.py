"""
band_agents.py — the four agents as REAL Band agents (SDK, @mention handoff).

Band collaboration model (per docs.band.ai): agents live in a shared chat room
and coordinate by @mentioning each other. Sequential pattern:

    User → @Risk-Data → @Risk-Quant → @Risk-Calibration → @Risk-Reviewer → User

Each agent does ONE job using the deterministic tools in risk_tools.py (the LLM
NEVER computes risk numbers), then @mentions the next agent with its structured
result. The Reviewer @mentions the human with the verdict, or escalates.

Run each agent as its own process (4 terminals, or a process manager):
    uv run python band_agents.py data
    uv run python band_agents.py quant
    uv run python band_agents.py calibration
    uv run python band_agents.py reviewer

Then create a chat room in Band, add all four agents, and post:
    @Risk-Data Should I add to my BTC position?

NOTE: This targets the Band SDK Anthropic adapter. Confirm the exact adapter
class/constructor name against https://docs.band.ai/integrations/sdks/tutorials/anthropic
(the documented LangGraph example uses `additional_tools=[...]`; Anthropic is
analogous). Everything else follows the documented Agent.create / agent.run flow.
"""
from __future__ import annotations
import asyncio, logging, sys
from dotenv import load_dotenv
from thenvoi import Agent
from thenvoi.adapters import AnthropicAdapter          # confirm name in docs
from thenvoi.config import load_agent_config

import risk_tools as T

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("band-risk-review")

MODEL = "claude-sonnet-4-6"   # or your AI/ML API model id (partner-prize path)

# Agent names MUST match the names you give the agents in the Band UI so that
# @mentions route correctly.
NAMES = {
    "data":        "Risk-Data",
    "quant":       "Risk-Quant",
    "calibration": "Risk-Calibration",
    "reviewer":    "Risk-Reviewer",
}

SYSTEM = {
"data": f"""You are {NAMES['data']}, the data agent in a 4-agent portfolio risk-review band.
When a human asks about adding to / trimming a position, identify the {{symbol}} and gather the
evidence packet: the current portfolio holdings (symbol, weight, annual_vol) and the subject
asset's market signals (momentum, funding, oi_trend, social_heat, fear_greed) and annual_vol.
In production you read these from MongoDB Atlas via the MongoDB MCP tool; never invent numbers.
If the subject asset has no data, say so explicitly.
Then hand off: post a message '@{NAMES['quant']} <evidence as compact JSON>'.""",

"quant": f"""You are {NAMES['quant']}, the risk agent. You receive an evidence packet.
Call compute_portfolio_risk(holdings) and drawdown_estimate(subject annual_vol). Do NOT
compute these yourself — always use the tools. Then hand off:
'@{NAMES['calibration']} <evidence + risk metrics as compact JSON>'.""",

"calibration": f"""You are {NAMES['calibration']}, the calibration agent. You receive evidence + risk metrics.
Call calibrated_probability(signals); if it does not abstain, call size_position(prob_up).
Never invent a probability or size — always use the tools. Then hand off:
'@{NAMES['reviewer']} <risk metrics + calibration result (prob, confidence, proposed_size or abstain) as compact JSON>'.""",

"reviewer": f"""You are {NAMES['reviewer']}, the INDEPENDENT compliance reviewer. You receive the
proposal + risk metrics. Call review_decision(proposed_size, top_risk_share, subject_drawdown_est,
abstain, abstain_reason). You may veto. Report the verdict (APPROVED / APPROVED_WITH_CONDITIONS /
ESCALATE / ABSTAIN_UPHELD), the final size, any breaches, and required actions, then @mention the
human who asked. Keep the full reasoning in the room — it is the audit trail.""",
}

TOOLS = {
    "data": [],   # in production: MongoDB MCP tool; here the LLM relays the seeded evidence
    "quant": [T.compute_portfolio_risk, T.drawdown_estimate],
    "calibration": [T.calibrated_probability, T.size_position],
    "reviewer": [T.review_decision],
}


async def run(role: str) -> None:
    load_dotenv()
    agent_id, api_key = load_agent_config(role)          # key in agent_config.yaml per role
    adapter = AnthropicAdapter(model=MODEL, system_prompt=SYSTEM[role],
                               additional_tools=TOOLS[role])
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    log.info(f"{NAMES[role]} connected to Band. Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in NAMES:
        raise SystemExit(f"usage: python band_agents.py [{'|'.join(NAMES)}]")
    asyncio.run(run(sys.argv[1]))
# end of band_agents.py
