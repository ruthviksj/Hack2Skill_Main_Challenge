# Aftermath AI — 3-Minute Demo Script

**One line:** An exam-aware wellness companion that responds to what students *avoid, miss, or stop saying* after high-stakes exams — not just what they type.

**To run:** open `aftermath-ai-demo.html` in any browser. Click **"View judge demo flow"** for a guided walkthrough, or **"Start student demo"** to drive it yourself. Hit **↺ Reset demo** anytime.

---

## The 30-second hook (say this first)

> "Most wellness apps wait for the student to journal or ask for help. But after a bad exam, students do the *opposite* — they go quiet. Aarav expected 600+ on the GMAT. The exam happened a week ago. He never told anyone the result. **That silence is the signal.** Watch what our companion does with it."

## The walkthrough (2 minutes)

| # | Do this | Say this / what to point at |
|---|---------|------------------------------|
| 1 | **Today** tab | "GMAT was 7 days ago, expected 600+, no result. The system flags **missing closure** on its own — no one had to report distress." |
| 2 | Tap **"It went badly"** | "It enters **Aftermath Mode** and — notice the banner — *'I won't ask for the score first.'* It validates the shock, checks safety gently, no productivity pressure." |
| 3 | Tap **"It's heavy"** | "Still no score-chasing. It offers **one tiny step** and asks if he wants someone from his circle." |
| 4 | **Care** tab → **Submit concern as Rohan** → Submit | "The student went quiet, so a trusted buddy raises a structured concern: *'Paper 2 is useless now.'* Note: Rohan never sees the private chat — only the signal he's allowed to send." |
| 5 | See the confirmation | "**Safety Gate** fires → escalation created → simulated human handoff. Academic advice is now blocked." |
| 6 | **Judge** tab | "Escalation timeline, the **continuity packet** — *future chats avoid score-first and productivity pressure* — and the full **agent decision trace**: phase, evidence, selected action, and the constraints the response had to obey." |

## The close (15 seconds)

> "The intelligence lives in the **gap between what the system expected to hear and what it actually heard.** Escalation isn't the end — the continuity packet means the *next* conversation already knows what helped and what to never say again."

---

## Why each piece scores

- **Innovation** — missing-closure-as-signal + post-escalation continuity. Not another mood tracker.
- **Technical depth** — Safety Gate overrides everything; support-state classifier; explainable agent runs in the Judge panel.
- **UX** — calm, premium, student-owned. Tap options for no-energy moments. Never asks for the score first.
- **Safety by design** — escalation is clearly labelled **simulated**; no diagnosis; parent *"he's lazy"* report is treated as context, **not** escalated.
- **Scalability** — one `AgentAdapter` interface: `MockAgentAdapter` swaps for the real Claude-built agent with zero app changes (see `nextjs/`).

## Edge cases worth showing if asked

- Type **"I want to hurt myself"** in chat → instant **Safety Mode**, escalation, academic flow blocked.
- **Care** tab → the parent (Priya) can't submit concerns; submit-concern button only appears for authorized members. **Revoke** removes access live.
- **Exams** tab → **+ Add** an exam, or **Simulate exam date passed** to re-trigger missing-closure detection.

## What we intentionally did *not* build

Real auth, real emergency SMS/WhatsApp, clinical diagnosis, predictive risk scoring, institution dashboards. All labelled as future scope — the MVP proves the core insight, safely.
