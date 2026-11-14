import numpy as np
from typing import Tuple, Dict, Any

def trim_silence(
    audio: np.ndarray,
    sample_rate: int = 16000,
    frame_length_ms: float = 20.0,
    frame_hop_ms: float = 10.0,
    energy_threshold_multiplier: float = 2.5,
    pad_frames: int = 5
) -> Tuple[np.ndarray, bool, Dict[str, Any]]:
    """
    Voice Activity Detection and silence trimming using Short-Time Energy (STE)
    and adaptive noise-floor estimation.
    
    Returns:
        trimmed_audio: audio segment between detected speech onset and offset
        has_speech: whether the audio contains speech above noise floor
        metrics: diagnostic dict with duration, energy, noise floor
    """
    if len(audio) == 0:
        return audio, False, {"error": "empty_audio"}
        
    frame_len = int(sample_rate * (frame_length_ms / 1000.0))
    frame_hop = int(sample_rate * (frame_hop_ms / 1000.0))
    
    if len(audio) < frame_len:
        return audio, False, {"error": "audio_too_short"}
        
    num_frames = (len(audio) - frame_len) // frame_hop + 1
    energies = np.zeros(num_frames, dtype=np.float32)
    
    for i in range(num_frames):
        start = i * frame_hop
        frame = audio[start : start + frame_len]
        energies[i] = np.sum(frame ** 2) / frame_len
        
    # Estimate noise floor from the lowest 15% energy frames
    sorted_energies = np.sort(energies)
    noise_frames_count = max(1, int(len(sorted_energies) * 0.15))
    noise_floor = float(np.mean(sorted_energies[:noise_frames_count]))
    
    # Adaptive threshold: noise floor scaled + minimum absolute threshold
    threshold = max(noise_floor * energy_threshold_multiplier, 1e-5)
    
    speech_mask = energies > threshold
    
    if not np.any(speech_mask):
        return audio, False, {
            "has_speech": False,
            "max_energy": float(np.max(energies)),
            "noise_floor": noise_floor,
            "threshold": threshold
        }
        
    indices = np.where(speech_mask)[0]
    start_frame = max(0, indices[0] - pad_frames)
    end_frame = min(num_frames - 1, indices[-1] + pad_frames)
    
    start_sample = start_frame * frame_hop
    end_sample = min(len(audio), end_frame * frame_hop + frame_len)
    
    trimmed_audio = audio[start_sample:end_sample]
    
    metrics = {
        "has_speech": True,
        "orig_duration_s": len(audio) / sample_rate,
        "trimmed_duration_s": len(trimmed_audio) / sample_rate,
        "noise_floor": noise_floor,
        "peak_energy": float(np.max(energies)),
        "threshold": threshold
    }
    
    return trimmed_audio, True, metrics

