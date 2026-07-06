"""ResponseGenerator (module 7).

Deterministic, template-based generator that turns a plan into a warm,
non-diagnostic, user-facing message. Templates are chosen primarily by the
plan's ``next_action`` and the classification mode, and they are written to
respect the plan's constraints by construction. The ResponseCritic (module 8)
provides the second line of defence.

There is no LLM call here: keeping generation deterministic makes the whole
agent testable and auditable. A production system could swap this for a
constrained LLM call that receives the same plan + constraints.
"""

from __future__ import annotations

from typing import List

from .classifier import Classification, Mode, Phase
from .planner import Plan
from .safety import SafetyVerdict
from .state import StudentState


class ResponseGenerator:
    def generate(
        self,
        state: StudentState,
        classification: Classification,
        plan: Plan,
        safety: SafetyVerdict,
    ) -> str:
        if plan.safety_override:
            return self._safety_response()

        mode = classification.mode
        if mode == Mode.PROTECT_NEXT_PAPER:
            return self._protect_next_paper(state)
        if mode == Mode.BAD_RESULT_CONTAINMENT:
            return self._bad_result(state)
        if mode == Mode.AFTERMATH_MISSING_CLOSURE:
            return self._aftermath(state)
        if mode == Mode.POST_EXAM_CHECKIN:
            return self._post_exam_checkin()
        if mode == Mode.PRE_EXAM:
            return self._pre_exam()
        if mode == Mode.POST_ESCALATION_STABILIZATION:
            return self._post_escalation_stabilization()
        if mode == Mode.POST_ESCALATION_REENTRY:
            return self._post_escalation_reentry(state)

        # Normal mode, scaled by phase.
        if classification.phase == Phase.ELEVATED:
            return ("I'm hearing that things feel heavier than usual right now. "
                    "I'm here and we can take it at whatever pace works for you. "
                    "What's weighing on you most today?")
        if classification.phase == Phase.AFTERMATH:
            return ("It sounds like a lot has landed on you lately. You don't have to "
                    "carry it on your own — I'm here with you. Would it help to talk "
                    "through what's been hardest, or would you rather just sit with it for a moment?")
        return ("Hey — good to hear from you. How are things going today?")

    # ------------------------------------------------------------------
    def _safety_response(self) -> str:
        return (
            "I'm really glad you told me, and I want to stay right here with you. "
            "What you're feeling sounds incredibly heavy, and you don't have to face "
            "it alone. Are you safe right now? "
            "I'd really like to help you connect with someone who can support you in "
            "person — a counsellor, or someone you trust. If you're in immediate danger, "
            "please reach out to a local emergency number or a crisis line right now. "
            "I'm not going anywhere — we can take the next small step together."
        )

    def _protect_next_paper(self, state: StudentState) -> str:
        nxt = self._next_paper_label(state)
        tail = f" before {nxt}" if nxt else ""
        return (
            "There's still a paper ahead of you, and the most useful thing we can do "
            f"right now is take care of you{tail}. We don't have to unpack everything "
            "today. What would help most for the next few hours — a bit of rest, a short "
            "plan for tonight, or just a moment to breathe?"
        )

    def _bad_result(self, state: StudentState) -> str:
        return (
            "That result is genuinely disappointing, and it's okay to feel that. "
            "One paper doesn't define how capable you are or who you are. "
            "We don't have to fix anything this second — I'm here. "
            "Do you want to talk about how it landed for you?"
        )

    def _aftermath(self, state: StudentState) -> str:
        return (
            "Hey — it's good to hear from you. I know things went quiet after the exam, "
            "and I didn't want to let that just pass by. No pressure at all about what "
            "happened or how it went. How have you been holding up since then?"
        )

    def _post_exam_checkin(self) -> str:
        return (
            "Hope you're doing okay after that paper. However it went, getting through "
            "it is the part that matters today. No need to share results unless you want "
            "to — how are you feeling now that it's behind you?"
        )

    def _pre_exam(self) -> str:
        return (
            "You've got a paper coming up soon. You've put the work in, and right now "
            "rest counts as much as revision. Is there anything small I can help you "
            "sort out so the next day or two feels a bit calmer?"
        )

    def _post_escalation_stabilization(self) -> str:
        return (
            "I'm really glad you're here. There's nothing you need to do or prove right "
            "now — I just wanted to check in gently. How are you feeling in this moment? "
            "We can keep things light and go at your pace."
        )

    def _post_escalation_reentry(self, state: StudentState) -> str:
        notes = state.continuity_packet.reentry_notes
        extra = f" {notes[0]}" if notes else ""
        return (
            "Good to be back in touch with you. We can ease into things slowly — no rush "
            f"to pick up everything at once.{extra} What feels manageable for you today?"
        )

    @staticmethod
    def _next_paper_label(state: StudentState) -> str:
        for p in state.all_papers():
            if p.next_paper_id:
                nxt = state.find_paper(p.next_paper_id)
                if nxt and nxt.status == "scheduled":
                    return nxt.label
        return ""
