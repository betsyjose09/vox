import os
import wave
import json
from pathlib import Path
import win32com.client
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TTS_DIR = PROJECT_ROOT / "data" / "tts"
TTS_DIR.mkdir(parents=True, exist_ok=True)

PHRASES = {
    "welcome": "Hello! I am KIT VOX, the Knotopian Institute of Technology voice assistant. How can I assist you today?",
    "get_attendance": "Your attendance record has been retrieved from the college database.",
    "get_timetable": "Here is your class timetable schedule.",
    "get_my_requests": "Here are your submitted student requests.",
    "list_pending": "Here are the pending student requests awaiting review.",
    "leave_date_prompt": "Which date do you need leave for? You can say today or tomorrow.",
    "leave_reason_prompt": "What is the reason for your leave?",
    "od_date_prompt": "Which date do you need On-Duty for? You can say today or tomorrow.",
    "od_event_prompt": "What is the event name for your On-Duty?",
    "request_id_prompt": "Which request ID would you like to review?",
    "confirm_leave": "You are requesting leave. Shall I submit this request? Please confirm with yes or cancel with no.",
    "confirm_od": "You are requesting On-Duty. Shall I submit this request? Please confirm with yes or cancel with no.",
    "confirm_approve": "You are about to approve this request. Do you confirm this action? Please say yes or no.",
    "confirm_reject": "You are about to reject this request. Do you confirm this action? Please say yes or no.",
    "action_confirmed": "Confirmed. Your action was executed successfully.",
    "action_cancelled": "The action was cancelled. What else can I help you with?",
    "college_info": "Knotopian Institute of Technology is an autonomous engineering institution in Coimbatore.",
    "get_courses": "KIT offers programs in Computer Science, Artificial Intelligence, and Electronics.",
    "get_eligibility": "Admission requires sixty percent in Physics, Chemistry and Math in higher secondary.",
    "get_holidays": "Here are the upcoming college holidays.",
    "get_exam_dates": "Here is the official examination schedule.",
    "login_required": "Please sign in with your student or teacher account first.",
    "repeat_prompt": "I didn't quite catch that. Could you please repeat your request?",
    "unknown": "I didn't recognize that command. You can ask for attendance, timetable, exam dates, or submit leave.",
    "error": "The operation could not be completed at this time."
}

def generate_assets():
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    # SAFT16kHz16BitMono = 18
    stream.Format.Type = 18

    manifest = {}
    print(f"Generating {len(PHRASES)} TTS audio assets in {TTS_DIR}...")
    
    for key, text in PHRASES.items():
        wav_filename = f"{key}.wav"
        wav_path = TTS_DIR / wav_filename
        
        stream.Open(str(wav_path), 3, False)
        speaker.AudioOutputStream = stream
        speaker.Speak(text)
        stream.Close()
        
        # Read back to ensure normalized volume and accurate stats
        with wave.open(str(wav_path), "rb") as wf:
            n_frames = wf.getnframes()
            rate = wf.getframerate()
            duration = round(n_frames / rate, 2)
            
        manifest[key] = {
            "filename": wav_filename,
            "text": text,
            "sample_rate": rate,
            "duration_sec": duration,
            "url": f"/tts/{wav_filename}"
        }
        print(f"  [OK] {wav_filename} ({duration}s)")

    manifest_path = PROJECT_ROOT / "data" / "tts_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest saved to {manifest_path}")

if __name__ == "__main__":
    generate_assets()

