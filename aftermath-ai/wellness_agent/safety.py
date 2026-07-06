"""SafetyGate (module 4).

The SafetyGate runs **before** normal conversation logic and can override the
planner. It looks for signals of acute risk and surfaces them as *evidence*,
never as a diagnosis.

Important boundaries (by design):
  - It does NOT compute a "suicide probability".
  - It does NOT diagnose depression, anxiety, or any condition.
  - It outputs a discrete risk level + the concrete evidence behind it, so a
    human (counsellor) can make the clinical call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from .signals import NormalizedSignal, Reliability
from .state import StudentState


class RiskLevel(str, Enum):
    NONE = "none"
    ELEVATED = "elevated"
    ACUTE = "acute"


# Phrases that indicate acute risk to self. Kept conservative and explicit.
_ACUTE_PATTERNS = [
    r"\bkill myself\b",
    r"\bend (my|it all|my life)\b",
    r"\bsuicide\b",
    r"\bdon'?t want to (be here|live|wake up)\b",
    r"\bno (point|reason) (in )?living\b",
    r"\bbetter off without me\b",
    r"\bwant to die\b",
    r"\bhurt(ing)? myself\b",
    r"\bself.?harm\b",
]

_ELEVATED_PATTERNS = [
    r"\bcan'?t (do this|cope|go on|take (it|this) anymore)\b",
    r"\bhopeless\b",
    r"\bworthless\b",
    r"\bgiving up\b",
    r"\beveryone hates me\b",
    r"\bi'?m a failure\b",
]


@dataclass
class SafetyVerdict:
    risk_level: RiskLevel
    override: bool                      # if True, planner must defer to safety
    evidence: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "override": self.override,
            "evidence": self.evidence,
            "triggers": self.triggers,
            "note": self.note,
        }


class SafetyGate:
    def evaluate(self, state: StudentState, signal: NormalizedSignal) -> SafetyVerdict:
        evidence: List[str] = []
        triggers: List[str] = []
        level = RiskLevel.NONE

        text = (signal.text or "").lower()

        # 1) Direct language from the student themselves carries the most weight.
        if signal.source.value == "student" and text:
            for pat in _ACUTE_PATTERNS:
                if re.search(pat, text):
                    level = RiskLevel.ACUTE
                    triggers.append(f"language:{pat}")
                    evidence.append("Student used acute self-risk language in their own words.")
                    break
            if level != RiskLevel.ACUTE:
                for pat in _ELEVATED_PATTERNS:
                    if re.search(pat, text):
                        level = _max_level(level, RiskLevel.ELEVATED)
                        triggers.append(f"language:{pat}")
                        evidence.append("Student expressed distress consistent with elevated risk.")
                        break

        # 2) A buddy or counsellor flagging an explicit, urgent safety concern.
        if signal.type in ("buddy_report", "counsellor_update"):
            urgent = bool(signal.payload.get("urgent")) or signal.payload.get("severity") == "urgent"
            concern = (signal.payload.get("concern") or signal.payload.get("category") or "").lower()
            safety_words = ("safety", "self-harm", "self harm", "harm", "suicid", "danger")
            if urgent and any(w in concern for w in safety_words):
                level = RiskLevel.ACUTE
                triggers.append(f"{signal.type}:urgent_safety")
                # Observed, not self-reported: note it, still act, but label clearly.
                evidence.append(
                    f"{signal.source.value.capitalize()} raised an URGENT safety concern "
                    f"(observed report, requires verification): {signal.payload.get('concern','')}"
                )
            elif concern and any(w in concern for w in safety_words):
                level = _max_level(level, RiskLevel.ELEVATED)
                triggers.append(f"{signal.type}:safety_concern")
                evidence.append(f"{signal.source.value.capitalize()} noted a safety-adjacent concern.")

        # 3) Parent reports are interpretive: they can RAISE attention but never
        #    by themselves justify an acute override (handled by reliability).
        if signal.type == "parent_report":
            concerning = (
                any(re.search(p, text) for p in _ACUTE_PATTERNS)
                or any(re.search(p, text) for p in _ELEVATED_PATTERNS)
                or "suicid" in text
            )
            if concerning:
                level = _max_level(level, RiskLevel.ELEVATED)
                triggers.append("parent_report:concerning_language")
                evidence.append(
                    "Parent report contains concerning language, but it is an "
                    "interpretive second-hand account and is treated as a flag to "
                    "check in, not as verified fact."
                )

        override = level == RiskLevel.ACUTE
        note = ""
        if signal.reliability == Reliability.INTERPRETIVE and override:
            # Guard: never let a purely interpretive signal force an acute override.
            override = False
            level = RiskLevel.ELEVATED
            note = "Downgraded: interpretive source cannot establish acute risk alone."

        return SafetyVerdict(
            risk_level=level,
            override=override,
            evidence=evidence,
            triggers=triggers,
            note=note,
        )


def _max_level(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    order = {RiskLevel.NONE: 0, RiskLevel.ELEVATED: 1, RiskLevel.ACUTE: 2}
    return a if order[a] >= order[b] else b
