@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python lister_cameras.py --apercu
echo.
echo Si besoin, ouvrez config.ini et changez la ligne "source =" dans la section [camera].
pause
