# 07 — DEEPSEEK HANDOFF (paste this as ONE message into your DeepSeek chat)

Use this in the **same DeepSeek chat** (it already has the docs) or a fresh one. If fresh: paste this first, then paste `06_MEMO`, `01_PRD`, `02_ARCHITECTURE`, `03_RULES`, `04_DESIGN`, `05_TASKS` (use the **updated** copies from this download).

~~~text
HANDOFF + CORRECTIONS. Read fully, then reply with the CONFIRMATION FORMAT at the bottom.

1) WHAT CHANGED SINCE YOUR LAST MESSAGE
- I did NOT send you T0.1 builder prompt to any agent. Ignore it; you will write a corrected one (see section 5).
- I replaced the coding agent: NOT Freebuff anymore. I now use GOOGLE ANTIGRAVITY with the model I selected there: "Gemini 3.8 Flash (High)". Everything else in our workflow is the same: you write ONE builder prompt -> I paste it into Antigravity -> Antigravity builds and runs tests -> I paste its full report to you -> you answer PASS (+ MEMO UPDATE block) or FIX (+ fix prompt) -> I say "next".
- Wherever the docs/your earlier replies say Freebuff, read it as Antigravity. The docs I give you are already updated.
- Never trust the agent's claims without real command output in its report.

2) DONE BY HAND ALREADY (do not redo)
- Windows 10/11, CMD (not bash). Repo root: E:\Projects\sakshi
- Git initialized, branch main, remote origin = https://github.com/manishchandraraturi/sakshi.git (username has "raraturi", two "ra"). First commit 5486ed9 contains .gitignore and docs\ (the 7 docs).
- NOT done: folder scaffold, requirements.txt, .env.example, any code.
- Current task per memo: Phase 0 / T0.1.

3) CORRECTIONS TO YOUR PREVIOUS T0.1 DRAFT (apply them)
- Windows `tree` has NO "-L" flag. Use `tree /f /a` (or `dir /s /b`).
- Git does not track empty folders. Every empty scaffold folder gets a `.gitkeep` file.
- Do NOT tell the agent to "pin to latest stable versions if you know them". Never pin from memory. Agent installs later, then records real versions via `pip freeze`.
- Give only CMD/PowerShell-safe commands. No heredocs, no `#` comments, no bash flags.
- Antigravity may open its own terminal/browser; tell the agent to run commands in the project root and to show real output. Tell it to stop and ask if a command fails twice.
- One task per prompt, max ~600 words, using the 8-part template.

4) HOW WE WORK (so you coach me correctly)
- Docs in /docs are the source of truth: 06_MEMO > 01_PRD > 02_ARCHITECTURE > 03_RULES > 04_DESIGN > 05_TASKS.
- Baby steps: I am a student running this alone. Tell me exactly what to click/type. After every PASS give me the MEMO UPDATE block and the git commit command (CMD-safe): git add . then git commit -m "phase-X.Y: task".
- Be honest, concise, token-efficient. No fluff. Deliverables over plans.
- If my request conflicts with the PRD, say so and ask before changing.

5) PROJECT SNAPSHOT
SAKSHI ("Skills, witnessed.") for Mystery Track "UnlockED", Problem 1: Localized Vocational Skill Verification. 24-hour hackathon, 2000+ participants. Goal: get SHORTLISTED by being unique and reliable.
Problem: blue-collar workers (plumbers, electricians, masons) have skill but no verifiable credential, so hirers can't trust them -> unsteady work, low pay.
Organisers want: micro-credentialing platform recording practical skill assessments via short video demos or peer verification into an easily shareable digital profile.

OUR SOLUTION: THREE LAYERS OF PROOF + AN AGENT
(a) AI-guided practical test: an agent interviews the worker (voice/text; English, Hindi, Kannada) with scenario questions from a hand-written Skill Blueprint, then the worker records a short in-app video showing a random CHALLENGE CODE. A vision model compares frames to the blueprint step by step and cites evidence frames.
(b) Witness vouches: peers/trainers/employers/customers vouch via no-login links (WhatsApp). Weighted by role, own credential, anti-collusion rules.
(c) Signed credential: Ed25519-signed, public profile page, QR, WhatsApp share card; verifiable in the hirer's own browser.
PRINCIPLE: AI proposes, deterministic code decides tier/score/fraud/signature. Blueprint JSON is ground truth.

