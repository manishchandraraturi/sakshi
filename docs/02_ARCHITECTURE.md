# 02 — ARCHITECTURE

## 1. Principles (bug minimizers)
1. **Contract first:** schemas (Pydantic on backend, mirrored TypeScript types on frontend) are written before logic.
2. **AI proposes, code decides:** tier/score/signing are pure deterministic functions with unit tests.
3. **One responsibility per module;** AI providers hidden behind one interface.
4. **Every external call has timeout, retry, fallback, and a demo cache.**
5. **Single envelope for all API responses:** `{ "ok": bool, "data": ..., "error": {"code","message","hint"} | null }`.
6. **Blueprint JSON is the only source of skill knowledge.** No skill facts come from the model.

## 2. System diagram
```
┌──────────────────────── BROWSER (React + Vite, mobile-first) ───────────────────────┐
│ Pages: Landing · Language · SkillPick · Interview · Record · Review · Witnesses     │
│        Credential · Profile(/c/:id) · Witness(/w/:token) · Directory · Dashboard    │
│ Browser APIs: MediaRecorder (video) · Web Speech (STT/TTS) · tweetnacl (verify)     │
└───────────────▲─────────────────────────────────────────────────────────────────────┘
                │ REST /api (JSON envelope, multipart for video)
┌───────────────┴──────────────────── FASTAPI BACKEND ───────────────────────────────┐
│ routers/ ─> services/ ─> (db | ai | video | crypto)                                │
│                                                                                    │
│  agent/        state machine + tool loop (interview, review decision, coaching)    │
│  ai/           provider interface: GeminiProvider · FallbackProvider · MockProvider│
│  video/        ffmpeg frames · ffprobe meta · sha256 · perceptual hash · fraud     │
│  trust/        witness weights · tier engine · trust score (pure functions)        │
│  crypto/       Ed25519 sign/verify · canonical JSON · QR · share-card (Pillow)     │
│  blueprints/   skills/*.json (ground truth)                                        │
│  db/           SQLModel + SQLite · audit_log                                       │
└────────────────────────────────────────────────────────────────────────────────────┘
        local disk: /data/videos, /data/frames, /data/cards, /backend/keys (gitignored)
```

## 3. Tech stack (all free)
| Layer | Choice | Why |
|---|---|---|
| Frontend | React 18 + Vite + TypeScript + Tailwind | Fast, fewer config bugs |
| Motion | Framer Motion | Layout animations, page transitions |
| State | Zustand (+ URL for ids) | Tiny, no boilerplate |
| Routing | react-router-dom | Standard |
| Icons | lucide-react (thin stroke fits design) | Free |
| Fonts | `@fontsource` packages | Self-hosted, works on bad venue wifi |
| Backend | FastAPI + Uvicorn + Pydantic v2 | Python, typed, auto docs at /docs |
| DB | SQLite + SQLModel | Zero setup |
| Vision/LLM | Google Gemini free tier (flash-class, verify current model name in AI Studio) | Free key, supports image input and multilingual text |
| Fallback AI | A second free provider (e.g. Groq or OpenRouter free vision model; verify availability) + MockProvider | Resilience |
| STT/TTS | Browser Web Speech API | Free, no key (Chrome); typing fallback always present |
| Video | MediaRecorder (browser), OpenCV-headless + imageio-ffmpeg (backend) | imageio-ffmpeg bundles ffmpeg, easy on Windows |
| Dedup | imagehash (pHash) + SHA-256 | Cheap fraud check |
| Crypto | PyNaCl (Ed25519), tweetnacl-js (browser verify) | Small, proven |
| QR / Card | qrcode + Pillow | Share-card PNG for WhatsApp |
| Tests | pytest, httpx TestClient; Vitest optional | Gate tests per phase |

