import pytest
import numpy as np

from backend.config import settings
from backend.asr.audio_io import load_wav_bytes, save_wav_bytes
from backend.asr.resample import resample_audio
from backend.asr.vad import trim_silence
from backend.asr.mfcc import extract_mfcc, get_mel_filterbank
from backend.asr.dtw import dtw_distance
from backend.asr.phrase_recognizer import PhraseRecognizer
from scripts.build_templates import synthesize_phrase_audio

def test_wav_io_roundtrip():
    # 1 second of 440Hz sine wave at 16kHz
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False, dtype=np.float32)
    orig_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    wav_bytes = save_wav_bytes(orig_audio, sample_rate=sr)
    assert len(wav_bytes) > 0
    
    loaded_audio, loaded_sr = load_wav_bytes(wav_bytes)
    assert loaded_sr == sr
    assert len(loaded_audio) == len(orig_audio)
    # 16-bit quantization difference is tiny (< 1e-4)
    np.testing.assert_allclose(orig_audio, loaded_audio, atol=1e-4)

def test_resample_audio():
    # Resample 8kHz signal to 16kHz
    sr_orig = 8000
    sr_target = 16000
    t = np.linspace(0, 0.5, int(0.5 * sr_orig), endpoint=False, dtype=np.float32)
    audio_8k = np.sin(2 * np.pi * 300 * t)
    
    audio_16k = resample_audio(audio_8k, orig_sr=sr_orig, target_sr=sr_target)
    assert len(audio_16k) == int(0.5 * sr_target)

def test_vad_silence_detection():
    # Pure silence test
    silence = np.zeros(16000, dtype=np.float32)
    trimmed, has_speech, metrics = trim_silence(silence, sample_rate=16000)
    assert not has_speech
    
    # Active sound test
    t = np.linspace(0, 0.5, 8000, endpoint=False, dtype=np.float32)
    sound = 0.5 * np.sin(2 * np.pi * 500 * t)
    # Pad with 0.5s silence on both sides
    padded_sound = np.pad(sound, (8000, 8000), mode='constant')
    trimmed, has_speech, metrics = trim_silence(padded_sound, sample_rate=16000)
    assert has_speech
    assert len(trimmed) < len(padded_sound)

def test_mfcc_extraction():
    sr = 16000
    audio = np.random.uniform(-0.2, 0.2, 16000).astype(np.float32)
    features = extract_mfcc(audio, sample_rate=sr, include_deltas=True, apply_cmvn=True)
    
    # Num MFCC (13) + Num Deltas (13) = 26 features
    assert features.ndim == 2
    assert features.shape[1] == 26
    assert np.all(np.isfinite(features))

def test_dtw_identity():
    # Self-distance must be exactly 0
    seq = np.random.uniform(-1, 1, (40, 26)).astype(np.float32)
    dist, path = dtw_distance(seq, seq)
    assert dist == pytest.approx(0.0, abs=1e-5)
    assert len(path) == 40

def test_phrase_recognizer_known_and_rejection():
    recognizer = PhraseRecognizer()
    
    # 1. Load audio for known phrase: "show my attendance"
    from pathlib import Path
    wav_files = list(Path("data/recordings").glob("*__show_my_attendance__*.wav"))
    assert len(wav_files) > 0, "Recording asset for 'show my attendance' must exist"
    wav_bytes = wav_files[0].read_bytes()
    
    result = recognizer.recognize_wav_bytes(wav_bytes)
    assert result["success"] is True
    assert result["recognized_text"] == "show my attendance"
    assert result["intent"] == "GET_ATTENDANCE"
    assert result["confidence"] >= 0.5
    
    # 2. Test rejection on random noise
    noise_audio = np.random.normal(0, 0.0001, 16000).astype(np.float32)
    noise_wav = save_wav_bytes(noise_audio, sample_rate=settings.sample_rate)
    noise_result = recognizer.recognize_wav_bytes(noise_wav)
    assert (noise_result["success"] is False) or (noise_result.get("rejected") is True)
