@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul
cd /d "%~dp0"

echo ============================================================
echo  Acoustic OK/NG Inspector Environment Check
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [FAILED] .venv not found. Please run install_env.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" --version
".venv\Scripts\python.exe" -c "import sys; print(sys.executable)"

echo.
echo Checking packages and models...
".venv\Scripts\python.exe" -c "import streamlit, numpy, pandas, scipy, sklearn, joblib, matplotlib, pywt; print('packages OK'); from src.lineA_mahalanobis import LineAMahalanobis; from src.lineB_classifier import LineBClassifier; a=LineAMahalanobis(); b=LineBClassifier(); print('Line A threshold=', a.threshold); print('Line B threshold=', b.threshold); print('models OK')"
if errorlevel 1 (
    echo [FAILED] Environment check failed.
    pause
    exit /b 1
)

echo.
echo [OK] Environment is ready. Run run_app.bat.
pause
exit /b 0
