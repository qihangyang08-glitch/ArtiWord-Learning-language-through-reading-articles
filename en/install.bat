@echo off
chcp 65001 >nul
echo ============================================
echo   Word-Lerning (English) — One-Click Install
echo ============================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.7+ first.
    echo         Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found
python --version

REM --- Detect version root ---
set "VERSION_ROOT=%~dp0"
echo [INFO] Version root: %VERSION_ROOT%

REM --- Find Claude Code user skills directory ---
set "USER_SKILLS=%USERPROFILE%\.claude\skills"
if not exist "%USER_SKILLS%" (
    echo [INFO] Creating user skills directory: %USER_SKILLS%
    mkdir "%USER_SKILLS%" 2>nul
)

REM --- Copy skill files ---
echo.
echo [INSTALL] Copying skills to user directory...
set "SRC_SKILLS=%VERSION_ROOT%.claude\skills"

copy /Y "%SRC_SKILLS%\init-wordlist.md" "%USER_SKILLS%\" >nul 2>&1
if %errorlevel% equ 0 (echo   [OK] init-wordlist.md) else (echo   [FAIL] init-wordlist.md)

copy /Y "%SRC_SKILLS%\generate-article.md" "%USER_SKILLS%\" >nul 2>&1
if %errorlevel% equ 0 (echo   [OK] generate-article.md) else (echo   [FAIL] generate-article.md)

REM --- Create data directories ---
echo.
echo [INFO] Ensuring data directories exist...
if not exist "%VERSION_ROOT%data" mkdir "%VERSION_ROOT%data"
if not exist "%VERSION_ROOT%articles" mkdir "%VERSION_ROOT%articles"

REM --- Verify installation ---
echo.
echo ============================================
echo   Verification
echo ============================================

set "ERRORS=0"

if exist "%VERSION_ROOT%tools\word-triage\index.html" (echo [OK] Web tool: index.html) else (echo [FAIL] Web tool missing & set /a ERRORS+=1)
if exist "%VERSION_ROOT%tools\word-triage\regex-config.txt" (echo [OK] Regex config: regex-config.txt) else (echo [FAIL] Regex config missing & set /a ERRORS+=1)
if exist "%VERSION_ROOT%tools\extract-words.py" (echo [OK] Script: extract-words.py) else (echo [FAIL] extract-words.py missing & set /a ERRORS+=1)
if exist "%VERSION_ROOT%tools\count-words.py" (echo [OK] Script: count-words.py) else (echo [FAIL] count-words.py missing & set /a ERRORS+=1)
if exist "%VERSION_ROOT%tools\check-similarity.py" (echo [OK] Script: check-similarity.py) else (echo [FAIL] check-similarity.py missing & set /a ERRORS+=1)

if exist "%USER_SKILLS%\init-wordlist.md" (echo [OK] User skill: init-wordlist.md) else (set /a ERRORS+=1 & echo [FAIL] User skill not installed)
if exist "%USER_SKILLS%\generate-article.md" (echo [OK] User skill: generate-article.md) else (set /a ERRORS+=1 & echo [FAIL] User skill not installed)

echo.
if %ERRORS% equ 0 (
    echo ============================================
    echo   Installation SUCCESSFUL!
    echo ============================================
    echo.
    echo   Skills installed to: %USER_SKILLS%
    echo.
    echo   To start:
    echo     1. Run: serve.bat (from the en/ directory)
    echo     2. Open Claude Code and type: /init-wordlist
    echo.
) else (
    echo ============================================
    echo   Installation completed with %ERRORS% warning(s).
    echo   Please check the FAIL items above.
    echo ============================================
)

pause
