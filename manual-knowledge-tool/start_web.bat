@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo =============================================
echo   산업설비 기술자료 웹 검색 대시보드
echo =============================================
echo.
echo Flask 가 설치되어 있지 않으면 먼저 설치합니다...
pip install flask --quiet

echo.
echo 웹 서버를 시작합니다...
echo 브라우저가 자동으로 열립니다: http://localhost:5000
echo 종료하려면 이 창을 닫거나 Ctrl+C 를 누르세요.
echo.
cd src
python web_app.py

pause
