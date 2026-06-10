"""
band_agents.py — the four agents as REAL Band agents, powered by Gemini.

Band collaboration model: agents share a chat room and hand off by @mentioning
the next agent. The chain is:

    User -> @Risk-Data -> @Risk-Quant -> @Risk-Calibration -> @Risk-Reviewer -> User

Each agent does ONE job using the deterministic tools in risk_tools.py — the LLM
NEVER computes a risk number, it only parses intent and narrates results. A small
JSON state blob (<DATA>...</DATA>) is carried in each message so the next agent
has exactly what it needs; the text above it is the human-readable narration that
forms the audit trail in the room.

There is no first-class Band Gemini adapter, so each agent is a custom
`SimpleAdapter` that calls Gemini directly for narration/parsing and calls
risk_tools for every number.

Run each agent as its own process:
    python band_agents.py data
    python band_agents.py quant
    python band_agents.py calibration
    python band_agents.py reviewer
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys

from dotenv import load_dotenv

from thenvoi import Agent
from thenvoi.core import SimpleAdapter
from thenvoi.config import load_agent_config

import risk_tools as T
from seed_data import STORE

load_dotenv()

WS = os.environ.get("THENVOI_WS_URL", "wss://app.band.ai/api/v1/socket/websocket")
REST = (os.environ.get("THENVOI_REST_URL", "https://app.band.ai")).rstrip("/")
OWNER = os.environ.get("BAND_OWNER_HANDLE", "zhangruiyang36")
GEMINI_MODEL = os.environ.get("CALIBRATED_COPILOT_MODEL", "gemini-3.1-pro-preview-customtools")

NAMES = {"data": "Risk-Data", "quant": "Risk-Quant",
         "calibration": "Risk-Calibration", "reviewer": "Risk-Reviewer"}
HANDLE = {role: f"@{OWNER}/{name.lower()}" for role, name in NAMES.items()}
NEXT = {"data": "quant", "quant": "calibration", "calibration": "reviewer"}

KNOWN_SYMBOLS = sorted(set(list(STORE["market"].keys()) + ["DOGE", "BTC", "ETH", "SOL"]))

DATA_RE = re.compile(r"<DATA>(.*?)</DATA>", re.DOTALL)


# --------------------------------------------------------------------------- #
# Gemini helper — narration / intent parse only. Falls back to a template so a
# flaky LLM call never breaks the deterministic pipeline.
# --------------------------------------------------------------------------- #
def _gemini(prompt: str, fallback: str) -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return fallback
    try:
        from google import genai
        client = genai.Client(api_key=key)
        for model in (GEMINI_MODEL, "gemini-2.5-pro"):
            try:
                r = client.models.generate_content(model=model, contents=prompt)
                if r and (r.text or "").strip():
                    return r.text.strip()
            except Exception:
                continue
    except Exception:
        pass
    return fallback


def _parse_symbol(question: str) -> str:
    up = question.upper()
    for s in KNOWN_SYMBOLS:
        if re.search(rf"\b{s}\b", up):
            return s
    ans = _gemini(
        f"Extract the single crypto ticker symbol the user is asking about, as "
        f"uppercase letters only (e.g. BTC). If none, reply UNKNOWN.\n\n{question}",
        "UNKNOWN",
    ).upper()
    m = re.search(r"\b[A-Z]{2,6}\b", ans)
    return m.group(0) if m else "UNKNOWN"


def _extract_state(content: str) -> dict:
    m = DATA_RE.search(content or "")
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception:
        return {}


def _pack(narration: str, state: dict) -> str:
    return f"{narration}\n\n<DATA>{json.dumps(state, default=str)}</DATA>"


# --------------------------------------------------------------------------- #
# Role logic — each returns (narration, state, next_handle)
# --------------------------------------------------------------------------- #
def _do_data(question: str) -> tuple[str, dict, str]:
    symbol = _parse_symbol(question)
    market = STORE["market"].get(symbol)
    have = symbol in STORE["market"]
    state = {
        "symbol": symbol,
        "question": question,
        "evidence": {
            "holdings": STORE["portfolio"],
            "subject": market,
            "have_subject_data": have,
            "signals": (market or {}).get("signals", {}),
            "subject_vol": (market or {}).get("annual_vol"),
        },
    }
    if have:
        narration = (f"Gathered evidence for **{symbol}**: {len(STORE['portfolio'])} "
                     f"portfolio holdings and the subject's market signals. "
                     f"Handing to @{NAMES['quant']} for risk metrics.")
    else:
        narration = (f"No market data found for **{symbol}** in the database. "
                     f"Flagging the gap and handing to @{NAMES['quant']}.")
    return narration, state, HANDLE["quant"]


def _do_quant(state: dict) -> tuple[str, dict, str]:
    ev = state.get("evidence", {})
    risk = T.compute_portfolio_risk(ev.get("holdings", []))
    vol = ev.get("subject_vol")
    risk["subject_drawdown_est"] = (
        T.drawdown_estimate(vol)["drawdown_estimate"] if vol else None)
    state["risk"] = risk
    top = risk.get("top_risk_symbol")
    narration = (f"Deterministic risk via tools: top risk driver **{top}** at "
                 f"{round((risk.get('top_risk_share') or 0)*100)}% of risk, "
                 f"HHI {risk.get('hhi')}. Handing to @{NAMES['calibration']}.")
    return narration, state, HANDLE["calibration"]


def _do_calibration(state: dict) -> tuple[str, dict, str]:
    ev = state.get("evidence", {})
    if not ev.get("have_subject_data") or not ev.get("signals"):
        cal = {"abstain": True, "reason": "no data for the subject asset",
               "prob_up": None, "confidence": 0.0}
    else:
        cal = T.calibrated_probability(ev["signals"])
        if not cal.get("abstain"):
            cal["proposed_size"] = T.size_position(cal["prob_up"])["proposed_size"]
    state["calibration"] = cal
    if cal.get("abstain"):
        narration = (f"Calibration **abstains**: {cal.get('reason')}. "
                     f"Handing to @{NAMES['reviewer']}.")
    else:
        narration = (f"Calibrated prob_up **{cal['prob_up']}** (confidence "
                     f"{cal['confidence']}), fractional-Kelly size "
                     f"**{cal['proposed_size']}**. Handing to @{NAMES['reviewer']}.")
    return narration, state, HANDLE["reviewer"]


def _do_reviewer(state: dict, asker_handle: str) -> tuple[str, dict, str]:
    cal = state.get("calibration", {})
    risk = state.get("risk", {})
    decision = T.review_decision(
        proposed_size=cal.get("proposed_size", 0.0) or 0.0,
        top_risk_share=risk.get("top_risk_share"),
        subject_drawdown_est=risk.get("subject_drawdown_est"),
        abstain=bool(cal.get("abstain")),
        abstain_reason=cal.get("reason", ""),
    )
    state["decision"] = decision
    facts = json.dumps({"symbol": state.get("symbol"), "decision": decision,
                        "calibration": cal}, default=str)
    narration = _gemini(
        "You are an independent compliance reviewer. In 2-3 sentences, plainly "
        "state the verdict and why, for the user who asked. Do not invent any "
        f"numbers; use only these facts:\n{facts}",
        f"Verdict: **{decision['verdict']}** (final size {decision['final_size']}). "
        f"{'; '.join(decision.get('breaches') or []) or 'Within policy limits.'}",
    )
    narration = f"{narration}\n\nVerdict: **{decision['verdict']}**"
    return narration, state, asker_handle


# --------------------------------------------------------------------------- #
# The Band adapter
# --------------------------------------------------------------------------- #
class RoleAdapter(SimpleAdapter):
    def __init__(self, role: str):
        super().__init__()
        self.role = role
        self.name = NAMES[role]
        self.my_handle = HANDLE[role]

    async def on_started(self, agent_name: str, agent_description: str) -> None:
        print(f"[{self.name}] connected to Band as {agent_name!r}", flush=True)

    async def on_message(self, msg, tools, history, participants_msg,
                         contacts_msg, *, is_session_bootstrap, room_id) -> None:
        content = msg.content or ""
        # Don't react to our own messages.
        if getattr(msg, "sender_name", "") == self.name:
            return
        # Act only when THIS agent is mentioned. Mentions arrive as @[[id]] in
        # content with the real id/handle/name in msg.metadata.mentions, so match
        # on metadata (robust to how the platform renders the mention text).
        if not self._is_mentioned(msg):
            return
        print(f"[{self.name}] handling: {content[:100]!r}", flush=True)

        try:
            if self.role == "data":
                narration, state, target = _do_data(content)
            else:
                state = _extract_state(content)
                if self.role == "quant":
                    narration, state, target = _do_quant(state)
                elif self.role == "calibration":
                    narration, state, target = _do_calibration(state)
                else:  # reviewer
                    asker = await self._asker_handle(tools, msg)
                    narration, state, target = _do_reviewer(state, asker)
            await tools.send_message(_pack(narration, state), mentions=[target])
            print(f"[{self.name}] -> {target}", flush=True)
        except Exception as e:
            print(f"[{self.name}] ERROR: {e}", flush=True)
            try:
                await tools.send_message(
                    f"@{OWNER} {self.name} hit an error: {e}", mentions=[f"@{OWNER}"])
            except Exception:
                pass

    def _is_mentioned(self, msg) -> bool:
        meta = getattr(msg, "metadata", None)
        mentions = getattr(meta, "mentions", None) or []
        myhandle = self.my_handle.lstrip("@").lower()
        for m in mentions:
            mh = (getattr(m, "handle", "") or "").lower()
            mn = (getattr(m, "name", "") or "").lower()
            if mh == myhandle or mn == self.name.lower():
                return True
        return False

    async def _asker_handle(self, tools, msg) -> str:
        """Mention the human who started the chain; fall back to the owner."""
        try:
            parts = await tools.get_participants()
            for p in (parts or []):
                pd = p if isinstance(p, dict) else getattr(p, "__dict__", {})
                if str(pd.get("type", "")).lower() in ("user", "human"):
                    h = pd.get("handle") or pd.get("name")
                    if h:
                        return h if h.startswith("@") else f"@{h}"
        except Exception:
            pass
        return f"@{OWNER}"


async def run(role: str) -> None:
    agent_id, api_key = load_agent_config(role, config_path="agent_config.yaml")
    agent = Agent.create(adapter=RoleAdapter(role), agent_id=agent_id,
                         api_key=api_key, ws_url=WS, rest_url=REST)
    print(f"[{NAMES[role]}] starting…", flush=True)
    await agent.start()
    try:
        await agent.run_forever()
    finally:
        await agent.stop()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in NAMES:
        raise SystemExit(f"usage: python band_agents.py [{'|'.join(NAMES)}]")
    asyncio.run(run(sys.argv[1]))
