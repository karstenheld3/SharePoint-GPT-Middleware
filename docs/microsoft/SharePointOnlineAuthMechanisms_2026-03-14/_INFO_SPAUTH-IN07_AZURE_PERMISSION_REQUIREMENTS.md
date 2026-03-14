<DevSystem MarkdownTablesAllowed=true />

# INFO: Azure Permission Requirements for SharePoint and Graph APIs

**Doc ID**: SPAUTH-IN07
**Goal**: Comprehensive guide to API permission configuration across all authentication methods
**Version Scope**: Microsoft Entra ID, Microsoft Graph, SharePoint Online (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## Overview

This document serves as the central reference for API permission requirements. All implementation guides (AM01-AM09) reference this document for permission configuration details.

**Key Dimensions:**
- **Permission Type**: Application (app-only) vs Delegated (user context)
- **API Target**: Microsoft Graph vs SharePoint REST API
- **Permission Scope**: Sites.Read.All, Sites.ReadWrite.All, Sites.Selected, etc.

## 1. Permission Types: Application vs Delegated

### Application Permissions (App-Only)

Application permissions are used when no user is present. The app acts as itself.

```
┌─────────────────────────────────────────────────────────────────┐
│ Application Permissions                                         │
│                                                                 │
│ App ────────────────────────────> API                           │
│      (app's own identity)         (full permission scope)       │
│                                                                 │
│ Used by:                                                        │
│ - AM01: Certificate Credentials                                 │
│ - AM02: Client Secret (Graph only)                              │
│ - AM03: Managed Identity                                        │
│                                                                 │
│ Characteristics:                                                │
│ - No user sign-in required                                      │
│ - Access determined by granted permissions                      │
│ - Sites.Selected available for least-privilege                  │
│ - Requires admin consent                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Delegated Permissions (User Context)

Delegated permissions are used when a user is present. The app acts on behalf of the user.

```
┌─────────────────────────────────────────────────────────────────┐
│ Delegated Permissions                                           │
│                                                                 │
│ User ──> App ──────────────────> API                            │
│          (on behalf of user)     (user's permissions apply)     │
│                                                                 │
│ Used by:                                                        │
│ - AM04: Interactive Browser                                     │
│ - AM05: Device Code                                             │
│ - AM06: Authorization Code                                      │
│ - AM07: Username/Password (ROPC)                                │
│ - AM08: On-Behalf-Of                                            │
│ - AM09: Development Tools                                       │
│                                                                 │
│ Characteristics:                                                │
│ - User must sign in                                             │
│ - Access = intersection of app permissions AND user permissions │
│ - Sites.Selected NOT available                                  │
│ - User or admin consent required                                │
└─────────────────────────────────────────────────────────────────┘
```

### Permission Type by Auth Method

**Application Permissions (Sites.Selected available):**
- **Certificate Credentials** (AM01) - Application, Sites.Selected: Yes
- **Client Secret** (AM02) - Application, Sites.Selected: Yes (Graph only)
- **Managed Identity** (AM03) - Application, Sites.Selected: Yes

**Delegated Permissions (Sites.Selected NOT available):**
- **Interactive Browser** (AM04) - Delegated
- **Device Code** (AM05) - Delegated
- **Authorization Code** (AM06) - Delegated
- **Username/Password (ROPC)** (AM07) - Delegated
- **On-Behalf-Of** (AM08) - Delegated
- **Development Tools** (AM09) - Delegated

## 2. API Targets: Microsoft Graph vs SharePoint REST

### Token Audience Requirement

Different APIs require different token audiences. You cannot use a Graph token for SharePoint REST API calls.

- **Microsoft Graph**
  - Token Audience: `https://graph.microsoft.com`
  - Endpoint Pattern: `https://graph.microsoft.com/v1.0/sites/...`

- **SharePoint REST**
  - Token Audience: `https://{tenant}.sharepoint.com`
  - Endpoint Pattern: `https://{tenant}.sharepoint.com/_api/...`

### Which API to Use?

- **Modern development** - Microsoft Graph (unified endpoint, cross-Microsoft 365, better docs)
- **Legacy migration** - SharePoint REST (compatibility with existing code)
- **Full SharePoint features** - SharePoint REST (some features not exposed in Graph)
- **Cross-tenant operations** - Microsoft Graph (easier multi-tenant configuration)

### Permission Registration Per API

When registering permissions in Azure Portal, you must select the correct API:

```
Azure Portal > App Registration > API Permissions > Add a permission
                                                          │
                    ┌─────────────────────────────────────┼─────────────────────────────────────┐
                    │                                     │                                     │
                    v                                     v                                     v
            Microsoft Graph                         SharePoint                           Custom API
            (for Graph API)                    (for SharePoint REST)                  (for your APIs)
```

**Common mistake:** Adding Graph permissions but calling SharePoint REST API. The token won't work.

## 3. Permission Scopes for SharePoint/Graph

### Read vs Write Operations

**Read Operations** (require `Sites.Read.All`):
- List sites
- Read list items
- Read files

**Write Operations** (require `Sites.ReadWrite.All`):
- Create list items
- Upload files
- Delete items
- Create lists

**Admin Operations** (require `Sites.FullControl.All`):
- Modify site settings

### Available Scopes

#### Microsoft Graph Scopes

**Application Permissions:**

- **`Sites.Read.All`** - Read all sites (reporting, indexing)
- **`Sites.ReadWrite.All`** - Read/write all sites (crawlers, automation)
- **`Sites.FullControl.All`** - Full control all sites (admin operations, site creation)
- **`Sites.Selected`** - Specific sites only (**Recommended** for least-privilege)

**Delegated Permissions:**

- **`Sites.Read.All`** - Read sites user can access (user-facing read apps)
- **`Sites.ReadWrite.All`** - Read/write sites user can access (user-facing editing apps)

**Note:** `Sites.Selected` is NOT available as a delegated permission.

#### SharePoint Scopes

**Application Permissions:** (all require certificate authentication)

- **`Sites.Read.All`** - Read all sites
- **`Sites.ReadWrite.All`** - Read/write all sites
- **`Sites.FullControl.All`** - Full control
- **`Sites.Selected`** - Specific sites

**Delegated Permissions:** (legacy scopes)

- **`AllSites.Read`** - Read all sites user can access
- **`AllSites.Write`** - Write all sites user can access
- **`AllSites.FullControl`** - Full control

### Choosing the Right Scope

```
┌─────────────────────────────────────────────────────────────────┐
│ Decision Tree: Which scope do I need?                           │
│                                                                 │
│ 1. Does your app write to SharePoint?                           │
│    ├── No  → Use Sites.Read.All or Sites.Selected (read)        │
│    └── Yes → Use Sites.ReadWrite.All or Sites.Selected (write)  │
│                                                                 │
│ 2. Does your app need ALL sites or specific sites?              │
│    ├── All sites → Use Sites.Read/ReadWrite.All                 │
│    └── Specific  → Use Sites.Selected (app-only) [RECOMMENDED]  │
│                                                                 │
│ 3. Is a user present during authentication?                     │
│    ├── No  → Use Application permissions                        │
│    └── Yes → Use Delegated permissions                          │
│              (user's SharePoint permissions apply automatically)│
└─────────────────────────────────────────────────────────────────┘
```

## 4. Sites.Selected: Least-Privilege Access

### What is Sites.Selected?

`Sites.Selected` allows granting app access to specific sites only, rather than all sites. This follows the principle of least privilege.

### Availability

- **Application permissions** - Yes (requires per-site grant via Graph API)
- **Delegated permissions** - **No** (use user's existing SharePoint permissions)

### How to Configure Sites.Selected

**Step 1: Grant Sites.Selected permission to app**

```
Azure Portal > App Registration > API Permissions
> Add permission > Microsoft Graph > Application
> Sites.Selected
> Grant admin consent
```

**Step 2: Grant per-site access via Graph API**

```powershell
# Connect with admin account
Connect-MgGraph -Scopes "Sites.FullControl.All"

# Get site ID
$site = Get-MgSite -SiteId "contoso.sharepoint.com:/sites/targetsite"

# Grant app access to site
$params = @{
    roles = @("write")  # "read" or "write"
    grantedToIdentities = @(
        @{
            application = @{
                id = "your-app-client-id"
                displayName = "Your App Name"
            }
        }
    )
}

New-MgSitePermission -SiteId $site.Id -BodyParameter $params
```

**Step 3: Verify access**

```powershell
# List permissions on site
Get-MgSitePermission -SiteId $site.Id
```

### Sites.Selected Roles

- **`read`** - Read access to site content
- **`write`** - Read and write access to site content
- **`owner`** - Full control including permissions management

### Sites.Selected vs Sites.Read/ReadWrite.All

**Sites.Selected:**
- Scope: Specific sites only
- Configuration: Per-site grants required
- Least privilege: Yes
- Maintenance: Higher (track site access)
- Security: Better (limited blast radius)

**Sites.Read/ReadWrite.All:**
- Scope: All sites in tenant
- Configuration: Single administrator consent
- Least privilege: No
- Maintenance: Lower
- Security: Worse (full tenant access)

## 5. Permission Matrix by Auth Method

### App-Only Methods (Application Permissions)

#### AM01: Certificate Credentials

- **Microsoft Graph** - `Sites.Selected` (preferred, grant per-site access)
- **Microsoft Graph** - `Sites.ReadWrite.All` (if all-site access needed)
- **SharePoint REST** - `Sites.ReadWrite.All` (**certificate required**)

#### AM02: Client Secret

- **Microsoft Graph** - `Sites.Selected` (preferred, grant per-site access)
- **Microsoft Graph** - `Sites.ReadWrite.All` (if all-site access needed)
- **SharePoint REST** - **NOT SUPPORTED** (client secrets blocked by SharePoint)

#### AM03: Managed Identity

- **Microsoft Graph** - `Sites.Selected` (preferred, grant via PowerShell)
- **Microsoft Graph** - `Sites.ReadWrite.All` (if all-site access needed)
- **SharePoint REST** - `Sites.ReadWrite.All` (via Graph API permission grant)

### User-Delegated Methods (Delegated Permissions)

#### AM04, AM05, AM06, AM07, AM08, AM09

- **Microsoft Graph** - `Sites.ReadWrite.All` (user's permissions apply)
- **SharePoint REST** - `AllSites.Write` (only if using REST API directly)

**Important:** For delegated flows, the effective permission is:
```
Effective Access = App Delegated Permission ∩ User's SharePoint Permissions
```

The app cannot access more than the user can access, regardless of granted scopes.

## 6. Common Configuration Scenarios

### Scenario: Read-Only Crawler (App-Only)

**Requirement:** Background service reads SharePoint content, no user interaction

**Recommended Setup:**
- Auth Method: AM01 (Certificate) or AM03 (Managed Identity)
- Permission Type: Application
- Graph Scope: `Sites.Selected` with `read` role per site
- Alternative: `Sites.Read.All` if many sites

### Scenario: Read-Write Crawler with Self-Test (App-Only)

**Requirement:** Background service reads and writes SharePoint content

**Recommended Setup:**
- Auth Method: AM01 (Certificate) or AM03 (Managed Identity)
- Permission Type: Application
- Graph Scope: `Sites.Selected` with `write` role per site
- Alternative: `Sites.ReadWrite.All` if many sites

### Scenario: User-Facing File Browser (Delegated)

**Requirement:** User browses their SharePoint files

**Recommended Setup:**
- Auth Method: AM04 (Interactive) or AM06 (Authorization Code)
- Permission Type: Delegated
- Graph Scope: `Sites.Read.All` (user's permissions apply)
- Alternative: `Sites.ReadWrite.All` if editing needed

### Scenario: Middle-Tier API (On-Behalf-Of)

**Requirement:** Backend API calls SharePoint on behalf of user

**Recommended Setup:**
- Auth Method: AM08 (On-Behalf-Of)
- Permission Type: Delegated
- Graph Scope: `Sites.ReadWrite.All` (user's permissions apply)
- SharePoint Scope: Only if calling REST API directly

## 7. Registering Permissions in Azure Portal

### Step-by-Step: Application Permissions

1. Navigate to **Azure Portal** > **Microsoft Entra ID** > **App registrations**
2. Select your app or create new registration
3. Go to **API permissions** > **Add a permission**
4. Select **Microsoft Graph** (or **SharePoint** for REST API)
5. Select **Application permissions**
6. Search and select required permissions:
   - `Sites.Selected` (recommended)
   - `Sites.Read.All` or `Sites.ReadWrite.All` (if needed)
7. Click **Add permissions**
8. Click **Grant admin consent for [tenant]**

### Step-by-Step: Delegated Permissions

1. Navigate to **Azure Portal** > **Microsoft Entra ID** > **App registrations**
2. Select your app or create new registration
3. Go to **API permissions** > **Add a permission**
4. Select **Microsoft Graph** (or **SharePoint** for REST API)
5. Select **Delegated permissions**
6. Search and select required permissions:
   - `Sites.Read.All` or `Sites.ReadWrite.All`
   - `User.Read` (for user profile)
   - `offline_access` (for refresh tokens)
7. Click **Add permissions**
8. Optionally click **Grant admin consent** (or users will consent on first use)

## 8. Troubleshooting Permission Issues

### Common Errors

- **AADSTS65001** - User/admin has not consented → Grant consent in Azure Portal
- **AADSTS70011** - Invalid scope format → Use correct scope format (e.g., `.default`)
- **AADSTS700016** - Application not found → Verify client_id and tenant_id
- **401 Unauthorized** - Token missing or invalid → Check token audience matches API
- **403 Forbidden** - Insufficient permissions → Add required permissions, re-consent

### Debugging Checklist

1. **Verify token audience matches API:**
   - Graph API: token audience should be `https://graph.microsoft.com`
   - SharePoint REST: token audience should be `https://{tenant}.sharepoint.com`

2. **Check permission type:**
   - App-only flow? → Need Application permissions
   - User flow? → Need Delegated permissions

3. **Verify admin consent granted:**
   - Azure Portal > App Registration > API permissions
   - Green checkmark = consent granted

4. **For Sites.Selected, verify per-site grant:**
   ```powershell
   Get-MgSitePermission -SiteId "site-id"
   ```

## Sources

**Primary:**
- SPAUTH-SC-MSFT-GRAPHPERM: Microsoft Graph permissions reference
- SPAUTH-SC-MSFT-SPPERM: SharePoint permissions reference
- SPAUTH-SC-MSFT-SITESSELECTED: Sites.Selected permission guide

## Document History

**[2026-03-14 19:30]**
- Initial document created
- Permission matrix by auth method documented
- Sites.Selected configuration guide added
- Common scenarios documented
