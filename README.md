# SAKSHI — Skills, Witnessed.

> **Micro-credentialing platform recording practical skill assessments via video demonstrations and peer verifications into shareable, tamper-proof digital profiles.**
>
> Built for the **UnlockED Mystery Track** — *Problem 1: Localized Vocational Skill Verification*.

---

## 1. Overview & Architecture

Informal and blue-collar workers (electricians, plumbers, masons) often lack formal, verifiable proof of their competence despite years of on-the-job mastery. SAKSHI solves this with **three independent layers of evidence**:

1. **Practical Demonstration & AI Video Audit**: The worker records a live video test demonstrating a standardized trade blueprint (with a dynamic, randomly generated challenge code). AI analyzes extracted frames against deterministic safety and quality criteria.
2. **Weighted Human Witnesses**: Zero-login WhatsApp invite links allow employers, master trainers, senior peers, and customers to vouch with anti-collusion algorithmic weighting.
3. **Ed25519 Cryptographic Credentials**: Finalized credentials are cryptographically signed using Ed25519 (`PyNaCl`), verified in real-time in the browser (`TweetNaCl.js`), and instantly verifiable by employers via QR code or public profile.

### Core Tech Stack (100% Free & Open-Source)
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Framer Motion, Zustand, Lucide Icons.
- **Backend**: FastAPI, SQLModel (Pydantic v2 + SQLAlchemy), SQLite, PyNaCl (Ed25519), OpenCV (cv2).
- **AI Layer**: Gemini Vision (`google-genai`), Fallback Provider Chain, Mock AI fixtures, and disk-based Cache (`AICache`).
- **Cryptography**: Ed25519 signatures, canonical JSON formatting, TweetNaCl browser verification.

---

## 2. Quickstart Guide (Windows CMD)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

---

### Step 1: Backend Setup & Run

Open a Windows Command Prompt (`cmd.exe`):

```cmd
cd E:\Projects\sakshi\backend

:: 1. Activate virtual environment
.venv\Scripts\activate

:: 2. Install dependencies (if not already installed)
pip install -r requirements.txt

:: 3. Run FastAPI server
uvicorn app.main:app --reload --port 8000
```

The backend API will be live at `http://localhost:8000`.  
Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

---

### Step 2: Database Demo Seed

To populate the database with realistic demo candidates across all three tiers:

```cmd
cd E:\Projects\sakshi\backend
.venv\Scripts\activate
python -m app.seed
```

This seeds 3 authentic candidates with valid Ed25519 cryptographic signatures:
- **Ravi Kumar** (Electrician) — **Tier 3: Trusted** (Trust Score: 92)
- **Suresh Patil** (Mason) — **Tier 2: Witnessed** (Trust Score: 78)
- **Anita Sharma** (Plumber) — **Tier 1: Demonstrated** (Trust Score: 71)

---

### Step 3: Frontend Setup & Run

Open a second Windows Command Prompt (`cmd.exe`):

```cmd
cd E:\Projects\sakshi\frontend

:: 1. Install dependencies (if needed)
npm install

:: 2. Start Vite development server
npm run dev
```

The frontend will start at `http://localhost:5173`.

---

## 3. DEMO_MODE (Offline Fallback for Pitching)

In high-stakes hackathon demos or unreliable venue Wi-Fi, enable **`DEMO_MODE`** in `backend/.env`:

```env
DEMO_MODE=true
```

When `DEMO_MODE=true`:
- The AI layer immediately checks the local disk cache (`backend/data/ai_cache/`) or serves deterministic mock responses (`MockAI`).
- External network calls to Gemini or fallback APIs are completely bypassed, preventing network timeouts or rate-limiting.
- The entire evaluation pipeline (interview state machine, frame analysis, N1 safety gate, scoring, and Ed25519 signing) executes flawlessly 100% offline.

---

## 4. Key Endpoints & Routes

