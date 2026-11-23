@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Site local : http://localhost:8000  (Ctrl+C pour arreter)
start "" http://localhost:8000
python -m http.server 8000
