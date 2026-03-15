@echo off
set PWSH="C:\Program Files\PowerShell\7\pwsh.exe"

rem Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ================================================================================
    echo   WARNING: This script requires Administrator privileges
    echo ================================================================================
    echo.
    echo Please right-click this batch file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

if not exist %PWSH% (
    echo ERROR: PowerShell 7 not found at '%PWSH%'
    echo Please install PowerShell 7 from: https://github.com/PowerShell/PowerShell/releases
    pause
    exit /b 1
)

rem change to folder where BAT file is
cd /d "%~dp0"
set SCRIPT=%~dp0AddRemoveComputerAsArcEnabledServer.ps1

rem unblock the PowerShell script first
%PWSH% -Command "Unblock-File -Path %SCRIPT%"

rem now run the script with PowerShell 7
%PWSH% -f %SCRIPT%
pause
