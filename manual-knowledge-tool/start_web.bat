@echo off
cd /d "%~dp0"

echo =============================================
echo   Equipment Manual Search - Web Dashboard
echo =============================================
echo.
echo Installing flask if not already installed...
pip install flask --quiet

echo.
echo Starting web server...
echo Browser will open automatically: http://localhost:5000
echo To stop: close this window or press Ctrl+C
echo.
cd src
python web_app.py

pause
