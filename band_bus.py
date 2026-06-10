"""
band_bus.py — the collaboration layer.

Band of Agents judges *agents collaborating through Band*. This file is the
single seam between our deterministic agent logic and Band's transport.

`LocalBandBus` is a faithful MOCK of a Band "room": agents register by role,
post structured messages, and hand off to the next agent. It lets us prove the
whole multi-agent workflow end-to-end with zero network/credentials.

At the June 12 kickoff, swap LocalBandBus for `RealBandBus` (a thin adapter
over the Band SDK) WITHOUT touching any agent code — the agents only depend on
the `Bus` protocol below. See band_wiring_prompt.md.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Protocol
import json
import time


@dataclass
class Message:
    sender: str                 # role name of the agent that posted
    kind: str                   # e.g. "evidence", "risk", "calibration", "decision"
    payload: Dict[str, Any]     # structured, JSON-serializable
    ts: float = field(default_factory=time.time)

    def short(self) -> str:
        return f"[{self.sender}->{self.kind}] {json.dumps(self.payload, default=str)[:200]}"


class Bus(Protocol):
    """Transport contract. LocalBandBus and RealBandBus both satisfy this.

    The agents depend on exactly these three methods, nothing more — that is
    what makes swapping LocalBandBus for RealBandBus a drop-in change.
    """
    def post(self, msg: Message) -> None: ...
    def history(self, kind: str | None = None) -> List[Message]: ...
    def latest(self, kind: str) -> "Message | None": ...


class LocalBandBus:
    """In-memory stand-in for a Band room. Records an ordered, auditable trace."""

    def __init__(self) -> None:
        self._log: List[Message] = []
        self._subscribers: Dict[str, List[Callable[[Message], None]]] = {}

    def post(self, msg: Message) -> None:
        self._log.append(msg)
        for cb in self._subscribers.get(msg.kind, []):
            cb(msg)

    def subscribe(self, kind: str, cb: Callable[[Message], None]) -> None:
        self._subscribers.setdefault(kind, []).append(cb)

    def history(self, kind: str | None = None) -> List[Message]:
        if kind is None:
            return list(self._log)
        return [m for m in self._log if m.kind == kind]

    def latest(self, kind: str) -> Message | None:
        items = self.history(kind)
        return items[-1] if items else None

    def transcript(self) -> str:
        return "\n".join(f"{i+1:>2}. {m.short()}" for i, m in enumerate(self._log))


# --------------------------------------------------------------------------- #
# RealBandBus — SKELETON for the June 12 kickoff.                              #
#                                                                             #
# This is intentionally NOT functional yet: the Band SDK and its docs are     #
# released at the kickoff, so the exact primitives below are filled in then.  #
# It is a faithful map of WHAT to wire — same `Bus` protocol as LocalBandBus, #
# same `Message` (sender, kind, payload) on the wire — so swapping it in      #
# requires zero changes to agents.py / risk_core.py.                          #
#                                                                             #
# Wiring checklist (see band_wiring_prompt.md):                               #
#   1. Read the Band SDK docs (https://docs.band.ai).                          #
#   2. Create a free account + four Remote Agents at https://app.band.ai;      #
#      put their api_key/uuid in agent_config.yaml (gitignored).               #
#   3. Implement the three TODOs below against the room's message log.         #
#   4. Run test_real_band.py with creds present to verify a live round-trip.   #
# --------------------------------------------------------------------------- #
class RealBandBus:
    """Thin adapter over a real Band room. Satisfies the same `Bus` protocol.

    `post()` publishes a Message to the shared room; `latest()/history()` read
    the room's message log back. Messages are serialized as JSON in the room so
    the (sender, kind, payload) schema survives the round-trip unchanged.
    """

    def __init__(self, room_id: str, rest_url: str, ws_url: str,
                 agent_config: dict | None = None) -> None:
        """Open/join a Band room.

        Args:
            room_id: the Band room (chat) all four agents collaborate in.
            rest_url: THENVOI_REST_URL  (e.g. https://app.band.ai/).
            ws_url:   THENVOI_WS_URL    (e.g. wss://app.band.ai/api/v1/socket/websocket).
            agent_config: parsed agent_config.yaml — api_key + uuid per agent.
        """
        self.room_id = room_id
        self.rest_url = rest_url
        self.ws_url = ws_url
        self.agent_config = agent_config or {}
        # TODO(kickoff): construct the Band client / open the websocket here.
        #   from band_sdk import BandClient            # exact import per docs
        #   self._client = BandClient(rest_url, ws_url, token=...)
        #   self._room = self._client.join_room(room_id)
        self._client = None
        self._room = None

    # -- write side --------------------------------------------------------- #
    def post(self, msg: Message) -> None:
        """Publish a Message to the Band room as a structured (JSON) chat message."""
        raise NotImplementedError(
            "RealBandBus.post: wire to the Band SDK at the June 12 kickoff. "
            "Publish json.dumps({'sender','kind','payload','ts'}) to the room."
        )
        # TODO(kickoff):
        #   self._room.send_message(json.dumps({
        #       "sender": msg.sender, "kind": msg.kind,
        #       "payload": msg.payload, "ts": msg.ts}))

    # -- read side ---------------------------------------------------------- #
    def history(self, kind: str | None = None) -> List[Message]:
        """Read the room's message log back as Messages, optionally filtered by kind."""
        raise NotImplementedError(
            "RealBandBus.history: wire to the Band SDK at the June 12 kickoff. "
            "Fetch the room log, parse each JSON body into a Message, filter by kind."
        )
        # TODO(kickoff):
        #   msgs = [self._to_message(m) for m in self._room.messages()]
        #   return msgs if kind is None else [m for m in msgs if m.kind == kind]

    def latest(self, kind: str) -> "Message | None":
        """Most recent Message of a given kind in the room (None if none yet)."""
        items = self.history(kind)
        return items[-1] if items else None

    @staticmethod
    def _to_message(raw: Any) -> Message:
        """Parse a Band room message body (JSON) back into our Message schema."""
        body = json.loads(raw.body if hasattr(raw, "body") else raw)
        return Message(body["sender"], body["kind"], body["payload"],
                       body.get("ts", time.time()))
