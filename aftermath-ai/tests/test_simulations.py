"""Simulation tests for the Aftermath-Aware Student Wellness Agent.

Run with:  python -m pytest tests/ -v
or simply: python tests/test_simulations.py   (falls back to a plain runner)

Each scenario drives the agent through a sequence of structured signals and
asserts on the structured JSON output.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wellness_agent import WellnessAgent  # noqa: E402
from wellness_agent.critic import ResponseCritic  # noqa: E402


T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)


def at(hours: float = 0, days: float = 0) -> datetime:
    return T0 + timedelta(hours=hours, days=days)


# ---------------------------------------------------------------------------
# Scenario 1: exam date passes, score missing, student silent, random return
# ---------------------------------------------------------------------------
def test_scenario_1_missing_closure_on_random_return():
    agent = WellnessAgent()
    sid = "stu_closure"

    # Exam is written on day 0.
    agent.handle({
        "type": "exam_event", "student_id": sid, "timestamp": at(days=0),
        "exam_id": "math", "subject": "Math", "paper_id": "math_p1",
        "label": "Math Paper 1", "scheduled_date": at(days=0), "status": "written",
    })
    # System notes silence after the event (2 days later).
    agent.handle({
        "type": "silence_after_event", "student_id": sid, "timestamp": at(days=2),
        "ref": "math_p1", "since": at(days=0).isoformat(),
    })

    # Student returns out of the blue, with no mention of the exam.
    out = agent.handle({
        "type": "student_chat", "student_id": sid, "timestamp": at(days=3),
        "text": "hey, you around?",
    })

    open_kinds = [c["kind"] for c in out["missing_closures"] if not c["resolved"]]
    assert "silence_after_exam" in open_kinds, out["missing_closures"]
    assert out["support_state"]["mode"] == "aftermath_missing_closure", out["support_state"]
    # The response must acknowledge the gap, not pretend nothing happened.
    assert out["critic"]["approved"] is True
    assert any(w in out["response"].lower() for w in ("quiet", "since", "exam"))
    return out


# ---------------------------------------------------------------------------
# Scenario 2: bad Paper 1 affecting Paper 2
# ---------------------------------------------------------------------------
def test_scenario_2_protect_next_paper():
    agent = WellnessAgent()
    sid = "stu_papers"

    # Paper 1 written, links to Paper 2.
    agent.handle({
        "type": "exam_event", "student_id": sid, "timestamp": at(days=0),
        "exam_id": "phys", "subject": "Physics", "paper_id": "phys_p1",
        "label": "Physics Paper 1", "scheduled_date": at(days=0),
        "status": "written", "max_score": 100, "next_paper_id": "phys_p2",
    })
    # Paper 2 scheduled in 3 days.
    agent.handle({
        "type": "exam_event", "student_id": sid, "timestamp": at(days=0, hours=1),
        "exam_id": "phys", "subject": "Physics", "paper_id": "phys_p2",
        "label": "Physics Paper 2", "scheduled_date": at(days=3), "status": "scheduled",
        "max_score": 100,
    })
    # A poor Paper 1 result lands.
    out = agent.handle({
        "type": "score_update", "student_id": sid, "timestamp": at(days=1),
        "paper_id": "phys_p1", "score": 31, "max_score": 100,
        "scored_at": at(days=1).isoformat(),
    })

    assert out["support_state"]["mode"] == "protect_next_paper", out["support_state"]
    assert "do_not_dwell_on_the_bad_paper_now" in out["response_constraints"]
    assert out["critic"]["approved"] is True
    # Response should not interrogate the bad paper.
    assert "why did you" not in out["response"].lower()
    return out


# ---------------------------------------------------------------------------
# Scenario 3: buddy reports urgent safety concern
# ---------------------------------------------------------------------------
def test_scenario_3_buddy_urgent_safety():
    agent = WellnessAgent()
    sid = "stu_buddy"

    out = agent.handle({
        "type": "buddy_report", "student_id": sid, "timestamp": at(days=0),
        "urgent": True, "concern": "talking about self-harm and not safe",
    })

    assert out["safety"]["risk_level"] == "acute", out["safety"]
    assert out["safety"]["override"] is True
    assert out["support_state"]["phase"] == "phase_3_acute_safety"
    assert out["next_action"] == "engage_safety_protocol"
    assert out["escalation"]["level"] == "urgent"
    members = {n["member"]: n for n in out["escalation"]["notifications"]}
    assert "counsellor" in members
    # Counsellor is permitted by default; parent is not -> intent blocked.
    assert members["counsellor"]["allowed"] is True
    assert members["parent"]["allowed"] is False
    # No diagnosis or probability in the response.
    assert "%" not in out["response"]
    assert "counsellor" in out["response"].lower() or "crisis" in out["response"].lower()
    return out


# ---------------------------------------------------------------------------
# Scenario 4: post-escalation continuity prevents a harmful response
# ---------------------------------------------------------------------------
def test_scenario_4_continuity_prevents_harm():
    agent = WellnessAgent()
    sid = "stu_post"

    # Trigger an acute escalation first so continuity seeds do_not_say.
    agent.handle({
        "type": "student_chat", "student_id": sid, "timestamp": at(days=0),
        "text": "I don't want to be here anymore, I want to die",
    })
    state = agent.store.get(sid)
    assert state.continuity_packet.last_escalation is not None
    assert "what did you get" in state.continuity_packet.do_not_say

    # Counsellor marks stabilization.
    agent.handle({
        "type": "post_escalation_update", "student_id": sid, "timestamp": at(days=1),
        "stage": "stabilization", "note": "Keep contact gentle and low-demand.",
    })

    # Now simulate an UPSTREAM generator slip: a harmful, score-demanding draft.
    classification = agent.classifier.classify(
        state,
        agent.normalizer.normalize({"type": "student_chat", "student_id": sid, "text": "hi"}),
        agent.safety_gate.evaluate(
            state,
            agent.normalizer.normalize({"type": "student_chat", "student_id": sid, "text": "hi"}),
        ),
        at(days=1, hours=1),
    )
    plan = agent.planner.plan(state, classification, agent.safety_gate.evaluate(
        state, agent.normalizer.normalize({"type": "student_chat", "student_id": sid, "text": "hi"})))

    harmful_draft = ("So what did you get on the exam? You should have studied harder. "
                     "Just move on already.")
    report = ResponseCritic().review(harmful_draft, state, classification, plan)

    assert report.approved is False, "critic should reject the harmful draft"
    assert report.violations, report.to_dict()
    low = report.final_response.lower()
    assert "what did you get" not in low
    assert "you should have" not in low
    assert "just move on" not in low
    return report.to_dict()


# ---------------------------------------------------------------------------
# Scenario 5: parent judgement-heavy report is not treated as fact
# ---------------------------------------------------------------------------
def test_scenario_5_parent_report_not_fact():
    agent = WellnessAgent()
    sid = "stu_parent"

    out = agent.handle({
        "type": "parent_report", "student_id": sid, "timestamp": at(days=0),
        "text": "He is being lazy and dramatic and is definitely suicidal for attention",
    })

    # Interpretive source must NOT establish an acute override on its own.
    assert out["signal"]["reliability"] == "interpretive"
    assert out["safety"]["override"] is False, out["safety"]
    assert out["support_state"]["phase"] != "phase_3_acute_safety"
    # Evidence should explicitly mark it as unverified / a flag, not fact.
    joined = " ".join(out["safety"]["evidence"]).lower()
    assert "interpretive" in joined or "not as verified fact" in joined or "flag" in joined
    return out


SCENARIOS = [
    ("1: missing closure on random return", test_scenario_1_missing_closure_on_random_return),
    ("2: protect next paper", test_scenario_2_protect_next_paper),
    ("3: buddy urgent safety", test_scenario_3_buddy_urgent_safety),
    ("4: continuity prevents harm", test_scenario_4_continuity_prevents_harm),
    ("5: parent report not fact", test_scenario_5_parent_report_not_fact),
]


if __name__ == "__main__":
    import json
    failures = 0
    for name, fn in SCENARIOS:
        try:
            result = fn()
            print(f"\n=== PASS scenario {name} ===")
            print(json.dumps(result, indent=2, default=str)[:1400])
        except AssertionError as e:
            failures += 1
            print(f"\n!!! FAIL scenario {name}: {e}")
    print(f"\n{len(SCENARIOS) - failures}/{len(SCENARIOS)} scenarios passed.")
    sys.exit(1 if failures else 0)
