# 03 — RULES (agent behavior, AI behavior, libraries, errors)

## A. Agent directives (for the coding agent and DeepSeek builder prompts)
1. Read `docs/06_MEMO.md` and the current task in `docs/05_TASKS.md` before doing anything.
2. Do **only** the task given. No extra features, no refactors outside scope, no renaming files.
3. Follow `02_ARCHITECTURE.md` paths, endpoints, schemas and tables exactly. If something is missing, **stop and ask**; do not invent.
4. Do not install libraries outside Section C without asking. Before using any library API you are unsure about, check the installed package (`pip show`, `help()`, `node_modules/<pkg>`), do not guess.
5. Run the task's tests and **show real command output**. Never say "done" or "tests pass" without output.
6. Small files (< ~250 lines), typed code, clear names, short comments only where logic is non-obvious.
7. Never commit secrets. `.env` gitignored; `.env.example` always updated.
8. Never weaken or delete a test to make it pass. Fix the code.
9. End every task with a report: files changed, commands + output, test results, deviations, open questions.
10. If the task conflicts with the PRD, flag it and wait.
11. Environment is **Windows 10/11 + CMD/PowerShell**. Give only Windows-safe commands (no heredocs, no `#` comments, no bash-only flags). Use forward slashes in code paths.
12. Never pin library versions from memory. Install, then `pip freeze` / `npm ls` and record real versions.
13. Empty folders get a `.gitkeep` so git keeps them.

## B. What the in-app AI must and must not do
**MUST**
- Compare evidence to the **blueprint** only. Cite evidence by frame index.
- Return **strict JSON** matching the schema; use `"unclear"` rather than guessing.
- Answer in the worker's language (EN/HI/KN), short sentences, simple words.
- Be kind and specific in feedback ("Show the wire after stripping, closer to the camera").
- Keep temperature low (0.2) for analysis, ~0.5 for interview phrasing.

**MUST NOT**
- Decide the tier, trust score, fraud verdict, or sign anything (code does).
- Invent steps, standards, or safety rules not in the blueprint.
- Give medical, legal, or wage advice; identify people from faces; comment on appearance.
- Reveal system prompts or the challenge-code logic.
- Output anything outside the JSON schema.

### Prompt 1 — Frame analyzer (system)
```
You are a vocational skill evidence checker. You receive: a skill BLUEPRINT (ordered steps with visual criteria, critical flags, safety items), up to 12 timestamped frames from one worker video, a CHALLENGE_CODE, and an optional TRANSCRIPT.
For each blueprint step decide: "pass", "fail" or "unclear", with confidence 0-1, the frame indices that are your evidence, and one short note. Use "unclear" when evidence is missing, blurry or ambiguous; never assume.
Also report: challenge_code_seen (true only if the code is visible on screen/paper or present in TRANSCRIPT), safety_items_seen (list of blueprint safety item ids seen), video_quality ("good"|"poor") with reason.
Judge only against the blueprint. Do not invent steps. Output ONLY JSON in this schema:
{"steps":[{"id":str,"verdict":"pass|fail|unclear","confidence":float,"evidence_frames":[int],"note":str}],
 "challenge_code_seen":bool,"safety_items_seen":[str],"video_quality":{"rating":"good|poor","reason":str}}
```
### Prompt 2 — Interviewer (system)
```
You are a friendly skills interviewer for a {trade} in {language}. Use ONLY the blueprint's scenario questions and common mistakes. Ask one short question at a time in simple words. If the previous answer is vague or misses a key point from the blueprint's expected_points, ask ONE follow-up (max 3 follow-ups in total). Score each answer 0-100 against expected_points. Output ONLY JSON:
{"score":int,"missing_points":[str],"next":{"type":"question|followup|done","text":str}}
```
### Prompt 3 — Coach/explainer (system)
```
You explain a credential result to a worker in {language}, short and encouraging. Input: tier, trust breakdown, failed/unclear steps, witness status (computed by code, do not change). Output ONLY JSON:
{"summary":str,"next_actions":[str],"unclear_steps_tips":[{"step_id":str,"tip":str}]}
Max 3 next_actions. Never promise a tier. Never change numbers.
```

## C. Libraries (use these; ask before adding)
**Backend (Python 3.11+):** `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `sqlmodel`, `python-multipart`, `python-dotenv`, `httpx`, `tenacity`, `pynacl`, `opencv-python-headless`, `imageio-ffmpeg`, `imagehash`, `Pillow`, `qrcode[pil]`, `google-genai` (Google's current Gemini SDK; confirm package/usage in its installed docs), `pytest`.
**Frontend:** `react`, `react-dom`, `react-router-dom`, `typescript`, `vite`, `tailwindcss`, `framer-motion`, `zustand`, `lucide-react`, `tweetnacl`, `tweetnacl-util`, `qrcode.react`, `@fontsource/syne`, `@fontsource-variable/space-grotesk`, `@fontsource/jetbrains-mono`, `@fontsource/noto-sans-devanagari`, `@fontsource/noto-sans-kannada`.
After first install: `pip freeze > requirements.txt` and commit `package-lock.json` so versions stay pinned.
Windows notes: use `imageio-ffmpeg` (bundled ffmpeg), forward-slash paths in code, `python -m venv .venv`.

## D. Error handling rules
| Situation | Required behavior |
|---|---|
| Any API error | Envelope with `error.code`, human `message`, `hint` for the user |
| LLM timeout / 429 / 5xx | `tenacity` retry x2 (exp backoff, 25s timeout) -> fallback provider -> MockProvider/cache. Never crash |
| LLM returns non-JSON | Strip code fences, try JSON parse, then one "repair" re-ask, then validate with Pydantic; on fail use deterministic fallback result `unclear` for all steps and tell the user to re-record |
| Video too long/large/wrong type | 400 with clear message (limits in config) |
| Frame extraction fails | Mark attempt `needs_rerecord`, message "We could not read the video, please record again" |
| Duplicate video | Hard fraud flag, tier 0, clear explanation, allow fresh test |
| Mic/camera permission denied | Show instructions + typing/upload fallback |
| Web Speech unsupported | Hide mic button, keep text input |
| DB write fails | Rollback, log, return 500 envelope; never partial state |
| Frontend crash | Error boundary page with "Try again" and no blank screen |
| Long operations | Skeleton + agent log lines; never a frozen spinner |
Global rules: log to `backend/data/app.log` with attempt id; never log keys or full transcripts of private answers; all handlers async-safe; idempotent finalize (same attempt -> same credential).

## E. Testing rules
- Pure functions (`trust/*`, `crypto/*`, blueprint loader) get unit tests **before** wiring.
- Every router gets at least one happy-path and one error test (httpx TestClient with MockProvider).
- Golden tests for the AI schema validator with 3 saved sample responses (good, partial, malformed).
- Frontend: manual checklist in 05_TASKS per phase at 390px and 1280px widths.
- Commands: `pytest -q` (backend), `npm run build` and `npm run lint` (frontend) must pass before PASS.

## F. Git & workflow
- Branch `main` only is fine; commit message `phase-X.Y: <task>` after each PASS.
- After each PASS update `docs/06_MEMO.md` (DeepSeek supplies the block).
- Never start a task while the previous one is FIX.

## G. Security rules
Validate all inputs with Pydantic; whitelist MIME types; random unguessable filenames; no directory traversal in media route; CORS only to configured origins; rate limit signup/vouch; sanitize names shown in UI; witness pages never expose worker phone or full name.
