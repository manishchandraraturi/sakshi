# 01 — PRD: SAKSHI ("Skills, witnessed.")

> `sakshi` = "witness" in Hindi/Kannada and several Indian languages. Name is changeable; the concept is not.

## 1. One-liner
SAKSHI turns what a tradesperson can actually do into a **trusted, signed, shareable credential** by combining an **AI-guided practical test**, **real people who vouch**, and a **tamper-proof proof anyone can verify in seconds**.

## 2. The problem (plain words)
Plumbers, electricians, masons and similar workers learn on the job. They have skill but no paper. Hirers cannot tell good from fake, so workers lose steady work, get lowballed, and keep re-proving themselves.

**Organisers ask for:** a micro-credentialing platform that records practical skill assessments (short video demos or peer verifications) into an easily shareable digital profile.

### Requirement -> how we satisfy it
| Organiser requirement | Our answer |
|---|---|
| Practical skill assessment | Skill blueprint + in-app video test checked by a vision model, step by step |
| Short video demonstration | 60-120s in-app recording with a random challenge code (anti-fake) |
| Peer verification | No-login witness links, weighted by role, own credential, anti-collusion |
| Easily shareable digital profile | Public profile page, QR, WhatsApp share-card image, verifiable link |
| Informal workers & trainees | Voice-first, 3 languages, low-literacy UX, Skill Ladder with coaching |
| Local hiring contractors | One-tap verify page, no login, local-area directory |
| Fair wages / steady work | Tier badge + evidence timeline hirers can trust at a glance |

## 3. Users
1. **Ravi, 34, electrician (worker).** Basic Android phone, speaks Kannada/Hindi, little typing. Wants proof so contractors stop doubting him.
2. **Suresh, 45, trainer/senior mason (witness).** Will vouch if it takes 30 seconds, no signup, on WhatsApp.
3. **Meena, 38, small contractor (hirer).** Needs to know in 10 seconds whether to trust a stranger.
4. **Anita, 19, ITI trainee.** Has nothing to show. Needs a path: "what to improve to reach Witnessed".

## 4. Why most teams will lose (and how we avoid it)
Most of the 2000+ teams will build: *upload video -> AI score -> badge*. That is one layer, easy to fake, and a form with a chatbot on top. We keep that layer but add what judges will not see elsewhere:

| # | Differentiator | Why it matters |
|---|---|---|
| 1 | **Three-layer evidence** (AI test + human witnesses + signed proof) | Trust comes from more than one source |
| 2 | **Agent, not form**: interviews, plans, asks to re-do only failed steps, explains, coaches | Real agentic behavior with decisions |
| 3 | **Anti-fraud by design**: random challenge code, in-app live capture, duplicate-video hash | Directly answers "can't they fake it?" |
| 4 | **Trust graph weights**: credentialed/trainer witnesses count more; reciprocal/same-device vouches discounted | Answers "can friends fake it?" |
| 5 | **Tamper-proof credential**: Ed25519 signed, verified in the hirer's browser | Live demo moment: edit one letter -> "INVALID" |
| 6 | **Deterministic tiering**: AI proposes, rules decide, every score explained | Explainable, auditable, no black box |
| 7 | **Local-first UX**: voice in/out, English/Hindi/Kannada | "Localized" in the problem title |
| 8 | **Skill Ladder coaching** | Trainees get a path, not just a rejection |

## 5. Solution: the Sakshi Method
```
WORKER ──> 1. AGENT INTERVIEW ──> 2. LIVE VIDEO TEST ──> 3. AI STEP CHECK
               (scenario Qs)         (+challenge code)       (vs blueprint)
                                                                  │
                  6. SIGNED CREDENTIAL <── 5. TIER ENGINE <── 4. WITNESS VOUCHES
                  (QR + card + profile)     (deterministic)       (no-login links)
                                  │
                       HIRER opens link ──> signature check + evidence timeline
```

### Skill Blueprints (the ground truth)
Hand-written JSON per skill: ordered steps, what each step looks like on camera, critical vs optional, safety items, 3-5 scenario questions, common mistakes. The AI is only ever asked "does the evidence match *this* blueprint?". V1 skills: **Electrician - socket/switch board wiring (mock board)**, **Plumber - pipe joint + leak test**, **Mason - brick wall alignment (plumb/level check)**. Blueprints are inspired by task-style occupational standards (e.g. NSQF-style); we do not claim official certification.

## 6. Trust model
**Tiers** (decided by code, not AI):
| Tier | Name | Rule |
|---|---|---|
| 0 | Needs retry | Hard fraud flag, or critical steps failed |
| 1 | Demonstrated | Video score >= 70, all critical steps pass, no fraud flags |
| 2 | Witnessed | Tier 1 + total witness weight >= 1.0 |
| 3 | Trusted | Tier 1 + weight >= 3.0 + >= 2 distinct witnesses + >= 1 trainer or employer |

