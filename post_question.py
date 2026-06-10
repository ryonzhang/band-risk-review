"""
post_question.py — headlessly post a question into the Band room, @mentioning
Risk-Data, so the four-agent chain runs without driving the chat UI.

This stands in for a human asker (it posts via the Risk-Quant agent's API key,
so Risk-Data doesn't skip it as its own message). For the real demo you can also
just type "@Risk-Data <question>" in the Band room yourself.

    BAND_ROOM_ID=<room-uuid> python post_question.py "Should I add to my BTC position?"
"""
import asyncio
import os
import sys

from dotenv import load_dotenv

from thenvoi import AgentTools
from thenvoi.client.rest import AsyncRestClient
from thenvoi.config import load_agent_config

load_dotenv()
REST = (os.environ.get("THENVOI_REST_URL", "https://app.band.ai")).rstrip("/")
OWNER = os.environ.get("BAND_OWNER_HANDLE", "zhangruiyang36")
ROOM = os.environ.get("BAND_ROOM_ID", "")
ROLES = ["data", "quant", "calibration", "reviewer"]


def _participants() -> list[dict]:
    parts = []
    for role in ROLES:
        agent_id, _ = load_agent_config(role, config_path="agent_config.yaml")
        parts.append({"id": agent_id,
                      "handle": f"{OWNER}/risk-{role}",
                      "name": f"Risk-{role.capitalize()}"})
    return parts


async def main():
    if not ROOM:
        sys.exit("Set BAND_ROOM_ID (the room uuid) in .env or the environment.")
    question = sys.argv[1] if len(sys.argv) > 1 else "Should I add to my BTC position?"
    _, key = load_agent_config("quant", config_path="agent_config.yaml")
    rest = AsyncRestClient(base_url=REST, api_key=key)
    tools = AgentTools(room_id=ROOM, rest=rest, participants=_participants())
    resp = await tools.send_message(question, mentions=[f"@{OWNER}/risk-data"])
    print("posted:", getattr(resp, "id", resp))


if __name__ == "__main__":
    asyncio.run(main())
