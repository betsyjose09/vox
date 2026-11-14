import json
from pathlib import Path
from typing import Optional, Dict, Any
from backend.config import settings

class LocalTtsSynthesizer:
    def __init__(self, tts_dir: Optional[Path] = None):
        self.tts_dir = tts_dir or settings.tts_dir
        self.manifest_path = self.tts_dir.parent / "tts_manifest.json"
        self._manifest: Dict[str, Any] = {}
        self.load_manifest()

    def load_manifest(self) -> None:
        if self.manifest_path.is_file():
            try:
                self._manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            except Exception:
                self._manifest = {}

    def get_audio_url_for_turn(
        self,
        intent: Optional[str],
        assistant_text: str,
        module: Optional[str] = None,
        needs_confirmation: bool = False
    ) -> Optional[str]:
        """
        Determines the appropriate local recorded voice WAV asset for an assistant turn.
        Returns a URL like '/tts/<filename>.wav'.
        """
        text_lower = assistant_text.lower()

        # 1. Action Confirmation Prompts
        if needs_confirmation:
            if "leave" in text_lower:
                return "/tts/confirm_leave.wav"
            elif "duty" in text_lower or "od" in text_lower:
                return "/tts/confirm_od.wav"
            elif "approve" in text_lower:
                return "/tts/confirm_approve.wav"
            elif "reject" in text_lower:
                return "/tts/confirm_reject.wav"

        # 2. Slot-filling Prompts
        if "which date do you need leave" in text_lower:
            return "/tts/leave_date_prompt.wav"
        elif "what is the reason for your leave" in text_lower:
            return "/tts/leave_reason_prompt.wav"
        elif "which date do you need on-duty" in text_lower:
            return "/tts/od_date_prompt.wav"
        elif "what is the event" in text_lower:
            return "/tts/od_event_prompt.wav"
        elif "which request id" in text_lower:
            return "/tts/request_id_prompt.wav"

        # 3. Intent-based mapping
        if intent:
            intent_map = {
                "GET_ATTENDANCE": "/tts/get_attendance.wav",
                "GET_TIMETABLE": "/tts/get_timetable.wav",
                "GET_MY_REQUESTS": "/tts/get_my_requests.wav",
                "LIST_PENDING": "/tts/list_pending.wav",
                "CONFIRM_ACTION": "/tts/action_confirmed.wav",
                "CANCEL_ACTION": "/tts/action_cancelled.wav",
                "GET_COLLEGE_INFO": "/tts/college_info.wav",
                "GET_COURSES": "/tts/get_courses.wav",
                "GET_ELIGIBILITY": "/tts/get_eligibility.wav",
                "GET_HOLIDAYS": "/tts/get_holidays.wav",
                "GET_EXAM_DATES": "/tts/get_exam_dates.wav",
                "UNKNOWN": "/tts/unknown.wav"
            }
            if intent in intent_map:
                return intent_map[intent]

        # 4. Text-based keyword matching
        if "log in" in text_lower or "sign in" in text_lower:
            return "/tts/login_required.wav"
        elif "didn't catch" in text_lower or "repeat" in text_lower:
            return "/tts/repeat_prompt.wav"
        elif "confirmed" in text_lower:
            return "/tts/action_confirmed.wav"
        elif "cancelled" in text_lower:
            return "/tts/action_cancelled.wav"

        # Default fallback asset
        return "/tts/welcome.wav"

tts_synthesizer = LocalTtsSynthesizer()
