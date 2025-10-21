# Configure SharePoint Crawler Permissions

This guide explains how to configure the necessary Microsoft Graph and SharePoint API permissions for the crawler app registration, and how to grant access to specific SharePoint sites.

## Overview

This guide walks you through 5 steps to configure SharePoint access for the crawler:

1. **Create App Registration** - Set up Azure AD app for the crawler
2. **Create Certificate** - Generate authentication certificate and prepare for deployment
3. **Configure Environment Variables** - Set up `.env` file with all required values
4. **Set API Permissions** - Grant Microsoft Graph and SharePoint API permissions
5. **Add SharePoint Sites** - Grant access to specific SharePoint sites using Sites.Selected

---

## Step 1: Create the Crawler App Registration

Before configuring permissions, you need to create an Azure AD app registration for the crawler.

### Method 1: Using Azure Portal (Recommended)

#### 1.1 Create the App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **+ New registration**
4. Configure the registration:
   - **Name:** `SharePoint-GPT-Crawler`
   - **Supported account types:** Select **"Accounts in this organizational directory only (Single tenant)"**
   - **Redirect URI:** Leave blank (not needed for service-to-service authentication)
5. Click **Register**

#### 1.2 Note the Application Details

After creation, you'll see the app registration overview page. **Copy and save** the following values:

- **Application (client) ID** - You'll use this as `CRAWLER_CLIENT_ID` in your `.env` file
- **Directory (tenant) ID** - You'll use this as `CRAWLER_TENANT_ID` in your `.env` file

Example:
```
Application (client) ID: 12345678-1234-1234-1234-123456789abc
Directory (tenant) ID: 87654321-4321-4321-4321-cba987654321
```

### Method 2: Using Azure CLI

If you prefer command-line tools:

```bash
# Login to Azure
az login

# Create the app registration
az ad app create \
  --display-name "SharePoint-GPT-Crawler" \
  --sign-in-audience AzureADMyOrg

# Note the appId (Application ID) and tenant ID from the output
```

### Alternative: Using PowerShell

```powershell
# Connect to Azure AD
Connect-AzAccount

# Create the app registration
$app = New-AzADApplication -DisplayName "SharePoint-GPT-Crawler"

# Display the important IDs
Write-Host "Application (client) ID: $($app.AppId)"
Write-Host "Directory (tenant) ID: $((Get-AzContext).Tenant.Id)"
```

> **Important:** The app registration name "SharePoint-GPT-Crawler" is for the **crawler service** that accesses SharePoint. This is different from "SharePoint-GPT-Middleware" which is the middleware application that handles user authentication.

---

## Step 2: Create and Configure Certificate

The crawler app uses certificate-based authentication for secure, unattended access to SharePoint.

### 2.1: Create the Certificate Files

1. **Right-click** on `CreateSelfSignedCertificateRunAsAdmin.bat` and select **"Run as Administrator"**
   - Administrator privileges are required to create certificates in the local machine store

2. **Review the certificate details:**
   - Certificate Name: `SharePoint-GPT-Crawler`
   - Valid From: `2025-01-01`
   - Valid To: `2030-01-01` (5-year validity)

3. **Press any key** to continue

4. **Enter a password** when prompted to protect the private key
   - Choose a strong password
   - Remember this password - you'll need it for the `.env` file

5. **Two files will be created** in the project root:
   - `SharePoint-GPT-Crawler.pfx` - Private key (keep secure!)
   - `SharePoint-GPT-Crawler.cer` - Public key (upload to Azure)

### 2.2: Prepare Certificate for Deployment

**For Local Development:**
1. Copy the `.pfx` file to your desired location
2. Note the path for Step 3 (environment variables)

**For Azure App Service Deployment:**
1. Create a `.zip` file containing the `.pfx` file
2. Place the `.zip` file in `src/.unzip_to_persistant_storage_overwrite/`
3. The certificate will be automatically extracted to `/home/data/` when you deploy

### 2.3: Upload Certificate to Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Find and click your **crawler app registration**
4. Click **Certificates & secrets** in the left menu
5. Under the **Certificates** tab, click **Upload certificate**
6. Select the `SharePoint-GPT-Crawler.cer` file
7. Add a description (e.g., "SharePoint Crawler Certificate 2025-2030")
8. Click **Add**

### 2.4: Verify Certificate Upload

After uploading, you should see:
- **Thumbprint** - A unique identifier for the certificate
- **Start date** - When the certificate becomes valid
- **Expiration date** - When the certificate expires

> **Important:** Set a reminder to renew the certificate before it expires!

### Alternative: Customize Certificate Parameters

If you want to customize the certificate name or validity period:

