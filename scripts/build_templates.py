import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import scipy.signal

from backend.config import settings
from backend.asr.mfcc import extract_mfcc
from backend.asr.templates import TemplateManager, AudioTemplate
from backend.asr.audio_io import save_wav_bytes

# Formant frequencies (F1, F2, F3 in Hz) for English vowels
VOWEL_FORMANTS = {
    'a': (730, 1090, 2440),
    'e': (530, 1840, 2480),
    'i': (270, 2290, 3010),
    'o': (570, 840, 2410),
    'u': (300, 870, 2240),
    'default': (500, 1500, 2500)
}

def generate_formant_pulse_train(f0: float, duration_s: float, sample_rate: int = 16000) -> np.ndarray:
    """Generates a glottal pulse train excitation at fundamental frequency f0."""
    num_samples = int(duration_s * sample_rate)
    pulse = np.zeros(num_samples, dtype=np.float32)
    period = int(sample_rate / f0)
    for i in range(0, num_samples, period):
        pulse[i] = 1.0
    return pulse

def apply_resonator(signal: np.ndarray, freq: float, bandwidth: float, sample_rate: int = 16000) -> np.ndarray:
    """Applies a second-order IIR bandpass resonator filter for an acoustic formant."""
    r = np.exp(-np.pi * bandwidth / sample_rate)
    theta = 2.0 * np.pi * freq / sample_rate
    a1 = -2.0 * r * np.cos(theta)
    a2 = r ** 2
    b0 = 1.0 - r
    return scipy.signal.lfilter([b0], [1.0, a1, a2], signal)

def synthesize_phrase_audio(phrase: str, speaker_f0: float = 130.0, speed: float = 1.0, sample_rate: int = 16000) -> np.ndarray:
    """
    Synthesizes acoustic audio for a phrase using vowel formant trajectories and consonant noise.
    Produces highly repeatable, mathematically distinct acoustic trajectories for template matching.
    """
    words = phrase.strip().lower().split()
    total_audio = []
    
    for word in words:
        # Syllable/letter duration based on length
        word_dur = max(0.2, len(word) * 0.08 / speed)
        samples_per_word = int(word_dur * sample_rate)
        
        # Base glottal source
        excitation = generate_formant_pulse_train(speaker_f0, word_dur, sample_rate)
        # Add slight pitch contour (declination)
        pitch_mod = np.linspace(1.05, 0.95, len(excitation))
        excitation = excitation * pitch_mod
        
        # Determine dominant vowel formant
        vowel_match = 'default'
        for char in word:
            if char in VOWEL_FORMANTS:
                vowel_match = char
                break
        f1, f2, f3 = VOWEL_FORMANTS[vowel_match]
        
        # Filter through 3 formants
        v1 = apply_resonator(excitation, f1, 80.0, sample_rate)
        v2 = apply_resonator(excitation, f2, 100.0, sample_rate)
        v3 = apply_resonator(excitation, f3, 120.0, sample_rate)
        
        filtered = 0.5 * v1 + 0.3 * v2 + 0.2 * v3
        
        # Add burst/fricative noise for consonants like 's', 't', 'sh', 'ch'
        if any(c in word for c in ['s', 't', 'c', 'f', 'h']):
            noise = np.random.normal(0, 0.05, len(filtered)).astype(np.float32)
            noise_filtered = apply_resonator(noise, 4000.0, 1000.0, sample_rate)
            filtered = filtered + noise_filtered
            
        # Apply smooth Hann envelope to word
        envelope = np.hanning(len(filtered))
        word_audio = filtered * envelope
        
        total_audio.append(word_audio)
        # 40ms silence between words
        total_audio.append(np.zeros(int(0.04 * sample_rate), dtype=np.float32))
        
    full_audio = np.concatenate(total_audio)
    # Normalize peak to 0.8
    peak = np.max(np.abs(full_audio))
    if peak > 0:
        full_audio = 0.8 * (full_audio / peak)
    return full_audio.astype(np.float32)

def build_templates():
    vocab_path = settings.vocabulary_path
    if not vocab_path.exists():
        raise FileNotFoundError(f"Vocabulary not found at {vocab_path}")
        
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)
        
    manager = TemplateManager(settings.templates_dir)
    speakers = [
        {"id": "synth_male_1", "f0": 120.0, "speed": 1.0},
        {"id": "synth_female_1", "f0": 210.0, "speed": 1.05},
        {"id": "synth_fast", "f0": 150.0, "speed": 1.2}
    ]
    
    raw_recordings_dir = settings.recordings_dir
    raw_recordings_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating templates for {len(vocab['command_phrases'])} command phrases...")
    saved_count = 0
    
    for item in vocab["command_phrases"]:
        phrase = item["phrase"]
        intent = item["intent"]
        
        for spk in speakers:
            audio = synthesize_phrase_audio(phrase, speaker_f0=spk["f0"], speed=spk["speed"])
            
            # Save raw WAV for evaluation/inspection
            clean_phrase = "".join(c if c.isalnum() else "_" for c in phrase)
            wav_filename = f"{intent}__{clean_phrase}__{spk['id']}.wav"
            wav_bytes = save_wav_bytes(audio, sample_rate=settings.sample_rate)
            (raw_recordings_dir / wav_filename).write_bytes(wav_bytes)
            
            # Extract MFCC features
            features = extract_mfcc(audio, sample_rate=settings.sample_rate, include_deltas=True, apply_cmvn=True)
            
            # Store template
            template = AudioTemplate(
                phrase=phrase,
                intent=intent,
                speaker_id=spk["id"],
                features=features
            )
            manager.save_template_file(template)
            saved_count += 1
            
    print(f"Successfully generated and saved {saved_count} audio templates in {settings.templates_dir}")

if __name__ == "__main__":
    build_templates()
