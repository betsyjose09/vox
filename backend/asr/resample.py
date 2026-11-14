import math
import numpy as np
import scipy.signal

def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """
    Resamples audio to target sample rate using anti-aliased polyphase filtering
    (scipy.signal.resample_poly), avoiding the aliasing artifacts of decimation/interpolation.
    """
    if orig_sr == target_sr:
        return audio.astype(np.float32)
        
    gcd = math.gcd(orig_sr, target_sr)
    up = target_sr // gcd
    down = orig_sr // gcd
    
    resampled = scipy.signal.resample_poly(audio, up, down)
    return resampled.astype(np.float32)