FLOW (end to end)
Worker: pick language -> pick trade -> agent interview (max 3 follow-ups) -> checklist + challenge code + consent -> live video -> agent review (accept / re-record only failed steps / reject) -> invite 2-3 witnesses -> tier engine -> credential (Seal animation, QR, card).
Witness: open link -> watch 20s clip -> 3 taps -> vouch.
Hirer: scan QR -> "Signature valid" + tier + evidence timeline + trust breakdown.
Tiers: 0 Needs retry, 1 Demonstrated, 2 Witnessed, 3 Trusted (exact rules in 01_PRD section 6).

WHY IT WILL BE SELECTED AMONG 2000+ TEAMS (use this to coach my pitch and keep scope focused)
Most teams build: upload video -> AI score -> badge. That is one layer, easy to fake. We differ:
1. Three independent evidence layers, not one AI score.
2. A real agent making decisions (follow-ups, re-record only step 3, explain, coach), not a form with a chatbot.
3. Anti-fraud by design: challenge code, live in-app capture, duplicate-video hash, upload = lower trust.
4. Trust-graph weights: trainers and credentialed witnesses count more; reciprocal/same-device vouches discounted.
5. Tamper-proof credential verified in the hirer's browser. Live demo moment: change one letter -> INVALID.
6. Deterministic, explainable tiers: every number has a visible reason.
7. Local-first UX: voice in/out in Hindi/Kannada/English, low-literacy friendly, mobile-first.
8. Skill Ladder: trainees get a coaching path, not just a rejection.
Demo must be rock solid: DEMO_MODE with cached AI results, backup recorded video, 2-minute scripted pitch (01_PRD section 10).

6) NEW IDEAS (PROPOSED. Do NOT build unless I approve. Evaluate each: effort, risk, judge impact, then recommend yes/no and which phase)
N1 SAFETY GATE (cheap, high judge value): each blueprint has safety_critical items (e.g. electrician shows power switched off before touching the board). If a safety_critical item is not seen, the tier is capped at 0 regardless of score, with a clear "safety first" message. Pure rule, no extra AI.
N2 CREDENTIAL FRESHNESS: credential payload includes valid_until (e.g. 12 months). Verify page shows "valid until". Re-verify = short 20s clip refresh. Small change in payload + UI.
N3 JOB PROOF ENTRIES (stretch): after a real job, the customer taps a link and confirms "job done well". Adds a "witnessed job" entry to the profile over time. Only after all P0/P1.
N4 OFFLINE-TOLERANT PWA (stretch): installable app that queues video upload when connectivity is weak (rural reality). Only if time remains.
Also tell me if you see a risk in the design, a bug-prone area, or a better simpler approach. Be direct.

7) RULES YOU MUST FOLLOW (unchanged)
- No invented endpoints, tables, fields, env vars or files outside 02_ARCHITECTURE. If missing, propose and ask.
- If unsure about a library API, tell the agent to check the installed package (pip show / help() / node_modules) first.
- No features outside 01_PRD. P2 only after P0/P1 pass. One task at a time. Never advance after FIX.
- The in-app AI (Gemini API, separate from Antigravity) must never decide tier/score/fraud/signature.

8) CONFIRMATION FORMAT (reply exactly in this structure, nothing else)
A. "HANDOFF RECEIVED"
B. Understanding check in 8 lines max (agent change, state, workflow, solution, tiers, principle).
C. Your verdict on N1-N4 (table: idea | effort | risk | impact | recommend).
D. Any risk or conflict you see in the docs (max 5 bullets).
E. Then WAIT. Do not write the T0.1 builder prompt until I say "next".
~~~

---

## What YOU do (baby steps)
1. Replace your local `docs\` files with the updated `00_START_PROMPT.md`, `03_RULES.md`, `06_MEMO.md` from this download (the other four are unchanged). Add `07_DEEPSEEK_HANDOFF.md` too.
2. In CMD: `git add .` then `git commit -m "docs: switch agent to Antigravity, windows rules"` then `git push`.
3. Paste the block above into DeepSeek. Read its reply (sections B-D). Tell it which of N1-N4 you approve.
4. Say `next`. It gives the corrected T0.1 prompt. Paste into Antigravity.

## Notes
- **Antigravity setup:** open the folder `E:\Projects\sakshi` as the workspace so the agent can read `docs\`. If it has a workspace rules file, paste the Agent directives from `03_RULES.md` there.
- **Two different AIs:** Antigravity's Gemini is your *coding agent*. The Gemini **API key** inside the app (needed from Phase 3) is separate. Don't mix them up.
- I could not verify the model name "Gemini 3.8 Flash (High)" or its free quota in Antigravity. Check your usage limits there before the event so you don't run out mid-build.
