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
| Current phase / task | **Phase 6 / T6.1-T6.2** |
| Last PASS | **T5.4** |
| Blocked by | nothing |
| DEMO_MODE | false |
| API keys set | GEMINI_API_KEY: no, FALLBACK_AI_KEY: no |

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