1. **Edit** `CreateSelfSignedCertificateRunAsAdmin.bat`
2. **Modify the parameters** at the top of the file:
   ```batch
   set CERTNAME="YourCustomCertName"
   set STARTDATE="2025-01-01"
   set ENDDATE="2027-01-01"
   ```
3. **Save** the file
4. **Run as Administrator** as described in Method 1

**Parameters you can customize:**
- `CERTNAME` - Name of the certificate (will appear as CN=YourName)
- `STARTDATE` - When the certificate becomes valid (format: YYYY-MM-DD)
- `ENDDATE` - When the certificate expires (format: YYYY-MM-DD)

---

## Step 3: Configure Environment Variables

Create a `.env` file in the project root with all required configuration values.

### 3.1: Create the .env File

Create a file named `.env` in the project root directory with the following content:

```bash
# Crawler App Registration (from Step 1)
CRAWLER_CLIENT_ID=12345678-1234-1234-1234-123456789abc  # Application (client) ID
CRAWLER_CLIENT_NAME=SharePoint-GPT-Crawler  # Name of your crawler app registration
CRAWLER_TENANT_ID=87654321-4321-4321-4321-cba987654321  # Directory (tenant) ID
CRAWLER_SHAREPOINT_TENANT_NAME=contoso  # Your tenant name (without .sharepoint.com)

# Certificate Authentication (from Step 2)
CRAWLER_CLIENT_CERTIFICATE_PFX_FILE=SharePoint-GPT-Crawler.pfx
CRAWLER_CLIENT_CERTIFICATE_PASSWORD=YourStrongPassword123!  # Password you entered in Step 2

# Certificate Location
# For Local Development:
LOCAL_PERSISTENT_STORAGE_PATH=C:\path\to\your\certificates
# For Azure App Service:
# LOCAL_PERSISTENT_STORAGE_PATH=/home/data

# PnP PowerShell (for interactive authentication)
# Find this in Azure AD > App registrations > Search for "PnP Management Shell" > Copy Application (client) ID
PNP_CLIENT_ID=31359c7f-bd7e-475c-86db-fdb8c937548e  # Default PnP Management Shell ID

# Azure Subscription (for API permissions script)
AZURE_SUBSCRIPTION_ID=your-azure-subscription-id
```

### 3.2: Verify Required Values

Ensure you have filled in:
- ✅ `CRAWLER_CLIENT_ID` - From Step 1.2
- ✅ `CRAWLER_TENANT_ID` - From Step 1.2
- ✅ `CRAWLER_SHAREPOINT_TENANT_NAME` - Your SharePoint tenant name
- ✅ `CRAWLER_CLIENT_CERTIFICATE_PASSWORD` - From Step 2.1
- ✅ `LOCAL_PERSISTENT_STORAGE_PATH` - Certificate location from Step 2.2
- ✅ `PNP_CLIENT_ID` - PnP Management Shell app ID
- ✅ `AZURE_SUBSCRIPTION_ID` - Your Azure subscription ID

---

## Step 4: Set API Permissions for App Registration

### Required Permissions

#### Microsoft Graph API (Application Permissions)

| Permission | ID | Purpose |
|------------|----|---------| 
| **Group.Read.All** | `5b567255-7703-4780-807c-7be8301ae99b` | Read all groups in the tenant |
| **GroupMember.Read.All** | `98830695-27a2-44f7-8c18-0c3ebc9698f6` | Read group memberships |
| **User.Read.All** | `df021288-bdef-4463-88db-98f22de89214` | Read all user profiles |

#### SharePoint API (Application Permissions)

| Permission | ID | Purpose |
|------------|----|---------| 
| **Sites.Selected** | `20d37865-089c-4dee-8c41-6967602d4ac8` | Access selected sites (required for certificate-based PnP authentication) |

> **Note:** The SharePoint API `Sites.Selected` permission is different from the Microsoft Graph API permission with the same name. This is the SharePoint-specific permission required for PnP PowerShell with certificate authentication.

### Method 1: Using the PowerShell Script (Recommended)

1. **Run the batch file:**
   ```cmd
   AddRemoveCrawlerPermissions.bat
   ```

2. **The script will:**
   - Check for existing permissions
   - Display current status (OK or MISSING)
   - Prompt you to add or remove permissions

3. **Select option 1** to add missing permissions

4. **Grant admin consent:**
   - The script will display an admin consent URL
   - Open the URL in your browser
   - Sign in as a Global Administrator or Application Administrator
   - Review and accept the permissions

### 4.2: Manual Configuration via Azure Portal

#### 4.2.1: Navigate to App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Find and click your **crawler app registration**

