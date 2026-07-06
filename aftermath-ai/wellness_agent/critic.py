"""ResponseCritic (module 8).

The critic is the second line of defence. It reviews a candidate response
against:

  - the plan's ``response_constraints``
  - the continuity packet's ``do_not_say`` list (durable, cross-session)
  - hard non-diagnosis guardrails

If a violation is found it tries to repair the response; if it can't safely
repair it, it replaces the response with a safe fallback for the current mode.
This is what lets post-escalation continuity *prevent* a harmful response even
if upstream generation slipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .classifier import Classification, Mode
from .planner import Plan
from .state import StudentState


# Diagnosis / probability language that must never appear.
_DIAGNOSIS_TERMS = [
    r"\byou (have|are) (depress|anxiet|anxious|bipolar|suicidal)",
    r"\bdiagnos",
    r"\b\d{1,3}\s?% (risk|chance|likely|probability)",
    r"\brisk (score|probability)\b",
    r"\byou'?re clinically\b",
]

# Toxic positivity / minimizing phrases.
_MINIMIZING_TERMS = [
    r"\bjust (relax|cheer up|get over it|move on)\b",
    r"\bit'?s not (a big deal|that bad)\b",
    r"\beverything happens for a reason\b",
    r"\bothers have it worse\b",
    r"\bstop (worrying|overthinking)\b",
]


@dataclass
class CriticReport:
    approved: bool
    final_response: str
    violations: List[str] = field(default_factory=list)
    repairs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "violations": self.violations,
            "repairs": self.repairs,
        }


class ResponseCritic:
    def review(
        self,
        draft: str,
        state: StudentState,
        classification: Classification,
        plan: Plan,
    ) -> CriticReport:
        violations: List[str] = []
        repairs: List[str] = []
        text = draft
        lowered = text.lower()

        # 1) Hard guardrails: diagnosis / probability language.
        for pat in _DIAGNOSIS_TERMS:
            if re.search(pat, lowered):
                violations.append(f"diagnosis_or_probability_language:{pat}")

        # 2) Minimizing / toxic positivity when constraints forbid it.
        forbids_minimize = any(
            c in plan.response_constraints
            for c in ("no_toxic_positivity", "do_not_minimize_the_result", "must_not_minimize")
        )
        if forbids_minimize:
            for pat in _MINIMIZING_TERMS:
                if re.search(pat, lowered):
                    violations.append(f"minimizing_language:{pat}")

        # 3) Continuity do_not_say list (durable, e.g. post-escalation).
        for forbidden in state.continuity_packet.do_not_say:
            if forbidden and forbidden.lower() in lowered:
                violations.append(f"continuity_do_not_say:{forbidden!r}")

        # 4) Mode-specific content constraints.
        if "do_not_demand_the_score" in plan.response_constraints:
            if re.search(r"\b(what did you (get|score)|tell me your (score|result|marks?)|how many marks)\b", lowered):
                violations.append("demanded_score")
        if "do_not_dwell_on_the_bad_paper_now" in plan.response_constraints:
            if re.search(r"\b(why did you (fail|do so badly|mess up)|what went wrong (on|with) (paper|the exam))\b", lowered):
                violations.append("dwelling_on_bad_paper")
        if "must_acknowledge_what_happened_since_we_last_spoke" in plan.response_constraints:
            if classification.mode == Mode.AFTERMATH_MISSING_CLOSURE and not re.search(
                r"\b(since|after|went quiet|quiet|last (spoke|talked|time)|the exam|been a while)\b", lowered
            ):
                violations.append("did_not_acknowledge_gap")
        if "must_offer_human_support_and_helpline" in plan.response_constraints:
            if not re.search(r"\b(counsellor|counselor|crisis|helpline|emergency|someone you trust|in person)\b", lowered):
                violations.append("missing_human_support_offer")

        if not violations:
            return CriticReport(approved=True, final_response=text, violations=[], repairs=[])

        # --- Attempt repair ------------------------------------------
        repaired, fixed = self._repair(text, violations, state, classification, plan)
        repairs.extend(fixed)
        # Re-scan after repair to confirm safety; if still unsafe, fall back.
        residual = self._rescan(repaired, state, plan)
        if residual:
            repaired = self._safe_fallback(classification, plan)
            repairs.append("replaced_with_safe_fallback")

        return CriticReport(
            approved=False,
            final_response=repaired,
            violations=violations,
            repairs=repairs,
        )

    # ------------------------------------------------------------------
    def _repair(self, text, violations, state, classification, plan) -> Tuple[str, List[str]]:
        fixed: List[str] = []
        out = text
        # Any continuity / diagnosis / dwelling / demand violation is unsafe to
        # patch in place -> signal a fallback by blanking those sentences.
        unsafe_kinds = ("continuity_do_not_say", "diagnosis", "demanded_score",
                        "dwelling_on_bad_paper", "minimizing_language")
        if any(v.split(":")[0].startswith(k.split("_")[0]) or k in v for v in violations for k in unsafe_kinds):
            # Drop offending sentences containing forbidden phrases.
            for forbidden in state.continuity_packet.do_not_say:
                if forbidden:
                    out = self._drop_sentences_containing(out, forbidden)
                    fixed.append(f"removed_sentence_with:{forbidden!r}")
        return out, fixed

    def _rescan(self, text: str, state: StudentState, plan: Plan) -> List[str]:
        residual: List[str] = []
        low = text.lower()
        for forbidden in state.continuity_packet.do_not_say:
            if forbidden and forbidden.lower() in low:
                residual.append("continuity")
        for pat in _DIAGNOSIS_TERMS:
            if re.search(pat, low):
                residual.append("diagnosis")
        if "do_not_demand_the_score" in plan.response_constraints and re.search(
            r"\b(what did you (get|score)|tell me your (score|result|marks?))\b", low):
            residual.append("score")
        return residual

    @staticmethod
    def _drop_sentences_containing(text: str, phrase: str) -> str:
        parts = re.split(r"(?<=[.!?])\s+", text)
        kept = [p for p in parts if phrase.lower() not in p.lower()]
        return " ".join(kept).strip()

    @staticmethod
    def _safe_fallback(classification: Classification, plan: Plan) -> str:
        if plan.safety_override:
            return (
                "I'm really glad you reached out, and I want to stay with you. "
                "Are you safe right now? I'd like to help you connect with a counsellor "
                "or someone you trust — you don't have to do this alone."
            )
        if classification.mode in (Mode.POST_ESCALATION_STABILIZATION, Mode.POST_ESCALATION_REENTRY):
            return (
                "I'm here with you, and there's nothing you need to prove right now. "
                "We can keep things gentle and go entirely at your pace. "
                "How are you feeling in this moment?"
            )
        return (
            "I'm here with you. We can take this at whatever pace feels right — "
            "no pressure at all. What would feel most helpful right now?"
        )
