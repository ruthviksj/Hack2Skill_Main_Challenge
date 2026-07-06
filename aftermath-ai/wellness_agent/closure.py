"""MissingClosureDetector (module 3).

A "missing closure" is an emotionally significant loop that opened but was never
resolved *with the student*:

  - an exam was written but the agent never checked in afterwards
  - a score landed but the student never acknowledged it (silence)
  - the student went quiet right after an event

The detector is idempotent: running it repeatedly will not create duplicate
closures, and it will mark closures resolved when the student re-engages with
the relevant topic.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from .state import MissingClosure, StudentState


class MissingClosureDetector:
    def __init__(
        self,
        silence_after_exam_hours: int = 18,
        unacknowledged_score_hours: int = 12,
    ) -> None:
        self.silence_after_exam_hours = silence_after_exam_hours
        self.unacknowledged_score_hours = unacknowledged_score_hours

    def detect(self, state: StudentState, now: datetime) -> List[MissingClosure]:
        """Update ``state.missing_closures`` in place; return the open ones."""
        existing = {(c.kind, c.ref) for c in state.missing_closures}

        for paper in state.all_papers():
            # 1) Exam written but no recent student contact => silence_after_exam.
            if paper.status in ("written", "scored") and paper.scheduled_date:
                quiet_for = self._hours_since_contact(state, paper.scheduled_date, now)
                if (
                    quiet_for is not None
                    and quiet_for >= self.silence_after_exam_hours
                    and ("silence_after_exam", paper.paper_id) not in existing
                ):
                    state.missing_closures.append(MissingClosure(
                        kind="silence_after_exam",
                        ref=paper.paper_id,
                        opened_at=now,
                        detail=f"No student contact for ~{int(quiet_for)}h after {paper.label}.",
                    ))
                    existing.add(("silence_after_exam", paper.paper_id))

            # 2) Score posted but never acknowledged by the student.
            if paper.status == "scored" and not self._score_acknowledged(state, paper.paper_id):
                if ("unacknowledged_score", paper.paper_id) not in existing:
                    state.missing_closures.append(MissingClosure(
                        kind="unacknowledged_score",
                        ref=paper.paper_id,
                        opened_at=now,
                        detail=f"Score for {paper.label} posted but not acknowledged.",
                    ))
                    existing.add(("unacknowledged_score", paper.paper_id))

        self._maybe_resolve(state)
        return state.open_closures()

    # ------------------------------------------------------------------
    @staticmethod
    def _hours_since_contact(state: StudentState, after: datetime, now: datetime):
        """Hours since the student last spoke, but only counting after ``after``.

        Returns None if the event hasn't actually happened yet.
        """
        if now < after:
            return None
        last_contact = None
        for entry in state.chat_log + state.journal_entries + state.mood_logs:
            ts = entry.get("timestamp")
            if isinstance(ts, datetime) and ts >= after:
                if last_contact is None or ts > last_contact:
                    last_contact = ts
        reference = last_contact or after
        return (now - reference).total_seconds() / 3600.0

    @staticmethod
    def _score_acknowledged(state: StudentState, paper_id: str) -> bool:
        paper = state.find_paper(paper_id)
        if paper is None or paper.scheduled_date is None:
            return False
        scored_at = paper.scheduled_date
        for entry in state.chat_log + state.journal_entries:
            ts = entry.get("timestamp")
            text = (entry.get("text") or "").lower()
            if isinstance(ts, datetime) and ts >= scored_at:
                if any(k in text for k in ("score", "result", "mark", "grade", "paper", "exam")):
                    return True
        return False

    def _maybe_resolve(self, state: StudentState) -> None:
        # A loop is only *closed* once the student actually engages with the
        # topic again — a casual "hey" return keeps it open on purpose, so the
        # agent can gently reopen it (aftermath_missing_closure mode).
        topic_words = ("score", "result", "mark", "grade", "paper", "exam",
                       "test", "how i did", "how it went", "failed", "passed")
        for closure in state.missing_closures:
            if closure.resolved:
                continue
            if closure.kind in ("silence_after_exam", "unacknowledged_score"):
                for entry in state.chat_log + state.journal_entries:
                    ts = entry.get("timestamp")
                    text = (entry.get("text") or "").lower()
                    if (isinstance(ts, datetime) and ts >= closure.opened_at
                            and any(w in text for w in topic_words)):
                        closure.resolved = True
                        break
