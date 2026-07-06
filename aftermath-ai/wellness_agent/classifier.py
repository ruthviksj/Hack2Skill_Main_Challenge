"""SupportStateClassifier (module 5).

Produces a *support state*, not a diagnosis. Two orthogonal axes:

  phase  -> how much support is needed right now (severity)
  mode   -> the situational overlay that shapes HOW we engage (context)

Phases:
  phase_0_stable
  phase_1_elevated_stress
  phase_2_aftermath_or_functional_disruption
  phase_3_acute_safety

Mode overlays:
  normal, pre_exam, post_exam_checkin, aftermath_missing_closure,
  protect_next_paper, bad_result_containment,
  post_escalation_stabilization, post_escalation_reentry

The classifier returns concrete evidence for every decision so its reasoning is
auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from .safety import RiskLevel, SafetyVerdict
from .signals import NormalizedSignal
from .state import StudentState


class Phase(str, Enum):
    STABLE = "phase_0_stable"
    ELEVATED = "phase_1_elevated_stress"
    AFTERMATH = "phase_2_aftermath_or_functional_disruption"
    ACUTE = "phase_3_acute_safety"


class Mode(str, Enum):
    NORMAL = "normal"
    PRE_EXAM = "pre_exam"
    POST_EXAM_CHECKIN = "post_exam_checkin"
    AFTERMATH_MISSING_CLOSURE = "aftermath_missing_closure"
    PROTECT_NEXT_PAPER = "protect_next_paper"
    BAD_RESULT_CONTAINMENT = "bad_result_containment"
    POST_ESCALATION_STABILIZATION = "post_escalation_stabilization"
    POST_ESCALATION_REENTRY = "post_escalation_reentry"


@dataclass
class Classification:
    phase: Phase
    mode: Mode
    evidence: List[str] = field(default_factory=list)
    signals_considered: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "mode": self.mode.value,
            "evidence": self.evidence,
            "signals_considered": self.signals_considered,
        }


class SupportStateClassifier:
    def __init__(self, pre_exam_window_hours: int = 72, stabilization_hours: int = 48) -> None:
        self.pre_exam_window_hours = pre_exam_window_hours
        self.stabilization_hours = stabilization_hours

    def classify(
        self,
        state: StudentState,
        signal: NormalizedSignal,
        safety: SafetyVerdict,
        now: datetime,
    ) -> Classification:
        evidence: List[str] = []
        considered: List[str] = [signal.type]

        phase = self._classify_phase(state, signal, safety, now, evidence)
        mode = self._classify_mode(state, signal, safety, now, phase, evidence)
        return Classification(phase=phase, mode=mode, evidence=evidence, signals_considered=considered)

    # ----- phase -------------------------------------------------------
    def _classify_phase(self, state, signal, safety, now, evidence) -> Phase:
        if safety.risk_level == RiskLevel.ACUTE and safety.override:
            evidence.append("SafetyGate: acute risk with override -> phase_3_acute_safety.")
            return Phase.ACUTE

        score = 0

        # Recent low mood relative to baseline.
        recent_mood = self._recent_mood(state, now)
        baseline_mood = state.baseline.get("typical_mood", 6)
        if recent_mood is not None and recent_mood <= baseline_mood - 3:
            score += 2
            evidence.append(f"Mood {recent_mood} is well below baseline {baseline_mood}.")
        elif recent_mood is not None and recent_mood <= baseline_mood - 1:
            score += 1
            evidence.append(f"Mood {recent_mood} is somewhat below baseline {baseline_mood}.")

        # Elevated risk language without override.
        if safety.risk_level == RiskLevel.ELEVATED:
            score += 2
            evidence.append("SafetyGate flagged elevated distress signals.")

        # Open missing closures (aftermath of an unresolved event).
        open_closures = state.open_closures()
        if open_closures:
            score += 2
            evidence.append(
                f"{len(open_closures)} open missing closure(s): "
                + ", ".join(c.kind for c in open_closures) + "."
            )

        # Functional disruption hints in journal/chat.
        if self._has_functional_disruption(state, now):
            score += 2
            evidence.append("Signals of functional disruption (sleep/eat/withdrawal/attendance).")

        # A bad result just landed.
        if self._recent_bad_result(state, now):
            score += 1
            evidence.append("A poor result landed recently.")

        if score >= 4:
            return Phase.AFTERMATH
        if score >= 2:
            return Phase.ELEVATED
        evidence.append("No strong stress indicators; treating as stable.")
        return Phase.STABLE

    # ----- mode --------------------------------------------------------
    def _classify_mode(self, state, signal, safety, now, phase, evidence) -> Mode:
        cp = state.continuity_packet

        # Post-escalation overlays take priority once an escalation has happened.
        if cp.last_escalation:
            esc_at = cp.last_escalation.get("at")
            esc_dt = _parse(esc_at)
            if signal.type == "post_escalation_update":
                stage = signal.payload.get("stage", "stabilization")
                if stage == "reentry":
                    evidence.append("Counsellor update marks post-escalation re-entry.")
                    return Mode.POST_ESCALATION_REENTRY
                evidence.append("Counsellor update keeps student in post-escalation stabilization.")
                return Mode.POST_ESCALATION_STABILIZATION
            if esc_dt and (now - esc_dt) <= timedelta(hours=self.stabilization_hours):
                evidence.append("Within stabilization window after a recent escalation.")
                return Mode.POST_ESCALATION_STABILIZATION
            if esc_dt:
                evidence.append("Past stabilization window -> re-entry mode after escalation.")
                return Mode.POST_ESCALATION_REENTRY

        # A bad result just arrived -> containment.
        if self._recent_bad_result(state, now):
            if self._has_upcoming_linked_paper(state, now):
                evidence.append("Bad result with an upcoming linked paper -> protect_next_paper.")
                return Mode.PROTECT_NEXT_PAPER
            evidence.append("A poor result landed -> bad_result_containment.")
            return Mode.BAD_RESULT_CONTAINMENT

        # Open missing closure after an exam/score -> aftermath overlay.
        if state.open_closures():
            evidence.append("Open missing closure -> aftermath_missing_closure overlay.")
            return Mode.AFTERMATH_MISSING_CLOSURE

        # An upcoming linked paper while stressed -> protect it.
        if phase in (Phase.ELEVATED, Phase.AFTERMATH) and self._has_upcoming_linked_paper(state, now):
            evidence.append("Stressed with an imminent linked paper -> protect_next_paper.")
            return Mode.PROTECT_NEXT_PAPER

        # Exam just finished -> post-exam check-in.
        if self._exam_recently_written(state, now):
            evidence.append("A paper was recently written -> post_exam_checkin.")
            return Mode.POST_EXAM_CHECKIN

        # Exam coming up soon -> pre-exam.
        if self._exam_upcoming(state, now):
            evidence.append("A paper is within the pre-exam window -> pre_exam.")
            return Mode.PRE_EXAM

        evidence.append("No special context -> normal mode.")
        return Mode.NORMAL

    # ----- feature helpers --------------------------------------------
    @staticmethod
    def _recent_mood(state: StudentState, now: datetime) -> Optional[int]:
        recent = [m for m in state.mood_logs
                  if isinstance(m.get("timestamp"), datetime)
                  and (now - m["timestamp"]) <= timedelta(days=3)]
        if not recent:
            return None
        recent.sort(key=lambda m: m["timestamp"])
        return recent[-1].get("mood")

    def _has_functional_disruption(self, state: StudentState, now: datetime) -> bool:
        keys = ("can't sleep", "cant sleep", "not eating", "haven't eaten", "skipped class",
                "missed class", "didn't go", "can't focus", "cant focus", "isolating",
                "not talking to anyone", "stopped going")
        for entry in state.journal_entries + state.chat_log:
            ts = entry.get("timestamp")
            text = (entry.get("text") or "").lower()
            if isinstance(ts, datetime) and (now - ts) <= timedelta(days=5):
                if any(k in text for k in keys):
                    return True
        return False

    @staticmethod
    def _recent_bad_result(state: StudentState, now: datetime) -> bool:
        for p in state.all_papers():
            if (p.status == "scored" and p.score is not None and p.max_score
                    and p.scheduled_date and (now - p.scheduled_date) <= timedelta(days=4)):
                if p.score / p.max_score <= 0.45:
                    return True
        return False

    @staticmethod
    def _has_upcoming_linked_paper(state: StudentState, now: datetime) -> bool:
        # A "next paper" exists, is still scheduled, and is in the near future.
        for p in state.all_papers():
            if p.next_paper_id:
                nxt = state.find_paper(p.next_paper_id)
                if nxt and nxt.status == "scheduled" and nxt.scheduled_date:
                    if timedelta(0) <= (nxt.scheduled_date - now) <= timedelta(days=7):
                        return True
        return False

    def _exam_recently_written(self, state: StudentState, now: datetime) -> bool:
        for p in state.all_papers():
            if p.status in ("written", "scored") and p.scheduled_date:
                if timedelta(0) <= (now - p.scheduled_date) <= timedelta(days=2):
                    return True
        return False

    def _exam_upcoming(self, state: StudentState, now: datetime) -> bool:
        window = timedelta(hours=self.pre_exam_window_hours)
        for p in state.all_papers():
            if p.status == "scheduled" and p.scheduled_date:
                if timedelta(0) <= (p.scheduled_date - now) <= window:
                    return True
        return False


def _parse(value) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
