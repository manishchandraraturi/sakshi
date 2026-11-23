# SAKSHI: Skills, witnessed.

> A WhatsApp-native, voice-first skill passport that turns what a tradesperson can already do into proof anyone can trust in 10 seconds.

**wHACKiest 2026 · Mystery Track (UnlockED) · Problem 1: Localized Vocational Skill Verification**
**Team 3 Musketeers · CMR Institute of Technology, Bengaluru**

## The problem
Plumbers, electricians and masons learn on the job, so they have skill but no verifiable proof. Hirers can't tell good from fake, so good workers lose jobs, get low pay, and must prove themselves again with every new hirer. It is a **trust gap**, not a skill gap.

## Our solution: three layers of proof
1. **AI-guided practical test:** an agent interviews the worker (English, Hindi, Kannada), then the worker records a short in-app video showing a random **challenge code**. A vision model checks the video against a hand-written skill checklist, step by step.
2. **Witness vouches:** peers, trainers and employers vouch through a no-login link. Votes are weighted by role, and mutual or same-device vouches count less.
3. **Signed credential:** an Ed25519-signed profile with a QR code and a WhatsApp card. A hirer's browser verifies the signature. Edit one character and it shows **INVALID**.

**Principle:** the AI proposes, deterministic rules decide. Every score has a visible reason.

## Trust tiers (decided by code)
| Tier | Name | Rule |
|---|---|---|
| 0 | Needs retry | Fraud flag, failed critical step, or a missing safety-critical step (**Safety Gate**) |
| 1 | Demonstrated | Video passes all critical steps, no fraud flags |
| 2 | Witnessed | Tier 1 + enough witness weight |
| 3 | Trusted | Tier 1 + multiple witnesses including a trainer or employer |

Credentials carry a valid-until date and can be refreshed with a short clip.

## How it works
```
Worker -> Agent interview -> Live video + challenge code -> AI step check (vs blueprint)
      -> Agent decision (accept / re-record failed steps / reject)
      -> Witness links -> Tier engine (rules) -> Signed credential (QR + card)
Hirer  -> Opens link -> "Signature valid" + tier + evidence timeline
```
Anti-fraud: challenge code, live capture, duplicate-video hash, witness weight discounts.

## Tech stack (all free)
- **Frontend:** React, Vite, TypeScript, Tailwind, Framer Motion
- **Backend:** Python, FastAPI, SQLModel, SQLite
- **AI:** Google Gemini free-tier vision API behind a provider interface with fallback and a cached demo mode
- **Voice:** browser Web Speech API
- **Video:** OpenCV, ffmpeg (imageio-ffmpeg), imagehash
- **Crypto:** PyNaCl (Ed25519), tweetnacl in the browser

## Project status
| Area | Status |
|---|---|
| Product spec, architecture, rules, design, task plan | Done (see `/docs`) |
| Repo scaffold and backend skeleton | In progress |
| Skill blueprints (Electrician, Plumber, Mason) | Planned |
| Video check, witness flow, tier engine | Planned |
| Signed credential and verify page | Planned |

This table is updated as each phase passes its tests. The repository is under active development until the ideation presentations.

## Documentation
All design decisions live in [`/docs`](./docs): product requirements, architecture, AI rules, design system, task phases and the project memo.

## Safety, privacy and honesty
Consent before recording, worker-owned credentials, delete-my-data. Test tasks use mock setups with no live hazards. SAKSHI issues a **verifiable skill proof**, not an official certificate; skill checklists are to be validated with ITIs and trainers.

## Team
3 Musketeers: Manish Chandra Raturi, Dalavai Vaishnavi, Shreesha S