#### 4.2.2: Add Microsoft Graph Permissions

1. Click **API permissions** in the left menu
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Application permissions**
5. Search for and add:
   - `Group.Read.All`
   - `GroupMember.Read.All`
   - `User.Read.All`
6. Click **Add permissions**

#### 4.2.3: Add SharePoint Permissions

1. Click **+ Add a permission** again
2. Select **SharePoint** (not Microsoft Graph)
3. Select **Application permissions**
4. Search for and add:
   - `Sites.Selected`
5. Click **Add permissions**

#### 4.2.4: Grant Admin Consent

1. Click **Grant admin consent for [Your Tenant]**
2. Click **Yes** to confirm
3. Verify all permissions show a green checkmark under "Status"

#### 4.2.5: Verify Permissions

Your API permissions should look like this:

| API | Permission | Type | Status |
|-----|------------|------|--------|
| Microsoft Graph | Group.Read.All | Application | ✓ Granted |
| Microsoft Graph | GroupMember.Read.All | Application | ✓ Granted |
| Microsoft Graph | User.Read.All | Application | ✓ Granted |
| SharePoint | Sites.Selected | Application | ✓ Granted |

---

## Step 5: Add SharePoint Sites to Sites.Selected

After configuring API-level permissions, you must grant the crawler access to specific SharePoint sites.

### Understanding Sites.Selected

The `Sites.Selected` permission model requires explicit grants for each site:

- **Read** - Read lists, libraries, and items
- **Write** - Read and write lists, libraries, and items
- **Full Control** - Full control over the site

### 5.1: Using the PowerShell Script (Recommended)

1. **Run the batch file:**
   ```cmd
   AddRemoveCrawlerSharePointSites.bat
   ```

2. **The script will:**
   - Connect to SharePoint Online (browser authentication required)
   - Scan all sites in your tenant for existing permissions
   - Test access to each configured site
   - Display a menu with options

3. **To add a new site:**
   - Select option **1**
   - Enter the SharePoint site URL (e.g., `https://contoso.sharepoint.com/sites/sitename`)
   - Choose permission level:
     - **1** - Read (recommended for crawlers)
     - **2** - Write
     - **3** - Full Control
   - The script will grant the permission

4. **To remove a site:**
   - Select the corresponding option number (2, 3, 4, etc.)
   - The script will revoke all permissions for that site

### 5.2: Using PnP PowerShell Manually

#### Prerequisites

```powershell
# Install PnP PowerShell module
Install-Module -Name PnP.PowerShell -Scope CurrentUser -Force
```

#### Grant Permission to a Site

```powershell
# Connect to SharePoint Admin Center
$tenantName = "contoso"  # Your tenant name
$adminUrl = "https://$tenantName-admin.sharepoint.com"
Connect-PnPOnline -Url $adminUrl -Interactive

# Grant permission
$appId = "your-crawler-app-id"
$appName = "Your Crawler App Name"
$siteUrl = "https://contoso.sharepoint.com/sites/sitename"
$permission = "read"  # or "write" or "fullcontrol"

Grant-PnPAzureADAppSitePermission `
    -AppId $appId `
    -DisplayName $appName `
    -Site $siteUrl `
    -Permissions $permission
```

#### List Permissions for a Site

```powershell
# Get all app permissions for a site
$siteUrl = "https://contoso.sharepoint.com/sites/sitename"
Get-PnPAzureADAppSitePermission -Site $siteUrl
```

#### Revoke Permission from a Site

```powershell
# Get permission ID
$appId = "your-crawler-app-id"
$siteUrl = "https://contoso.sharepoint.com/sites/sitename"
$permission = Get-PnPAzureADAppSitePermission -Site $siteUrl -AppIdentity $appId

# Revoke permission
Revoke-PnPAzureADAppSitePermission `
    -PermissionId $permission.Id `
    -Site $siteUrl `
    -Force
```

### 5.3: Using Microsoft Graph API

#### Grant Permission via Graph API

```http
POST https://graph.microsoft.com/v1.0/sites/{site-id}/permissions
Content-Type: application/json

{
  "roles": ["read"],
  "grantedToIdentities": [{
    "application": {
      "id": "your-crawler-app-id",
      "displayName": "Your Crawler App Name"
    }
  }]
}
```

#### List Permissions via Graph API

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/permissions
```

#### Revoke Permission via Graph API

```http
DELETE https://graph.microsoft.com/v1.0/sites/{site-id}/permissions/{permission-id}
```

---

## Testing Access

### Test with the Script

The `AddRemoveCrawlerSharePointSites.ps1` script automatically tests access to each configured site by:

