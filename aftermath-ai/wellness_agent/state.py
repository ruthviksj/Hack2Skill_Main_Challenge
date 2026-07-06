"""Structured student state and in-memory store (module 2).

The :class:`StudentState` is the single source of truth the agent reasons over.
It deliberately separates:

  - ``baseline``            : the student's normal patterns (so we can detect drift)
  - ``exam_event_graph``    : exams + their papers + links between papers
  - ``missing_closures``    : events that opened a loop the agent never closed
  - ``support_state``       : current phase + mode overlay + history
  - ``care_circle``         : who may be contacted and what may be shared
  - ``conversation_rules``  : active constraints on what the agent may say
  - ``continuity_packet``   : durable memory that survives across sessions

:class:`StudentStateStore` is an in-memory store for now (no persistence layer),
but exposes a small interface that a database-backed store could implement later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ExamPaper:
    paper_id: str
    label: str
    scheduled_date: Optional[datetime] = None
    status: str = "scheduled"  # scheduled | written | scored | skipped
    score: Optional[float] = None
    max_score: Optional[float] = None
    next_paper_id: Optional[str] = None  # paper that this one feeds into

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "label": self.label,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "status": self.status,
            "score": self.score,
            "max_score": self.max_score,
            "next_paper_id": self.next_paper_id,
        }


@dataclass
class ExamEvent:
    exam_id: str
    subject: str
    papers: Dict[str, ExamPaper] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exam_id": self.exam_id,
            "subject": self.subject,
            "papers": {pid: p.to_dict() for pid, p in self.papers.items()},
        }


@dataclass
class MissingClosure:
    """A loop the agent opened/observed but never resolved with the student."""

    kind: str            # e.g. "unacknowledged_score", "silence_after_exam"
    ref: str             # what it refers to (paper_id, exam_id, event id)
    opened_at: datetime
    detail: str = ""
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "ref": self.ref,
            "opened_at": self.opened_at.isoformat(),
            "detail": self.detail,
            "resolved": self.resolved,
        }


@dataclass
class CareCircle:
    """Permissions for the people around the student.

    Each member maps to the set of actions permitted and the share scope.
    Absence of a member means no permission to contact them.
    """

    members: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @staticmethod
    def default() -> "CareCircle":
        return CareCircle(members={
            "buddy": {"may_contact": True, "share_scope": "wellbeing_flags"},
            "counsellor": {"may_contact": True, "share_scope": "full"},
            "parent": {"may_contact": False, "share_scope": "none"},
        })

    def may_contact(self, member: str) -> bool:
        return bool(self.members.get(member, {}).get("may_contact"))

    def to_dict(self) -> Dict[str, Any]:
        return {"members": self.members}


@dataclass
class SupportState:
    phase: str = "phase_0_stable"
    mode: str = "normal"
    since: datetime = field(default_factory=_now)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, phase: str, mode: str, ts: datetime) -> None:
        if phase != self.phase or mode != self.mode:
            self.history.append({
                "phase": self.phase, "mode": self.mode,
                "ended_at": ts.isoformat(),
            })
            self.phase, self.mode, self.since = phase, mode, ts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "mode": self.mode,
            "since": self.since.isoformat(),
            "history": self.history,
        }


@dataclass
class ContinuityPacket:
    """Durable cross-session memory. Survives even after escalation."""

    summary: str = ""
    open_threads: List[str] = field(default_factory=list)
    sensitivities: List[str] = field(default_factory=list)
    do_not_say: List[str] = field(default_factory=list)
    last_escalation: Optional[Dict[str, Any]] = None
    reentry_notes: List[str] = field(default_factory=list)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "open_threads": self.open_threads,
            "sensitivities": self.sensitivities,
            "do_not_say": self.do_not_say,
            "last_escalation": self.last_escalation,
            "reentry_notes": self.reentry_notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class StudentState:
    student_id: str
    baseline: Dict[str, Any] = field(default_factory=lambda: {
        "typical_mood": 6,            # self-rated 1-10
        "typical_reply_latency_hours": 6,
        "communication_style": "responsive",
        "known_stressors": [],
    })
    exam_event_graph: Dict[str, ExamEvent] = field(default_factory=dict)
    missing_closures: List[MissingClosure] = field(default_factory=list)
    support_state: SupportState = field(default_factory=SupportState)
    care_circle: CareCircle = field(default_factory=CareCircle.default)
    conversation_rules: List[str] = field(default_factory=list)
    continuity_packet: ContinuityPacket = field(default_factory=ContinuityPacket)

    # Rolling logs used by detectors/classifiers.
    mood_logs: List[Dict[str, Any]] = field(default_factory=list)
    journal_entries: List[Dict[str, Any]] = field(default_factory=list)
    chat_log: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    last_seen: Optional[datetime] = None

    # ----- helpers -----------------------------------------------------
    def all_papers(self) -> List[ExamPaper]:
        out: List[ExamPaper] = []
        for exam in self.exam_event_graph.values():
            out.extend(exam.papers.values())
        return out

    def find_paper(self, paper_id: str) -> Optional[ExamPaper]:
        for exam in self.exam_event_graph.values():
            if paper_id in exam.papers:
                return exam.papers[paper_id]
        return None

    def open_closures(self) -> List[MissingClosure]:
        return [c for c in self.missing_closures if not c.resolved]

    def add_rule(self, rule: str) -> None:
        if rule not in self.conversation_rules:
            self.conversation_rules.append(rule)

    def clear_rule(self, rule: str) -> None:
        if rule in self.conversation_rules:
            self.conversation_rules.remove(rule)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "baseline": self.baseline,
            "exam_event_graph": {k: v.to_dict() for k, v in self.exam_event_graph.items()},
            "missing_closures": [c.to_dict() for c in self.missing_closures],
            "support_state": self.support_state.to_dict(),
            "care_circle": self.care_circle.to_dict(),
            "conversation_rules": list(self.conversation_rules),
            "continuity_packet": self.continuity_packet.to_dict(),
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "mood_logs": [
                {**ml, "timestamp": ml["timestamp"].isoformat() if isinstance(ml.get("timestamp"), datetime) else ml.get("timestamp")}
                for ml in self.mood_logs
            ],
            "journal_entries": [
                {**je, "timestamp": je["timestamp"].isoformat() if isinstance(je.get("timestamp"), datetime) else je.get("timestamp")}
                for je in self.journal_entries
            ],
            "chat_log": [
                {**cl, "timestamp": cl["timestamp"].isoformat() if isinstance(cl.get("timestamp"), datetime) else cl.get("timestamp")}
                for cl in self.chat_log
            ],
            "events": [
                {**ev, "timestamp": ev["timestamp"].isoformat() if isinstance(ev.get("timestamp"), datetime) else ev.get("timestamp")}
                for ev in self.events
            ],
            "counts": {
                "mood_logs": len(self.mood_logs),
                "journal_entries": len(self.journal_entries),
                "chat_log": len(self.chat_log),
                "events": len(self.events),
            },
        }


class StudentStateStore:
    """Module 2: in-memory state store (swap for a DB later)."""

    def __init__(self) -> None:
        self._states: Dict[str, StudentState] = {}

    def get(self, student_id: str) -> StudentState:
        if student_id not in self._states:
            self._states[student_id] = StudentState(student_id=student_id)
        return self._states[student_id]

    def exists(self, student_id: str) -> bool:
        return student_id in self._states

    def save(self, state: StudentState) -> None:
        self._states[state.student_id] = state

    def reset(self, student_id: Optional[str] = None) -> None:
        if student_id is None:
            self._states.clear()
        else:
            self._states.pop(student_id, None)
