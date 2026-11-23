@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set /p NOM=Prenom du resident a enregistrer : 
python enroler.py --nom "%NOM%"
python enroler.py --lister
pause
