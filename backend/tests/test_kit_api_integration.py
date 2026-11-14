import pytest
from unittest.mock import patch, MagicMock
from backend.config import settings
from backend.tools.kit_client import KitApiClient
from backend.schemas import SessionData

@pytest.fixture(autouse=True)
def force_real_api_path(monkeypatch):
    # These tests unit-test the real-KIT-API branch with _http_request patched out.
    # conftest.py forces KIT_USE_MOCK=true globally (deterministic/offline suite),
    # so override it to False here for the duration of each test.
    monkeypatch.setattr(settings, "kit_use_mock", False)

@pytest.fixture
def test_client():
    return KitApiClient(base_url="https://ht.knowvally.com", participant_key="test_key_123")

def test_kit_login_success(test_client):
    with patch.object(test_client, '_http_request', return_value={
        "access_token": "valid_token_xyz",
        "token_type": "bearer",
        "user": {"id": 76, "login_id": "arjun", "full_name": "Arjun K", "role": "student"}
    }):
        res = test_client.login("arjun", "Kit@2026")
        assert res["success"] is True
        assert res["access_token"] == "valid_token_xyz"
        assert res["user"]["role"] == "student"

def test_kit_login_failure(test_client):
    with patch.object(test_client, '_http_request', return_value={
        "error": "Invalid credentials", "status_code": 401
    }):
        res = test_client.login("arjun", "WrongPass")
        assert res["success"] is False

def test_missing_participant_key():
    client_no_key = KitApiClient(base_url="https://ht.knowvally.com", participant_key="")
    assert client_no_key._should_use_real_api() is False

def test_attendance_retrieval(test_client):
    with patch.object(test_client, '_http_request', return_value={
        "overall_percentage": 78.5,
        "subjects": [{"subject_name": "Algorithms", "percentage": 85.0}]
    }):
        res = test_client.get_attendance("76", token="valid_token")
        assert res["success"] is True
        assert res["overall_pct"] == 78.5
        assert len(res["breakdown"]) == 1

def test_timetable_retrieval(test_client):
    with patch.object(test_client, '_http_request', return_value=[
        {"weekday": 1, "start_time": "09:00", "subject_name": "Operating Systems", "subject_code": "CS303"}
    ]):
        res = test_client.get_timetable("76", token="valid_token")
        assert res["success"] is True
        assert len(res["timetable"]) == 1
        assert "Operating Systems" in res["timetable"][0]["schedule"]

def test_request_submission_with_idempotency(test_client):
    with patch.object(test_client, '_http_request', return_value={
        "id": 120, "status": "pending"
    }) as mock_http:
        res = test_client.submit_leave_request(
            account_id="76",
            leave_date="2026-11-20",
            reason="Medical visit",
            idempotency_key="unique-idemp-key-1",
            token="valid_token"
        )
        assert res["success"] is True
        assert res["request_id"] == "120"
        mock_http.assert_called_once()
        assert mock_http.call_args[1]["idempotency_key"] == "unique-idemp-key-1"

def test_teacher_approval_and_rejection(test_client):
    with patch.object(test_client, '_http_request', return_value={"success": True}):
        appr = test_client.review_request(
            account_id="73", request_id="120", action="APPROVE", token="valid_tea_token"
        )
        assert appr["success"] is True
        assert appr["status"] == "APPROVED"

        rej = test_client.review_request(
            account_id="73", request_id="120", action="REJECT", reason="Missing medical slip", token="valid_tea_token"
        )
        assert rej["success"] is True
        assert rej["status"] == "REJECTED"

