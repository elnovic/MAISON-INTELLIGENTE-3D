@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Flux video pour le site : http://localhost:8081/flux
python surveillance.py
pause
