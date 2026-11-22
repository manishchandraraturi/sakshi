# 05 — TASKS (phases, gates, tests)

**Rules:** one task at a time. A phase is DONE only when its **GATE** passes. Commit after each PASS. Update `06_MEMO.md`. If time runs short, follow the **cut line** at the bottom.

## Phase 0 — Setup (about 1h)
- T0.1 Create repo + folders per 02_ARCHITECTURE; `.gitignore` (venv, node_modules, .env, data/, keys/).
- T0.2 Backend: venv, install libs, `main.py` with `/api/health`, CORS, envelope + global error handler, `config.py` (DEMO_MODE etc).
- T0.3 Frontend: Vite + React + TS + Tailwind, fonts via @fontsource, router with placeholder pages, API client with envelope types.
- **GATE 0:** `GET /api/health` returns `{ok:true}`; frontend shows health result on landing; `pytest -q` and `npm run build` pass.

## Phase 1 — Data + Blueprints (about 2h)
- T1.1 SQLModel models + `db.py` + create tables on startup.
- T1.2 Write 3 blueprint JSONs (electrician socket board, plumber joint+leak test, mason wall alignment): steps (id,title,visual_criteria,critical), safety_items, scenario questions with expected_points, common_mistakes. Blueprint loader + validator.
- T1.3 `GET /api/skills`, `POST /api/workers`, `POST /api/attempts` (challenge code generator).
- **GATE 1:** pytest: loader rejects a malformed blueprint; skills endpoint lists 3 trades; creating a worker+attempt returns a unique challenge code; DB rows exist.

## Phase 2 — Design system + shell (about 3h)
- T2.1 Tokens, globals (paper grid), fonts, Tailwind theme per 04_DESIGN.
- T2.2 UI kit: Button, Card, Tag, SectionIndex, Toast, Skeleton, ErrorBoundary.
- T2.3 Page transitions, i18n (`t()` with en/hi/kn, language store), Landing, Language, SkillPick (expanding panels).
- **GATE 2:** manual checklist at 390px and 1280px: no horizontal scroll, fonts render in EN/HI/KN (no clipped glyphs), transitions smooth, reduced-motion respected, `npm run build` + lint pass.

## Phase 3 — AI layer + Agent interview (about 4h)
- T3.1 `ai/base.py` provider interface; `mock.py` (fixtures); `cache.py` (hash of input -> saved JSON); `gemini.py`; `fallback.py` chain with tenacity retries.
- T3.2 JSON parse/repair/validate utility with Pydantic schemas (prompts from 03_RULES).
- T3.3 Agent loop (`agent/loop.py`, `tools.py`, `state.py`) and `POST /interview/next` with max 3 follow-ups.
- T3.4 Interview UI: question stream, mic (Web Speech) + text fallback, progress dots, TTS toggle.
- **GATE 3:** pytest with MockProvider: scripted 4-answer interview ends `done`; malformed LLM output triggers repair then fallback (tested); with real key, one manual interview works in English and Kannada; with network off + DEMO_MODE the same flow still works.

## Phase 4 — Video capture, frames, fraud (about 4h)
- T4.1 `useRecorder` hook + Record page (code overlay, timer, preview, retry); upload fallback marked `source=upload`.
- T4.2 `POST /video`: save, SHA-256, metadata, limits.
- T4.3 `frames.py` (<= 12 frames, 768px) and `fraud.py` (duplicate SHA/pHash, duration bounds, upload flag, challenge-code pending).
- **GATE 4:** pytest: same video uploaded twice -> duplicate flag; 3-second clip rejected; oversized rejected. Manual: record on a real phone, frames appear in `data/frames`. Prepare 3 sample videos (good, incomplete, reused).

## Phase 5 — AI video analysis + review decision (about 4h)
- T5.1 `ai.analyze_frames` with Prompt 1, schema validation, DEMO cache for the 3 sample videos.
- T5.2 `trust/score.video_score` (critical steps weigh double; unclear = half credit) with unit tests.
- T5.3 Agent `review_decision`: accept / rerecord(step_ids) / reject; `GET /attempts/{id}` returns steps, flags, agent_log.
- T5.4 Review UI: AgentLog streaming, StepList, evidence thumbnails, TrustBreakdown preview, rerecord CTA.
- **GATE 5:** golden tests on 3 sample videos give expected verdict class (good -> accept, incomplete -> rerecord with right step ids, reused -> fraud). Review page renders with network blocked in DEMO_MODE.

## Phase 6 — Witnesses + tier engine (about 3h)
- T6.1 `trust/weights.py`, `tiers.py` exactly per 01_PRD Section 6; table-driven unit tests (at least 12 cases: reciprocal, same device, trainer, needs_work, etc).
- T6.2 Invite endpoints, witness page, vouch endpoint with device fingerprint.
- T6.3 Witnesses UI with live status polling and WhatsApp share intent.
- **GATE 6:** all tier tests pass; end-to-end test: attempt reviewed -> 2 vouches -> tier = Witnessed; add trainer + more weight -> Trusted; same-device vouch adds 0.

## Phase 7 — Credential, signing, share (about 3h)
- T7.1 `crypto/sign.py` (keygen, canonical JSON, sign, verify) + `finalize` endpoint (idempotent).
- T7.2 `GET /credentials/{id}`, `/pubkey`, `card.png` (Pillow share card with QR), QR component.
- T7.3 Credential page with Seal animation; Public profile `/c/:id` with Verify banner and evidence timeline.
- T7.4 In-browser verification with tweetnacl.
- **GATE 7:** pytest: signature verifies; flipping one character in payload fails; finalize twice -> same credential id. Manual: scan QR on another phone, verify banner shows; tamper demo shows INVALID.

## Phase 8 — Worker dashboard, directory, consent (about 2h) [P1]
- T8.1 Consent screen + delete-my-data endpoint (removes media, revokes credential).
- T8.2 Dashboard with tier ladder + coaching (Prompt 3).
- T8.3 Directory with trade/area filters.
- T8.4 Fix-and-resubmit failed steps via short clips (if not done in Phase 5).
- **GATE 8:** delete-my-data removes files and marks credential revoked; directory filters correct; rerecord merges step results.

## Phase 9 — Polish, demo hardening, pitch (about 3h)
- T9.1 Seed demo data (1 Trusted worker, 1 Witnessed, 1 trainee) via script; `DEMO_MODE=true` flow tested end to end offline.
- T9.2 Error/empty/loading states audit on every page; accessibility pass; HI/KN copy check.
- T9.3 Tunnel setup for phone demo; README with run steps; record a **backup demo video**.
- T9.4 Rehearse the 2-minute script (01_PRD Section 10) three times; prepare answers from Section 11.
- **GATE 9:** full run-through on phone over tunnel without errors; offline DEMO_MODE run passes; backup video saved on laptop and phone.

## Regression checklist (run after every phase)
`pytest -q` · `npm run build` · health endpoint · create worker -> attempt -> interview mock flow still works · no console errors on main pages.

## Cut line (if time runs out)
Keep **P0 only**: Phases 0-7 with minimal UI polish. Drop in this order: Directory, Dashboard coaching, rerecord, in-browser verify. Never drop: tamper-proof verify page, witness weights, challenge code, DEMO_MODE.

## Rollback rule
If a phase breaks previous gates, revert to the last green commit (`git reset --hard <sha>`), re-run its prompt with the failure notes.
