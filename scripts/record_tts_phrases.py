"""
Interactive script for recording human speech replacements for all TTS voice assets.
Preserves 16kHz 16-bit mono WAV format for seamless playback in the voice assistant.
"""
import sys
import json
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
TTS_DIR = settings.tts_dir
MANIFEST_PATH = PROJECT_ROOT / "data" / "tts_manifest.json"

def record_audio_device(duration_s: float, sample_rate: int = 16000):
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        print("sounddevice not installed. Please run: pip install sounddevice")
        return None

    print(f"  [RECORDING] {duration_s}s... Speak clearly into your mic:")
    audio = sd.rec(int(duration_s * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    print("  [DONE] Recording captured.")
    
    # Simple silence trim & normalize to -16 LUFS (~0.1 RMS)
    flat = audio.flatten()
    rms = float(np.sqrt(np.mean(flat**2)))
    if rms > 0.001:
        target_rms = 0.1
        gain = min(target_rms / rms, 8.0)
        flat = np.clip(flat * gain, -1.0, 1.0)
        
    int16_pcm = (flat * 32767).astype(np.int16)
    return int16_pcm

def main():
    if not MANIFEST_PATH.exists():
        print(f"Manifest not found at {MANIFEST_PATH}. Run build_tts_assets.py first.")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print("=================================================================")
    print(" KIT VOX - Human Speech Assistant Voice Recording Studio")
    print("=================================================================")
    print(f"Target directory: {TTS_DIR}")
    print(f"Total phrases: {len(manifest)}")
    print("For each phrase, read the sentence aloud naturally when prompted.\n")

    for key, info in manifest.items():
        fname = info["filename"]
        text = info["text"]
        est_dur = max(3.0, info.get("duration_sec", 4.0))

        print(f"\n--- [{key}] ---")
        print(f"Text to speak: \"{text}\"")
        ans = input(f"Press ENTER to record ({est_dur}s), or 's' to skip: ").strip().lower()
        if ans == 's':
            continue

        pcm_data = record_audio_device(duration_s=est_dur, sample_rate=settings.sample_rate)
        if pcm_data is None:
            break

        out_path = TTS_DIR / fname
        with wave.open(str(out_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(settings.sample_rate)
            wf.writeframes(pcm_data.tobytes())
            
        print(f"  [SAVED] {out_path.name} overwritten with human recording.")

    print("\nRecording session complete! All saved voice assets are immediately live.")

if __name__ == "__main__":
    main()

