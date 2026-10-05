@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
  echo [ERROR] Run setup.bat first.
  pause
  exit /b 1
)

echo ==========================================
echo BigIMG Generate - Download Test Model
echo ==========================================
echo.
echo Source:
echo stable-diffusion-v1-5/stable-diffusion-v1-5
echo File:
echo v1-5-pruned-emaonly.safetensors
echo Size: about 4.27 GB
echo.
echo Make sure you have enough disk space and internet access.
echo.

.venv\Scripts\python.exe download_validation_model.py
set ERR=%ERRORLEVEL%

echo.
if "%ERR%"=="0" (
  echo [PASS] Model is ready.
  echo Next, double-click first_image_test.bat
) else (
  echo [FAIL] Download/setup did not finish.
)
pause
exit /b %ERR%
