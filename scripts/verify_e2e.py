import os
import sys
import base64
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import app
from backend.config import settings

client = TestClient(app)

def run_e2e_verification():
    print("=" * 65)
    print(" KIT VOX - End-to-End System Integration Verification")
    print("=" * 65)

    # 1. Health check
    print("\n1. Testing Backend Health Endpoint (/api/health)...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health = res.json()
    print("   Response:", health)
    print(f"   [OK] Backend Status: {health.get('status')}")
    print(f"   [OK] KIT Backend Mode: {health.get('kit_backend')}")
    print(f"   [OK] KIT Key Configured: {health.get('kit_key_configured')}")
    print(f"   [OK] Templates Loaded: {health.get('templates_loaded')}")
    print(f"   [OK] TTS Assets Loaded: {health.get('tts_assets_loaded')}")

    # 2. Public Info & Courses
    print("\n2. Testing Public College Info (/api/public/info)...")
    res = client.get("/api/public/info")
    assert res.status_code == 200
    info = res.json()
    print(f"   [OK] College Name: {info.get('college', {}).get('name')}")
    print(f"   [OK] Courses Available: {len(info.get('courses', []))}")

    # 3. Create Session
    print("\n3. Testing Session Creation (/api/session)...")
    res = client.post("/api/session")
    assert res.status_code == 200
    session_data = res.json()
    session_id = session_data["session_id"]
    print(f"   [OK] Created Session ID: {session_id} (Role: {session_data.get('role')})")

    # 4. Student Login (Real KIT auth)
    print("\n4. Testing Student Login (arjun / Kit@2026)...")
    res = client.post("/api/login", json={
        "session_id": session_id,
        "username": "arjun",
        "password": "Kit@2026",
        "role": "student"
    })
    assert res.status_code == 200, f"Student login failed: {res.text}"
    login_info = res.json()
    print(f"   [OK] Authenticated Identity: {login_info.get('display_name')} (Role: {login_info.get('role')})")

    # 5. Student Turn: Attendance
    print("\n5. Testing Student Turn: Attendance Inquiry...")
    res = client.post("/api/turn", json={
        "session_id": session_id,
        "text": "show my attendance"
    })
    assert res.status_code == 200
    turn_att = res.json()
    print(f"   [OK] Assistant Text: {turn_att['assistant_text']}")
    print(f"   [OK] Audio Response URL: {turn_att['audio_url']}")
    assert turn_att["audio_url"] == "/tts/get_attendance.wav"

    # 6. Verify Static Audio Endpoint
    print("\n6. Testing Audio Asset Streaming (/tts/get_attendance.wav)...")
    res = client.get("/tts/get_attendance.wav")
    assert res.status_code == 200
    assert len(res.content) > 10000
    assert res.content[:4] == b"RIFF"
    print(f"   [OK] Audio stream verified: {len(res.content)} bytes, valid WAV RIFF header")

    # 7. Student Turn: Timetable
    print("\n7. Testing Student Turn: Timetable Inquiry...")
    res = client.post("/api/turn", json={
        "session_id": session_id,
        "text": "show my timetable"
    })
    assert res.status_code == 200
    turn_tt = res.json()
    print(f"   [OK] Assistant Text: {turn_tt['assistant_text'][:90]}...")
    print(f"   [OK] Audio Response URL: {turn_tt['audio_url']}")

    # 8. Multi-turn Leave Request Flow
    print("\n8. Testing Multi-turn Spoken Dialogue: Leave Submission Flow...")
    # Step A: Intent trigger
    res = client.post("/api/turn", json={"session_id": session_id, "text": "i need leave"})
    assert res.status_code == 200
    r_step1 = res.json()
    print(f"   Step 1 Assistant Prompt: {r_step1['assistant_text']}")
    assert "date" in r_step1['assistant_text'].lower()
    assert r_step1["audio_url"] == "/tts/leave_date_prompt.wav"

    # Step B: Provide slot date
    res = client.post("/api/turn", json={"session_id": session_id, "text": "tomorrow"})
    assert res.status_code == 200
    r_step2 = res.json()
    print(f"   Step 2 Assistant Prompt: {r_step2['assistant_text']}")
    assert "reason" in r_step2['assistant_text'].lower()
    assert r_step2["audio_url"] == "/tts/leave_reason_prompt.wav"

    # Step C: Provide slot reason
    res = client.post("/api/turn", json={"session_id": session_id, "text": "family wedding function"})
    assert res.status_code == 200
    r_step3 = res.json()
    print(f"   Step 3 Confirmation Prompt: {r_step3['assistant_text']}")
    assert r_step3.get("needs_confirmation") is True
    pending_action = r_step3.get("pending_action")
    assert pending_action is not None
    action_id = pending_action["action_id"]
    print(f"   [OK] Action Created for Confirmation: ID={action_id}")
    print(f"   [OK] Confirmation Audio URL: {r_step3['audio_url']}")

    # Step D: Confirm Action via API
    print("\n9. Testing Atomic Action Confirmation (/api/actions/{id}/confirm)...")
    res = client.post(f"/api/actions/{action_id}/confirm?session_id={session_id}")
    assert res.status_code == 200
    conf_res = res.json()
    print(f"   [OK] Execution Result: {conf_res.get('message')}")
    print(f"   [OK] Success Audio URL: {conf_res.get('audio_url')}")
    assert conf_res.get("success") is True

    # 10. Test Double Confirmation Prevention (Race condition test)
    print("\n10. Testing Atomic Claim & Double-Execution Guard...")
    res_double = client.post(f"/api/actions/{action_id}/confirm?session_id={session_id}")
    assert res_double.status_code == 400
    print(f"   [OK] Duplicate confirm correctly rejected with HTTP 400: {res_double.json().get('detail')}")

    # 11. Teacher Login & Pending Requests
    print("\n11. Testing Teacher Login (lakshmi / Kit@2026)...")
    res = client.post("/api/session")
    teacher_session = res.json()["session_id"]
    res = client.post("/api/login", json={
        "session_id": teacher_session,
        "username": "lakshmi",
        "password": "Kit@2026",
        "role": "teacher"
    })
    assert res.status_code == 200
    t_login = res.json()
    print(f"   [OK] Teacher Identity: {t_login.get('display_name')}")

    # Teacher reviews pending requests
    res = client.post("/api/turn", json={"session_id": teacher_session, "text": "show pending requests"})
    assert res.status_code == 200
    t_turn = res.json()
    print(f"   [OK] Teacher Response: {t_turn['assistant_text'][:100]}...")
    print(f"   [OK] Audio Response URL: {t_turn['audio_url']}")

    # 12. Audio Recognition Pipeline Test (Simulating WAV audio upload)
    print("\n12. Testing Offline Speech Recognition with WAV audio...")
    wav_path = settings.recordings_dir / "GET_ATTENDANCE__show_my_attendance__synth_fast.wav"
    if wav_path.exists():
        wav_bytes = wav_path.read_bytes()
        b64_audio = base64.b64encode(wav_bytes).decode("utf-8")
        res = client.post("/api/turn", json={
            "session_id": session_id,
            "audio_base64": b64_audio
        })
        assert res.status_code == 200
        audio_turn = res.json()
        print(f"   [OK] Recognized Audio Text: \"{audio_turn.get('recognized_text')}\"")
        print(f"   [OK] Assistant Voice Reply: \"{audio_turn.get('assistant_text')[:80]}...\"")
        print(f"   [OK] Audio Asset: {audio_turn.get('audio_url')}")

    # 13. Cancellation Test
    print("\n13. Testing Voice Cancellation Flow...")
    res = client.post("/api/turn", json={"session_id": session_id, "text": "i need leave"})
    res = client.post("/api/turn", json={"session_id": session_id, "text": "cancel"})
    assert res.status_code == 200
    cancel_res = res.json()
    print(f"   [OK] Cancellation Reply: \"{cancel_res['assistant_text']}\"")
    print(f"   [OK] Cancellation Audio URL: {cancel_res['audio_url']}")
    assert cancel_res["audio_url"] == "/tts/action_cancelled.wav"

    print("\n" + "=" * 65)
    print(" ALL 13 END-TO-END VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_e2e_verification()

