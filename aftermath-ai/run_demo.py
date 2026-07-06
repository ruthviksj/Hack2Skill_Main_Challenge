"""Tiny demo driver for the Aftermath-Aware Student Wellness Agent.

Run:  python run_demo.py
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from wellness_agent import WellnessAgent

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)


def show(label, result):
    print("\n" + "=" * 70)
    print(label)
    print("-" * 70)
    print("response :", result["response"])
    print("phase    :", result["support_state"]["phase"])
    print("mode     :", result["support_state"]["mode"])
    print("action   :", result["next_action"])
    print("safety   :", result["safety"]["risk_level"], "| override:", result["safety"]["override"])
    print("escalate :", result["escalation"]["level"])
    print("full json:")
    print(json.dumps(result, indent=2, default=str))


def main():
    agent = WellnessAgent()
    sid = "demo_student"

    show("1) Casual hello (stable)", agent.handle({
        "type": "student_chat", "student_id": sid, "text": "hey what's up",
        "timestamp": T0,
    }))

    show("2) Upcoming exam (pre_exam)", agent.handle({
        "type": "exam_event", "student_id": sid, "exam_id": "bio", "subject": "Biology",
        "paper_id": "bio_p1", "label": "Biology Paper 1",
        "scheduled_date": T0 + timedelta(days=2), "status": "scheduled",
        "timestamp": T0 + timedelta(hours=1),
    }))

    show("3) Acute language (safety override)", agent.handle({
        "type": "student_chat", "student_id": sid,
        "text": "honestly I don't want to be here anymore",
        "timestamp": T0 + timedelta(days=1),
    }))


if __name__ == "__main__":
    main()
