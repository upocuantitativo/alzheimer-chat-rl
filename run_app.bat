@echo off
title Alzheimer Chat-RL
cd /d "%~dp0"

echo.
echo  Alzheimer Chat-RL  ^|  http://localhost:8000
echo  Pulsa Ctrl+C para detener.
echo.

:: Abre el navegador tras 2 segundos (en segundo plano)
start /min cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:8000"

python scripts\run_api.py
pause
