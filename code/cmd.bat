@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo PDF Grammar Extraction Tool
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Install pdfplumber if not already installed
echo Checking dependencies...
python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 (
    echo Installing pdfplumber...
    pip install pdfplumber >nul 2>&1
    if errorlevel 1 (
        echo Error: Failed to install pdfplumber
        echo Please run: pip install pdfplumber
        pause
        exit /b 1
    )
)

REM Run the extraction script
echo Starting extraction...
echo.
cd /d "%~dp0code"
python extract_grammar.py
set exit_code=%errorlevel%

echo.
echo ========================================
if %exit_code% equ 0 (
    echo Completed successfully!
) else (
    echo Completed with errors. Check logs/run_*.log for details.
)
echo ========================================
echo.
pause
exit /b %exit_code%
