"""
Vercel serverless entry point.

Vercel's Python runtime imports this module and serves the module-level
ASGI ``app`` (FastAPI) for every request routed here by ``vercel.json``
(`/api/*` and `/tts/*`).
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backend.app import app  # noqa: E402,F401  (ASGI app consumed by Vercel)