1. Connecting using certificate-based authentication
2. Retrieving all lists and libraries
3. Displaying the count and names

### Test Manually with PnP PowerShell

```powershell
# Connect using certificate authentication
$clientId = "your-crawler-app-id"
$tenantId = "your-tenant-id"
$certPath = "path\to\certificate.pfx"
$certPassword = ConvertTo-SecureString "your-cert-password" -AsPlainText -Force
$siteUrl = "https://contoso.sharepoint.com/sites/sitename"

Connect-PnPOnline `
    -Url $siteUrl `
    -ClientId $clientId `
    -Tenant $tenantId `
    -CertificatePath $certPath `
    -CertificatePassword $certPassword

# Test access
Get-PnPList
```

### Test with Microsoft Graph API

```http
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists
Authorization: Bearer {access-token}
```

---

## Troubleshooting

### "Access Denied" Errors

**Possible causes:**

1. **API permissions not granted**
   - Run `AddRemoveCrawlerPermissions.bat` to verify
   - Ensure admin consent was granted

2. **Site-level permission not granted**
   - Run `AddRemoveCrawlerSharePointSites.bat` to verify
   - Check if the site appears in the list

3. **Certificate issues**
   - Verify certificate file exists at the specified path
   - Check certificate password is correct
   - Ensure certificate is not expired

### "Certificate file not found"

Check your `.env` file:
- `CRAWLER_CLIENT_CERTIFICATE_PFX_FILE` should point to the certificate filename
- `LOCAL_PERSISTENT_STORAGE_PATH` should be set correctly (or empty to use script folder)

### "Failed to connect to SharePoint Admin"

Ensure:
- `CRAWLER_SHAREPOINT_TENANT_NAME` is correct (without `.sharepoint.com`)
- `PNP_CLIENT_ID` is set correctly:
  - Go to **Azure AD** > **App registrations** > **All applications**
  - Search for **"PnP Management Shell"**
  - Copy the **Application (client) ID**
- You have SharePoint Administrator or Global Administrator role

### Permission Not Working After Grant

Wait a few minutes for permissions to propagate across Microsoft 365 services. If issues persist:

1. Revoke and re-grant the permission
2. Clear token cache
3. Verify the correct app ID is being used

---

## Additional Resources

- [Microsoft Graph API Permissions Reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [SharePoint Sites.Selected Permission](https://learn.microsoft.com/en-us/sharepoint/dev/solution-guidance/security-apponly-azuread)
- [PnP PowerShell Documentation](https://pnp.github.io/powershell/)
- [Certificate-based Authentication](https://learn.microsoft.com/en-us/sharepoint/dev/solution-guidance/security-apponly-azuread#setting-up-an-azure-ad-app-for-app-only-access)

---

## Quick Reference

### Configuration Checklist

Complete these 5 steps in order:

- [ ] **Step 1:** Create App Registration `SharePoint-GPT-Crawler`
  - Save Application (client) ID
  - Save Directory (tenant) ID
  
- [ ] **Step 2:** Create Certificate
  - Run `CreateSelfSignedCertificateRunAsAdmin.bat`
  - Save certificate password
  - Create `.zip` file with `.pfx` for deployment to `src/.unzip_to_persistant_storage_overwrite/`
  - Upload `.cer` file to Azure AD app registration
  
- [ ] **Step 3:** Configure `.env` File
  - Set `CRAWLER_CLIENT_ID`
  - Set `CRAWLER_TENANT_ID`
  - Set `CRAWLER_CLIENT_CERTIFICATE_PASSWORD`
  - Set `LOCAL_PERSISTENT_STORAGE_PATH`
  - Set all other required variables
  
- [ ] **Step 4:** Set API Permissions
  - Run `AddRemoveCrawlerPermissions.bat` OR configure manually
  - Grant admin consent
  - Verify all permissions show green checkmark
  
- [ ] **Step 5:** Add SharePoint Sites
  - Run `AddRemoveCrawlerSharePointSites.bat`
  - Add each SharePoint site URL with Read permission
  - Test access to verify configuration

### Script Locations

| Script | Purpose | Step |
|--------|---------|------|
| `CreateSelfSignedCertificateRunAsAdmin.bat` | Create authentication certificate | Step 2 |
| `AddRemoveCrawlerPermissions.bat` | Manage API-level permissions | Step 4 |
| `AddRemoveCrawlerSharePointSites.bat` | Manage site-level permissions | Step 5 |

### Admin Consent URL Format

```
https://login.microsoftonline.com/{tenant-id}/adminconsent?client_id={app-id}
```

### Azure Portal Links

- **App Registration:** `https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/{app-id}`
- **API Permissions:** `https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/{app-id}`
