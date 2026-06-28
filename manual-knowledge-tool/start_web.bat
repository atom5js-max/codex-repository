@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo   Equipment Manual Search - Web Dashboard
echo =============================================
echo.
echo Installing required packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Package installation failed.
  pause
  exit /b 1
)

echo.
echo Local access: http://localhost:5000
echo Network access: http://YOUR-PC-IP:5000
echo To stop: close this window or press Ctrl+C
set "HOST=0.0.0.0"
set "PORT=5000"
set "OPEN_BROWSER=1"
cd src
python web_app.py

pause