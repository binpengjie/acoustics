@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul
cd /d "%~dp0"

if /I "%~1"=="--help" goto :HELP

if not exist "logs" mkdir "logs"
set "LOG=logs\install_env.log"
echo [%DATE% %TIME%] OKNG installer started > "%LOG%"

echo.
echo ============================================================
echo  Acoustic OK/NG Inspector - Windows local installer
echo ============================================================
echo.
echo This installer will:
echo   1. Find Python 3.10 or 3.11
echo   2. Create .venv if needed
echo   3. Install requirements.txt
echo   4. Verify model imports
echo.
echo Detailed log: %CD%\%LOG%
echo.

call :FIND_PYTHON
if not defined PYTHON_CMD (
    call :TRY_WINGET
    call :FIND_PYTHON
)

if not defined PYTHON_CMD goto :NO_PYTHON

echo Found Python command: %PYTHON_CMD%
echo [%DATE% %TIME%] Found Python command: %PYTHON_CMD% >> "%LOG%"

if exist ".venv\Scripts\python.exe" (
    echo Existing .venv found. Reusing it.
) else (
    echo Creating local virtual environment: .venv
    %PYTHON_CMD% -m venv .venv >> "%LOG%" 2>&1
    if errorlevel 1 goto :VENV_FAILED
)

set "VENV_PY=%CD%\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" goto :VENV_FAILED

echo Ensuring pip is available...
"%VENV_PY%" -m ensurepip --upgrade >> "%LOG%" 2>&1

echo Upgrading pip tools if possible...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel >> "%LOG%" 2>&1

echo Installing Python packages...
if exist "wheelhouse" (
    echo Using offline wheelhouse folder.
    "%VENV_PY%" -m pip install --no-index --find-links "wheelhouse" -r requirements.txt >> "%LOG%" 2>&1
) else (
    "%VENV_PY%" -m pip install -r requirements.txt >> "%LOG%" 2>&1
)
if errorlevel 1 goto :PIP_FAILED

echo Verifying installation...
"%VENV_PY%" -c "import streamlit, numpy, pandas, scipy, sklearn, joblib, matplotlib, pywt; from src.lineA_mahalanobis import LineAMahalanobis; from src.lineB_classifier import LineBClassifier; LineAMahalanobis(); LineBClassifier(); print('OK')" >> "%LOG%" 2>&1
if errorlevel 1 goto :VERIFY_FAILED

echo.
echo ============================================================
echo  Installation finished successfully.
echo  Next step: double-click run_app.bat
echo ============================================================
echo.
pause
exit /b 0

:FIND_PYTHON
set "PYTHON_CMD="

if defined OKNG_PYTHON (
    set "CAND="%OKNG_PYTHON%""
    call :CHECK_CANDIDATE
    if defined PYTHON_CMD exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
    set "CAND=py -3.11"
    call :CHECK_CANDIDATE
    if defined PYTHON_CMD exit /b 0
    set "CAND=py -3.10"
    call :CHECK_CANDIDATE
    if defined PYTHON_CMD exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    set "CAND=python"
    call :CHECK_CANDIDATE
    if defined PYTHON_CMD exit /b 0
)

where python3 >nul 2>nul
if not errorlevel 1 (
    set "CAND=python3"
    call :CHECK_CANDIDATE
    if defined PYTHON_CMD exit /b 0
)

for %%P in (
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\Python310\python.exe"
    "C:\Program Files (x86)\Python311-32\python.exe"
    "C:\Program Files (x86)\Python310-32\python.exe"
) do (
    if exist "%%~P" (
        set "CAND="%%~P""
        call :CHECK_CANDIDATE
        if defined PYTHON_CMD exit /b 0
    )
)
exit /b 0

:CHECK_CANDIDATE
if defined PYTHON_CMD exit /b 0
%CAND% -c "import sys, venv; ok=sys.version_info[:2] in [(3,10),(3,11)]; print(sys.executable); print('%d.%d' % sys.version_info[:2]); raise SystemExit(0 if ok else 7)" > "%TEMP%\okng_python_check.txt" 2>> "%LOG%"
if errorlevel 1 exit /b 0
set "PYTHON_CMD=%CAND%"
type "%TEMP%\okng_python_check.txt" >> "%LOG%" 2>nul
exit /b 0

:TRY_WINGET
if /I "%OKNG_NO_WINGET%"=="1" exit /b 0
where winget >nul 2>nul
if errorlevel 1 exit /b 0
echo Python 3.10/3.11 not found. Trying winget user-scope install of Python 3.11...
echo [%DATE% %TIME%] Trying winget install Python 3.11 >> "%LOG%"
winget install -e --id Python.Python.3.11 --scope user --accept-package-agreements --accept-source-agreements >> "%LOG%" 2>&1
exit /b 0

:NO_PYTHON
echo.
echo ============================================================
echo  Python 3.10/3.11 was not found.
echo ============================================================
echo.
echo The earlier error "'py' is not recognized" means Python Launcher is not installed.
echo This installer also checked python, python3, common install folders, and winget.
echo.
echo Please install Python 3.11 for Windows:
echo   https://www.python.org/downloads/release/python-3119/
echo.
echo During installation, check:
echo   [x] Add python.exe to PATH
echo   [x] pip
echo   [x] py launcher  (optional but recommended)
echo.
echo If Python is installed in a custom path, run:
echo   set OKNG_PYTHON=C:\Path\To\python.exe
echo   install_env.bat
echo.
echo See log: %CD%\%LOG%
pause
exit /b 1

:VENV_FAILED
echo.
echo Failed to create .venv. Please check Python permissions and disk space.
echo See log: %CD%\%LOG%
pause
exit /b 1

:PIP_FAILED
echo.
echo Package installation failed.
echo Common causes:
echo   - No internet
echo   - Company proxy/firewall
echo   - Python version is not 3.10/3.11
echo.
echo Offline option:
echo   Put pre-downloaded .whl files in a folder named wheelhouse, then run install_env.bat again.
echo.
echo See log: %CD%\%LOG%
pause
exit /b 1

:VERIFY_FAILED
echo.
echo Packages installed, but model/app verification failed.
echo Please check that the models folder is complete.
echo See log: %CD%\%LOG%
pause
exit /b 1

:HELP
echo Acoustic OK/NG Inspector installer
echo.
echo Usage:
echo   install_env.bat
echo.
echo Optional:
echo   set OKNG_PYTHON=C:\Path\To\python.exe
echo   install_env.bat
echo.
echo Offline wheels:
echo   Put .whl files in .\wheelhouse and run install_env.bat.
exit /b 0
