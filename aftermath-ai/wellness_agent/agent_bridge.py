import sys
import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Add the parent directory of this file to the python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wellness_agent import WellnessAgent
from wellness_agent.state import StudentState, ExamEvent, ExamPaper, MissingClosure, SupportState, CareCircle, ContinuityPacket

def parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    s_cleaned = str(s).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s_cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None

def from_dict(d: Dict[str, Any]) -> StudentState:
    student_id = d["student_id"]
    state = StudentState(student_id=student_id)
    
    # baseline
    state.baseline = d.get("baseline", state.baseline)
    
    # exam_event_graph
    exam_graph = {}
    for exam_id, exam_dict in d.get("exam_event_graph", {}).items():
        exam = ExamEvent(exam_id=exam_id, subject=exam_dict["subject"])
        for paper_id, paper_dict in exam_dict.get("papers", {}).items():
            paper = ExamPaper(
                paper_id=paper_id,
                label=paper_dict["label"],
                scheduled_date=parse_dt(paper_dict.get("scheduled_date")),
                status=paper_dict.get("status", "scheduled"),
                score=paper_dict.get("score"),
                max_score=paper_dict.get("max_score"),
                next_paper_id=paper_dict.get("next_paper_id"),
            )
            exam.papers[paper_id] = paper
        exam_graph[exam_id] = exam
    state.exam_event_graph = exam_graph
    
    # missing_closures
    closures = []
    for c_dict in d.get("missing_closures", []):
        c = MissingClosure(
            kind=c_dict["kind"],
            ref=c_dict["ref"],
            opened_at=parse_dt(c_dict["opened_at"]) or datetime.now(timezone.utc),
            detail=c_dict.get("detail", ""),
            resolved=c_dict.get("resolved", False),
        )
        closures.append(c)
    state.missing_closures = closures
    
    # support_state
    ss_dict = d.get("support_state", {})
    state.support_state = SupportState(
        phase=ss_dict.get("phase", "phase_0_stable"),
        mode=ss_dict.get("mode", "normal"),
        since=parse_dt(ss_dict.get("since")) or datetime.now(timezone.utc),
        history=ss_dict.get("history", []),
    )
    
    # care_circle
    cc_dict = d.get("care_circle", {})
    state.care_circle = CareCircle(members=cc_dict.get("members", {}))
    
    # conversation_rules
    state.conversation_rules = d.get("conversation_rules", [])
    
    # continuity_packet
    cp_dict = d.get("continuity_packet", {})
    state.continuity_packet = ContinuityPacket(
        summary=cp_dict.get("summary", ""),
        open_threads=cp_dict.get("open_threads", []),
        sensitivities=cp_dict.get("sensitivities", []),
        do_not_say=cp_dict.get("do_not_say", []),
        last_escalation=cp_dict.get("last_escalation"),
        reentry_notes=cp_dict.get("reentry_notes", []),
        updated_at=parse_dt(cp_dict.get("updated_at")),
    )
    
    # logs
    def parse_log_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
        res = dict(entry)
        if "timestamp" in res:
            res["timestamp"] = parse_dt(res["timestamp"])
        return res

    state.mood_logs = [parse_log_entry(x) for x in d.get("mood_logs", [])]
    state.journal_entries = [parse_log_entry(x) for x in d.get("journal_entries", [])]
    state.chat_log = [parse_log_entry(x) for x in d.get("chat_log", [])]
    state.events = [parse_log_entry(x) for x in d.get("events", [])]
    state.last_seen = parse_dt(d.get("last_seen"))
    
    return state

