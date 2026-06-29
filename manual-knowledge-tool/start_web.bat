@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo   Equipment Manual Search - Web Dashboard
echo =============================================
echo.

set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"
set "CODEX_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if exist "%VENV_PYTHON%" goto check_packages

echo [1/3] Creating the Python virtual environment...
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -m venv .venv >nul 2>&1
  if exist "%VENV_PYTHON%" goto check_packages
)

if exist "%CODEX_PYTHON%" (
  "%CODEX_PYTHON%" -m venv .venv
  if exist "%VENV_PYTHON%" goto check_packages
)

where python >nul 2>&1
if not errorlevel 1 (
  python -m venv .venv
  if exist "%VENV_PYTHON%" goto check_packages
)

echo.
echo [ERROR] Python 3.9 or later was not found.
echo Install Python and run this file again.
goto end

:check_packages
echo [1/3] Checking the runtime...
"%VENV_PYTHON%" -c "import flask, yaml, pdfplumber, pypdf, pypdfium2" >nul 2>&1
if not errorlevel 1 goto show_access

echo [2/3] Installing required packages for the first run...
"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [ERROR] Package installation failed. Check the Internet connection.
  goto end
)

:show_access
if not defined HOST set "HOST=0.0.0.0"
if not defined PORT set "PORT=5000"
if not defined OPEN_BROWSER set "OPEN_BROWSER=1"

set "LAN_IP="
for /f "tokens=2 delims=:" %%I in ('ipconfig ^| findstr /c:"IPv4"') do if not defined LAN_IP set "LAN_IP=%%I"
for /f "tokens=* delims= " %%I in ("%LAN_IP%") do set "LAN_IP=%%I"

echo.
echo [3/3] Starting the server...
echo.
echo   PC URL            : http://localhost:%PORT%
if defined LAN_IP (
  echo   Tablet/Phone URL  : http://%LAN_IP%:%PORT%
) else (
  echo   Tablet/Phone URL  : http://YOUR-PC-IP:%PORT%
)
echo.
echo Mobile devices must use the same Wi-Fi as this PC.
echo If Windows Firewall asks, allow access on Private networks.
echo Press Ctrl+C or close this window to stop the server.
echo.

cd src
"%VENV_PYTHON%" web_app.py

:end
if "%NO_PAUSE%"=="1" exit /b
pause
