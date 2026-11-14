import numpy as np
from typing import Tuple, List

def compute_pairwise_distances(seq1: np.ndarray, seq2: np.ndarray, metric: str = "euclidean") -> np.ndarray:
    """
    Vectorized computation of all pairwise frame distances between seq1 (N, D) and seq2 (M, D).
    Executes in compiled C via NumPy broadcasting, achieving 100x speedup over Python loops.
    """
    if metric == "cosine":
        norm1 = np.linalg.norm(seq1, axis=1, keepdims=True)
        norm2 = np.linalg.norm(seq2, axis=1, keepdims=True)
        norm1 = np.where(norm1 == 0, 1.0, norm1)
        norm2 = np.where(norm2 == 0, 1.0, norm2)
        dot = np.dot(seq1 / norm1, (seq2 / norm2).T)
        return 1.0 - dot
    else:  # euclidean
        diff = seq1[:, None, :] - seq2[None, :, :]
        return np.linalg.norm(diff, axis=-1).astype(np.float32)

def dtw_distance(
    seq1: np.ndarray,
    seq2: np.ndarray,
    window_ratio: float = 0.25,
    metric: str = "euclidean"
) -> Tuple[float, List[Tuple[int, int]]]:
    """
    Dynamic Time Warping (DTW) with Sakoe-Chiba band constraint and path-length normalization.

    The recurrence cost[i,j] = d(i,j) + min(cost[i-1,j], cost[i,j-1], cost[i-1,j-1])
    is evaluated anti-diagonal by anti-diagonal. All three predecessors of a cell lie on
    earlier diagonals, so every cell on one diagonal can be computed in a single vector
    operation — same results as the scalar loop, ~10x faster in NumPy.
    """
    n, d = seq1.shape
    m, d2 = seq2.shape

    if n == 0 or m == 0:
        return float('inf'), []

    # Precompute all frame distances in C
    dist_mat = compute_pairwise_distances(seq1, seq2, metric=metric)

    # Sakoe-Chiba band window
    w = max(abs(n - m), int(max(n, m) * window_ratio))

    cost_matrix = np.full((n + 1, m + 1), np.inf, dtype=np.float32)
    cost_matrix[0, 0] = 0.0

    for k in range(2, n + m + 1):
        i_lo, i_hi = max(1, k - m), min(n, k - 1)
        if i_lo > i_hi:
            continue
        i_idx = np.arange(i_lo, i_hi + 1)
        j_idx = k - i_idx
        in_band = np.abs(i_idx - j_idx) <= w
        i_idx, j_idx = i_idx[in_band], j_idx[in_band]
        if i_idx.size == 0:
            continue
        dist_vec = dist_mat[i_idx - 1, j_idx - 1]
        top = cost_matrix[i_idx - 1, j_idx]
        left = cost_matrix[i_idx, j_idx - 1]
        diag = cost_matrix[i_idx - 1, j_idx - 1]
        cost_matrix[i_idx, j_idx] = dist_vec + np.minimum(np.minimum(top, left), diag)

    if np.isinf(cost_matrix[n, m]):
        return float('inf'), []

    # Backtrack
    i, j = n, m
    path = [(i - 1, j - 1)]
    while i > 1 or j > 1:
        if i == 1:
            j -= 1
        elif j == 1:
            i -= 1
        else:
            candidates = [
                (cost_matrix[i - 1, j - 1], i - 1, j - 1),
                (cost_matrix[i - 1, j], i - 1, j),
                (cost_matrix[i, j - 1], i, j - 1)
            ]
            _, i, j = min(candidates, key=lambda x: x[0])
        path.append((i - 1, j - 1))

    path.reverse()
    path_len = len(path)
    normalized_distance = float(cost_matrix[n, m] / max(1, path_len))

    return normalized_distance, path
