import numpy as np
from typing import Optional

def hz_to_mel(hz: np.ndarray) -> np.ndarray:
    """Converts frequency in Hz to Mel scale."""
    return 2595.0 * np.log10(1.0 + hz / 700.0)

def mel_to_hz(mel: np.ndarray) -> np.ndarray:
    """Converts Mel scale to frequency in Hz."""
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

def get_mel_filterbank(
    num_filters: int = 26,
    fft_size: int = 512,
    sample_rate: int = 16000,
    low_freq: float = 20.0,
    high_freq: Optional[float] = None
) -> np.ndarray:
    """
    Constructs triangular Mel filterbank matrix of shape (num_filters, fft_size // 2 + 1).
    """
    if high_freq is None:
        high_freq = sample_rate / 2.0
        
    low_mel = hz_to_mel(np.array([low_freq]))[0]
    high_mel = hz_to_mel(np.array([high_freq]))[0]
    
    # Uniformly spaced points in Mel scale
    mel_points = np.linspace(low_mel, high_mel, num_filters + 2)
    hz_points = mel_to_hz(mel_points)
    
    # Map to FFT bin numbers
    bins = np.floor((fft_size + 1) * hz_points / sample_rate).astype(int)
    
    num_bins = fft_size // 2 + 1
    filterbank = np.zeros((num_filters, num_bins), dtype=np.float32)
    
    for m in range(1, num_filters + 1):
        f_left = bins[m - 1]
        f_center = bins[m]
        f_right = bins[m + 1]
        
        # Upward slope
        for k in range(f_left, f_center):
            if f_center > f_left:
                filterbank[m - 1, k] = (k - f_left) / (f_center - f_left)
                
        # Downward slope
        for k in range(f_center, f_right):
            if f_right > f_center:
                filterbank[m - 1, k] = (f_right - k) / (f_right - f_center)
                
    return filterbank

def compute_deltas(features: np.ndarray, n: int = 2) -> np.ndarray:
    """
    Computes delta (velocity) features using linear regression across 2*n+1 frames.
    """
    num_frames, num_feats = features.shape
    deltas = np.zeros_like(features)
    
    padded = np.pad(features, ((n, n), (0, 0)), mode='edge')
    denominator = 2 * sum(i ** 2 for i in range(1, n + 1))
    
    for t in range(num_frames):
        # centered at index t + n in padded
        sum_delta = np.zeros(num_feats, dtype=np.float32)
        for i in range(1, n + 1):
            sum_delta += i * (padded[t + n + i] - padded[t + n - i])
        deltas[t] = sum_delta / denominator
        
    return deltas

def extract_mfcc(
    audio: np.ndarray,
    sample_rate: int = 16000,
    frame_length_ms: float = 25.0,
    frame_hop_ms: float = 10.0,
    fft_size: int = 512,
    num_mel_filters: int = 26,
    num_mfcc: int = 13,
    pre_emphasis_coeff: float = 0.97,
    include_deltas: bool = True,
    apply_cmvn: bool = True
) -> np.ndarray:
    """
    Complete team-implemented MFCC extraction pipeline without external speech dependencies.
    Returns:
        Feature matrix of shape (num_frames, num_features)
    """
    if len(audio) == 0:
        return np.empty((0, num_mfcc * (2 if include_deltas else 1)), dtype=np.float32)
        
    # 1. Pre-emphasis filter
    emphasized = np.append(audio[0], audio[1:] - pre_emphasis_coeff * audio[:-1])
    
    # 2. Frame blocking
    frame_len = int(sample_rate * (frame_length_ms / 1000.0))
    frame_hop = int(sample_rate * (frame_hop_ms / 1000.0))
    
    if len(emphasized) < frame_len:
        # Pad with zeros if too short
        pad_width = frame_len - len(emphasized)
        emphasized = np.pad(emphasized, (0, pad_width), mode='constant')
        
    num_frames = (len(emphasized) - frame_len) // frame_hop + 1
    
    # 3. Windowing (Hamming window)
    window = np.hamming(frame_len).astype(np.float32)
    
    # Create frames
    frames = np.zeros((num_frames, frame_len), dtype=np.float32)
    for i in range(num_frames):
        start = i * frame_hop
        frames[i] = emphasized[start : start + frame_len] * window
        
    # 4. FFT & Power spectrum
    mag_frames = np.absolute(np.fft.rfft(frames, n=fft_size))
    power_frames = (mag_frames ** 2) / fft_size
    
    # 5. Mel Filterbank application
    filterbank = get_mel_filterbank(
        num_filters=num_mel_filters,
        fft_size=fft_size,
        sample_rate=sample_rate
    )
    
    filterbank_energies = np.dot(power_frames, filterbank.T)
    filterbank_energies = np.where(filterbank_energies == 0, np.finfo(float).eps, filterbank_energies)
    log_energies = np.log(filterbank_energies)
    
    # 6. Discrete Cosine Transform (DCT Type II)
    # Standard formula: X_k = sum_{n=0}^{N-1} x_n * cos(pi * k * (2n + 1) / (2N))
    num_filters = filterbank_energies.shape[1]
    n_idx = np.arange(num_filters)
    k_idx = np.arange(num_mfcc)[:, None]
    dct_basis = np.cos(np.pi * k_idx * (2 * n_idx + 1) / (2 * num_filters))
    
    mfcc = np.dot(log_energies, dct_basis.T)
    
    # 7. Dynamic features (Deltas)
    if include_deltas:
        deltas = compute_deltas(mfcc, n=2)
        features = np.hstack([mfcc, deltas])
    else:
        features = mfcc
        
    # 8. Cepstral Mean and Variance Normalization (CMVN)
    if apply_cmvn and features.shape[0] > 1:
        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0)
        std = np.where(std < 1e-6, 1.0, std)
        features = (features - mean) / std
        
    return features.astype(np.float32)

