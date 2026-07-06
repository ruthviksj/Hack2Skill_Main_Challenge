"""WellnessAgent orchestrator.

Wires the ten modules into a single ``handle(signal)`` pipeline:

    normalize -> ingest into state -> detect missing closures -> SAFETY GATE
    -> classify support state -> plan (safety can override) -> generate
    -> critic -> escalate -> update continuity -> persist -> return JSON

The return value is a structured dict containing the user-facing response plus
a full, auditable trace of every module's output.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .classifier import SupportStateClassifier
from .closure import MissingClosureDetector
from .continuity import ContinuityPacketUpdater
from .critic import ResponseCritic
from .escalation import EscalationEngine
from .planner import AgentPlanner
from .response import ResponseGenerator
from .safety import SafetyGate
from .signals import NormalizedSignal, SignalNormalizer
from .state import ExamEvent, ExamPaper, StudentState, StudentStateStore


def _to_dt(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class WellnessAgent:
    def __init__(self, store: Optional[StudentStateStore] = None) -> None:
        self.normalizer = SignalNormalizer()
        self.store = store or StudentStateStore()
        self.closure_detector = MissingClosureDetector()
        self.safety_gate = SafetyGate()
        self.classifier = SupportStateClassifier()
        self.planner = AgentPlanner()
        self.generator = ResponseGenerator()
        self.critic = ResponseCritic()
        self.escalation_engine = EscalationEngine()
        self.continuity_updater = ContinuityPacketUpdater()

    # ------------------------------------------------------------------
    def handle(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        signal = self.normalizer.normalize(raw)
        now = signal.timestamp
        state = self.store.get(signal.student_id)

        self._ingest(state, signal)
        state.last_seen = now

        # Detection BEFORE safety so closures are part of the picture.
        self.closure_detector.detect(state, now)

        # SAFETY GATE runs before conversation logic and can override.
        safety = self.safety_gate.evaluate(state, signal)

        classification = self.classifier.classify(state, signal, safety, now)
        plan = self.planner.plan(state, classification, safety)

        draft = self.generator.generate(state, classification, plan, safety)
        critic_report = self.critic.review(draft, state, classification, plan)
        final_response = critic_report.final_response

        escalation = self.escalation_engine.evaluate(state, classification, safety, now)

        self.continuity_updater.update(
            state, signal, classification, plan, safety, escalation, now
        )
        self.store.save(state)

        return {
            "student_id": state.student_id,
            "signal": signal.to_dict(),
            "support_state": classification.to_dict(),
            "evidence": classification.evidence,
            "safety": safety.to_dict(),
            "next_action": plan.next_action,
            "response_constraints": plan.response_constraints,
            "plan": plan.to_dict(),
            "escalation": escalation.to_dict(),
            "critic": critic_report.to_dict(),
            "continuity_packet": state.continuity_packet.to_dict(),
            "missing_closures": [c.to_dict() for c in state.missing_closures],
            "conversation_rules": list(state.conversation_rules),
            "response": final_response,
        }

    # ------------------------------------------------------------------
    def _ingest(self, state: StudentState, signal: NormalizedSignal) -> None:
        """Apply a normalized signal to the structured student state."""
        p = signal.payload
        ts = signal.timestamp

        # Optional care-circle permission updates can ride on any signal.
        if "care_circle" in p and isinstance(p["care_circle"], dict):
            for member, perms in p["care_circle"].items():
                state.care_circle.members[member] = perms

        if signal.type == "student_chat":
            state.chat_log.append({"timestamp": ts, "text": signal.text or ""})

        elif signal.type == "journal_entry":
            state.journal_entries.append({"timestamp": ts, "text": signal.text or ""})

        elif signal.type == "mood_log":
            mood = p.get("mood")
            state.mood_logs.append({"timestamp": ts, "mood": mood, "text": signal.text or ""})

        elif signal.type == "exam_event":
            self._upsert_paper(state, signal)

        elif signal.type == "score_update":
            self._apply_score(state, signal)

        elif signal.type == "silence_after_event":
            state.events.append({
                "timestamp": ts, "type": "silence_after_event",
                "ref": p.get("ref"), "since": p.get("since"),
            })

        elif signal.type in ("buddy_report", "parent_report", "counsellor_update", "post_escalation_update"):
            state.events.append({
                "timestamp": ts,
                "type": signal.type,
                "source": signal.source.value,
                "reliability": signal.reliability.value,
                "text": signal.text or "",
                "payload": p,
            })
            # Counsellor updates may carry baseline or permission corrections.
            if signal.type in ("counsellor_update", "post_escalation_update"):
                if isinstance(p.get("baseline"), dict):
                    state.baseline.update(p["baseline"])

    def _upsert_paper(self, state: StudentState, signal: NormalizedSignal) -> None:
        p = signal.payload
        exam_id = p.get("exam_id") or "exam_default"
        subject = p.get("subject", "Unknown")
        exam = state.exam_event_graph.get(exam_id)
        if exam is None:
            exam = ExamEvent(exam_id=exam_id, subject=subject)
            state.exam_event_graph[exam_id] = exam

        paper_id = p.get("paper_id") or f"{exam_id}_p1"
        paper = exam.papers.get(paper_id)
        if paper is None:
            paper = ExamPaper(paper_id=paper_id, label=p.get("label", paper_id))
            exam.papers[paper_id] = paper

        if "label" in p:
            paper.label = p["label"]
        if "scheduled_date" in p:
            paper.scheduled_date = _to_dt(p["scheduled_date"])
        if "status" in p:
            paper.status = p["status"]
        if "max_score" in p:
            paper.max_score = p["max_score"]
        if "next_paper_id" in p:
            paper.next_paper_id = p["next_paper_id"]

    def _apply_score(self, state: StudentState, signal: NormalizedSignal) -> None:
        p = signal.payload
        paper_id = p.get("paper_id")
        paper = state.find_paper(paper_id) if paper_id else None
        if paper is None:
            # Create a minimal paper to hold the score.
            self._upsert_paper(state, signal)
            paper = state.find_paper(paper_id) if paper_id else None
        if paper is not None:
            paper.score = p.get("score")
            if p.get("max_score") is not None:
                paper.max_score = p["max_score"]
            paper.status = "scored"
            scored_at = _to_dt(p.get("scored_at")) or signal.timestamp
            # Anchor the scored timestamp so recency checks work.
            paper.scheduled_date = paper.scheduled_date or scored_at
            if p.get("scored_at"):
                paper.scheduled_date = scored_at
