# INFO: Managed Identity for Private Laptop

**Doc ID**: MGID-IN01
**Goal**: Research how to add a private laptop to Azure Entra ID and assign managed identity
**Strategy**: MEPI (curated options)
**Domain**: SOFTWARE
**Timeline**: Created 2026-03-15

## Summary

- **Managed identities cannot be assigned directly to physical devices** - they are for Azure compute resources only [VERIFIED]
- **Azure Arc is the solution** - onboard laptop as Arc-enabled server to get system-assigned managed identity [VERIFIED]
- **Entra ID device registration (BYOD) does NOT provide managed identity** - only provides device identity for Conditional Access [VERIFIED]
- **Windows 10/11 client OS supported by Azure Arc** - but only for "server-like" scenarios (always on, connected) [VERIFIED]
- **Alternative: Use service principal with certificate** - if Azure Arc is not suitable [VERIFIED]

## Table of Contents

1. [Core Concepts](#1-core-concepts)
2. [Option A: Azure Arc (Recommended)](#2-option-a-azure-arc-recommended)
3. [Option B: Service Principal with Certificate](#3-option-b-service-principal-with-certificate)
4. [What Does NOT Work](#4-what-does-not-work)
5. [Comparison](#5-comparison)
6. [Sources](#6-sources)
7. [Next Steps](#7-next-steps)
8. [Document History](#8-document-history)

## 1. Core Concepts

### 1.1 Managed Identity Definition

A managed identity is an identity that can be assigned to an **Azure compute resource**:
- Azure Virtual Machine
- Azure Virtual Machine Scale Set
- Service Fabric Cluster
- Azure Kubernetes cluster
- App hosting platforms (App Service, Functions, etc.)

Managed identities:
- Eliminate the need to manage credentials
- Use certificate-based authentication internally (90-day expiration, rolled after 45 days)
- Create a service principal in Entra ID
- Cannot be assigned to physical devices directly

### 1.2 Entra ID Device Registration Types

Three types of device states in Entra ID:

- **Entra ID Registered** (BYOD/Workplace joined)
  - For personal devices
  - Local account sign-in + Entra ID account for org resources
  - Used for Conditional Access, NOT for managed identity

- **Entra ID Joined**
  - For organization-owned devices
  - Sign in with Entra ID account
  - Full MDM/Intune management
  - Still no managed identity support

- **Hybrid Entra ID Joined**
  - Joined to on-premises AD and Entra ID
  - For existing AD infrastructure
  - No managed identity support

**Key insight**: None of these device registration types provide managed identity capabilities.

## 2. Option A: Azure Arc (Recommended)

Azure Arc extends Azure management to machines outside Azure, including private laptops.

### 2.1 How It Works

1. Install Azure Connected Machine agent on laptop
2. Agent connects laptop to Azure as "Arc-enabled server"
3. Azure creates a system-assigned managed identity for the server
4. Applications on laptop can request tokens via local IMDS endpoint

### 2.2 Prerequisites

- Azure subscription
- Windows 10/11 (client OS supported for "server-like" scenarios)
- Admin permissions on laptop
- Laptop requirements for "server-like" use:
  - Always connected to internet
  - Connected to power source
  - Powered on most of the time

### 2.3 Installation Steps

1. Go to Azure Portal > Azure Arc > Machines > Add
2. Select "Add a single server" or generate script
3. Download and run `OnboardingScript.ps1` on laptop
4. Agent installs and registers with Azure

PowerShell installation (silent):
```powershell
msiexec.exe /i AzureConnectedMachineAgent.msi /qn /l*v "C:\Support\Logs\Azcmagentsetup.log"
```

### 2.4 Using Managed Identity

After onboarding, applications can acquire tokens via:

```powershell
$apiVersion = "2020-06-01"
$resource = "https://management.azure.com/"
$endpoint = "{0}?resource={1}&api-version={2}" -f $env:IDENTITY_ENDPOINT,$resource,$apiVersion

$secretFile = ""
try {
    Invoke-WebRequest -Method GET -Uri $endpoint -Headers @{Metadata='True'} -UseBasicParsing
} catch {
    $wwwAuthHeader = $_.Exception.Response.Headers["WWW-Authenticate"]
    if ($wwwAuthHeader -match "Basic realm=.+") {
        $secretFile = ($wwwAuthHeader -split "Basic realm=")[1]
    }
}

$secret = cat -Raw $secretFile
$response = Invoke-WebRequest -Method GET -Uri $endpoint -Headers @{Metadata='True'; Authorization="Basic $secret"} -UseBasicParsing
$token = (ConvertFrom-Json -InputObject $response.Content).access_token
```

Environment variables set by agent:
- `IMDS_ENDPOINT`: `http://localhost:40342`
- `IDENTITY_ENDPOINT`: `http://localhost:40342/metadata/identity/oauth2/token`

### 2.5 Granting Permissions

1. Find Arc server in Azure Portal
2. Go to Identity > System assigned
3. Assign Azure RBAC roles to the managed identity

### 2.6 Limitations

- Designed for long-term management (not ephemeral machines)
- Windows client OS: only for "server-like" scenarios
- Agent requires ongoing connectivity for heartbeat
- Cannot use user-assigned managed identities (system-assigned only)

## 3. Option B: Service Principal with Certificate

If Azure Arc is not suitable (e.g., laptop frequently offline), use a service principal.

### 3.1 How It Works

1. Create App Registration in Entra ID
2. Generate certificate (self-signed or CA-issued)
3. Upload certificate public key to App Registration
4. Install certificate on laptop
5. Application authenticates using certificate

### 3.2 Implementation

```powershell
# Authenticate with certificate
$tenantId = "your-tenant-id"
$clientId = "your-app-client-id"
$certThumbprint = "your-cert-thumbprint"

Connect-AzAccount -ServicePrincipal -TenantId $tenantId -ApplicationId $clientId -CertificateThumbprint $certThumbprint
```

### 3.3 Pros and Cons vs Managed Identity

Pros:
- Works offline (certificate stored locally)
- No agent required
- Works on any machine

Cons:
- Must manage certificate lifecycle (rotation, expiration)
- Certificate must be securely stored
- Manual credential management

## 4. What Does NOT Work

### 4.1 Entra ID Device Registration

Registering device via Settings > Accounts > Access work or school > Connect:
- Creates device identity in Entra ID
- Enables Conditional Access policies
- Does NOT provide managed identity
- Does NOT enable token acquisition for Azure resources

### 4.2 Entra ID Join

Joining device to Entra ID:
- Enables cloud-only management
- SSO to cloud resources
- Does NOT provide managed identity capabilities

### 4.3 Intune Enrollment

Enrolling in Microsoft Intune:
- Enables MDM management
- Device compliance
- Does NOT provide managed identity

## 5. Comparison

**Azure Arc (Recommended for your scenario)**
- Identity type: System-assigned managed identity
- Credential management: Automatic (Azure handles rotation)
- Offline support: No (requires connectivity)
- Setup complexity: Medium (install agent)
- Best for: Development machines, always-on scenarios

**Service Principal with Certificate**
- Identity type: Application identity
- Credential management: Manual (must rotate certificates)
- Offline support: Yes
- Setup complexity: Medium (create app, manage cert)
- Best for: Occasional use, offline scenarios

## 6. Sources

**Primary Sources:**

- `MGID-IN01-SC-MSFT-MIOVW`: https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview - Managed identities are for Azure compute resources only [VERIFIED]

- `MGID-IN01-SC-MSFT-DEVREG`: https://learn.microsoft.com/en-us/entra/identity/devices/concept-device-registration - Entra registered devices are for BYOD, not managed identity [VERIFIED]

- `MGID-IN01-SC-MSFT-ARCMI`: https://learn.microsoft.com/en-us/azure/azure-arc/servers/managed-identity-authentication - Arc-enabled servers support managed identity [VERIFIED]

- `MGID-IN01-SC-MSFT-ARCPRQ`: https://learn.microsoft.com/en-us/azure/azure-arc/servers/prerequisites - Windows 10/11 supported for server-like scenarios [VERIFIED]

- `MGID-IN01-SC-MSFT-ARCONB`: https://learn.microsoft.com/en-us/azure/azure-arc/servers/onboard-portal - How to onboard machines to Azure Arc [VERIFIED]

- `MGID-IN01-SC-MSFT-AZFMI`: https://learn.microsoft.com/en-us/azure/storage/files/files-managed-identities - Non-Azure machines need Azure Arc for managed identity [VERIFIED]

- `MGID-IN01-SC-MSFT-MIFAQ`: https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/managed-identities-faq - Managed identity limitations and implementation details [VERIFIED]

- `MGID-IN01-SC-MSFT-DEVJN`: https://learn.microsoft.com/en-us/entra/identity/devices/concept-directory-join - Entra joined devices do not provide managed identity [VERIFIED]

## 7. Next Steps

1. **Decide approach**: Azure Arc (managed identity) vs Service Principal (certificate)
2. **If Azure Arc**:
   - Ensure laptop meets "server-like" requirements
   - Run onboarding script from Azure Portal
   - Assign RBAC roles to managed identity
3. **If Service Principal**:
   - Create App Registration
   - Generate and install certificate
   - Update application code to use certificate auth

## 8. Document History

**[2026-03-15 18:45]**
- Initial research document created
- Verified: Managed identities are Azure-resource-only
- Verified: Azure Arc provides managed identity for non-Azure machines
- Verified: Entra ID device registration does not provide managed identity
