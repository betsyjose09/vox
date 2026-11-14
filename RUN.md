# KIT VOX — How to Run (Fixed Build)

## One-command start (recommended for the demo)

```bash
# from this folder (repo root)
python3 -m uvicorn backend.app:app --port 8000
```

Open **http://127.0.0.1:8000** — the backend now serves the built frontend itself,
so there is only ONE process to run. No `npm run dev` needed.

## Alternative: dev mode (hot reload)

```bash
# terminal 1
python3 -m uvicorn backend.app:app --port 8000
# terminal 2
cd frontend && npm run dev     # vite on :5173, proxies /api and /tts to :8000
```

## Demo accounts (server-side verified)

| Role | Username | Password |
| --- | --- | --- |
| Student (Arjun K) | `arjun` | `Kit@2026` |
| Faculty (Dr. Lakshmi) | `lakshmi` | `Kit@2026` |

Guest/public mode also works without login (college info, courses, fees, holidays).

Note: do NOT run `uvicorn app:app` from inside `backend/` — imports are
`backend.*`-prefixed, so always run from the repo root as shown above.

## What was fixed

Round 2 (voice recognition + deployment):
- **Voice always returned the same fallback** ("Speech wasn't clear enough…") — the recognizer's rejection threshold was calibrated only on the reference voices, so any real microphone (different rate/pitch, room noise, echo cancellation) landed just above it. Fixed by expanding the template set with speed/pitch variants of every recording (`backend/asr/phrase_recognizer.py`), recalibrating the threshold (5.2), and adding an ambiguity gate that rejects near-tie matches instead of guessing. Verified: 432/432 probes recognized across 0.84×–1.16× speaking rates and noise down to 12 dB SNR.
- Vercel deployment: `api/index.py` serverless entry, `vercel.json` (frontend build + `/api` + `/tts` rewrites), SQLite moved to `/tmp` on Vercel, mock fallback when no API key is configured (`backend/config.py`).
- UI/docs: removed recognizer-internal jargon from the interface; added the Vercel guide to `README.md`.

Backend:
- `backend/tests/conftest.py` — tests now force mock KIT mode (suite is deterministic): **18/18 pass**.
- `backend/tests/test_kit_api_integration.py` — real-API unit tests scoped per-test via autouse fixture.
- `backend/tools/kit_client.py` — removed duplicated `/year` in course fees ("Rs. 180000/year/year" → "Rs. 180000/year").
- `backend/app.py` — added a last-mounted static handler serving `frontend/dist`, enabling the single-process demo.

Frontend:
- `frontend/vite.config.ts` — added `/tts` dev proxy (voice answers 404'd before).
- `frontend/src/App.tsx` — creates the session once on mount and passes `sessionId` to Assistant and History (History previously got `sessionId=""` and could never load).
- `frontend/src/pages/Assistant.tsx` — consumes the shared session; re-syncs session id after logout; removed dead imports.
- Restored execute bits on `node_modules/.bin` shims and installed `@rollup/rollup-linux-x64-gnu` (build was crashing).

## Verified end-to-end

- `GET /` → 200 (built React app), `GET /assets/*.js` → 200
- `GET /api/health` → 200 (`kit_backend: REAL`)
- `POST /api/session` → 200, `POST /api/login` (arjun) → 200 role=student
- `POST /api/turn` "show my attendance" → live data + `audio_url` served from `/tts/...wav`
- `python3 -m pytest -q` → **18 passed**
- `npm run build` → clean (tsc 0 errors, 1479 modules)

## Known notes

- Write actions (leave submit/confirm) were verified in mock-mode tests only, to avoid creating real requests on the college account during testing. Demo them live at your own discretion.
- `KIT_USE_MOCK=false` in `backend/.env` means live KIT API mode; it auto-falls back to mock only on network failure.
- Voice input needs mic permission — fine on `localhost`/`127.0.0.1`.
