@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found in PATH. Please install Python 3.x and try again.
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv venv
)

set "VENV_PY=venv\Scripts\python.exe"

echo Syncing requirements with requirements.txt...
"%VENV_PY%" -m pip install -r requirements.txt -q --disable-pip-version-check

"%VENV_PY%" -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('en_core_web_sm') else 1)" >nul 2>nul
if errorlevel 1 (
  echo Downloading spaCy model en_core_web_sm...
  "%VENV_PY%" -m spacy download en_core_web_sm
) else (
  echo spaCy model already installed. Skipping download.
)

echo Launching app...
"%VENV_PY%" -m streamlit run app.py

endlocal
