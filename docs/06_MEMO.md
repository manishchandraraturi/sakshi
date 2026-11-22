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
| Current phase / task | **Phase 0 / T0.2** |
| Last PASS | **T0.1** |
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
