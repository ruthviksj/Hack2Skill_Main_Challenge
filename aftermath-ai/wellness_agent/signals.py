"""Signal schema and SignalNormalizer (module 1).

Raw inbound signals are loosely structured dicts. The normalizer validates the
type, attaches a timestamp, infers the *source* and *reliability* of the signal,
and produces a uniform :class:`NormalizedSignal` for the rest of the pipeline.

Crucially, reliability tagging is where we encode that some signals are
**facts** (a score update from the system, a mood log from the student) while
others are **interpretations** (a judgement-heavy parent report). Downstream
modules must never treat an interpretive signal as ground truth.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


# The structured input signal vocabulary the agent accepts.
SIGNAL_TYPES = (
    "student_chat",
    "journal_entry",
    "mood_log",
    "exam_event",
    "score_update",
    "silence_after_event",
    "buddy_report",
    "parent_report",
    "counsellor_update",
    "post_escalation_update",
)


class SignalSource(str, Enum):
    STUDENT = "student"
    SYSTEM = "system"
    BUDDY = "buddy"
    PARENT = "parent"
    COUNSELLOR = "counsellor"


class Reliability(str, Enum):
    # Objective, machine- or self-recorded data.
    FACTUAL = "factual"
    # Second-hand observation that may be accurate but is unverified.
    OBSERVED = "observed"
    # Subjective, judgement-laden, or emotionally framed. Never a fact.
    INTERPRETIVE = "interpretive"


# Which source each signal type comes from, and how much we trust it as fact.
_SIGNAL_META: Dict[str, Dict[str, Any]] = {
    "student_chat": {"source": SignalSource.STUDENT, "reliability": Reliability.OBSERVED},
    "journal_entry": {"source": SignalSource.STUDENT, "reliability": Reliability.OBSERVED},
    "mood_log": {"source": SignalSource.STUDENT, "reliability": Reliability.FACTUAL},
    "exam_event": {"source": SignalSource.SYSTEM, "reliability": Reliability.FACTUAL},
    "score_update": {"source": SignalSource.SYSTEM, "reliability": Reliability.FACTUAL},
    "silence_after_event": {"source": SignalSource.SYSTEM, "reliability": Reliability.FACTUAL},
    "buddy_report": {"source": SignalSource.BUDDY, "reliability": Reliability.OBSERVED},
    "parent_report": {"source": SignalSource.PARENT, "reliability": Reliability.INTERPRETIVE},
    "counsellor_update": {"source": SignalSource.COUNSELLOR, "reliability": Reliability.FACTUAL},
    "post_escalation_update": {"source": SignalSource.COUNSELLOR, "reliability": Reliability.FACTUAL},
}


@dataclass
class NormalizedSignal:
    """A validated, uniform internal representation of an inbound signal."""

    signal_id: str
    type: str
    student_id: str
    timestamp: datetime
    source: SignalSource
    reliability: Reliability
    text: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_fact(self) -> bool:
        return self.reliability == Reliability.FACTUAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "type": self.type,
            "student_id": self.student_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source.value,
            "reliability": self.reliability.value,
            "text": self.text,
            "payload": self.payload,
        }


class SignalNormalizer:
    """Module 1: validate and normalize raw inbound signals."""

    def normalize(self, raw: Dict[str, Any]) -> NormalizedSignal:
        if not isinstance(raw, dict):
            raise TypeError("signal must be a dict")

        stype = raw.get("type")
        if stype not in SIGNAL_TYPES:
            raise ValueError(
                f"unknown signal type {stype!r}; expected one of {SIGNAL_TYPES}"
            )

        student_id = raw.get("student_id")
        if not student_id:
            raise ValueError("signal must include a student_id")

        ts = raw.get("timestamp")
        if ts is None:
            timestamp = datetime.now(timezone.utc)
        elif isinstance(ts, datetime):
            timestamp = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        else:
            timestamp = self._parse_ts(str(ts))

        meta = _SIGNAL_META[stype]
        # Allow an explicit override of source/reliability if a caller knows
        # better (e.g. a counsellor relaying a verified fact).
        source = SignalSource(raw["source"]) if raw.get("source") else meta["source"]
        reliability = (
            Reliability(raw["reliability"])
            if raw.get("reliability")
            else meta["reliability"]
        )

        # Everything that isn't a recognised top-level key lands in payload.
        reserved = {"type", "student_id", "timestamp", "source", "reliability", "text", "payload"}
        payload: Dict[str, Any] = dict(raw.get("payload", {}))
        for k, v in raw.items():
            if k not in reserved:
                payload[k] = v

        return NormalizedSignal(
            signal_id=raw.get("signal_id") or f"sig_{uuid.uuid4().hex[:10]}",
            type=stype,
            student_id=str(student_id),
            timestamp=timestamp,
            source=source,
            reliability=reliability,
            text=raw.get("text"),
            payload=payload,
        )

    @staticmethod
    def _parse_ts(value: str) -> datetime:
        v = value.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(v)
        except ValueError:
            # Fall back to a date-only string.
            dt = datetime.fromisoformat(v[:10])
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
