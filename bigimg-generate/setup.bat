@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================
echo BigIMG Generate - Windows Setup
echo ==========================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python launcher not found.
  echo Please install Python 3.11 x64 first.
  pause
  exit /b 1
)

if not exist .venv (
  echo [1/5] Creating Python 3.11 environment...
  py -3.11 -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Python 3.11 x64 not found.
    echo Install Python 3.11 x64 and try again.
    pause
    exit /b 1
  )
) else (
  echo [1/5] Existing environment found.
)

call .venv\Scripts\activate.bat

echo [2/5] Updating pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail

where nvidia-smi >nul 2>nul
if errorlevel 1 goto :cpu

echo [3/5] NVIDIA GPU detected. Installing PyTorch CUDA 12.6 build...
python -m pip install --upgrade torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cu126
if errorlevel 1 (
  echo.
  echo [WARN] CUDA package install failed. Falling back to CPU package.
  goto :cpu
)
goto :deps

:cpu
echo [3/5] Installing PyTorch CPU build...
python -m pip install --upgrade torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto :fail

:deps
echo [4/5] Installing BigIMG Generate dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [5/5] Running environment check...
python diagnostics.py
if errorlevel 1 goto :fail

echo.
echo Setup complete.
echo You can now run run.bat.
pause
exit /b 0

:fail
echo.
echo [ERROR] Setup failed.
echo Please copy the error message above when reporting the problem.
pause
exit /b 1
