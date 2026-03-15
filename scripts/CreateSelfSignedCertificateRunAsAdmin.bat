@echo off
set PWSH="C:\Program Files\PowerShell\7\pwsh.exe"
set CERTNAME="SharePoint-GPT-Crawler"
set STARTDATE="2025-01-01"
set ENDDATE="2030-01-01"

if not exist %PWSH% (
    echo ERROR: PowerShell 7 not found at '%PWSH%'
    echo Please install PowerShell 7 from: https://github.com/PowerShell/PowerShell/releases
    pause
    exit /b 1
)

echo This will create a self-signed certificate for SharePoint app-only authentication
echo See: https://learn.microsoft.com/en-us/sharepoint/dev/solution-guidance/security-apponly-azuread
echo Certificate Name: %CERTNAME% Valid From: %STARTDATE% Valid To: %ENDDATE%
echo.
echo After the certificate has been created (PFX and CER files):
echo.
echo 1) Copy the PFX file to
echo   Option A) Local Dev Computer: Your path specified in the .env file LOCAL_PERSISTENT_STORAGE_PATH
echo   Option B) Azure App Service: /home/data folder by
echo          B.1) creating a .zip file with the pfx file in the src/.unzip_to_persistant_storage_overwrite folder
echo          B.2) and deploying the app to Azure using DeployAzureAppService.bat
echo.
echo 2) Upload the CER file to your Azure App Registration - Certificates and secrets
echo.
pause

rem change to folder where BAT file is
cd /d "%~dp0"
set SCRIPT=%~dp0CreateSelfSignedCertificate.ps1

rem unblock the PowerShell script first
%PWSH% -Command "Unblock-File -Path %SCRIPT%"

rem now run the script with PowerShell 7 as Administrator
rem -Force will overwrite any existing certificate with the same name
%PWSH% -f %SCRIPT% -CommonName %CERTNAME% -StartDate %STARTDATE% -EndDate %ENDDATE% -Force

pause