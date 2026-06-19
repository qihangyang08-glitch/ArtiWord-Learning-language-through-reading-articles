@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   Word-Lerning (English) - One-Click Install
echo ============================================
echo.

REM --- Detect script directory ---
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

REM --- Check / run language configuration ---
echo.
echo [CONFIG] Checking language setup...

if not exist "%SCRIPT_DIR%\config.json" (
    echo   [WARN] No config.json found. Running configure.py...
    echo.
    python "%SCRIPT_DIR%\configure.py"
    if %errorlevel% neq 0 (
        echo   [ERROR] configure.py failed. Run it manually:
        echo          cd en ^&^& python configure.py
        pause
        exit /b 1
    )
)

if not exist "%SRC_SKILLS%\init-wordlist.md" (
    echo   [INFO] Generating skill files from templates...
    python "%SCRIPT_DIR%\configure.py"
)

REM Verify skills exist now
if not exist "%SRC_SKILLS%\init-wordlist.md" (
    echo   [ERROR] Skill files not found after configure. Aborting.
    pause
    exit /b 1
)
echo   [OK] Skills ready (%SCRIPT_DIR%\.claude\skills\)

REM --- Copy skills ---
echo.
echo [INSTALL] Copying skills...

mkdir "%USER_SKILLS%\init-wordlist" 2>nul
copy /Y "%SRC_SKILLS%\init-wordlist.md" "%USER_SKILLS%\init-wordlist\SKILL.md" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] init-wordlist
) else (
    echo   [FAIL] init-wordlist - copy failed
)

mkdir "%USER_SKILLS%\generate-article" 2>nul
copy /Y "%SRC_SKILLS%\generate-article.md" "%USER_SKILLS%\generate-article\SKILL.md" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] generate-article
) else (
    echo   [FAIL] generate-article - copy failed
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
    echo   Language: see config.json
    echo   Run 'python configure.py' to change languages.
    echo.
    echo   Skills available in Claude Code:
    echo     /init-wordlist   - Initialize word list
    echo     /generate-article - Generate memory article
    echo.
    echo   Next: double-click serve.bat to start
) else (
    echo ============================================
    echo   Installation FAILED - %ERRORS% error(s)
    echo ============================================
)

pause
