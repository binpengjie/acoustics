@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo Building OKNG_Inspector Windows portable onedir package
echo ============================================================
echo.
echo This build computer needs Python. End-user computers do NOT need Python after the build.
echo.

set "PIP_CACHE_DIR=%CD%\.pip_cache"
set "TMP=%CD%\tmp"
set "TEMP=%CD%\tmp"
set "PYINSTALLER_CONFIG_DIR=%CD%\.pyinstaller_config"
if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%"
if not exist "%TMP%" mkdir "%TMP%"
if not exist "%PYINSTALLER_CONFIG_DIR%" mkdir "%PYINSTALLER_CONFIG_DIR%"

set "PY_CMD="
python --version >nul 2>&1
if not errorlevel 1 set "PY_CMD=python"

if "%PY_CMD%"=="" (
  py -3.11 --version >nul 2>&1
  if not errorlevel 1 set "PY_CMD=py -3.11"
)

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
  call :maybe_pause
  exit /b 1
)

echo Using Python command: %PY_CMD%
%PY_CMD% -c "import sys; print('Python executable:', sys.executable); print('Python version:', sys.version)"
if errorlevel 1 (
  echo ERROR: Python diagnostic command failed.
  call :maybe_pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  %PY_CMD% -m venv .venv
  if errorlevel 1 (
    echo ERROR: Failed to create .venv. Make sure Python venv support is installed.
    call :maybe_pause
    exit /b 1
  )
)

set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
  echo ERROR: Virtual environment Python was not found at %PYTHON_EXE%
  call :maybe_pause
  exit /b 1
)

"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto build_failed
"%PYTHON_EXE%" -m pip install -r requirements_windows.txt
if errorlevel 1 goto build_failed

if exist build\pyinstaller rmdir /s /q build\pyinstaller
if errorlevel 1 goto build_failed
if exist dist\OKNG_Inspector rmdir /s /q dist\OKNG_Inspector
if errorlevel 1 goto build_failed
if exist dist\OKNG_Inspector_Windows rmdir /s /q dist\OKNG_Inspector_Windows
if errorlevel 1 goto build_failed
if exist dist\OKNG_Inspector_Windows_v0.1.zip del /f /q dist\OKNG_Inspector_Windows_v0.1.zip
if errorlevel 1 goto build_failed

"%PYTHON_EXE%" -m PyInstaller --noconfirm --onedir --console --name OKNG_Inspector --distpath dist --workpath build\pyinstaller ^
  --collect-all streamlit --collect-all sklearn --collect-all scipy --collect-all pywt ^
  --collect-all numpy --collect-all pandas --collect-all matplotlib --collect-all joblib ^
  launcher.py
if errorlevel 1 goto build_failed

if not exist dist\OKNG_Inspector\OKNG_Inspector.exe (
  echo ERROR: PyInstaller did not create dist\OKNG_Inspector\OKNG_Inspector.exe
  goto build_failed
)

ren dist\OKNG_Inspector OKNG_Inspector_Windows
if errorlevel 1 goto build_failed

REM Keep app source/config/model files visible beside the EXE. This makes the folder portable and easy to inspect/update.
copy app.py dist\OKNG_Inspector_Windows\app.py >nul
if errorlevel 1 goto build_failed
copy batch_predict.py dist\OKNG_Inspector_Windows\batch_predict.py >nul
if errorlevel 1 goto build_failed
copy generate_html_report.py dist\OKNG_Inspector_Windows\generate_html_report.py >nul
if errorlevel 1 goto build_failed
xcopy /E /I /Y src dist\OKNG_Inspector_Windows\src >nul
if errorlevel 1 goto build_failed
xcopy /E /I /Y models dist\OKNG_Inspector_Windows\models >nul
if errorlevel 1 goto build_failed
xcopy /E /I /Y configs dist\OKNG_Inspector_Windows\configs >nul
if errorlevel 1 goto build_failed
xcopy /E /I /Y assets dist\OKNG_Inspector_Windows\assets >nul
if errorlevel 1 goto build_failed
if not exist dist\OKNG_Inspector_Windows\outputs mkdir dist\OKNG_Inspector_Windows\outputs
if errorlevel 1 goto build_failed
if not exist dist\OKNG_Inspector_Windows\outputs\diagnostics mkdir dist\OKNG_Inspector_Windows\outputs\diagnostics
if errorlevel 1 goto build_failed
if not exist dist\OKNG_Inspector_Windows\outputs\reports mkdir dist\OKNG_Inspector_Windows\outputs\reports
if errorlevel 1 goto build_failed
copy README_WINDOWS_USER.md dist\OKNG_Inspector_Windows\README_WINDOWS_USER.md >nul
if errorlevel 1 goto build_failed
copy README_ENGINEER.md dist\OKNG_Inspector_Windows\README_ENGINEER.md >nul
if errorlevel 1 goto build_failed
copy run_local_webapp.bat dist\OKNG_Inspector_Windows\run_local_webapp.bat >nul
if errorlevel 1 goto build_failed

echo.
echo Creating zip package...
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path 'dist\OKNG_Inspector_Windows_v0.1.zip') { Remove-Item 'dist\OKNG_Inspector_Windows_v0.1.zip' -Force }; Compress-Archive -Path 'dist\OKNG_Inspector_Windows' -DestinationPath 'dist\OKNG_Inspector_Windows_v0.1.zip' -Force"
if errorlevel 1 goto build_failed

echo.
echo Verifying build outputs...
if exist dist\OKNG_Inspector_Windows\OKNG_Inspector.exe (
  echo OK: dist\OKNG_Inspector_Windows\OKNG_Inspector.exe exists
) else (
  echo ERROR: dist\OKNG_Inspector_Windows\OKNG_Inspector.exe is missing
  goto build_failed
)

if exist dist\OKNG_Inspector_Windows_v0.1.zip (
  echo OK: dist\OKNG_Inspector_Windows_v0.1.zip exists
  for %%A in (dist\OKNG_Inspector_Windows_v0.1.zip) do echo Zip size bytes: %%~zA
) else (
  echo ERROR: dist\OKNG_Inspector_Windows_v0.1.zip is missing
  goto build_failed
)

echo.
echo Build complete.
echo Portable folder: dist\OKNG_Inspector_Windows
echo Main executable: dist\OKNG_Inspector_Windows\OKNG_Inspector.exe
echo Zip package: dist\OKNG_Inspector_Windows_v0.1.zip
echo.
echo End users can copy/unzip this folder and double-click OKNG_Inspector.exe.
echo To uninstall/delete: close the app, then delete the whole OKNG_Inspector_Windows folder.
echo.

call :maybe_pause
exit /b 0

:build_failed
echo.
echo Build failed.
echo Check the error above. Common causes: no internet for pip install, antivirus blocking files, or incompatible Python version.
call :maybe_pause
exit /b 1

:maybe_pause
if /I not "%GITHUB_ACTIONS%"=="true" pause
exit /b 0
