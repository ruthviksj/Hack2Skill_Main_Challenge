"""AgentPlanner (module 6).

Turns a (phase, mode, safety) tuple into an actionable plan:

  - ``next_action``         : what the agent intends to do
  - ``response_constraints``: hard rules the response MUST obey
  - ``goals``               : what a good response should accomplish
  - ``safety_override``     : whether the SafetyGate took control

The SafetyGate can override the planner: when an acute override is present the
plan is replaced wholesale with a safety-first plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .classifier import Classification, Mode, Phase
from .safety import SafetyVerdict
from .state import StudentState


@dataclass
class Plan:
    next_action: str
    goals: List[str] = field(default_factory=list)
    response_constraints: List[str] = field(default_factory=list)
    safety_override: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "next_action": self.next_action,
            "goals": self.goals,
            "response_constraints": self.response_constraints,
            "safety_override": self.safety_override,
            "notes": self.notes,
        }


# Constraints that apply to every plan (non-diagnosis guardrails).
_BASE_CONSTRAINTS = [
    "do_not_diagnose_any_condition",
    "do_not_estimate_risk_probability",
    "no_toxic_positivity",
    "do_not_treat_interpretive_reports_as_fact",
]


class AgentPlanner:
    def plan(
        self,
        state: StudentState,
        classification: Classification,
        safety: SafetyVerdict,
    ) -> Plan:
        # --- Safety override path ---------------------------------------
        if safety.override:
            return Plan(
                next_action="engage_safety_protocol",
                safety_override=True,
                goals=[
                    "stay_present_and_calm",
                    "express_unconditional_care",
                    "gently_assess_immediate_safety",
                    "connect_to_human_support",
                ],
                response_constraints=_BASE_CONSTRAINTS + [
                    "must_not_minimize",
                    "must_not_leave_student_alone_in_conversation",
                    "must_offer_human_support_and_helpline",
                    "must_not_make_promises_about_confidentiality_or_authorities",
                    "short_warm_direct_language",
                ],
                notes=["SafetyGate override active: planner deferred to safety protocol."],
            )

        phase = classification.phase
        mode = classification.mode
        constraints = list(_BASE_CONSTRAINTS)
        goals: List[str] = []
        notes: List[str] = []

        # --- Mode-driven constraints/goals ------------------------------
        if mode == Mode.PROTECT_NEXT_PAPER:
            goals += ["stabilize_before_next_paper", "build_a_small_concrete_plan"]
            constraints += [
                "do_not_dwell_on_the_bad_paper_now",
                "do_not_introduce_new_worry",
                "keep_focus_on_the_immediate_next_step",
            ]
            notes.append("Protecting performance/wellbeing for an imminent linked paper.")
        elif mode == Mode.BAD_RESULT_CONTAINMENT:
            goals += ["acknowledge_disappointment", "separate_result_from_self_worth"]
            constraints += [
                "do_not_minimize_the_result",
                "do_not_pile_on_or_problem_solve_prematurely",
            ]
        elif mode == Mode.AFTERMATH_MISSING_CLOSURE:
            goals += ["gently_reopen_the_loop", "acknowledge_the_gap_without_pressure"]
            constraints += [
                "must_acknowledge_what_happened_since_we_last_spoke",
                "do_not_pretend_nothing_happened",
                "no_guilt_tripping_about_silence",
            ]
            notes.append("There is an unresolved loop from a prior event.")
        elif mode == Mode.POST_EXAM_CHECKIN:
            goals += ["light_check_in", "open_space_without_pressure"]
            constraints += ["do_not_demand_the_score"]
        elif mode == Mode.PRE_EXAM:
            goals += ["reduce_anticipatory_anxiety", "reinforce_preparation_and_rest"]
            constraints += ["do_not_add_pressure"]
        elif mode == Mode.POST_ESCALATION_STABILIZATION:
            goals += ["prioritize_safety_and_stability", "low_demand_supportive_contact"]
            constraints += [
                "honor_continuity_do_not_say_list",
                "no_performance_or_exam_talk_unless_student_raises_it",
                "keep_it_low_pressure",
            ]
            notes.append("Student is stabilizing after an escalation.")
        elif mode == Mode.POST_ESCALATION_REENTRY:
            goals += ["gentle_reentry", "rebuild_routine_gradually"]
            constraints += [
                "honor_continuity_do_not_say_list",
                "follow_counsellor_reentry_notes",
                "let_student_set_the_pace",
            ]

        # --- Phase-driven action ----------------------------------------
        if phase == Phase.AFTERMATH:
            action = "supportive_followthrough"
            goals.append("offer_concrete_support_options")
        elif phase == Phase.ELEVATED:
            action = "active_supportive_checkin"
            goals.append("validate_and_co_regulate")
        else:  # STABLE
            action = "light_touch_conversation"

        # Mode can refine the headline action.
        if mode == Mode.PROTECT_NEXT_PAPER:
            action = "protect_next_paper_plan"
        elif mode in (Mode.POST_ESCALATION_STABILIZATION, Mode.POST_ESCALATION_REENTRY):
            action = "post_escalation_support"

        # Always honor any standing conversation rules from state.
        for rule in state.conversation_rules:
            constraints.append(f"rule:{rule}")

        # De-duplicate while preserving order.
        constraints = list(dict.fromkeys(constraints))
        goals = list(dict.fromkeys(goals))
        return Plan(
            next_action=action,
            goals=goals,
            response_constraints=constraints,
            safety_override=False,
            notes=notes,
        )
