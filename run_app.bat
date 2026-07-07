@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul
cd /d "%~dp0"
if not exist "logs" mkdir "logs"

if /I "%~1"=="--check" goto :CHECK

if not exist ".venv\Scripts\python.exe" (
    echo Local environment not found. Running installer first...
    call install_env.bat
    if errorlevel 1 exit /b 1
)

set "PY=.venv\Scripts\python.exe"
"%PY%" -c "import streamlit; import app" > "logs\run_app_check.log" 2>&1
if errorlevel 1 (
    echo App check failed. Re-running installer may fix missing packages.
    echo See logs\run_app_check.log
    pause
    exit /b 1
)

start "" http://localhost:8501
"%PY%" -m streamlit run app.py
if errorlevel 1 (
    echo Streamlit exited with an error.
    pause
    exit /b 1
)
exit /b 0

:CHECK
echo run_app.bat syntax/check mode OK.
exit /b 0
