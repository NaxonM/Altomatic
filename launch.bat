@echo off
setlocal ENABLEDELAYEDEXPANSION

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "APP_EXIT_CODE=1"
set "REQ_HASH_FILE=%VENV_DIR%\requirements.sha256"
set "PACKAGE_SENTINEL=%VENV_DIR%\altomatic.editable"
set "PIP_SENTINEL=%VENV_DIR%\pip.upgraded"

set "PY_CMD="
for %%P in (python python3 py) do (
    where %%P >NUL 2>&1
    if not errorlevel 1 (
        set "PY_CMD=%%P"
        goto :FOUND_PY
    )
)

echo No suitable Python interpreter found on PATH.
echo Please install Python 3 and rerun this script.
goto :CLEAN_EXIT

:FOUND_PY
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo Using existing virtual environment at "%VENV_DIR%"
) else (
    echo Creating virtual environment...
    if /I "!PY_CMD!"=="py" (
        py -m venv "%VENV_DIR%"
    ) else (
        "!PY_CMD!" -m venv "%VENV_DIR%"
    )
    if errorlevel 1 (
        echo Failed to create virtual environment.
        goto :CLEAN_EXIT
    )
)

if exist "%PIP_SENTINEL%" (
    echo Pip already upgraded for this environment. Skipping upgrade.
) else (
    echo Upgrading pip...
    "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >NUL
    if errorlevel 1 (
        echo Failed to upgrade pip.
        goto :CLEAN_EXIT
    )
    >"%PIP_SENTINEL%" echo upgraded
)

set "CURRENT_REQ_HASH="
for /f "tokens=1" %%H in ('certutil -hashfile "%SCRIPT_DIR%requirements.txt" SHA256 ^| findstr /R "^[0-9A-F]"') do (
    if not defined CURRENT_REQ_HASH set "CURRENT_REQ_HASH=%%H"
)

set "SKIP_DEP_INSTALL=0"
if defined CURRENT_REQ_HASH if exist "%REQ_HASH_FILE%" (
    set /p "SAVED_REQ_HASH=" < "%REQ_HASH_FILE%"
    if /I "!SAVED_REQ_HASH!"=="!CURRENT_REQ_HASH!" set "SKIP_DEP_INSTALL=1"
)

if "!SKIP_DEP_INSTALL!"=="1" (
    echo Requirements unchanged. Skipping dependency installation.
) else (
    echo Installing dependencies...
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%SCRIPT_DIR%requirements.txt"
    if errorlevel 1 (
        echo Failed to install requirements.
        goto :CLEAN_EXIT
    )
    if defined CURRENT_REQ_HASH >"%REQ_HASH_FILE%" echo !CURRENT_REQ_HASH!
)

if exist "%PACKAGE_SENTINEL%" (
    echo Altomatic already installed in editable mode. Skipping reinstall.
) else (
    echo Installing Altomatic in editable mode...
    "%VENV_DIR%\Scripts\python.exe" -m pip install -e "%SCRIPT_DIR%."
    if errorlevel 1 (
        echo Failed to install the Altomatic package.
        goto :CLEAN_EXIT
    )
    >"%PACKAGE_SENTINEL%" echo installed
)

echo Checking for Tesseract OCR...
set "TESSERACT_DIR="
if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" set "TESSERACT_DIR=%ProgramFiles%\Tesseract-OCR"
if not defined TESSERACT_DIR if exist "%ProgramFiles(x86)%\Tesseract-OCR\tesseract.exe" set "TESSERACT_DIR=%ProgramFiles(x86)%\Tesseract-OCR"

if not defined TESSERACT_DIR (
    for /f "delims=" %%I in ('where tesseract 2^>NUL') do (
        if not defined TESSERACT_DIR set "TESSERACT_DIR=%%~dpI"
    )
)

if defined TESSERACT_DIR (
    set "PATH=%TESSERACT_DIR%;%PATH%"
    echo Tesseract detected at "%TESSERACT_DIR%".
) else (
    echo Tesseract not found. Attempting installation via winget...
    where winget >NUL 2>&1
    if errorlevel 1 (
        echo winget is not available. Please install Tesseract manually from https://github.com/UB-Mannheim/tesseract/wiki.
    ) else (
        winget install --id UB-Mannheim.TesseractOCR -e --silent --accept-package-agreements --accept-source-agreements
        if errorlevel 1 (
            echo winget could not install Tesseract. Please install it manually.
        ) else (
            if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" set "TESSERACT_DIR=%ProgramFiles%\Tesseract-OCR"
            if not defined TESSERACT_DIR if exist "%ProgramFiles(x86)%\Tesseract-OCR\tesseract.exe" set "TESSERACT_DIR=%ProgramFiles(x86)%\Tesseract-OCR"
            if defined TESSERACT_DIR (
                set "PATH=%TESSERACT_DIR%;%PATH%"
                echo Tesseract installed via winget and added to PATH.
            ) else (
                echo Tesseract installed via winget.
            )
        )
    )
)

echo Launching Altomatic...
"%VENV_DIR%\Scripts\python.exe" -m altomatic
set "APP_EXIT_CODE=%errorlevel%"

if %APP_EXIT_CODE% neq 0 (
    echo Altomatic exited with code %APP_EXIT_CODE%.
) else (
    echo Altomatic closed successfully.
)
:CLEAN_EXIT
if "%~1"=="--no-pause" (
    endlocal & exit /b %APP_EXIT_CODE%
) else (
    echo.
    pause
    endlocal & exit /b %APP_EXIT_CODE%
)
