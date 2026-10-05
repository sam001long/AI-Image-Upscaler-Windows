@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
  echo [ERROR] Environment not found.
  echo Run setup.bat first.
  pause
  exit /b 1
)

.venv\Scripts\python.exe diagnostics.py --quick
if errorlevel 1 (
  echo.
  echo [ERROR] Environment check failed.
  echo Run setup.bat again.
  pause
  exit /b 1
)

.venv\Scripts\python.exe app.py
