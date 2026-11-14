import os
from pathlib import Path
from typing import Tuple
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"


def _load_env_file(path: Path) -> None:
    """Minimal .env loader (no extra dependency). Real environment variables win."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(BASE_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings(BaseModel):
    environment: str = os.getenv("ENVIRONMENT", "development")

    # --- KIT college API (secrets come ONLY from the environment; no defaults) ---
    kit_api_base_url: str = os.getenv("KIT_API_BASE_URL", "https://ht.knowvally.com")
    kit_participant_key: str = os.getenv("KIT_PARTICIPANT_KEY", "")
    # The current kit_client.py is an in-memory mock. This flag makes that explicit
    # and visible (see /api/health). It must become False once the real client exists.
    kit_use_mock: bool = _env_bool("KIT_USE_MOCK", not bool(os.getenv("KIT_PARTICIPANT_KEY", "")))
    session_secret_key: str = os.getenv("SESSION_SECRET_KEY", "")
    # Serverless hosts (Vercel) have a read-only filesystem except /tmp.
    database_path: Path = Path(
        os.getenv("KIT_DB_PATH")
        or ("/tmp/kit_vox.db" if os.getenv("VERCEL") else str(BASE_DIR / "kit_vox.db"))
    )

    # Audio & Signal Processing constants (16kHz standard for ASR)
    sample_rate: int = 16000
    frame_length_ms: float = 25.0
    frame_hop_ms: float = 10.0
    fft_size: int = 512
    num_mel_filters: int = 26
    num_mfcc: int = 13

    # VAD & DTW thresholds
    vad_energy_threshold: float = 0.005
    dtw_rejection_threshold: float = 5.2
    # Reject when the runner-up belongs to a DIFFERENT phrase and sits closer
    # than this margin fraction behind the best match (ambiguity gate).
    dtw_margin_ratio: float = 0.10
    # Speed/pitch factors for expanding the template set so real voices
    # (different rate & pitch from the reference speakers) stay recognizable.
    speed_variants: Tuple[float, ...] = (0.88, 1.12)
    min_audio_duration_sec: float = 0.2
    max_audio_duration_sec: float = 10.0

    # Data paths
    templates_dir: Path = DATA_DIR / "templates"
    recordings_dir: Path = DATA_DIR / "recordings"
    tts_dir: Path = DATA_DIR / "tts"
    documents_dir: Path = DATA_DIR / "documents"
    vocabulary_path: Path = DATA_DIR / "vocabulary.json"


settings = Settings()
