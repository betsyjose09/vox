import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.asr.audio_io import save_wav_bytes
from backend.asr.templates import TemplateManager, AudioTemplate
from backend.asr.mfcc import extract_mfcc

def record_audio_device(duration_s: float = 3.0, sample_rate: int = 16000):
    try:
        import sounddevice as sd
    except ImportError:
        print("sounddevice not installed. Please install sounddevice to record live audio from microphone.")
        return None
        
    print(f"Recording for {duration_s} seconds... Speak now!")
    audio = sd.rec(int(duration_s * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    print("Recording finished.")
    return audio.flatten()

def main():
    speaker_id = input("Enter speaker ID (e.g. speaker_01): ").strip() or "speaker_01"
    vocab_path = settings.vocabulary_path
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)
        
    manager = TemplateManager(settings.templates_dir)
    recordings_dir = settings.recordings_dir / speaker_id
    recordings_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nStarting recording session for command phrases:")
    for item in vocab["command_phrases"]:
        phrase = item["phrase"]
        intent = item["intent"]
        input(f"\nPress ENTER when ready to speak: '{phrase}'")
        audio = record_audio_device(duration_s=3.0, sample_rate=settings.sample_rate)
        if audio is None:
            break
            
        clean_phrase = "".join(c if c.isalnum() else "_" for c in phrase)
        wav_path = recordings_dir / f"{intent}__{clean_phrase}.wav"
        wav_bytes = save_wav_bytes(audio, sample_rate=settings.sample_rate)
        wav_path.write_bytes(wav_bytes)
        
        # Extract features and save template
        features = extract_mfcc(audio, sample_rate=settings.sample_rate)
        tmpl = AudioTemplate(phrase=phrase, intent=intent, speaker_id=speaker_id, features=features)
        manager.save_template_file(tmpl)
        print(f"Saved recording and template for '{phrase}'")

if __name__ == "__main__":
    main()

