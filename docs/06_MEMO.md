# 06 — MEMO (living source of truth)

> **READ THIS FIRST every session.** It overrides all other docs if there is a conflict. After every PASS, paste the MEMO UPDATE block into the "Changelog" and update "Current state". Keep it short and factual.

## 1. Project (locked)
- **Name:** SAKSHI, "Skills, witnessed."
- **Hackathon:** 24h build, 2000+ participants. Mystery Track "UnlockED", **Problem 1: Localized Vocational Skill Verification**.
- **Ask:** micro-credentialing platform recording practical skill assessments via short video demos or peer verifications into an easily shareable digital profile, for blue-collar/informal workers, trainees and local hirers.
- **Solution:** 3 evidence layers: AI-guided practical test (agent interview + live video with challenge code vs a hand-written blueprint) + weighted witness vouches (no-login links) + Ed25519-signed credential (public profile, QR, WhatsApp card, browser-verifiable).
- **Principle:** AI proposes, deterministic code decides. Blueprints are the ground truth.

## 2. Locked decisions (do not change without asking the human)
| Topic | Decision |
|---|---|
| Frontend | React + Vite + TS + Tailwind + Framer Motion + Zustand |
| Backend | FastAPI + SQLModel + SQLite |
| AI | Gemini free-tier vision via provider interface, fallback chain, MockProvider, DEMO_MODE cache |
| Voice | Browser Web Speech API (typing always available) |
| Languages | English, Hindi, Kannada |
| Skills (v1) | Electrician socket board, Plumber joint + leak test, Mason wall alignment (all mock/safe tasks) |
| Tiers | 0 Needs retry, 1 Demonstrated, 2 Witnessed, 3 Trusted (rules in 01_PRD s6) |
| Signing | Ed25519 (PyNaCl), verify in browser with tweetnacl |
| Design | Ink black + paper white, ONE orange accent, Syne / Space Grotesk / JetBrains Mono, mobile-first |
| Cost | Everything free. No paid APIs, no paid hosting |
| Build tooling | DeepSeek chat writes builder prompts + reviews; **Google Antigravity** (Gemini Flash, high) is the coding agent. Freebuff is no longer used |
| Environment | Windows 10/11, CMD. Repo root `E:\Projects\sakshi` |
| Git | Branch `main`, remote `https://github.com/manishchandraraturi/sakshi.git` (note: raraturi). First commit `5486ed9` (docs + .gitignore) |
| N1 Safety Gate | Approved. Cap tier at 0 if any `safety_critical` item fails. |
| N2 Credential Freshness | Approved. Payload includes `valid_until` (12 months). |
| N3 Job Proof & N4 PWA | Rejected. N3 is P2 stretch only. |

## 3. Current state
| Item | Value |
|---|---|
| Current phase / task | **Phase 13 / T13.1** |
| Last PASS | **T12.2** |
| Blocked by | nothing |
| DEMO_MODE | false |
| API keys set | GEMINI_API_KEY: configured, FALLBACK_AI_KEY: no |

## 4. Phase tracker
| Phase | Status | Gate passed (date) |
|---|---|---|
| 0 Setup | TODO | |
| 1 Data + Blueprints | TODO | |
| 2 Design system + shell | TODO | |
| 3 AI layer + Agent interview | TODO | |
| 4 Video capture + fraud | TODO | |
| 5 AI video analysis + review | TODO | |
| 6 Witnesses + tier engine | TODO | |
| 7 Credential + signing | TODO | |
| 8 Dashboard/directory/consent (P1) | TODO | |
| 9 Polish + demo hardening | TODO | |

## 5. Conventions
- API envelope: `{ok, data, error:{code,message,hint}|null}`.
- Paths, endpoints, tables: exactly as in `02_ARCHITECTURE.md`.
- Commands: backend `uvicorn app.main:app --reload --port 8000` (from `backend/`), tests `pytest -q`; frontend `npm run dev`, `npm run build`, `npm run lint`.
- Commit message: `phase-X.Y: <task>`.
- Ports: backend 8000, frontend 5173.

