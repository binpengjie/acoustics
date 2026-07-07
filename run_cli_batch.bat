@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul
cd /d "%~dp0"

if /I "%~1"=="--help" goto :HELP

if "%~1"=="" goto :HELP
if "%~2"=="" goto :HELP

if not exist ".venv\Scripts\python.exe" (
    echo Missing .venv. Please run install_env.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m src.batch_inference --input "%~1" --output "%~2" --mode fusion
if errorlevel 1 (
    echo Batch inference failed.
    pause
    exit /b 1
)
pause
exit /b 0

:HELP
echo Usage:
echo   run_cli_batch.bat C:\audio_batch C:\results\batch_results.csv
echo.
echo Advanced direct command:
echo   .venv\Scripts\python.exe -m src.batch_inference --input "C:\audio_batch" --output "C:\results\results.csv" --mode fusion
echo.
echo Modes: fusion, lineB_only, lineA_only, conservative
exit /b 0
