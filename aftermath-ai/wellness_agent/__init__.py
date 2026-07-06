"""Aftermath-Aware Student Wellness Agent.

A standalone, rule-based agent package that ingests structured wellness signals
about a student, maintains a structured student state, and produces a
*support-oriented* (non-diagnostic) response plus a structured JSON trace.

This package is intentionally NOT:
  - a full application, web server, or UI
  - an authentication / payment / production-notification system

It is a self-contained decision core that can be embedded inside such systems.

Public entry point:

    >>> from wellness_agent import WellnessAgent
    >>> agent = WellnessAgent()
    >>> result = agent.handle({
    ...     "type": "student_chat",
    ...     "student_id": "stu_1",
    ...     "text": "hey",
    ... })
    >>> result["support_state"]["phase"]
    'phase_0_stable'
"""

from .agent import WellnessAgent
from .signals import (
    SignalNormalizer,
    NormalizedSignal,
    SIGNAL_TYPES,
    SignalSource,
    Reliability,
)
from .state import StudentState, StudentStateStore
from .closure import MissingClosureDetector
from .safety import SafetyGate, SafetyVerdict, RiskLevel
from .classifier import (
    SupportStateClassifier,
    Phase,
    Mode,
    Classification,
)
from .planner import AgentPlanner, Plan
from .response import ResponseGenerator
from .critic import ResponseCritic, CriticReport
from .escalation import EscalationEngine, EscalationDecision
from .continuity import ContinuityPacketUpdater

__all__ = [
    "WellnessAgent",
    "SignalNormalizer",
    "NormalizedSignal",
    "SIGNAL_TYPES",
    "SignalSource",
    "Reliability",
    "StudentState",
    "StudentStateStore",
    "MissingClosureDetector",
    "SafetyGate",
    "SafetyVerdict",
    "RiskLevel",
    "SupportStateClassifier",
    "Phase",
    "Mode",
    "Classification",
    "AgentPlanner",
    "Plan",
    "ResponseGenerator",
    "ResponseCritic",
    "CriticReport",
    "EscalationEngine",
    "EscalationDecision",
    "ContinuityPacketUpdater",
]

__version__ = "0.1.0"