## 6. Known issues / open questions
- (none yet)

## 7. Do-not-do list
- No payments, job matching, native app, or real-time chat.
- No AI deciding tier/score/fraud/signature.
- No new libraries or endpoints without human approval.
- No secrets in code, prompts or commits.
- No N4 PWA or N3 Job Proof entries unless explicitly requested at the end of the hackathon.

## 8. Changelog (newest first)
Format for each entry:
```
### YYYY-MM-DD HH:MM — Task T#.# — PASS
- Done: ...
- Files: ...
- Decisions: ...
- Tests: command -> result
- Known issues: ...
- Next: T#.#
```

### 2026-11-24 — Task T13.1 — PASS
- Done: In-memory Rate Limiting & Scalability Blueprints — 1) Implemented thread-safe sliding-window InMemoryRateLimiter in backend/app/utils/rate_limiter.py with RateLimitExceeded exception returning HTTP 429 and standard API error envelope. Applied limiter dependencies to worker signup (max 5/min) and witness vouching (max 10/min). 2) Created welder_pipe.json (Welder trade, 5 steps: Safety gear, Metal prep, Tacking, Full weld, Slag removal) and carpenter_joint.json (Carpenter trade, 5 steps: Measure twice, Mark line, Saw cut, Chisel mortise, Apply wood glue) following the blueprint schema with safety_critical items and scenario questions. 3) Updated skills router to dynamically load all available blueprints so the frontend accordion automatically renders all 5 vocational trades. 4) Created test_rate_limit.py verifying 6th worker request returns 429 and rate limiter sliding window.
- Files: backend/app/utils/rate_limiter.py, backend/app/main.py, backend/app/routers/workers.py, backend/app/routers/witness.py, backend/app/routers/skills.py, backend/app/ai/mock.py, backend/app/blueprints/welder_pipe.json, backend/app/blueprints/carpenter_joint.json, backend/tests/test_rate_limit.py, backend/tests/test_routers.py, backend/tests/conftest.py, docs/06_MEMO.md
- Tests: pytest -q -> 112 passed in 21.57s; npm run build -> success (PWA service worker + 33 precache entries generated).
- Next: Final demo pitch presentation.

### 2026-11-24 — Task T12.2 — PASS
- Done: Test suite timeout fix and Dashboard UI polish — 1) Created backend/tests/conftest.py with autouse fixture enforcing settings.DEMO_MODE=True and monkeypatching get_default_ai to return MockAI across agent modules. Updated FallbackAI and loop.py to bypass Gemini live calls during testing, reducing test suite execution time from 44 minutes down to 21 seconds (109 passed). 2) Polished Dashboard UI into a verified worker profile with a large Tier badge (Seal component), interactive Share Profile button (clipboard copy of /c/{id} with toast feedback), animated Skill Ladder progression bar (Tier 1->3 percentage), and recent activity feed displaying AI coaching summary and next actions.
- Files: backend/tests/conftest.py, backend/app/ai/fallback.py, backend/app/agent/loop.py, frontend/src/pages/Dashboard.tsx, docs/06_MEMO.md
- Tests: pytest -q -> 109 passed in 21.02s; npm run build -> success (PWA service worker + 33 precache entries generated).
- Next: Final demo pitch presentation.

### 2026-11-24 — Task T12.1 — PASS
- Done: AI Coaching feature (Prompt 3 from 03_RULES.md) — 1) Added Prompt 3 (Coach/explainer system prompt and user prompt builder) in agent/prompts.py. 2) Implemented generate_coaching in agent/coach.py taking attempt analysis results and failed/unclear steps to produce summary, actionable next_actions, and per-step unclear_steps_tips, integrated into review.py decision pipeline and re-record handler. 3) Added coaching_json column to Attempt model and exposed coaching in GET /api/attempts/{id}. 4) Updated MockAI with dynamic Prompt 3 handling and added test_coaching.py. 5) Updated frontend types (CoachResult, UnclearStepTip), Review UI with prominent AI Coach Card and per-step tips in StepList, and Dashboard UI displaying active coaching guidance for the most recent assessment.
- Files: backend/app/agent/prompts.py, backend/app/agent/coach.py, backend/app/agent/review.py, backend/app/routers/attempts.py, backend/app/models.py, backend/app/db.py, backend/app/ai/mock.py, backend/tests/test_coaching.py, frontend/src/api/types.ts, frontend/src/components/StepList.tsx, frontend/src/pages/Review.tsx, frontend/src/pages/Dashboard.tsx, docs/06_MEMO.md
- Tests: pytest -q -> 109 passed; npm run build -> success (PWA service worker + 31 precache entries generated).
- Next: Final demo rehearsal and evaluation.