## 4. Repo structure
```
sakshi/
├─ docs/                      (these 7 files)
├─ backend/
│  ├─ app/
│  │  ├─ main.py              (app, CORS, error handlers, routers)
│  │  ├─ config.py            (env, DEMO_MODE, limits)
│  │  ├─ schemas.py           (Pydantic contracts, envelope)
│  │  ├─ db.py, models.py
│  │  ├─ routers/ (skills, workers, attempts, witnesses, credentials, directory)
│  │  ├─ services/ (attempt_service, witness_service, credential_service)
│  │  ├─ agent/ (state.py, loop.py, tools.py, prompts.py)
│  │  ├─ ai/ (base.py, gemini.py, fallback.py, mock.py, cache.py)
│  │  ├─ video/ (frames.py, meta.py, fraud.py)
│  │  ├─ trust/ (weights.py, tiers.py, score.py)
│  │  ├─ crypto/ (sign.py, card.py, qr.py)
│  │  └─ blueprints/ (electrician_socket.json, plumber_joint.json, mason_wall.json)
│  ├─ tests/
│  ├─ data/ (gitignored) · keys/ (gitignored)
│  └─ requirements.txt, .env.example
├─ frontend/
│  ├─ src/
│  │  ├─ main.tsx, App.tsx, router.tsx
│  │  ├─ api/ (client.ts, types.ts)
│  │  ├─ store/ (session.ts)
│  │  ├─ i18n/ (en.json, hi.json, kn.json, t.ts)
│  │  ├─ styles/ (tokens.css, globals.css)
│  │  ├─ components/ (ui/*, Seal, ChallengeCode, StepList, TrustBreakdown, AgentLog, ...)
│  │  ├─ pages/
│  │  └─ hooks/ (useRecorder, useSpeech, useSession)
│  └─ index.html, tailwind.config.ts, vite.config.ts
└─ MEMORY pointer: docs/06_MEMO.md
```

## 5. Data model (SQLite)
- **workers**(id, name, language, area, phone_optional, device_fp, token, consent_at, created_at)
- **attempts**(id, worker_id, skill_id, status, challenge_code, interview_json, interview_score, video_path, video_sha256, video_phash, video_meta_json, ai_result_json, fraud_flags_json, video_score, decision, created_at, updated_at)
- **witness_invites**(id, attempt_id, token, created_at, used_at)
- **vouches**(id, invite_id, attempt_id, witness_name, role, device_fp, seen_in_person, known_years_bucket, would_hire, verdict[yes|needs_work], weight, created_at)
- **credentials**(id, attempt_id, worker_id, skill_id, tier, trust_score, payload_json, signature_b64, evidence_sha256, issued_at, revoked)
- **audit_log**(id, ts, actor, action, ref_id, detail_json)

`attempts.status`: `created -> interviewing -> awaiting_video -> analyzing -> needs_rerecord | reviewed -> awaiting_witnesses -> finalized | rejected`.

## 6. API contract
All responses use the envelope. Auth: simple bearer `worker.token` returned at signup, stored in localStorage (hackathon scope). Witness and public routes need no auth.

| Method & path | Purpose | Request -> Response (data) |
|---|---|---|
| GET `/api/health` | liveness | `{status, demo_mode}` |
| GET `/api/skills` | trades + skills (public blueprint fields) | `[{trade, skills:[{id,name,steps:[{id,title,critical}]}]}]` |
| POST `/api/workers` | signup | `{name,language,area,consent,device_fp}` -> `{worker_id, token}` |
| POST `/api/attempts` | start | `{skill_id}` -> `{attempt_id, challenge_code, checklist}` |
| POST `/api/attempts/{id}/interview/next` | next question/follow-up | `{answer?}` -> `{question?, done, progress}` |
| POST `/api/attempts/{id}/video` | upload video (multipart: file, source=live|upload, transcript?) | -> `{status:"analyzing"}` |
| GET `/api/attempts/{id}` | poll state/result | -> `{status, steps:[{id,verdict,confidence,evidence_frames,note}], fraud_flags, video_score, decision, agent_log:[...]}` |
| POST `/api/attempts/{id}/rerecord` | P1: short clip for failed steps | multipart (file, step_ids[]) |
| POST `/api/attempts/{id}/witnesses` | create invite links | `{count}` -> `[{token,url}]` |
| GET `/api/w/{token}` | witness page data | `{worker_first_name, skill, clip_url, steps}` |
| POST `/api/w/{token}/vouch` | submit vouch | `{name,role,seen_in_person,known_years,would_hire,verdict,device_fp}` |
| POST `/api/attempts/{id}/finalize` | compute tier + issue credential | -> `{credential_id}` |
| GET `/api/credentials/{id}` | public credential | `{payload, signature, tier, trust_breakdown, timeline, pubkey}` |
| GET `/api/credentials/{id}/card.png` | WhatsApp share card | image/png |
| GET `/api/pubkey` | Ed25519 public key (base64) | `{pubkey}` |
| GET `/api/directory?trade=&area=` | P1 verified workers list | `[{credential_id,name,trade,tier,area}]` |
| GET `/api/media/{kind}/{name}` | serve clip/frames (guarded) | file |

