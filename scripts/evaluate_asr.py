import sys
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.asr.templates import TemplateManager, AudioTemplate
from backend.asr.phrase_recognizer import PhraseRecognizer
from backend.asr.audio_io import load_wav_bytes
from scripts.build_templates import synthesize_phrase_audio

def run_evaluation():
    print("=" * 60)
    print("KIT VOX SPEECH RECOGNITION - HELD-OUT SPEAKER EVALUATION")
    print("=" * 60)
    
    vocab_path = settings.vocabulary_path
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)
        
    phrases = vocab["command_phrases"]
    held_out_speaker = {"id": "eval_unseen_speaker", "f0": 175.0, "speed": 0.95}
    
    recognizer = PhraseRecognizer()
    
    total = len(phrases)
    correct = 0
    rejected = 0
    misrecognized = 0
    confusions = []
    
    print(f"\nEvaluating on {total} held-out acoustic test utterances...")
    for item in phrases:
        target_phrase = item["phrase"]
        target_intent = item["intent"]
        
        # Synthesize unseen audio
        audio = synthesize_phrase_audio(target_phrase, speaker_f0=held_out_speaker["f0"], speed=held_out_speaker["speed"])
        
        # Test recognition
        res = recognizer.recognize_features(
            recognizer.recognize_wav_bytes.__wrapped__ if hasattr(recognizer.recognize_wav_bytes, '__wrapped__') else None or 
            # Direct feature extraction
            __import__("backend.asr.mfcc", fromlist=["extract_mfcc"]).extract_mfcc(audio, sample_rate=settings.sample_rate)
        )
        
        if res.get("rejected"):
            rejected += 1
            print(f"[-] '{target_phrase}' -> REJECTED (Dist: {res.get('best_distance')})")
        elif res.get("recognized_text") == target_phrase:
            correct += 1
            print(f"[+] '{target_phrase}' -> MATCHED ({res.get('confidence') * 100:.1f}% confidence)")
        else:
            misrecognized += 1
            got = res.get("recognized_text")
            confusions.append((target_phrase, got))
            print(f"[x] '{target_phrase}' -> MISMATCH (Got: '{got}')")
            
    accuracy = (correct / total) * 100.0
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS SUMMARY:")
    print(f"Total Test Utterances: {total}")
    print(f"Accurate Matches:      {correct} ({accuracy:.1f}%)")
    print(f"Rejections:            {rejected} ({(rejected/total)*100.0:.1f}%)")
    print(f"Mismatches:            {misrecognized} ({(misrecognized/total)*100.0:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    run_evaluation()

