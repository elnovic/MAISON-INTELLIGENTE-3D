@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Installation de la vision par ordinateur ===
if not exist .venv (
  python -m venv .venv || (echo Python introuvable. Installez-le depuis python.org & pause & exit /b 1)
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || (echo Echec de l'installation des bibliotheques. & pause & exit /b 1)
python telecharger_modeles.py
if not exist config.ini copy config.exemple.ini config.ini >nul
echo.
echo Installation terminee. Etape suivante : 2-chercher-camera.bat
pause
