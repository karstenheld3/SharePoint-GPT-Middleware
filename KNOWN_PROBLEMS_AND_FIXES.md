# INFO: Known Problems and Fixes

**Doc ID**: GLOB-IN01
**Goal**: Document known errors, their causes, and resolutions for the SharePoint-GPT-Middleware application
**Timeline**: Created 2026-03-12

## Summary

- ManagedIdentityCredential errors occur when running outside Azure managed environment [VERIFIED]
- AADSTS700016 errors occur when app ID is incorrect or not found in tenant [VERIFIED]

## Table of Contents

1. [Authentication Errors](#1-authentication-errors)
2. [Sources](#2-sources)
3. [Next Steps](#3-next-steps)
4. [Document History](#4-document-history)

## 1. Authentication Errors

### 1.1 ManagedIdentityCredential Authentication Unavailable

**Error Message:**
```
Error retrieving vector stores: ManagedIdentityCredential authentication unavailable, no response from the IMDS endpoint.
```

**Cause:** Application is running on a computer that is not a managed VM or machine in your Azure tenant. The Instance Metadata Service (IMDS) endpoint is not available outside Azure-managed environments.

**Resolution:** Assign the Managed Identity to the computer or VM. This requires:
- Running on an Azure VM with system-assigned or user-assigned managed identity
- Or running on Azure App Service with managed identity enabled
- Or configuring Azure Arc for on-premises servers

**Workaround for Local Development:** Use alternative authentication methods such as:
- Azure CLI credentials (`az login`)
- Environment variables with service principal credentials
- Interactive browser authentication

### 1.2 Application Not Found in Directory (AADSTS700016)

**Error Message:**
```
Error retrieving vector stores: Microsoft Entra ID error '(unauthorized_client) AADSTS700016: Application with identifier '[app-id]' was not found in the directory '[tenant-name]'. This can happen if the application has not been installed by the administrator of the tenant or consented to by any user in the tenant. You may have sent your authentication request to the wrong tenant.
```

**Cause:** The configured application (client) ID does not exist in the specified Azure AD tenant. Common reasons:
- Incorrect app ID in configuration
- App registration was deleted
- Authenticating against the wrong tenant
- App registration exists in a different tenant

**Resolution:** Assign a working app ID that has access to the OpenAI backend:
1. Verify the app ID in your configuration matches an existing app registration
2. Check the app registration exists in the correct tenant
3. Ensure the app has the required API permissions for Azure OpenAI
4. If using a different tenant, update the tenant ID in configuration

## 2. Sources

**Primary Sources:**
- `GLOB-IN01-SC-MSFT-IMDS`: Microsoft Azure IMDS documentation - Managed identity endpoint requirements

## 3. Next Steps

1. Add additional known errors as they are discovered
2. Document local development authentication alternatives in detail

## 4. Document History

**[2026-03-12 14:49]**
- Added: AADSTS700016 application not found error and resolution

**[2026-03-12 14:47]**
- Initial document created
- Added: ManagedIdentityCredential authentication error and resolution
