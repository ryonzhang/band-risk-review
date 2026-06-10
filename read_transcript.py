"""
read_transcript.py — print a Band room's message trail (the audit trail).

Each agent's `fetch_room_context` returns the window of messages relevant to that
agent, so pass the role whose view you want (default: reviewer, to see verdicts).

    BAND_ROOM_ID=<room-uuid> python read_transcript.py reviewer
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
ROOM = os.environ.get("BAND_ROOM_ID", "")


def _g(o, k, d=None):
    return o.get(k, d) if isinstance(o, dict) else getattr(o, k, d)


async def main():
    if not ROOM:
        sys.exit("Set BAND_ROOM_ID (the room uuid) in .env or the environment.")
    role = sys.argv[1] if len(sys.argv) > 1 else "reviewer"
    _, key = load_agent_config(role, config_path="agent_config.yaml")
    rest = AsyncRestClient(base_url=REST, api_key=key)
    ctx = await AgentTools(room_id=ROOM, rest=rest).fetch_room_context(
        room_id=ROOM, page=1, page_size=80)
    msgs = _g(ctx, "messages") or _g(ctx, "data") or _g(ctx, "items") or []
    print(f"=== ROOM TRANSCRIPT ({len(msgs)} messages, {role}'s view) ===")
    for m in msgs:
        sender = _g(m, "sender_name") or _g(m, "sender") or "?"
        content = (_g(m, "content") or "").replace("\n", " ")
        print(f"[{sender}] {content[:300]}")


if __name__ == "__main__":
    asyncio.run(main())
