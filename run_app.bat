@echo off
title Alzheimer Chat-RL
cd /d "%~dp0"

echo.
echo  Alzheimer Chat-RL — iniciando servidor...
echo  Abre el navegador en: http://localhost:8000
echo  Pulsa Ctrl+C para detener.
echo.

python scripts\run_api.py
pause
