@echo off
echo Starting Word-Lerning local server...
echo Open http://localhost:8080/tools/word-triage/ in your browser.
echo Press Ctrl+C to stop.
cd /d "%~dp0"
python -m http.server 8080
pause
