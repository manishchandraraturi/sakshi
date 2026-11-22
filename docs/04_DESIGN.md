# 04 — DESIGN (minimal, black & white, smooth)

## 1. What we take from the reference images (inspiration, not copying)
The 4 track screenshots share a strong language. We borrow the **ideas**, not the artwork:
- **Paper-grid background:** warm off-white with very fine grid lines, like engineering paper.
- **Big black rounded cards** with generous radius, floating on the paper.
- **Heavy, wide display headline** with a single colored full stop (`Make MCP Matter.`).
- **Tiny mono, uppercase, letter-spaced labels** (`PICK A TRACK`, `HOURS TO BUILD`) and numbered sections (`04/Tracks`, `01`, `02`).
- **Expanding panels:** a row of slim vertical cards (rotated titles); the active one grows and the rest shrink. We use this for the **skill picker**.
- **Thin outline pills** for tags, thin hairlines as dividers, line-art doodle in the background.
- Our twist: **almost no color.** Ink + paper + ONE orange accent. Doodles are original thin line drawings of trade tools (not the reference drawings).

## 2. Design tokens
```css
:root{
  --ink:#0A0A0A;          /* primary black */
  --ink-2:#171717;        /* card surface on paper */
  --ink-3:#2A2A2A;        /* borders on dark */
  --paper:#F6F3EC;        /* page background */
  --paper-2:#EDE9DF;      /* subtle panels */
  --line:rgba(10,10,10,.10);   /* grid + hairlines on paper */
  --line-dark:rgba(246,243,236,.14);
  --muted:#6B6B66;        /* secondary text on paper */
  --muted-dark:#A3A39B;   /* secondary text on ink */
  --accent:#FF7A1A;       /* ONE accent: full stops, active, key CTA hover */
  --danger:#B42318;       /* only for errors/INVALID */
  --radius-lg:28px; --radius-md:18px; --radius-sm:12px; --radius-pill:999px;
  --ease:cubic-bezier(.22,1,.36,1);
  --dur-fast:150ms; --dur:350ms; --dur-page:500ms;
}
```
**Color rules:** max **two** accent touches per screen (e.g. full stop + active tab). Success = filled ink/paper inversion plus a check icon (no green). Tiers are shown with **1-3 filled rings/dots**, not colors. Error = `--danger` text/outline + icon + clear message.

## 3. Typography
| Role | Font | Notes |
|---|---|---|
| Display | **Syne** 700/800 | Wide, characterful; tight tracking `-0.03em`, line-height `0.92` |
| Body/UI | **Space Grotesk** 400/500 | Modern, friendly, readable on phones |
| Labels/data | **JetBrains Mono** 400/500 | Uppercase, `letter-spacing:.14em`, 11-12px |
| Hindi/Kannada | **Noto Sans Devanagari / Noto Sans Kannada** | Required fallbacks; test every screen in HI and KN |

```css
--font-display:'Syne','Noto Sans Devanagari','Noto Sans Kannada',system-ui,sans-serif;
--font-body:'Space Grotesk','Noto Sans Devanagari','Noto Sans Kannada',system-ui,sans-serif;
--font-mono:'JetBrains Mono',ui-monospace,monospace;
```
Scale: display `clamp(2.75rem,9vw,7.5rem)` · h1 `clamp(2rem,5vw,3.75rem)` · h2 `1.75rem` · body `1rem/1.6` · small `.875rem` · mono label `.72rem`. Kannada/Hindi display text uses slightly larger line-height (`1.15`) to avoid clipping. Headlines end with an accent-colored full stop `.` (not in Hindi/Kannada where the danda/period style differs; keep the accent dot as a separate span).

## 4. Layout
- **Mobile-first.** Worker flow max width 480px, centered; desktop shows the same column inside a big black "device-like" card on the paper grid (looks intentional).
- Hirer/public profile and directory are responsive, up to 1100px.
- 8px spacing grid; page padding 20px mobile, 48px desktop; cards padded 24-32px.
- Paper grid: `background-image: linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px); background-size:48px 48px;` with a soft radial fade so it does not fight content.
- Touch targets >= 48px high. Bottom-anchored primary button on mobile.

## 5. Components
- **Button:** pill, ink fill / paper text; hover: arrow slides, accent underline grows; secondary: 1px outline. Loading = inline progress line, never a spinner alone.
- **Card:** `--ink-2` or `--paper-2`, radius 28, 1px border, subtle inner highlight; hover lifts 4px.
- **Tag/pill:** 1px outline, mono uppercase 11px.
- **Section index:** `01 / SKILL` mono label + hairline above sections.
- **Expanding panels (SkillPick):** flex row of 3 trade cards; active has `flex: 4`, others `flex: 1` with rotated vertical title; Framer `layout` spring (stiffness 260, damping 30). On mobile becomes vertical accordion.
- **ChallengeCode:** large mono 4-char/word code in an outlined box, subtle pulse; overlay on video preview corner.
- **StepList:** numbered hairline rows; verdict icons (check / cross / dashed circle for unclear); evidence frame thumbnails on tap.
- **AgentLog:** mono lines typed in one by one (`> checking step 2: wire stripped...`), max 10 lines visible.
- **TrustBreakdown:** three horizontal bars (Video / Interview / Witnesses) filling with count-up numbers; tier rings on the right.
- **Seal:** circular SVG badge, hairline ring with the tier mark; **stroke-draws itself** on issue. Doodle-style, minimal.
- **Verify banner:** big "SIGNATURE VALID" (ink on paper, accent check) or "INVALID" (danger, shake once).
- **Toasts:** bottom, ink pill, auto-dismiss 4s.
- **Skeletons:** paper-2 shimmer lines.