**N1 Safety Gate:** If any `safety_critical` item in the blueprint is "fail" or "unclear", the tier is capped at 0 (Needs retry), regardless of the overall score. This is a deterministic rule.

**Witness weight** = role base (peer 1.0, trainer 1.5, employer 1.2, customer 0.8) x 1.5 if witness holds own credential in same trade x 0.5 if reciprocal vouch with this worker x 0.5 if "did not see in person". Same device/IP as the worker -> 0. Duplicate device among witnesses -> only first counts. "Needs work" vouches add 0 weight and show as private feedback to the worker.

**Display Trust Score (0-100)** = 0.5 x video + 0.15 x interview + 0.35 x min(100, weight/3 x 100). Shown with its breakdown. Tier, not score, is what gates.

## 7. Features
**P0 (demo-critical, must ship)**
- Language pick (EN/HI/KN) and skill pick
- Agent interview (text + voice input via Web Speech, voice output) with adaptive follow-ups (max 3)
- In-app video recording with challenge code overlay; upload as lower-trust fallback
- Frame extraction + AI step-by-step verdict mapped to blueprint, with evidence frames
- Fraud checks: challenge code, duplicate hash, duration/metadata sanity
- Witness invite links + witness vouch page (no login)
- Deterministic tier engine + trust score breakdown
- Signed credential, public profile page, QR, WhatsApp share-card PNG
- Hirer verify page with live signature check and evidence timeline
- DEMO_MODE with cached AI responses (live demo can never die)

**P1 (should ship)**
- Fix-and-resubmit failed steps only (short clips)
- Worker dashboard (attempts, tier progress, witness status, coaching)
- Skill Ladder coaching ("do this to reach Witnessed")
- Directory: hirer filters verified workers by trade + area
- In-browser signature verification (tweetnacl)
- Consent screen + "delete my data"
- **N2 Credential Freshness:** Add `valid_until` (issued_at + 12 months) to the credential payload. Verify page displays "Valid until [date]".

**P2 (stretch, only after P0+P1 pass)**
- Face blur on shared clips; WhatsApp deep-link share; trainer mini-dashboard; PDF credential export

**Out of scope:** payments, real job posting/matching (that is Problem 3), official certification, native app, real-time chat.

## 8. Journeys
**Worker (3 min):** pick language -> pick trade -> agent asks 3-4 scenario questions (voice ok) -> sees checklist + challenge code -> records video -> watches agent review ("step 3 unclear, re-record 15s") -> sends 2-3 WhatsApp witness links -> gets credential + QR + card.
**Witness (30 s):** open link -> watch 20s clip -> answer 3 taps (seen in person? how long known? would hire?) -> vouch.
**Hirer (10 s):** scan QR / open link -> see tier, trust breakdown, evidence timeline, "Signature valid" -> trust.

## 9. Success metrics (for demo and pitch)
- Full worker flow under 4 minutes on a phone
- Tamper test: change one character in the credential -> verification fails visibly
- Fake test: reused video -> flagged; missing challenge code -> flagged
- Every score has a visible reason (no unexplained number)

## 10. Pitch narrative
**Hook:** "A plumber with 15 years of work has less proof than a teenager with a LinkedIn. Sakshi fixes that in 3 minutes."
**2-minute demo script**
1. (0:00) Hook + problem in one line.
2. (0:15) Ravi picks Kannada, agent asks a safety scenario by voice.
3. (0:40) Records the test; challenge code on screen. Agent: "Step 3 unclear" -> re-record a short clip.
4. (1:05) Two witnesses vouch (pre-seeded); tier jumps to Witnessed; breakdown animates.
5. (1:25) Credential issued; hirer scans QR; "Signature valid".
6. (1:40) Tamper demo: edit a character, "INVALID". Fake demo: reused video flagged.
7. (1:50) Close: "Evidence from AI, people and cryptography: skill, witnessed."

## 11. Judge Q&A prep
- **Can they fake the video?** Random challenge code in live capture, duplicate hash, metadata checks, and AI is only layer 1; witnesses and tiers sit on top.
- **Can friends collude?** Weights drop for reciprocal/same-device vouches; Trusted needs a trainer/employer and 3+ weight.
- **Why trust AI?** It only compares evidence to a human-written blueprint, outputs evidence frames, and never decides tiers.
- **Privacy?** Worker owns the credential, consent first, clips shared only by link, delete-my-data, no raw data sold.
- **Scale/business?** Free for workers; paid verification for training institutes, contractors' associations and staffing firms; blueprints validated with ITIs and trainers next.
- **What if AI is down?** Provider fallback chain + cached DEMO_MODE; core flow still works.

## 12. Risks
| Risk | Mitigation |
|---|---|
| Free AI quota/outage | Provider interface, fallback, DEMO_MODE cache |
| Weak low-light/shaky video | Capture guidance, "unclear -> re-record that step" |
| Hindi/Kannada voice recognition errors | Always allow typing; show transcript for confirmation |
| Time overrun | Strict cut line in 05_TASKS (P0 first) |
