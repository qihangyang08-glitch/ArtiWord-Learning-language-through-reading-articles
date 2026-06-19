@echo off
cd /d "%~dp0"
echo Starting Word-Lerning local server...
echo.
echo   Web tool: http://localhost:8080/tools/word-triage/
echo.
echo Press Ctrl+C to stop.
echo.
REM Open browser after a short delay to let the server start
start "" http://localhost:8080/tools/word-triage/
python -m http.server 8080
