@echo off
REM ==============================================================================
REM SIP & Fintech Investor Discovery Engine — Windows Launch Script
REM ==============================================================================
echo ================================================================================
echo   Starting SIP ^& Fintech Investor Discovery Engine (Windows)
echo ================================================================================

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: python is required but not found in PATH.
    pause
    exit /b 1
)

python run.py