## 7. Core flows
### 7.1 Video pipeline
1. Browser records with MediaRecorder (webm/mp4), 60-120s, overlay shows challenge code. Optional live transcript via Web Speech sent along.
2. Backend saves file, computes SHA-256, ffprobe-style metadata (duration, resolution), rejects out-of-limit.
3. `frames.py`: extract up to 12 frames (1 per ~duration/12), resize to 768px max, JPEG.
4. `fraud.py`: duplicate SHA/pHash vs DB, duration bounds, metadata time vs session (best effort), `source=upload` flag (lower trust), challenge-code check (from AI + transcript).
5. `ai.analyze_frames(blueprint, frames, challenge_code, transcript)` -> strict JSON (see 03_RULES).
6. `agent.review_decision(...)` returns accept / rerecord(step_ids) / reject with reasons. Rerecord only applies to non-fraud, unclear/failed steps.
7. `trust.video_score` computed deterministically from step verdicts and weights.

### 7.2 Agent design (hybrid: pipeline backbone + agent at decision points)
- **Backbone:** the status state machine above (fixed, testable).
- **Agent decision points:** (a) interview follow-ups, (b) review decision (accept/rerecord/reject), (c) tier explanation + coaching text.
- **Loop:** LLM returns `{"action": "<tool>", "args": {...}}` or `{"final": ...}`; Python validates against allowed tools + Pydantic, executes, appends result, max 4 iterations, then forced finalize. Tools: `get_blueprint`, `ask_question`, `score_answer`, `request_rerecord`, `run_fraud_checks`, `compute_tier` (deterministic, read-only for the agent), `write_feedback`.
- Agent output is logged to `agent_log` and shown in the UI as a live "reasoning log" (short, factual lines, not chain-of-thought).

### 7.3 Credential signing & verification
- Canonical payload: `{cred_id, worker_name, area, trade, skill, tier, trust_score, issued_at, evidence_sha256, witness_count}` -> JSON with sorted keys, no whitespace -> Ed25519 sign -> base64 signature.
- Keypair generated on first run in `backend/keys/` (gitignored). Public key at `/api/pubkey`.
- Verify page recomputes canonical JSON in the browser and verifies with tweetnacl -> green "Signature valid" or red "INVALID". Server also verifies.
- Revocation flag shown prominently.

### 7.4 Witness flow
Worker creates 2-3 invites -> links `https://<host>/w/<token>` (WhatsApp share intent `https://wa.me/?text=...`) -> witness vouches -> `trust.weights` computes weight -> `finalize` re-runs tier engine.

## 8. Frontend structure rules
- Routes: `/`, `/start`, `/skill`, `/interview/:attemptId`, `/record/:attemptId`, `/review/:attemptId`, `/witnesses/:attemptId`, `/credential/:id`, `/c/:id` (public), `/w/:token`, `/directory`, `/dashboard`.
- Server state through a thin `api/client.ts` returning typed envelope; no data fetching inside presentational components.
- Polling `GET /attempts/{id}` every 1.5s with backoff during `analyzing`; show agent log lines as they appear.
- Every page handles: loading (skeleton), error (message + retry), empty.

## 9. Environment
```
GEMINI_API_KEY=            # free key from Google AI Studio
FALLBACK_AI_KEY=           # optional second provider
DEMO_MODE=false            # true = serve cached AI responses, never call network
MAX_VIDEO_MB=50
MAX_VIDEO_SECONDS=120
CORS_ORIGINS=http://localhost:5173
PUBLIC_BASE_URL=http://localhost:5173
```
Run locally; for the demo expose with a free tunnel (e.g. cloudflared or ngrok free) so witnesses/hirers can open links on real phones. Free hosts (Vercel + Render) are optional and can sleep; always keep a recorded backup demo.

## 10. Security & privacy basics
Consent before recording; video access only via unguessable media names; witnesses see only a short clip and first name; rate limit signup/vouch (simple in-memory); validate file type/size; strip nothing secret from logs; delete-my-data endpoint removes videos, frames, vouches and marks credential revoked.
