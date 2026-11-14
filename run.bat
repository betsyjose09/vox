@echo off
rem ---------------------------------------------------------------------------
rem KIT VOX - install dependencies and start the app (Windows)
rem
rem Usage:
rem   double-click run.bat            (starts on http://127.0.0.1:8000)
rem   set PORT=9000 && run.bat        (start on a different port)
rem
rem The frontend ships prebuilt in frontend\dist, so npm/Node is only needed
rem if you want to rebuild it after changing frontend source code.
rem ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0"

set PORT=8000
if defined PORT_OVERRIDE set PORT=%PORT_OVERRIDE%

rem Pick a Python interpreter (python, then py)
set PY=python
where python >nul 2>nul
if errorlevel 1 (
  set PY=py
  where py >nul 2>nul
  if errorlevel 1 (
    echo Python not found. Install Python 3.10+ from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" during setup.
    pause
    exit /b 1
  )
)

echo Using Python:
%PY% --version

echo.
echo [1/4] Installing Python dependencies (backend\requirements.txt)...
%PY% -m pip install --quiet --disable-pip-version-check -r backend\requirements.txt
if errorlevel 1 (
  echo pip install failed. Try: %PY% -m pip install --upgrade pip
  pause
  exit /b 1
)
echo   done.

if not exist "frontend\dist\index.html" (
  echo [2/4] frontend\dist missing - building the frontend...
  where npm >nul 2>nul
  if errorlevel 1 (
    echo npm not found. Install Node.js 18+ from https://nodejs.org and re-run.
    pause
    exit /b 1
  )
  pushd frontend
  if not exist node_modules call npm install --no-audit --no-fund
  call npm run build
  popd
  echo   done.
) else (
  echo [2/4] Prebuilt frontend found in frontend\dist - skipping build.
)

echo [3/4] Starting KIT VOX at http://127.0.0.1:%PORT%
echo       (Student: arjun / Kit@2026   Faculty: lakshmi / Kit@2026)
echo.
echo [4/4] Opening your browser...
start "" /min cmd /c "timeout /t 3 /nobreak >nul && start "" http://127.0.0.1:%PORT%"

%PY% -m uvicorn backend.app:app --host 127.0.0.1 --port %PORT%

echo.
echo The server has stopped.
pause
