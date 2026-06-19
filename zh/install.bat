@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   Word-Lerning (Chinese) - One-Click Install
echo ============================================
echo.

REM --- Detect script directory (works even if run from elsewhere) ---
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
echo [INFO] Install directory: %SCRIPT_DIR%

REM --- Check Python ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.7+ first.
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo [OK] Python: %%i

REM --- Find Claude Code skills directory ---
REM Try user-level skills first, then project-level
set "USER_SKILLS=%USERPROFILE%\.claude\skills"
echo [INFO] Skills target: %USER_SKILLS%

if not exist "%USER_SKILLS%" (
    echo [INFO] Creating directory...
    mkdir "%USER_SKILLS%" 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Cannot create %USER_SKILLS%
        pause
        exit /b 1
    )
)

REM --- Locate source files ---
set "SRC_SKILLS=%SCRIPT_DIR%\.claude\skills"
echo [INFO] Source skills: %SRC_SKILLS%

if not exist "%SRC_SKILLS%\init-wordlist.md" (
    echo [ERROR] Source skill not found: init-wordlist.md
    echo         Make sure you run this from the zh/ directory.
    pause
    exit /b 1
)

REM --- Copy skills (must be DIR/SKILL.md for Claude Code) ---
echo.
echo [INSTALL] Installing skills...

mkdir "%USER_SKILLS%\init-wordlist" 2>nul
copy /Y "%SRC_SKILLS%\init-wordlist.md" "%USER_SKILLS%\init-wordlist\SKILL.md" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] init-wordlist
) else (
    echo   [FAIL] init-wordlist - copy failed
    set "HAD_ERROR=1"
)

mkdir "%USER_SKILLS%\generate-article" 2>nul
copy /Y "%SRC_SKILLS%\generate-article.md" "%USER_SKILLS%\generate-article\SKILL.md" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] generate-article
) else (
    echo   [FAIL] generate-article - copy failed
    set "HAD_ERROR=1"
)

REM --- Verify ---
echo.
echo [VERIFY] Checking installation...

set "ERRORS=0"

if exist "%USER_SKILLS%\init-wordlist\SKILL.md" (
    echo   [OK] init-wordlist
) else (
    echo   [FAIL] init-wordlist not installed
    set /a ERRORS+=1
)

if exist "%USER_SKILLS%\generate-article\SKILL.md" (
    echo   [OK] generate-article
) else (
    echo   [FAIL] generate-article not installed
    set /a ERRORS+=1
)

REM --- Result ---
echo.
if "%ERRORS%"=="0" (
    echo ============================================
    echo   Installation SUCCESSFUL!
    echo ============================================
    echo.
    echo   Skills are now available in Claude Code:
    echo     /init-wordlist   - Initialize word list
    echo     /generate-article - Generate memory article
    echo.
    echo   Next: double-click serve.bat to start
    echo         then use the web tool to triage words.
) else (
    echo ============================================
    echo   Installation FAILED - %ERRORS% error(s)
    echo ============================================
    echo   Check the [FAIL] lines above.
)

pause
