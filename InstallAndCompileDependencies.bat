@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Determine paths (root script)
set SCRIPT_DIR=%~dp0
set SRC_DIR=%SCRIPT_DIR%src
set VENV_DIR=%SCRIPT_DIR%.venv
set VENV_PY=%VENV_DIR%\Scripts\python.exe
set VENV_UV=%VENV_DIR%\Scripts\uv.exe

echo ==================================================
echo SharePoint-GPT-Middleware - Install Dependencies
echo Root dir : %SCRIPT_DIR%
echo Src dir  : %SRC_DIR%
echo Venv dir : %VENV_DIR%
echo Py dir   : %VENV_PY%
echo UV dir   : %VENV_UV%
echo ==================================================

REM Ensure virtual environment exists (prefer Python 3.12, fallback to 3.13)
if exist "%VENV_PY%" (
  echo [OK] Virtual environment already exists.
) else (
  echo [INFO] Creating virtual environment...
  where py >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python launcher 'py' not found. Install Python 3.12+ from https://www.python.org/downloads/windows/
    pause
    exit /b 1
  )
  py -3.12 -m venv "%VENV_DIR%" 2>nul
  if errorlevel 1 (
    echo [WARN] Python 3.12 not available via 'py'. Trying 3.13...
    py -3.13 -m venv "%VENV_DIR%"
    if errorlevel 1 (
      echo [ERROR] Failed to create virtual environment with Python 3.12 or 3.13.
      pause
      exit /b 1
    )
  )
  echo [OK] Virtual environment created at %VENV_DIR%.
)

REM Upgrade pip inside venv
"%VENV_PY%" -m pip install -U pip >nul
if errorlevel 1 (
  echo [ERROR] Failed to upgrade pip in the virtual environment.
  pause
  exit /b 1
)

REM Ensure 'uv' is installed in the venv
if exist "%VENV_UV%" (
  echo [OK] uv is already installed in the venv.
) else (
  echo [INFO] Installing uv into the venv...
  "%VENV_PY%" -m pip install uv >nul
  if errorlevel 1 (
    echo [ERROR] Failed to install 'uv' in the virtual environment.
    pause
    exit /b 1
  )
)

REM Sync/install project dependencies from src/pyproject.toml using uv
pushd "%SRC_DIR%" >nul
"%VENV_UV%" pip install -e .[dev]
if errorlevel 1 (
  echo [WARN] Dependency installation failed via 'uv'. Trying 'uv --native-tls'...
  "%VENV_UV%" --native-tls pip install -e .[dev]
  if errorlevel 1 (
    echo [ERROR] Dependency installation failed via 'uv'.
    popd >nul
    pause
    exit /b 1
  )
)
popd >nul

REM ---------------------------------------------------------------------------
REM Compile/export dependencies into a requirements.txt for Azure deployment
REM First, prefer a resolver-based export from pyproject.toml using uv pip compile
REM If not available, fall back to freezing the current environment
echo [INFO] Generating requirements.txt at repo root...
"%VENV_UV%" pip compile "%SRC_DIR%\pyproject.toml" -o "%SCRIPT_DIR%requirements.txt" >nul 2>nul
if errorlevel 1 (
  echo [WARN] 'uv pip compile' failed or not supported. Falling back to 'pip freeze'.
  "%VENV_UV%" pip freeze > "%SCRIPT_DIR%requirements.txt"
  if errorlevel 1 (
    echo [ERROR] Failed to generate requirements.txt via pip freeze.
    pause
    exit /b 1
  ) else (
    echo [OK] requirements.txt generated via pip freeze.
    copy /Y "%SCRIPT_DIR%requirements.txt" "%SRC_DIR%\requirements.txt" >nul
    if errorlevel 1 (
      echo [WARN] Failed to copy requirements.txt into src folder.
    ) else (
      echo [OK] requirements.txt also written to src\requirements.txt.
    )
  )
) else (
  echo [OK] requirements.txt generated via 'uv pip compile'.
  copy /Y "%SCRIPT_DIR%requirements.txt" "%SRC_DIR%\requirements.txt" >nul
  if errorlevel 1 (
    echo [WARN] Failed to copy requirements.txt into src folder.
  ) else (
    echo [OK] requirements.txt also written to src\requirements.txt.
  )
)

echo [DONE] Dependencies installed. Activate the venv with:
echo   %VENV_DIR%\Scripts\activate

echo To run the dev server:
echo   %VENV_DIR%\Scripts\python -m uvicorn app:app --app-dir "%SRC_DIR%" --reload --host 127.0.0.1 --port 8000

pause
exit /b 0
