# INFO: Manual Setup Guide

**Doc ID**: SETUP-IN01
**Goal**: Step-by-step manual deployment of SharePoint-GPT-Middleware to Azure App Service
**Timeline**: Created 2026-03-15

## Summary

- Total estimated time: **8-12 hours** (first-time setup with security)
- Resources required: **Azure Administrator**, **SharePoint Administrator**
- Per-site addition: **45-90 minutes** per SharePoint site
- Per-client addition: **30-60 minutes** per middleware client
- All portal steps, no scripts or command line required
- **Middleware is secured** - not open to internet

## Table of Contents

1. [Resource Legend](#1-resource-legend)
2. [Phase 1: Azure App Service Setup](#2-phase-1-azure-app-service-setup)
3. [Phase 2: App Registration Setup](#3-phase-2-app-registration-setup)
4. [Phase 3: Certificate Setup](#4-phase-3-certificate-setup)
5. [Phase 4: API Permissions](#5-phase-4-api-permissions)
6. [Phase 5: Deploy Code](#6-phase-5-deploy-code)
7. [Phase 6: Secure Middleware](#7-phase-6-secure-middleware)
8. [Phase 7: Per-Client Configuration](#8-phase-7-per-client-configuration)
9. [Phase 8: Per-Site Configuration](#9-phase-8-per-site-configuration)
10. [Phase 9: Verification](#10-phase-9-verification)
11. [Quick Reference](#11-quick-reference)
12. [Document History](#12-document-history)

## 1. Resource Legend

- **[AZURE-ADMIN]** - Azure Administrator (subscription access, resource creation)
- **[SP-ADMIN]** - SharePoint Administrator (site permissions, tenant admin)
- **[DEV]** - Developer (code packaging, configuration)

## 2. Phase 1: Azure App Service Setup

**Resource**: [AZURE-ADMIN]
**Estimated Time**: 45-90 minutes

### 2.1 Create Resource Group

1. Go to portal.azure.com
2. Search "Resource groups" → Create
3. Fill in:
   - **Subscription**: Your subscription
   - **Name**: `rg-sharepoint-gpt` (or your choice)
   - **Region**: Sweden Central (or preferred)
4. Click Review + Create → Create

**Test**: Resource group appears in portal

### 2.2 Create App Service Plan

1. Search "App Service plans" → Create
2. Fill in:
   - **Resource Group**: Select the one created above
   - **Name**: `asp-sharepoint-gpt`
   - **Operating System**: Linux
   - **Region**: Same as resource group
   - **Pricing Tier**: Basic B1 (or higher for production)
3. Click Review + Create → Create

**Test**: App Service Plan appears in portal

### 2.3 Create Web App

1. Search "App Services" → Create → Web App
2. Fill in:
   - **Resource Group**: Select yours
   - **Name**: `your-app-name` (becomes `your-app-name.azurewebsites.net`)
   - **Publish**: Code
   - **Runtime stack**: Python 3.12
   - **Operating System**: Linux
   - **App Service Plan**: Select yours
3. Click Review + Create → Create

**Test**: Browse to `https://your-app-name.azurewebsites.net` (will show default page)

## 3. Phase 2: App Registration Setup

**Resource**: [AZURE-ADMIN]
**Estimated Time**: 20-40 minutes

### 3.1 Create Crawler App Registration

1. Azure Portal → Azure Active Directory → App registrations → New registration
2. Fill in:
   - **Name**: `SharePoint-GPT-Crawler`
   - **Supported account types**: Single tenant
   - **Redirect URI**: Leave blank
3. Click Register
4. **Save these values**:
   - Application (client) ID → `CRAWLER_CLIENT_ID`
   - Directory (tenant) ID → `CRAWLER_TENANT_ID`

**Test**: App registration appears in list

## 4. Phase 3: Certificate Setup

**Resource**: [DEV] + [AZURE-ADMIN]
**Estimated Time**: 45-90 minutes

### 4.1 Create Certificate

**[DEV]** performs:

1. Open PowerShell as Administrator
2. Run:
   ```powershell
   $cert = New-SelfSignedCertificate `
     -Subject "CN=SharePoint-GPT-Crawler" `
     -CertStoreLocation "Cert:\CurrentUser\My" `
     -NotAfter (Get-Date).AddYears(5) `
     -KeySpec KeyExchange
   ```
3. Export private key (.pfx):
   ```powershell
   $password = ConvertTo-SecureString -String "YourPassword" -Force -AsPlainText
   Export-PfxCertificate -Cert $cert -FilePath "SharePoint-GPT-Crawler.pfx" -Password $password
   ```
4. Export public key (.cer):
   ```powershell
   Export-Certificate -Cert $cert -FilePath "SharePoint-GPT-Crawler.cer"
   ```
5. **Save the password** → `CRAWLER_CLIENT_CERTIFICATE_PASSWORD`

### 4.2 Upload Certificate to Azure AD

**[AZURE-ADMIN]** performs:

1. Azure Portal → Azure Active Directory → App registrations
2. Click `SharePoint-GPT-Crawler`
3. Certificates & secrets → Certificates tab → Upload certificate
4. Select the `.cer` file → Add

**Test**: Certificate appears with thumbprint and expiry date

### 4.3 Deploy Certificate to App Service

**[AZURE-ADMIN]** performs:

1. App Service → Advanced Tools → Go (opens Kudu)
2. Debug console → Bash
3. Navigate to `/home/data/`
4. Drag and drop the `.pfx` file to upload

**Test**: File appears in `/home/data/` directory

## 5. Phase 4: API Permissions

**Resource**: [AZURE-ADMIN]
**Estimated Time**: 30-60 minutes

### 5.1 Add Microsoft Graph Permissions

1. App registration → API permissions → Add a permission
2. Select Microsoft Graph → Application permissions
3. Add these permissions:
   - `Group.Read.All`
   - `GroupMember.Read.All`
   - `User.Read.All`
4. Click Add permissions

### 5.2 Add SharePoint Permissions

1. Add a permission → Select SharePoint → Application permissions
2. Add:
   - `Sites.Selected`
3. Click Add permissions

### 5.3 Grant Admin Consent

1. Click "Grant admin consent for [Your Tenant]"
2. Click Yes
3. Verify all permissions show green checkmark

**Test**: All permissions show "Granted for [Tenant]"

## 6. Phase 5: Deploy Code

**Resource**: [DEV] + [AZURE-ADMIN]
**Estimated Time**: 60-120 minutes

### 6.1 Prepare Deployment Package

**[DEV]** performs:

1. Create a folder with:
   - All files from `src/` folder
   - `requirements.txt` from project root
2. ZIP the folder contents (not the folder itself)

### 6.2 Configure App Settings

**[AZURE-ADMIN]** performs:

1. App Service → Configuration → Application settings
2. Add these settings:

| Name | Value |
|------|-------|
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `1` |
| `BUILD_FLAGS` | `UseExpressBuild` |
| `CRAWLER_CLIENT_ID` | Your app client ID |
| `CRAWLER_TENANT_ID` | Your tenant ID |
| `CRAWLER_SHAREPOINT_TENANT_NAME` | `contoso` (without .sharepoint.com) |
| `CRAWLER_CLIENT_CERTIFICATE_PFX_FILE` | `SharePoint-GPT-Crawler.pfx` |
| `CRAWLER_CLIENT_CERTIFICATE_PASSWORD` | Your certificate password |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_SERVICE_TYPE` | `openai` or `azure_openai` |

3. Click Save

### 6.3 Set Startup Command

1. Configuration → General settings tab
2. Startup Command: `python -m uvicorn app:app --host 0.0.0.0 --port 8000`
3. Click Save

### 6.4 Deploy via Kudu

1. App Service → Advanced Tools → Go
2. Tools → Zip Push Deploy
3. Drag your ZIP file onto the page
4. Wait for deployment to complete (watch logs)

**Test**: Browse to `https://your-app-name.azurewebsites.net/alive` → should return "OK"

## 7. Phase 6: Secure Middleware

**Resource**: [AZURE-ADMIN]
**Estimated Time**: 45-90 minutes

**Important**: The middleware must not be open to the internet. All requests require Azure AD authentication.

### 7.1 Enable Authentication on App Service

1. Azure Portal → Resource Group → Your App Service
2. Settings → Authentication → Add identity provider
3. Configure:
   - **Identity provider**: Microsoft
   - **Tenant**: Workforce configuration (current tenant)
   - **App registration type**: Create new app registration
   - **Name**: `SharePoint-GPT-Middleware` (or your choice)
   - **Client secret expiration**: 12-24 months
   - **Supported account types**: Current tenant - Single tenant
   - **Client application requirement**: Allow requests from specific client applications
   - **Identity requirement**: Allow requests from any identity
   - **Tenant requirement**: Allow requests only from the issuer tenant
   - **Restrict access**: Require authentication
   - **Unauthenticated requests**: HTTP 302 Found redirect
   - **Token store**: Yes
4. Click Add
5. **Save the App (client) ID** → `MIDDLEWARE_APP_ID`

**Test**: Browsing to app URL now redirects to Microsoft login

### 7.2 Add GUID-Only Token Audience

1. App Service → Settings → Authentication
2. Under Identity provider → Microsoft → click Edit
3. Allowed token audiences:
   - First entry shows: `api://MIDDLEWARE_APP_ID`
   - Add second entry: `MIDDLEWARE_APP_ID` (GUID only, no `api://` prefix)
4. Save

**Why?** Service Principals and Managed Identities send tokens with `aud` claim as plain GUID. Without this entry, their requests will be rejected.

### 7.3 Create App Role for Application Permissions

1. Azure Portal → Microsoft Entra ID → App registrations
2. Search for your middleware app registration → click it
3. App roles → Create app role:
   - **Display name**: `FullControl`
   - **Allowed member types**: Both (Users/Groups + Applications)
   - **Value**: `Middleware.FullControl`
   - **Description**: Full access to all endpoints and admin pages
   - **Enable this app role**: Yes
4. Click Apply

**Test**: App role appears in list

## 8. Phase 7: Per-Client Configuration

**Resource**: [AZURE-ADMIN]
**Estimated Time**: 30-60 minutes per client

**Repeat this phase for each application that needs to access the middleware** (frontends, automation scripts, other services).

### 8.1 Create Client App Registration

1. Azure Portal → Microsoft Entra ID → App registrations → New registration
2. Configure:
   - **Name**: `[Your-Client-Name]-Frontend` (e.g., `HR-Portal-Frontend`)
   - **Supported account types**: Single tenant
   - **Redirect URI**: Leave blank (for service-to-service) or add your frontend URL
3. Click Register
4. **Save the Application (client) ID** → `CLIENT_APP_ID`

### 8.2 Create Client Secret

1. Client App Registration → Certificates & secrets → New client secret
2. Configure:
   - **Description**: `Secret01`
   - **Expires**: 12-24 months
3. Click Add
4. **Copy and save the secret value immediately** (shown only once)

### 8.3 Grant API Permission to Middleware

1. Client App Registration → API permissions → Add a permission
2. Select "APIs my organization uses" tab
3. Search for your middleware app registration name → click it
4. Select **Application permissions**
5. Check **Middleware.FullControl**
6. Click Add permissions
7. Click **Grant admin consent for [Tenant]** → Yes

**Test**: Permission shows green checkmark "Granted"

### 8.4 Add Client to Middleware Allowed List

1. Azure Portal → Your App Service → Settings → Authentication
2. Under Identity provider → Microsoft → click Edit
3. Allowed client applications → Edit
4. Add the `CLIENT_APP_ID`
5. Click OK → Save

**Test**: Client can now authenticate and call middleware endpoints

### 8.5 Client Configuration Values

Provide these values to the client application:

- **Tenant ID**: Your Azure AD tenant ID
- **Client ID**: The client app's Application ID
- **Client Secret**: The secret created in step 8.2
- **Scope**: `api://MIDDLEWARE_APP_ID/.default`
- **Middleware URL**: `https://your-app-name.azurewebsites.net`

## 9. Phase 8: Per-Site Configuration

**Resource**: [SP-ADMIN] + [AZURE-ADMIN]
**Estimated Time**: 45-90 minutes per site

### 9.1 Get Site ID

**[SP-ADMIN]** performs via Graph Explorer (graph.microsoft.com):

1. Sign in with admin account
2. Run query:
   ```
   GET https://graph.microsoft.com/v1.0/sites/contoso.sharepoint.com:/sites/YourSiteName
   ```
3. Copy the `id` value from response

### 9.2 Grant Sites.Selected Permission

**[SP-ADMIN]** performs via Graph Explorer:

1. Run query:
   ```
   POST https://graph.microsoft.com/v1.0/sites/{site-id}/permissions
   ```
2. Request body:
   ```json
   {
     "roles": ["read"],
     "grantedToIdentities": [{
       "application": {
         "id": "<CRAWLER_CLIENT_ID>",
         "displayName": "SharePoint-GPT-Crawler"
       }
     }]
   }
   ```
3. Click Run Query

**Test**: Response shows permission granted

### 9.3 Register Site in Middleware

**[DEV]** or **[SP-ADMIN]** performs:

1. Browse to `https://your-app-name.azurewebsites.net/v2/sites?format=ui`
2. Click Create
3. Fill in:
   - **Site ID**: Short name (e.g., `HR`)
   - **Site URL**: `https://contoso.sharepoint.com/sites/YourSite`
   - **Description**: Human-readable description
4. Submit

**Test**: Site appears in list

### 9.4 Create Domain

1. Browse to `https://your-app-name.azurewebsites.net/v2/domains?format=ui`
2. Click Create
3. Fill in:
   - **Domain ID**: Identifier (e.g., `HRDOCS`)
   - **Name**: Display name
   - **Vector Store Name**: Name for OpenAI vector store
4. Configure sources (document libraries, lists, site pages to crawl)
5. Submit

**Test**: Domain appears in list

### 9.5 Run Initial Crawl

1. Browse to `https://your-app-name.azurewebsites.net/v2/crawler?format=ui`
2. Select domain
3. Mode: Full, Scope: All
4. Click Start Crawl
5. Monitor progress in job stream

**Test**: Job completes successfully, files appear in vector store

### 9.6 Test Query

1. Browse to `https://your-app-name.azurewebsites.net/query2?format=ui`
2. Enter a test query related to your content
3. Verify results return with correct source URLs

**Test**: Search returns relevant results with SharePoint links

## 10. Phase 9: Verification

**Resource**: [DEV]
**Estimated Time**: 30-60 minutes

### 10.1 Health Checks

| Endpoint | Expected Result |
|----------|-----------------|
| `/alive` | Returns "OK" |
| `/` | Shows home page with links |
| `/docs` | Shows OpenAPI documentation |

### 10.2 Functional Tests

| Test | Endpoint | Expected |
|------|----------|----------|
| Site connectivity | `/v2/sites/selftest?format=stream` | All tests pass |
| Vector store | `/v2/inventory?format=ui` | Shows vector stores |
| Search | `/query2?format=ui` | Returns results |

### 10.3 Log Review

1. App Service → Log stream
2. Verify no errors during crawl
3. Check for authentication issues

## 11. Quick Reference

### Time Estimates Summary

| Phase | Resource | Time |
|-------|----------|------|
| Phase 1: Azure App Service | [AZURE-ADMIN] | 45-90 min |
| Phase 2: App Registration | [AZURE-ADMIN] | 20-40 min |
| Phase 3: Certificate | [DEV] + [AZURE-ADMIN] | 45-90 min |
| Phase 4: API Permissions | [AZURE-ADMIN] | 30-60 min |
| Phase 5: Deploy Code | [DEV] + [AZURE-ADMIN] | 60-120 min |
| Phase 6: Secure Middleware | [AZURE-ADMIN] | 45-90 min |
| Phase 7: Per-Client (first) | [AZURE-ADMIN] | 30-60 min |
| Phase 8: Per-Site (first) | [SP-ADMIN] | 45-90 min |
| Phase 9: Verification | [DEV] | 30-60 min |
| **Total First-Time Setup** | | **8-12 hours** |
| **Each Additional Client** | | **30-60 min** |
| **Each Additional Site** | | **45-90 min** |

### Portal URLs

| Portal | URL |
|--------|-----|
| Azure Portal | portal.azure.com |
| Graph Explorer | developer.microsoft.com/graph/graph-explorer |
| SharePoint Admin | contoso-admin.sharepoint.com |
| App Kudu | your-app-name.scm.azurewebsites.net |

### Environment Variables Required

**Crawler Authentication:**
- `CRAWLER_CLIENT_ID`
- `CRAWLER_TENANT_ID`
- `CRAWLER_SHAREPOINT_TENANT_NAME`
- `CRAWLER_CLIENT_CERTIFICATE_PFX_FILE`
- `CRAWLER_CLIENT_CERTIFICATE_PASSWORD`

**OpenAI:**
- `OPENAI_API_KEY` (or Azure OpenAI equivalents)
- `OPENAI_SERVICE_TYPE`

**Azure Build:**
- `SCM_DO_BUILD_DURING_DEPLOYMENT=1`
- `BUILD_FLAGS=UseExpressBuild`

## 12. Document History

**[2026-03-15 08:57]**
- Added Phase 6: Secure Middleware (Azure AD authentication)
- Added Phase 7: Per-Client Configuration
- Updated time estimates

**[2026-03-15 08:55]**
- Initial manual setup guide created
