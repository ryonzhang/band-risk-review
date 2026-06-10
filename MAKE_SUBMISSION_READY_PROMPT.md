# Code-AI prompt — push to GitHub & make Band Risk-Review submission-ready

Paste into your code AI (Claude Code / Cursor) ON YOUR MACHINE. It needs your GitHub
auth and your Band + LLM keys (it will pause and ask). Do not let it invent
credentials or fake results.

ROLE: You are finishing and shipping "Band Risk-Review" for the Band of Agents
Hackathon (lablab.ai, Track 3). The code is in this folder (or band-risk-review.bundle).
Your job: push the public repo AND get the project to a verified submission-ready state.

DEFINITION OF DONE (submission-ready):
- [ ] Public repo ryonzhang/band-risk-review pushed, MIT license present.
- [ ] Four agents connect to Band and collaborate IN A REAL BAND ROOM via @mention
      handoff (Data -> Quant -> Calibration -> Reviewer -> user).
- [ ] The four demo asks reproduce live: APPROVED / ABSTAIN(conflict) / ABSTAIN(no-data)
      / ESCALATE, with the full message+tool trace visible in the room.
- [ ] README updated with real run steps; SUBMISSION.md, cover_band.png,
      Band-Risk-Review-Deck.pptx all present and correct.
- [ ] You print: the repo URL, the live room transcript as evidence, and the only-human
      steps left (record video, paste submission text, add demo URL, click submit).

STEP 1 - Code + repo
- If using the bundle: git clone band-risk-review.bundle band-risk-review ; cd band-risk-review
  (delete any stray corrupt .git/ inside first).
- Create + push the public repo:
  gh repo create ryonzhang/band-risk-review --public --source=. --remote=origin --push
  (or add the remote manually and `git push -u origin main`). Confirm the push.

STEP 2 - Stand up Band (guide me, the human)
- Tell me to: create a free account at app.band.ai, create FOUR External Agents named
  EXACTLY Risk-Data, Risk-Quant, Risk-Calibration, Risk-Reviewer, and give you each
  agent's API Key + UUID. Wait for me.
- Copy .env.example -> .env (add my ANTHROPIC_API_KEY or AI/ML API key) and
  agent_config.example.yaml -> agent_config.yaml (paste the 4 agent_id+api_key). Keep
  both gitignored - never commit secrets.

STEP 3 - Fail-fast, then fix the real integration
- Run: uv add "band-sdk[anthropic]" ; then `uv run python band_connect_test.py`.
- If it fails, fix it. Likely first-run issues to confirm against docs.band.ai: the exact
  adapter class/constructor name (band_agents.py assumes AnthropicAdapter - confirm at
  docs.band.ai/integrations/sdks/tutorials/anthropic), the Agent.create/run signature, and
  how a remote agent posts a chat message with an @mention to hand off. Adapt
  band_bus.py / band_agents.py as needed - but DO NOT change the risk math in risk_core.py
  or the decision thresholds in risk_tools.py.

STEP 4 - Run all four agents and verify live
- Start the four agents (band_agents.py data|quant|calibration|reviewer).
- In a Band room with all four added, post each demo ask and confirm the handoff and the
  four verdicts reproduce. Capture the room transcript (text + tool calls) as evidence.
- Keep test_workflow.py green against LocalBandBus (offline); add a guarded live smoke
  test that skips when creds are absent.

STEP 5 - Finalize assets
- Update README with the verified run steps. Ensure SUBMISSION.md, cover_band.png,
  Band-Risk-Review-Deck.pptx are present. Commit and push everything (except secrets).

HARD CONSTRAINTS:
- 3+ agents must genuinely collaborate THROUGH Band (the core judging criterion) - not a
  wrapper or a homegrown bus. The LocalBandBus mock does NOT qualify; it is offline test
  scaffolding only.
- Original work, MIT. The LLM must never compute risk numbers - those come only from
  risk_core.py via the tools.
- Do not claim any professional certification for me. "Passed all three CFA Program exams"
  is the only credential phrasing allowed; never add "CFA" or "ASA" after my name.

OUTPUT: the repo URL, the live room transcript, and the remaining human checklist.

<!-- end of MAKE_SUBMISSION_READY_PROMPT -->
