"""EscalationEngine (module 9).

Decides whether and how to involve the care circle, respecting permissions.
This is NOT a production notification system — it only produces structured
*intents* (who to notify, with what scope, and why). A host application is
responsible for actually delivering anything.

Permissions are honoured strictly: if the care circle does not permit contacting
a member, the engine records the intent as blocked rather than silently
notifying them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from .classifier import Classification, Mode, Phase
from .safety import RiskLevel, SafetyVerdict
from .state import StudentState


@dataclass
class NotificationIntent:
    member: str
    scope: str
    reason: str
    allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "member": self.member,
            "scope": self.scope,
            "reason": self.reason,
            "allowed": self.allowed,
        }


@dataclass
class EscalationDecision:
    escalate: bool
    level: str                       # none | monitor | notify | urgent
    notifications: List[NotificationIntent] = field(default_factory=list)
    rationale: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalate": self.escalate,
            "level": self.level,
            "notifications": [n.to_dict() for n in self.notifications],
            "rationale": self.rationale,
        }


class EscalationEngine:
    def evaluate(
        self,
        state: StudentState,
        classification: Classification,
        safety: SafetyVerdict,
        now: datetime,
    ) -> EscalationDecision:
        rationale: List[str] = []
        notifications: List[NotificationIntent] = []

        # --- Acute safety -> urgent escalation --------------------------
        if safety.override and safety.risk_level == RiskLevel.ACUTE:
            rationale.append("Acute safety override from SafetyGate.")
            for member, scope in (("counsellor", "full"), ("parent", "safety_only")):
                allowed = state.care_circle.may_contact(member)
                notifications.append(NotificationIntent(
                    member=member,
                    scope=scope,
                    reason="Acute safety concern requires immediate human support.",
                    allowed=allowed,
                ))
                if not allowed:
                    rationale.append(f"{member} contact not permitted -> intent recorded as blocked.")
            return EscalationDecision(
                escalate=True, level="urgent",
                notifications=notifications, rationale=rationale,
            )

        # --- Elevated (incl. observed buddy/parent flags) -> notify -----
        if safety.risk_level == RiskLevel.ELEVATED:
            rationale.append("Elevated distress signals; routing to counsellor for review.")
            allowed = state.care_circle.may_contact("counsellor")
            notifications.append(NotificationIntent(
                member="counsellor",
                scope="wellbeing_review",
                reason="Elevated distress signals warrant a human check-in.",
                allowed=allowed,
            ))
            return EscalationDecision(
                escalate=allowed, level="notify",
                notifications=notifications, rationale=rationale,
            )

        # --- Aftermath / functional disruption -> monitor + buddy -------
        if classification.phase == Phase.AFTERMATH:
            rationale.append("Aftermath phase: keep a closer eye and lean on the buddy.")
            allowed = state.care_circle.may_contact("buddy")
            notifications.append(NotificationIntent(
                member="buddy",
                scope="wellbeing_flags",
                reason="Gentle peer support during an aftermath period.",
                allowed=allowed,
            ))
            return EscalationDecision(
                escalate=False, level="monitor",
                notifications=notifications, rationale=rationale,
            )

        rationale.append("No escalation indicated.")
        return EscalationDecision(escalate=False, level="none", rationale=rationale)
