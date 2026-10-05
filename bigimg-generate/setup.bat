@echo off
setlocal
cd /d "%~dp0"

if not exist .venv (
  py -3.11 -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Python 3.11 not found.
    echo Install Python 3.11 x64 and try again.
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup complete.
pause
