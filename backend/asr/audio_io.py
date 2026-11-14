import io
import wave
import numpy as np
from typing import Tuple

def load_wav_bytes(audio_bytes: bytes) -> Tuple[np.ndarray, int]:
    """
    Reads WAV bytes safely from memory.
    Returns:
        audio_float32: 1D numpy array normalized between -1.0 and 1.0
        sample_rate: sampling frequency in Hz
    """
    with io.BytesIO(audio_bytes) as bio:
        with wave.open(bio, 'rb') as wf:
            num_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            num_frames = wf.getnframes()
            
            raw_data = wf.readframes(num_frames)
            
            if sample_width == 1:
                # 8-bit unsigned PCM
                data = np.frombuffer(raw_data, dtype=np.uint8)
                data = (data.astype(np.float32) - 128.0) / 128.0
            elif sample_width == 2:
                # 16-bit signed PCM (most common)
                data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 4:
                # 32-bit signed PCM
                data = np.frombuffer(raw_data, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                raise ValueError(f"Unsupported sample width: {sample_width} bytes")
                
            if num_channels > 1:
                # Reshape and average channels to mono
                data = data.reshape(-1, num_channels)
                data = np.mean(data, axis=1)
                
            return data.astype(np.float32), sample_rate

def save_wav_bytes(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
    """
    Encodes a 1D float32 audio array into standard 16-bit PCM WAV bytes.
    """
    audio_clipped = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio_clipped * 32767.0).astype(np.int16)
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()

