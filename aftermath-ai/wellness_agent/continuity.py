"""ContinuityPacketUpdater (module 10).

Maintains the durable, cross-session memory that lets the agent stay coherent
across time — especially through and after an escalation. It records:

  - a rolling summary of where things stand
  - open threads (the missing closures the agent should revisit)
  - sensitivities to be careful about
  - a ``do_not_say`` list (phrases that would re-traumatize / undo progress)
  - the last escalation event and any counsellor re-entry notes

After an escalation, the updater seeds ``do_not_say`` so that even a future,
context-light turn cannot produce a harmful response (the ResponseCritic
enforces this list).
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from .classifier import Classification, Mode, Phase
from .planner import Plan
from .safety import RiskLevel, SafetyVerdict
from .signals import NormalizedSignal
from .state import StudentState
from .escalation import EscalationDecision


class ContinuityPacketUpdater:
    def update(
        self,
        state: StudentState,
        signal: NormalizedSignal,
        classification: Classification,
        plan: Plan,
        safety: SafetyVerdict,
        escalation: EscalationDecision,
        now: datetime,
    ) -> None:
        cp = state.continuity_packet

        # Open threads mirror current open closures.
        cp.open_threads = [f"{c.kind}:{c.ref}" for c in state.open_closures()]

        # Record an escalation and seed protective do_not_say entries.
        if escalation.level == "urgent":
            cp.last_escalation = {
                "at": now.isoformat(),
                "trigger": safety.triggers,
                "level": escalation.level,
            }
            self._add_sensitivity(cp, "recent_acute_safety_episode")
            for phrase in (
                "what did you get",
                "why did you fail",
                "you should have",
                "snap out of it",
                "just move on",
            ):
                if phrase not in cp.do_not_say:
                    cp.do_not_say.append(phrase)
            # Standing conversation rule reflecting the episode.
            state.add_rule("post_escalation_care")

        # Counsellor re-entry guidance flows into reentry_notes.
        if signal.type == "post_escalation_update":
            note = signal.payload.get("reentry_note") or signal.payload.get("note")
            if note and note not in cp.reentry_notes:
                cp.reentry_notes.append(note)
            if signal.payload.get("stage") == "reentry":
                self._add_sensitivity(cp, "re_entry_in_progress")

        # Sensitivities derived from mode.
        if classification.mode == Mode.PROTECT_NEXT_PAPER:
            self._add_sensitivity(cp, "imminent_next_paper")
        if classification.mode == Mode.BAD_RESULT_CONTAINMENT:
            self._add_sensitivity(cp, "recent_disappointing_result")

        # Rolling human-readable summary.
        cp.summary = (
            f"Phase={classification.phase.value}; mode={classification.mode.value}; "
            f"open_threads={len(cp.open_threads)}; "
            f"last_signal={signal.type}; "
            f"escalation={escalation.level}."
        )
        cp.updated_at = now

        # Persist the active phase/mode into support_state history.
        state.support_state.record(classification.phase.value, classification.mode.value, now)

    @staticmethod
    def _add_sensitivity(cp, item: str) -> None:
        if item not in cp.sensitivities:
            cp.sensitivities.append(item)
