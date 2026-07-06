# Aftermath AI — Platform Features & Brand Guidelines

A calm, premium, student-owned wellness platform built around one insight: *the most important signal is often what a student avoids, misses, or stops saying after a high-stakes exam.* The dashboard makes everyday study life feel light and motivating, while the companion quietly watches for the gaps.

---

## Part 1 — Feature Priorities

Prioritised with MoSCoW. **Must-have** = the platform isn't credible without it. **Should-have** = strong value, build right after. **Could-have** = differentiators for later. **Won't-build** = deliberate guardrails.

### Must-have (core platform)

| Area | Feature | Notes |
|------|---------|-------|
| Onboarding | Profile setup: name, exam track, preferred tone & language, consent, first exam, optional buddy | Sets the companion's context. Consent is explicit and explained. |
| Dashboard ("Today") | Modular card home: greeting + current support state, today's focus, next exam, missing-closure cue, mood check-in, streaks, suggested next step | The hub. Calm, scannable, one clear action. |
| Exams | Add exam (name, type, date, importance, **expected score**, **confidence**, next dependent event); exam list + timeline; update outcome; statuses (upcoming / passed / outcome-missing / reported) | Expected-vs-actual is the heart of the product. |
| Tasks / to-do | Add task with due date, priority, optional link to an exam; mark complete; "Today's focus" subset | Lightweight, never overwhelming. |
| Calendar | Month / week view with exams, result days, and tasks | Visual sense of what's coming. |
| Mood tracker | 10-second tap check-in (mood + energy); history strip | No forced journaling. |
| Streaks & progress | Study streak + check-in streak; **"kind streak"** rules (freezes, no shaming on a break) | Motivating without adding pressure — see §wellbeing. |
| Learning progress | Per-subject / topic readiness (rings or bars); % toward target score | Turns prep into visible momentum. |
| Companion cues | Context buttons across the dashboard ("Check in", "I'm okay / It went badly", "Talk it through") that open the chat **with context** | Low-effort entry into support. |
| Companion chat | Conversational AI with mode indicator (Normal / Aftermath / Protect Next Paper / Safety) | Already prototyped. |
| Care circle & safety | Add trusted people + permissions, buddy concern form, Safety Gate, escalation, continuity packet | Student-owned, privacy by default. |
| Foundations | Responsive layout, accessibility (AA, tap-first), empty / loading / error states | Premium feel lives in the details. |

### Should-have

| Area | Feature |
|------|---------|
| Insights | Mood trend charts + correlation with exam events ("your toughest days follow mocks") |
| Pattern summary | Cautious, hypothesis-framed reflections the student can confirm or correct |
| Focus | Pomodoro / focus timer linked to a task |
| Protect Next Paper | Dashboard surfaces a recovery path when a dependent exam is near |
| Reminders | Gentle, opt-in nudges (never guilt-based) |
| Personalisation | Rearrangeable dashboard widgets; light/dark theme |
| Journal | Private journal with a privacy lock |
| Milestones | Low-key achievements (first check-in, recovered after a bad mock) |
| Resources | Grounding exercises + helplines library |
| Weekly recap | A warm "your week" summary |
| Judge / debug | Agent reasoning panel (toggle) |

### Could-have

Hinglish / multi-language · voice notes · Google Calendar & exam-platform integrations · buddy accountability / shared sessions · consented counsellor context view · export continuity summary · longitudinal analytics · PWA + home-screen widgets · spaced-repetition study planner.

### Won't-build (guardrails)

Clinical diagnosis · predictive suicide / risk scoring · real emergency dispatch at MVP (escalation is **simulated and labelled**) · parent surveillance or raw journal access · dark-pattern streak pressure or shame mechanics.

### Design principles

1. **The gap is the product** — always make expected-vs-observed visible.
2. **One clear next action** per screen; never a wall of widgets.
3. **Tap before type** — every prompt has low-effort options.
4. **Never score-first after a hard moment.**
5. **Student-owned** — they control who sees what, always revocable.
6. **Calm, not clinical** — supportive language, no diagnosis.

### Wellbeing-aware gamification

Streaks and progress motivate, but for already-stressed students they can backfire. So: streak **freezes** and grace days, no red "you broke it" states, no leaderboards or peer comparison, and progress framed as *readiness* not *ranking*. Celebrate recovery and self-care actions, not just study volume.

---

## Part 2 — Brand Guidelines

### Personality