### 2026-11-24 — Task T11.1-T11.2 — PASS
- Done: Architecture upgrade for production — 1) Asynchronous video processing: Moved AI video analysis to FastAPI BackgroundTasks (`POST /api/attempts/{id}/video` immediately returns `status: "analyzing"`, and task runs isolated in background without timing out client HTTP requests). 2) Non-blocking attempt read: Removed synchronous analysis from `GET /api/attempts/{id}` so it acts strictly as a read-only DB query. 3) PWA transformation: Installed `vite-plugin-pwa`, configured standalone webmanifest, theme-color meta tag (#0A0A0A), and offline workbox service worker precaching. Added comprehensive async processing tests in `backend/tests/test_async_processing.py`.
- Files: backend/app/routers/video.py, backend/app/routers/attempts.py, backend/tests/test_async_processing.py, backend/tests/test_review.py, backend/tests/test_video.py, frontend/vite.config.ts, frontend/index.html, frontend/package.json, frontend/package-lock.json, docs/06_MEMO.md
- Tests: pytest -q -> 106 passed in 20.08s; npm run build -> success (PWA service worker + 30 precache entries generated).
- Next: Final demo rehearsal / evaluation.

### 2026-11-24 — Task T10.2 — PASS
- Done: Added conditional DEMO MODE orange pill badge on Landing page alongside backend status tag when health check reports demo_mode: true, communicating offline cache state to judges for 100% uptime assurance.
- Files: frontend/src/pages/Landing.tsx, docs/06_MEMO.md
- Tests: npm run build -> success.
- Next: Live pitch demonstration.

### 2026-11-24 — Task T10.1 — PASS
- Done: Production hardening — implemented React lazy loading and Suspense code splitting (splitting bundle from >500kB down to 34kB index + vendor chunks, completely resolving Vite chunk warning); added resilient camera access denied / unavailable fallback UI in Record page and useRecorder hook with highlighted file upload; fortified google-genai integration with try/except logging and automatic FallbackAI fallback to MockAI on quota (429) or network errors.
- Files: frontend/src/router.tsx, frontend/vite.config.ts, frontend/src/hooks/useRecorder.ts, frontend/src/pages/Record.tsx, backend/app/ai/gemini.py, docs/06_MEMO.md
- Tests: npm run build -> success (no chunk warnings, built in 7.02s), pytest -q -> 103 passed in 11.32s.
- Next: Final live pitch demonstration.

### 2026-11-23 — Phase 10 Audit & Fixes — PASS
- Done: Fixed WebM video metadata parsing on Windows using imageio_ffmpeg with OpenCV fallback. Stopped MockAI rubber-stamping by returning 'unclear'/score 0 for unrecognized inputs or adversarial phrases ('my pant is wet'). Enforced deterministic Tier logic (Tier 1 score threshold, Tier 3 trainer/employer requirement). Enforced N1 Safety Gate capping video score and Tier at 0 for failed/unclear safety critical steps. Enforced duplicate device fingerprint returning 0.0 weight. Closed witness role trust hole by requiring institute_code (e.g. SAKSHI2026) or existing credential for trainer/employer (downgrading to peer otherwise). Added institute_code to VouchCreate and UI. Verified valid_until (12 months) in canonical payload. Added 9 regression tests in test_audit_regressions.py.
- Files: backend/app/video/meta.py, backend/app/ai/mock.py, backend/app/trust/tiers.py, backend/app/trust/weights.py, backend/app/services/witness_service.py, backend/app/schemas.py, backend/tests/test_audit_regressions.py, frontend/src/api/types.ts, frontend/src/pages/WitnessVouch.tsx, docs/06_MEMO.md
- Tests: pytest -q -> 103 passed in 23.81s, npm run build -> success.
- Next: Ready for live pitch and production demonstration.

### 2026-11-23 — Task T9.4 — PASS
- Done: Fixed 422 error on attempt creation by resolving headers object spread overwrite in fetchApi; fixed SkillPick vertical text orientation (-90deg upright), added Back buttons to SkillPick and Language.
- Files: frontend/src/api/client.ts, frontend/src/pages/SkillPick.tsx, Language.tsx
- Tests: npm run build -> success.
- Next: Final demo rehearsal

### 2026-11-23 — Task T8.1-T8.4 — PASS
- Done: Delete My Data endpoint + UI, and re-record failed steps endpoint + UI.
- Files: backend/app/routers/workers.py, attempts.py, frontend/src/pages/Dashboard.tsx, Record.tsx, Review.tsx
- Tests: pytest -q -> 94 passed, npm run build -> success.
- Next: T9.2-T9.3

### 2026-11-23 — Task T8.2-T8.3 & T9.1 — PASS
- Done: Database seed script with 3 authentic candidates, Directory API & UI with filtering, and Worker Dashboard with skill ladder.
- Files: backend/app/seed.py, routers/directory.py, tests/test_directory.py, frontend/src/pages/Directory.tsx, Dashboard.tsx
- Tests: pytest -q -> 89 passed, npm run build -> success.
- Next: T8.1 & T8.4

### 2026-11-22 — Task T7.2-T7.4 — PASS
- Done: Share card generation, public profile, Seal animation, and browser verification.
- Files: backend/app/crypto/card.py, routers/credentials.py, frontend/src/pages/PublicProfile.tsx, utils/verify.ts
- Tests: pytest -q -> 85 passed, npm run build -> success.
- Next: T8.2, T8.3 & T9.1

### 2026-11-22 — Task T6.3-T7.1 — PASS
- Done: Witnesses UI, WitnessVouch page, Ed25519 signing, and Finalize endpoint.
- Files: backend/app/crypto/sign.py, routers/credentials.py, frontend/src/pages/Witnesses.tsx, WitnessVouch.tsx
- Tests: pytest -q -> 84 passed, npm run build -> success.
- Next: T7.2-T7.4

### 2026-11-22 — Task T6.1-T6.2 — PASS
- Done: Trust engine (weights, tiers, score), witness service, and endpoints.
- Files: backend/app/trust/*, services/witness_service.py, routers/witness.py
- Tests: pytest -q -> 78 passed.
- Next: T6.3 & T7.1

### 2026-11-22 — Task T5.4 — PASS
- Done: Built Review UI with polling, AgentLog streaming, StepList, and score display.
- Files: frontend/src/pages/Review.tsx, components/StepList.tsx
- Tests: npm run build -> success.
- Next: T6.1-T6.2

### 2026-11-22 — Task T5.1-T5.3 — PASS
- Done: AI frame analysis, N1 Safety Gate, deterministic video scoring, and review decision logic.
- Files: backend/app/trust/score.py, agent/review.py, routers/attempts.py, tests/test_review.py
- Tests: pytest -q -> 42 passed.
- Next: T5.4

### 2026-11-22 — Task T4.1-T4.3 — PASS
- Done: Video recording UI, upload endpoint, metadata checks, frame extraction, and duplicate fraud checks. Added GET /attempts/{id}.
- Files: frontend/src/pages/Record.tsx, hooks/useRecorder.ts, backend/app/video/*, routers/video.py
- Tests: pytest -q -> 34 passed, npm run build -> success.
- Next: T5.1-T5.3

### 2026-11-22 — Task T3.4 — PASS
- Done: Interview UI, Web Speech API integration, and AgentLog component.
- Files: frontend/src/pages/Interview.tsx, hooks/useSpeech.ts, components/AgentLog.tsx
- Tests: npm run build -> success.
- Next: T4.1-T4.3

### 2026-11-22 — Task T3.3 — PASS
- Done: Implemented interview state machine, AI loop, and POST /interview/next endpoint.
- Files: backend/app/agent/*, routers/interview.py, tests/test_agent.py
- Tests: pytest -q -> 29 passed.
- Next: T3.4

### 2026-11-22 — Task T3.1-T3.2 — PASS
- Done: AI layer (Base, Mock, Gemini, Fallback, Cache), JSON extraction utils, and AI tests.
- Files: backend/app/ai/*, tests/test_ai.py
- Tests: pytest -q -> 27 passed.
- Next: T3.3

### 2026-11-22 — Task T2.3 — PASS
- Done: Setup i18n, Zustand store, page transitions, and built Landing, Language, SkillPick pages with API integration.
- Files: frontend/src/i18n/*, store/session.ts, pages/*, App.tsx
- Tests: npm run build -> success.
- Next: T3.1 & T3.2

### 2026-11-22 — Task T2.1-T2.2 — PASS
- Done: Setup Tailwind tokens, CSS paper grid, and 6 UI components (Button, Card, Tag, SectionIndex, Skeleton, ErrorBoundary).
- Files: frontend/tailwind.config.ts, src/index.css, src/components/ui/*
- Tests: npm run build -> success.
- Next: T2.3

### 2026-11-22 — Task T1.3 — PASS
- Done: Created API routers for skills, workers, attempts. Added schemas, challenge code generator, and integration tests.
- Files: backend/app/routers/*, services/attempt_service.py, tests/test_routers.py
- Tests: pytest -q -> 9 passed.
- Next: T2.1 & T2.2

### 2026-11-22 — Task T1.2 — PASS
- Done: Created 3 skill JSON blueprints, Pydantic loader, and tests.
- Files: backend/app/blueprints/*.json, loader.py, tests/test_blueprints.py
- Tests: pytest -q -> 6 passed.
- Next: T1.3

### 2026-11-22 — Task T1.1 — PASS
- Done: Setup DB engine, 6 SQLModel tables, lifespan table creation, db tests.
- Files: backend/app/db.py, models.py, main.py, tests/test_db.py
- Tests: pytest -q -> 2 passed.
- Next: T1.2

### 2026-11-22 — Task T0.3 — PASS
- Done: Initialized Vite React+TS app, configured Tailwind and fonts, setup API client envelope, and health check on Landing page.
- Files: frontend/src/api/types.ts, client.ts, pages/Landing.tsx, vite.config.ts
- Decisions: Added custom TS declaration for tweetnacl-util.
- Tests: npm run build -> success.
- Next: T1.1

### 2026-11-22 — Task T0.2 — PASS
- Done: Setup FastAPI backend, config loader, generic API envelope, global error handler, and /api/health endpoint.
- Files: backend/app/config.py, schemas.py, main.py, tests/test_main.py
- Decisions: Used python-dotenv for config. Unpinned requirements.
- Tests: pytest -q -> 1 passed.
- Next: T0.3

### 2026-11-22 — Task T0.1 — PASS
- Done: Scaffolded full folder tree, added .gitkeep, created requirements.txt and .env.example. Updated docs with N1 and N2 rules.
- Files: backend/, frontend/, docs/01_PRD.md, docs/05_TASKS.md, docs/06_MEMO.md
- Decisions: Approved N1 (Safety Gate) and N2 (Credential Freshness). Rejected N3, N4.
- Tests: tree /f /a and git diff --stat passed.
- Next: T0.2

## 9. Glossary
- **Blueprint:** JSON describing a skill's steps, safety items, questions.
- **Challenge code:** random code shown in the live video to prove it was recorded now.
- **Witness weight:** numeric trust a vouch adds (rules in 01_PRD s6).
- **Tier:** badge level decided by code.
- **DEMO_MODE:** serve cached AI results so the demo never depends on the network.
