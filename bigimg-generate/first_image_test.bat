@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
  echo [ERROR] Run setup.bat first.
  pause
  exit /b 1
)

echo.
echo BigIMG Generate - First Image Test
echo This test uses the first checkpoint found under models\checkpoints.
echo It runs txt2img only: no LoRA, VAE, ControlNet, or IP-Adapter.
echo.

.venv\Scripts\python.exe first_image_test.py
set ERR=%ERRORLEVEL%

echo.
if "%ERR%"=="0" (
  echo [PASS] A real image was generated.
  echo Check outputs\validation
) else (
  echo [FAIL] The test did not finish.
  echo Copy the error text above for debugging.
)
pause
exit /b %ERR%
