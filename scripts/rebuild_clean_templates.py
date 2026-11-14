import os
import sys
import json
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import win32com.client
import numpy as np
TEMPLATES_DIR = PROJECT_ROOT / "data" / "templates"
RECORDINGS_DIR = PROJECT_ROOT / "data" / "recordings"
VOCAB_PATH = PROJECT_ROOT / "data" / "vocabulary.json"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

from backend.asr.audio_io import load_wav_bytes
from backend.asr.resample import resample_audio
from backend.asr.vad import trim_silence
from backend.asr.mfcc import extract_mfcc

def build_templates():
    with open(VOCAB_PATH, "r", encoding="utf-8") as f:
        vocab = json.load(f)
        
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    # SAFT16kHz16BitMono = 18
    stream.Format.Type = 18

    # We use 3 distinct rate settings to capture natural speed variations:
    # 0 = normal, 1 = slightly faster, -1 = deliberate/clear
    speaker_variations = [
        ("synth_male_1", 0),
        ("synth_female_1", -1),
        ("synth_fast", 1)
    ]

    print("Building clear natural templates for 18 command phrases...")
    for item in vocab["command_phrases"]:
        phrase = item["phrase"]
        intent = item["intent"]
        clean_phrase = "".join(c if c.isalnum() else "_" for c in phrase).strip("_")

        for spk_name, rate in speaker_variations:
            speaker.Rate = rate
            wav_name = f"{intent}__{clean_phrase}__{spk_name}.wav"
            npz_name = f"{intent}__{clean_phrase}__{spk_name}.npz"
            wav_path = RECORDINGS_DIR / wav_name
            npz_path = TEMPLATES_DIR / npz_name

            stream.Open(str(wav_path), 3, False)
            speaker.AudioOutputStream = stream
            speaker.Speak(phrase)
            stream.Close()

            # Load and process
            raw_audio, sr = load_wav_bytes(wav_path.read_bytes())
            audio_16k = resample_audio(raw_audio, sr, 16000)
            trimmed, has_speech, _ = trim_silence(audio_16k, 16000, energy_threshold_multiplier=1.8)
            if not has_speech or len(trimmed) < 1600:
                trimmed = audio_16k

            features = extract_mfcc(trimmed, sample_rate=16000, include_deltas=True, apply_cmvn=True)
            np.savez_compressed(
                npz_path,
                phrase=phrase,
                intent=intent,
                speaker_id=spk_name,
                features=features
            )
            print(f"  [OK] {phrase} ({spk_name}) -> {features.shape[0]} frames")

if __name__ == "__main__":
    build_templates()
