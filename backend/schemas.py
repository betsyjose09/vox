from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    account_id: str
    role: str  # 'student', 'teacher', 'public'
    name: str
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None
    department: Optional[str] = None

class SessionData(BaseModel):
    session_id: str
    account_id: Optional[str] = None
    role: str = "public"
    display_name: str = "Guest"
    kit_token: Optional[str] = None
    created_at: str
    expires_at: str

class TurnRequest(BaseModel):
    session_id: str
    text: Optional[str] = None
    audio_base64: Optional[str] = None  # Optional base64 encoded wav audio

class TurnResponse(BaseModel):
    session_id: str
    recognized_text: Optional[str] = None
    intent: Optional[str] = None
    module: Optional[str] = None
    assistant_text: str
    audio_url: Optional[str] = None
    pending_action: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
    context: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ConfirmActionRequest(BaseModel):
    session_id: str
    action_id: str

class CancelActionRequest(BaseModel):
    session_id: str
    action_id: str

class LoginRequest(BaseModel):
    session_id: str
    username: str
    password: str
    role: str  # 'student' or 'teacher'