def sync_db_state(state: StudentState, db_state: Dict[str, Any]) -> None:
    # 1. Sync Exams
    for exam_data in db_state.get("exams", []):
        exam_id = exam_data["id"]
        subject = exam_data["name"]
        
        # Map score
        actual_score_str = exam_data.get("actual_score")
        score = None
        if actual_score_str is not None and actual_score_str != "":
            # Extract digits
            digits = "".join([c for c in str(actual_score_str) if c.isdigit()])
            if digits:
                score = float(digits)
                
        max_score = 800.0 if "gmat" in subject.lower() else 100.0
        
        # Map status
        ns_status = exam_data.get("status")
        if ns_status == "upcoming":
            status = "scheduled"
        elif ns_status == "outcome_reported":
            status = "scored"
        elif ns_status == "outcome_missing":
            status = "written"
        else:
            status = "written" if score is None else "scored"
            
        exam = state.exam_event_graph.get(exam_id)
        if exam is None:
            exam = ExamEvent(exam_id=exam_id, subject=subject)
            state.exam_event_graph[exam_id] = exam
            
        paper = exam.papers.get(exam_id)
        if paper is None:
            paper = ExamPaper(
                paper_id=exam_id,
                label=subject,
                scheduled_date=parse_dt(exam_data.get("exam_date")),
                status=status,
                score=score,
                max_score=max_score,
            )
            exam.papers[exam_id] = paper
        else:
            paper.status = status
            paper.score = score
            paper.scheduled_date = parse_dt(exam_data.get("exam_date"))
            
    # 2. Sync Care Circle Members
    care_members = {}
    for member in db_state.get("care_circle_members", []):
        role = member.get("role")
        if role:
            may_contact = bool(member.get("can_receive_emergency_alert") or member.get("can_submit_concern"))
            share_scope = "full" if member.get("can_view_private_chat") else ("wellbeing_flags" if member.get("can_submit_concern") else "safety_only")
            care_members[role] = {
                "may_contact": may_contact,
                "share_scope": share_scope
            }
            
    # Ensure buddy/counsellor/parent defaults exist if not customized
    for role in ["buddy", "counsellor", "parent"]:
        if role not in care_members:
            if role == "buddy":
                care_members[role] = {"may_contact": True, "share_scope": "wellbeing_flags"}
            elif role == "counsellor":
                care_members[role] = {"may_contact": True, "share_scope": "full"}
            else:
                care_members[role] = {"may_contact": False, "share_scope": "none"}
    state.care_circle = CareCircle(members=care_members)
    
    # 3. Sync Chat Messages
    chat_log = []
    for msg in db_state.get("chat_messages", []):
        if msg.get("role") == "user":
            chat_log.append({
                "timestamp": parse_dt(msg.get("created_at")),
                "text": msg.get("content")
            })
    state.chat_log = chat_log
    
    # 4. Sync mood logs from signals
    mood_logs = []
    for sig in db_state.get("signals", []):
        if sig.get("signal_type") == "mood_log":
            mood_logs.append({
                "timestamp": parse_dt(sig.get("created_at")),
                "mood": sig.get("metadata_json", {}).get("mood", 6),
                "text": sig.get("raw_content", "")
            })
    state.mood_logs = mood_logs

def main():
    try:
        # Read from stdin
        input_data = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"error": f"Failed to parse stdin: {e}"}))
        sys.exit(1)
        
    raw_signal = input_data.get("raw_signal")
    db_state = input_data.get("db_state")
    
    if not raw_signal:
        print(json.dumps({"error": "Missing raw_signal field in input JSON"}))
        sys.exit(1)
        
    student_id = raw_signal.get("student_id")
    if not student_id:
        print(json.dumps({"error": "Missing student_id field in raw_signal"}))
        sys.exit(1)
        
    # State file path
    states_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "states")
    os.makedirs(states_dir, exist_ok=True)
    state_file = os.path.join(states_dir, f"{student_id}.json")
    
    # Load state if exists
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_dict = json.load(f)
            student_state = from_dict(state_dict)
        except Exception as e:
            student_state = StudentState(student_id=student_id)
    else:
        student_state = StudentState(student_id=student_id)
        
    # Sync with current database status
    if db_state:
        sync_db_state(student_state, db_state)
        
    # Create agent and load state
    from wellness_agent.state import StudentStateStore
    store = StudentStateStore()
    store.save(student_state)
    
    agent = WellnessAgent(store=store)
    
    # Handle the signal
    result = agent.handle(raw_signal)
    
    # Save the updated state
    updated_state = store.get(student_id)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(updated_state.to_dict(), f, indent=2, default=str)
        
    # Print result to stdout
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