Calm · premium · trustworthy · warm · student-owned · non-clinical. It should feel like a thoughtful friend who remembers what matters — never like a hospital, a parent dashboard, or a productivity drill sergeant. Visual cousins: Linear's precision, Notion's friendliness, Headspace's calm, Stripe's polish.

### Color palette

Soft, low-saturation, lots of breathing room. Color carries meaning — calm states are cool, attention is warm amber, safety is a gentle rose (deliberately **not** alarm-red).

**Core**

| Token | Hex | Use |
|-------|-----|-----|
| Companion Indigo (primary) | `#5B7CFA` | Primary actions, links, focus, brand |
| Indigo Tint | `#EEF1FE` | Soft fills, selected states, info cards |
| Indigo Deep | `#3A55D6` | Text on tint, pressed states |
| Calm Teal (positive) | `#2FB6A3` | Streaks, completion, "all calm", safe states |
| Teal Tint | `#E7F6F4` | Success fills |
| Study Lavender (secondary) | `#8B7DE8` | Learning progress, focus, counsellor accents |
| Lavender Tint | `#F0EDFC` | Progress backgrounds |

**Signal / semantic**

| Token | Hex | Use |
|-------|-----|-----|
| Signal Amber (attention) | `#E5A857` | Missing-closure cues, gentle attention — calm, not urgent |
| Amber Tint | `#FBF2E3` | Attention card backgrounds |
| Gentle Rose (safety) | `#E0688A` | Safety mode, escalation — soft on purpose, never panic-red |
| Rose Tint | `#FDECF1` | Safety card backgrounds |

**Neutrals**

| Token | Hex | Use |
|-------|-----|-----|
| Ink | `#1A1D26` | Primary text, headings |
| Slate | `#5B6472` | Secondary text |
| Mist | `#8A93A3` | Hints, captions, disabled |
| Line | `#E8EAF0` | Borders, dividers |
| Cloud | `#F5F7FA` | App background |
| White | `#FFFFFF` | Surfaces, cards |

**Brand gradient** (logo / hero only, used sparingly): Companion Indigo → Calm Teal, `135deg`.

Rule of thumb: backgrounds neutral, one accent per view, semantic colors only when they mean something. Always pair color with a label or icon — never rely on color alone (accessibility).

### Typography

| Role | Font | Weights | Notes |
|------|------|---------|-------|
| Display / headings | **Plus Jakarta Sans** | 600 / 700 | Friendly-geometric, premium. Tight tracking on large sizes. |
| Body / UI | **Inter** | 400 / 500 / 600 | Workhorse, highly legible. |
| Mono | **JetBrains Mono** | 400 / 500 | Agent reasoning / debug panel only. |

All free on Google Fonts. Scale (px): 34 / 26 / 20 / 17 display & headings; 15 body; 13 caption; 12 micro. Line-height 1.5 body, 1.2 headings. Sentence case everywhere — never ALL CAPS in UI. Minimum body size 14px.

### Shape, depth & motion

- **Radius:** cards 18–20px, inputs/buttons 12–14px, pills full. Generous and soft.
- **Shadows:** subtle and low — `0 8px 24px rgba(20,24,40,.06)`. No heavy or neon glows.
- **Borders:** 1px `Line`; soft dashed borders for "schematic" / placeholder zones.
- **Spacing:** 8-pt grid. Lots of whitespace; never cramped.
- **Motion:** lightweight and calming — 150–250ms ease, gentle fade/slide. Typing dots and soft transitions, no bouncy or attention-grabbing animation.
- **Touch targets:** ≥44px.

### Iconography & imagery

Outline icons, 1.8px stroke, rounded caps (Tabler / Lucide style). Soft, abstract, human illustration — calming shapes and gradients, never clinical stock photography or distress imagery. Mood uses warm, simple faces, not clinical scales.

### Voice & tone

Warm, plain, human. Short sentences. Validate before suggesting. Offer, don't instruct.

- ✅ "That really sucks, and I'm sorry. No pressure — how are you holding up?"
- ✅ "Your GMAT was a week ago and we never closed the loop. Want to check in gently?"
- ✅ "Your private journal stays private. Buddies can only send signals you allow."
- ❌ "You failed to log your result." · ❌ "Why didn't you study?" · ❌ "You broke your streak!" · ❌ clinical terms like "depressive episode detected."

Never: shame, score-first after a hard moment, "again" / "you promised", diagnosis, or surveillance framing.

### Accessibility

WCAG AA contrast minimum; verify amber and rose text pairs against tints. Full keyboard navigation, visible focus rings (Indigo). Tap-first interaction for low-energy moments. Respect reduced-motion. Plain language, no jargon.
