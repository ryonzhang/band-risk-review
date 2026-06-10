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
    """Transport contract. LocalBandBus and RealBandBus both satisfy this."""
    def post(self, msg: Message) -> None: ...
    def history(self, kind: str | None = None) -> List[Message]: ...


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
