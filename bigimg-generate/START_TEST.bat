@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title BigIMG Generate - Start Test

echo ==========================================
echo BigIMG Generate - One Click Test
echo ==========================================
echo.
echo This developer test will:
echo   1. Check Python / environment
echo   2. Install dependencies if needed
echo   3. Download the SD1.5 validation model if needed
echo   4. Generate one real test image
echo.
echo The validation model is about 4.27 GB.
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo [STOP] Python 3.11 x64 is not installed.
  echo Install Python 3.11 x64 first, then run this file again.
  echo.
  pause
  exit /b 2
)

if not exist .venv\Scripts\python.exe (
  echo [STEP 1] Environment not found. Running setup...
  call setup.bat
  if errorlevel 1 goto :failed
) else (
  echo [STEP 1] Environment already exists.
  .venv\Scripts\python.exe diagnostics.py --quick
  if errorlevel 1 (
    echo Environment check failed. Running setup again...
    call setup.bat
    if errorlevel 1 goto :failed
  )
)

echo.
echo [STEP 2] Checking validation model...
if exist "models\checkpoints\sd15\v1-5-pruned-emaonly.safetensors" (
  echo Validation model already exists.
) else (
  echo Validation model not found. Starting download...
  .venv\Scripts\python.exe download_validation_model.py
  if errorlevel 1 goto :failed
)

echo.
echo [STEP 3] Generating the first real image...
.venv\Scripts\python.exe first_image_test.py
if errorlevel 1 goto :failed

echo.
echo ==========================================
echo [PASS] BigIMG Generate basic test passed.
echo ==========================================
echo.
echo Test image:
echo outputs\validation\first_image_seed12345.png
echo.
echo You can now run run.bat to open BigIMG Generate.
echo.
choice /C YN /N /M "Open BigIMG Generate now? [Y/N]: "
if errorlevel 2 goto :done
if errorlevel 1 start "" run.bat

:done
pause
exit /b 0

:failed
echo.
echo ==========================================
echo [FAIL] BigIMG Generate test stopped.
echo ==========================================
echo Copy or screenshot the error above and send it back for debugging.
echo.
pause
exit /b 1