### Frontend Routes
| Route | Description |
|---|---|
| `/` | Landing page with 3-layer proof highlights and language options |
| `/language` | Multi-language selection (English, हिन्दी, ಕನ್ನಡ) |
| `/skill` | Trade selection (Electrician, Plumber, Mason) with visual blueprints |
| `/interview/:id` | AI voice/text scenario interview with adaptive follow-ups |
| `/record/:id` | Video demonstration recording with challenge code overlay |
| `/record/:id?rerecord=true` | Short-clip re-recording flow for failed/unclear steps |
| `/review/:id` | AI video analysis, N1 safety gate check, and verdict |
| `/witnesses/:id` | WhatsApp witness invite generation & live vouch polling |
| `/w/:token` | Public zero-login witness vouching portal |
| `/credential/:id` | Issued credential view with animated wax seal & share card |
| `/c/:id` | Public tamper-proof profile with **live client-side Ed25519 verification** |
| `/directory` | Hirer trades directory filtering by trade and area |
| `/dashboard` | Worker dashboard with Skill Ladder coaching & "Delete My Data" |

### API Endpoints
- `GET /api/health` — Service health and demo mode status.
- `GET /api/skills` — Blueprint catalog for supported trades.
- `POST /api/workers` — Worker registration with explicit privacy consent.
- `DELETE /api/workers/{id}/data` — Privacy erasure (deletes videos, frames, revokes credentials).
- `POST /api/attempts` — Create new practical skill attempt with challenge code.
- `POST /api/attempts/{id}/interview/next` — Interview dialogue step.
- `POST /api/attempts/{id}/video` — Video upload, frame extraction, metadata & fraud check.
- `POST /api/attempts/{id}/rerecord` — Targeted step re-recording and step merging.
- `GET /api/attempts/{id}` — Poll attempt status, video score, and agent decision.
- `POST /api/attempts/{id}/witnesses` — Generate tamper-resistant witness vouch tokens.
- `GET /api/w/{token}` — Fetch witness vouch payload.
- `POST /api/w/{token}/vouch` — Submit witness vouch with anti-collusion device fingerprinting.
- `POST /api/attempts/{id}/finalize` — Deterministic tier engine & Ed25519 signing.
- `GET /api/credentials/{id}` — Public credential payload with cryptographic signature.
- `GET /api/pubkey` — Platform Ed25519 public key.
- `GET /api/directory` — Filter verified workers by trade and geographic area.

---

## 5. Live Pitch Demonstration Script (2 Minutes)

1. **The Problem (0:00 - 0:15)**: Show landing page. *"A plumber with 15 years of experience has less verifiable proof than a teenager with a LinkedIn. SAKSHI fixes that in 3 minutes."*
2. **Worker Demo (0:15 - 0:45)**: Pick trade, voice scenario check in English/Hindi/Kannada, live camera recording with random challenge code.
3. **AI Video Review & N1 Safety Gate (0:45 - 1:10)**: AI analyzes frames against blueprint criteria; critical safety steps are deterministically enforced.
4. **Witness Layer (1:10 - 1:30)**: Two witnesses vouch via no-login WhatsApp link; weighted engine boosts candidate to Tier 2 (Witnessed).
5. **The Cryptographic Climax (1:30 - 2:00)**:
   - Navigate to `/c/:credential_id`.
   - Show green **"SIGNATURE VALID"** banner verified inside the browser via TweetNaCl.
   - Click **"Tamper with Data"**: Modifying even 1 byte in the candidate's name causes an immediate violent red **"SIGNATURE INVALID — TAMPER DETECTED"** error.
   - Show Worker Dashboard and 1-click **"Delete My Data"** privacy sovereignty.

---

## 6. Running Tests

### Backend Tests
```cmd
cd backend
.venv\Scripts\activate
pytest -q
```
*Current test suite: 94 passing tests covering models, cryptography, blueprints, fraud checks, review engine, witness weights, directory filters, deletion, and re-recording.*

### Frontend Production Build
```cmd
cd frontend
npm run build
```
*TypeScript type-check and Vite production bundling.*

---

## License
MIT License. Built for the UnlockED Hackathon 2026.