## 6. Doodles (original, thin line)
SVG strokes 1.25-1.5px, `--ink` at 8-14% opacity, placed in corners/behind headings, slightly rotated: spirit level, pipe elbow with drip, plug/bolt, trowel, plumb bob, measuring tape curl, small dashed arcs and crosshairs. Max 2-3 per screen; never behind body text; hide on very small screens if cluttered. Draw them as inline SVG components in `components/doodles/`.

## 7. Motion spec (smooth, purposeful)
- **Easing** `--ease`; micro 150ms, standard 350ms, page 500ms.
- **Page transition:** `AnimatePresence mode="wait"`; enter: `opacity 0->1, y 16->0, blur 4px->0`; exit: `opacity 1->0, y 0->-8`.
- **Stagger:** children reveal with 60ms stagger on mount.
- **Headline reveal:** words slide up from a mask (overflow hidden), 80ms stagger.
- **Expanding panels:** shared layout spring; background label cross-fades.
- **Numbers:** count-up 800ms on Trust Score and bars.
- **Seal:** SVG `pathLength` 0->1 over 1.2s then a soft scale pop (1.0->1.04->1.0).
- **Agent thinking:** lines type in at ~40ms/char; blinking caret.
- **Button hover:** 4px lift, arrow translate 6px.
- **Tamper demo:** INVALID shakes once (x: -6,6,-3,3,0 in 400ms).
- **Reduced motion:** `prefers-reduced-motion` disables blur, y-motion, stagger, and shake; keep simple opacity fades.
- Performance: animate only `transform`/`opacity`; no big blur on mobile; no heavy 3D or video backgrounds.

## 8. Screens (what each shows)
1. **Landing:** huge display `Skills, witnessed.`, one-line promise, mono stat row (`3 LAYERS OF PROOF / 3 LANGUAGES / 0 PAPER`), CTA "Get verified" + secondary "I'm a hirer". Doodles in corners.
2. **Language:** three big pill cards (English / हिन्दी / ಕನ್ನಡ).
3. **Skill pick:** expanding panels for Electrician / Plumber / Mason, each with skill name + step count + estimated time.
4. **Interview:** chat-like but minimal: one question at a time, big mic button (hold or tap), text fallback, progress dots, replies shown as paper-on-ink bubbles.
5. **Test brief:** checklist + challenge code + safety note + consent checkbox; "Start recording".
6. **Record:** full-screen camera, code overlay, timer ring, step hints that fade in; stop -> preview -> submit.
7. **Review:** AgentLog streaming, then StepList verdicts; "Re-record steps 3" CTA if needed; TrustBreakdown preview.
8. **Witnesses:** invite cards with copy/WhatsApp buttons and live "vouched / waiting" status.
9. **Credential:** Seal draws, tier name in display type, QR, "Share on WhatsApp", download card.
10. **Public profile `/c/:id`:** hirer-optimized: Verify banner first, tier, evidence timeline, witnesses (first names + roles), Report button.
11. **Witness page `/w/:token`:** short clip, 3 tap questions, big Vouch / Needs work buttons.
12. **Directory:** filters (trade, area) + list of verified workers, tier rings.
13. **Dashboard:** attempts, tier progress ladder, coaching tips.

## 9. Copy tone
Short, warm, direct. No jargon. Examples: "Show us your work." / "Step 3 was unclear. Record just that part again." / "2 people have vouched for you." Agent lines in mono, lowercase, factual.

## 10. Accessibility
Contrast >= 4.5:1; visible focus ring (2px ink + 2px paper offset); labels on all inputs; captions for any voice output as text; large tap targets; works without sound; test with browser zoom 200%.

## 11. Do / Don't
**Do:** whitespace, hairlines, big type, one accent, calm motion. **Don't:** gradients, drop-shadow soup, emojis as icons, rainbow badges, more than 3 fonts, stock photos, copying the reference drawings.

## 12. Tailwind hint
Extend theme with the tokens above (`colors.ink/paper/accent`, `fontFamily.display/body/mono`, `borderRadius.xl2: '28px'`, `transitionTimingFunction.sakshi: 'cubic-bezier(.22,1,.36,1)'`). Put the paper-grid in `globals.css` on `body`.
