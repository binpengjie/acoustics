@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo Building OKNG_Inspector Windows portable onedir package
echo ============================================================
echo.

echo This build computer needs Python. End-user computers do NOT need Python after the build.
echo.

set "PY_CMD="
python --version >nul 2>&1
if not errorlevel 1 set "PY_CMD=python"

if "%PY_CMD%"=="" (
  py -3 --version >nul 2>&1
  if not errorlevel 1 set "PY_CMD=py -3"
)

if "%PY_CMD%"=="" (
  echo ERROR: Python was not found on this build computer.
  echo.
  echo Install 64-bit Python 3.11 from:
  echo https://www.python.org/downloads/windows/
  echo.
  echo During installation, check: Add python.exe to PATH
  echo.
  echo If Windows opens Microsoft Store instead, disable these aliases:
  echo Settings ^> Apps ^> Advanced app settings ^> App execution aliases
  echo Turn off: python.exe and python3.exe
  echo.
  pause
  exit /b 1
)

echo Using Python command: %PY_CMD%
%PY_CMD% -m venv .venv
if errorlevel 1 (
  echo ERROR: Failed to create .venv. Make sure Python venv support is installed.
  pause
  exit /b 1
)

set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto build_failed
"%PYTHON_EXE%" -m pip install -r requirements_windows.txt
if errorlevel 1 goto build_failed

if exist build\pyinstaller rmdir /s /q build\pyinstaller
if exist dist\OKNG_Inspector rmdir /s /q dist\OKNG_Inspector
if exist dist\OKNG_Inspector_Windows rmdir /s /q dist\OKNG_Inspector_Windows

"%PYTHON_EXE%" -m PyInstaller --noconfirm --onedir --console --name OKNG_Inspector --distpath dist --workpath build\pyinstaller ^
  --collect-all streamlit --collect-all sklearn --collect-all scipy --collect-all pywt ^
  --collect-all numpy --collect-all pandas --collect-all matplotlib --collect-all joblib ^
  launcher.py
if errorlevel 1 goto build_failed

ren dist\OKNG_Inspector OKNG_Inspector_Windows

REM Keep app source/config/model files visible beside the EXE. This makes the folder portable and easy to inspect/update.
copy app.py dist\OKNG_Inspector_Windows\app.py >nul
copy batch_predict.py dist\OKNG_Inspector_Windows\batch_predict.py >nul
copy generate_html_report.py dist\OKNG_Inspector_Windows\generate_html_report.py >nul
xcopy /E /I /Y src dist\OKNG_Inspector_Windows\src >nul
xcopy /E /I /Y models dist\OKNG_Inspector_Windows\models >nul
xcopy /E /I /Y configs dist\OKNG_Inspector_Windows\configs >nul
xcopy /E /I /Y assets dist\OKNG_Inspector_Windows\assets >nul
if not exist dist\OKNG_Inspector_Windows\outputs mkdir dist\OKNG_Inspector_Windows\outputs
if not exist dist\OKNG_Inspector_Windows\outputs\diagnostics mkdir dist\OKNG_Inspector_Windows\outputs\diagnostics
if not exist dist\OKNG_Inspector_Windows\outputs\reports mkdir dist\OKNG_Inspector_Windows\outputs\reports
copy README_WINDOWS_USER.md dist\OKNG_Inspector_Windows\README_WINDOWS_USER.md >nul
copy README_ENGINEER.md dist\OKNG_Inspector_Windows\README_ENGINEER.md >nul
copy run_local_webapp.bat dist\OKNG_Inspector_Windows\run_local_webapp.bat >nul

echo.
echo Build complete.
echo Portable folder: dist\OKNG_Inspector_Windows
echo Main executable: dist\OKNG_Inspector_Windows\OKNG_Inspector.exe
echo.
echo End users can copy/unzip this folder and double-click OKNG_Inspector.exe.
echo To uninstall/delete: close the app, then delete the whole OKNG_Inspector_Windows folder.
echo.

echo Creating zip package...
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path distOKNG_Inspector_Windows_v0.1.zip) { Remove-Item distOKNG_Inspector_Windows_v0.1.zip -Force }; Compress-Archive -Path distOKNG_Inspector_Windows -DestinationPath distOKNG_Inspector_Windows_v0.1.zip -Force"
if errorlevel 1 (
  echo Zip creation failed, but the portable folder was built.
) else (
  echo Zip package: dist\OKNG_Inspector_Windows_v0.1.zip
)

pause
exit /b 0

:build_failed
echo.
echo Build failed.
echo Check the error above. Common causes: no internet for pip install, antivirus blocking files, or incompatible Python version.
pause
exit /b 1
