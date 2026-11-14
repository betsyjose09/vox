import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from backend.session_manager import create_session, update_session_auth
from backend.agents.orchestrator import orchestrator
from backend.tools.kit_client import kit_client

def test_public_and_knowledge():
    session = create_session()
    # 1. Ask for college info
    res = orchestrator.handle_turn(session.session_id, user_text="tell me about kit")
    assert "Knotopian Institute of Technology" in res["assistant_text"]
    
    # 2. Ask for courses
    res = orchestrator.handle_turn(session.session_id, user_text="what courses do you offer")
    assert "B.Tech in Computer Science" in res["assistant_text"]
    
    # 3. Ask for campus rules via BM25 retrieval
    res = orchestrator.handle_turn(session.session_id, user_text="what is the minimum attendance requirement")
    assert "75%" in res["assistant_text"]
    assert "Source: kit_handbook.txt" in res["assistant_text"]

def test_student_read_slice_attendance():
    session = create_session()
    
    # 1. Public user trying to access attendance
    res = orchestrator.handle_turn(session.session_id, user_text="show my attendance")
    assert "log in" in res["assistant_text"].lower()
    
    # 2. Authenticate session as student
    update_session_auth(
        session_id=session.session_id,
        account_id="kit_stu_101",
        role="student",
        display_name="Aarav Sharma",
        kit_token="token_123"
    )
    
    # 3. Student asks for attendance -> gets actual attendance
    res = orchestrator.handle_turn(session.session_id, user_text="show my attendance")
    assert "84.5%" in res["assistant_text"]
    assert "Aarav Sharma" in res["assistant_text"]

def test_multi_turn_leave_submission():
    session = create_session()
    update_session_auth(session.session_id, "kit_stu_101", "student", "Aarav Sharma", "token_123")
    
    # Turn 1: "i need leave" -> asks for date
    t1 = orchestrator.handle_turn(session.session_id, user_text="i need leave")
    assert "date" in t1["assistant_text"].lower()
    
    # Turn 2: "tomorrow" -> asks for reason
    t2 = orchestrator.handle_turn(session.session_id, user_text="tomorrow")
    assert "reason" in t2["assistant_text"].lower()
    
    # Turn 3: "medical appointment" -> creates pending action requiring confirmation
    t3 = orchestrator.handle_turn(session.session_id, user_text="medical appointment")
    assert t3["needs_confirmation"] is True
    assert "shall i submit" in t3["assistant_text"].lower()
    assert t3["pending_action"]["status"] == "READY_FOR_CONFIRMATION"
    
    # Turn 4: "yes" -> confirms and executes
    t4 = orchestrator.handle_turn(session.session_id, user_text="yes")
    assert "executed successfully" in t4["assistant_text"].lower()

def test_exam_conflict_policy_rejection():
    session = create_session()
    update_session_auth(session.session_id, "kit_stu_101", "student", "Aarav Sharma", "token_123")
    
    # Attempt leave on 2026-11-20 (CS304 Database Systems Midterm)
    orchestrator.handle_turn(session.session_id, user_text="i need leave")
    orchestrator.handle_turn(session.session_id, user_text="2026-11-20")
    t_blocked = orchestrator.handle_turn(session.session_id, user_text="personal reason")
    
    assert "blocked" in t_blocked["assistant_text"].lower()
    assert "conflicts with scheduled examination" in t_blocked["assistant_text"].lower()

def test_role_authorization_rejection():
    session = create_session()
    update_session_auth(session.session_id, "kit_stu_101", "student", "Aarav Sharma", "token_123")
    
    # Student attempting teacher command
    res = orchestrator.handle_turn(session.session_id, user_text="show pending requests")
    assert "teacher account" in res["assistant_text"].lower()

if __name__ == "__main__":
    test_public_and_knowledge()
    print("Passed: public & knowledge")
    test_student_read_slice_attendance()
    print("Passed: student attendance read slice")
    test_multi_turn_leave_submission()
    print("Passed: multi-turn leave submission")
    test_exam_conflict_policy_rejection()
    print("Passed: exam conflict policy rejection")
    test_role_authorization_rejection()
    print("Passed: role authorization rejection")
    print("\nALL WORKFLOW & POLICY TESTS PASSED 100%!")
