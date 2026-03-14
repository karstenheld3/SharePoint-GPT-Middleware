# INFO: SharePoint REST API - Site Designs and Site Scripts

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Site Design and Site Script REST API endpoints with request/response JSON
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Create reusable site templates
- Apply customizations to new and existing sites
- Define site scripts with declarative actions
- Manage access to site designs

**Key findings**:
- Site scripts contain JSON actions (create list, set theme, etc.) [VERIFIED]
- Site designs reference one or more site scripts [VERIFIED]
- WebTemplate: 64=Team site, 68=Communication site [VERIFIED]
- All endpoints use `/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility` [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 15 site design/script endpoints

**Site Scripts**:
- `CreateSiteScript` - Create site script
- `GetSiteScripts` - Get all site scripts
- `GetSiteScriptMetadata` - Get script by ID
- `UpdateSiteScript` - Update site script
- `DeleteSiteScript` - Delete site script
- `GetSiteScriptFromWeb` - Extract script from site
- `GetSiteScriptFromList` - Extract script from list

**Site Designs**:
- `CreateSiteDesign` - Create site design
- `GetSiteDesigns` - Get all site designs
- `GetSiteDesignMetadata` - Get design by ID
- `UpdateSiteDesign` - Update site design
- `DeleteSiteDesign` - Delete site design
- `ApplySiteDesign` - Apply design to site
- `GrantSiteDesignRights` - Grant access
- `RevokeSiteDesignRights` - Revoke access

**Permissions required**:
- Application: `Sites.FullControl.All`
- Delegated: SharePoint Admin or Site Collection Admin

## Base Endpoint

All site design/script operations use:

```
/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.[Method]
```

## WebTemplate Values [VERIFIED]

- **64** - Team site (STS#3)
- **68** - Communication site
- **1** - Team site (classic)

## 1. CreateSiteScript - Create Site Script

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.CreateSiteScript(Title=@title,Description=@desc)?@title='{title}'&@desc='{description}'
```

### Request Body [VERIFIED]

The request body contains the site script JSON:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/sp/site-design-script-actions.schema.json",
  "actions": [
    {
      "verb": "createSPList",
      "listName": "Customer Tracking",
      "templateType": 100,
      "subactions": [
        {
          "verb": "setDescription",
          "description": "List for tracking customers"
        },
        {
          "verb": "addSPField",
          "fieldType": "Text",
          "displayName": "Customer Name",
          "isRequired": true
        }
      ]
    },
    {
      "verb": "applyTheme",
      "themeName": "Corporate Theme"
    }
  ],
  "version": 1
}
```

### Response JSON [VERIFIED]

```json
{
  "Id": "7647d3d6-1046-41fe-b9cd-db9be4b57a5f",
  "Title": "Customer Tracking Script",
  "Description": "Creates customer list",
  "Content": "{...}",
  "Version": 1
}
```

## 2. GetSiteScripts - Get All Site Scripts

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteScripts
```

### Response JSON [VERIFIED]

```json
{
  "value": [
    {
      "Id": "7647d3d6-1046-41fe-b9cd-db9be4b57a5f",
      "Title": "Customer Tracking Script",
      "Description": "Creates customer list",
      "Version": 1
    }
  ]
}
```

## 3. GetSiteScriptMetadata - Get Script by ID

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteScriptMetadata
```

### Request Body

```json
{
  "id": "7647d3d6-1046-41fe-b9cd-db9be4b57a5f"
}
```

## 4. UpdateSiteScript - Update Site Script

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.UpdateSiteScript
```

### Request Body

```json
{
  "updateInfo": {
    "Id": "7647d3d6-1046-41fe-b9cd-db9be4b57a5f",
    "Title": "Updated Script Title",
    "Description": "Updated description",
    "Content": "{...updated JSON...}",
    "Version": 2
  }
}
```

## 5. DeleteSiteScript - Delete Site Script

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.DeleteSiteScript
```

### Request Body

```json
{
  "id": "7647d3d6-1046-41fe-b9cd-db9be4b57a5f"
}
```

## 6. GetSiteScriptFromWeb - Extract from Site

### Description [VERIFIED]

Generates site script JSON from an existing site's configuration.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteScriptFromWeb
```

### Request Body

```json
{
  "webUrl": "https://contoso.sharepoint.com/sites/SourceSite",
  "info": {
    "IncludeBranding": true,
    "IncludeLists": ["Documents", "Tasks"],
    "IncludeRegionalSettings": true,
    "IncludeSiteExternalSharingCapability": true,
    "IncludeTheme": true
  }
}
```

## 7. GetSiteScriptFromList - Extract from List

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteScriptFromList
```

### Request Body

```json
{
  "listUrl": "https://contoso.sharepoint.com/sites/TeamSite/Lists/Tasks"
}
```

## 8. CreateSiteDesign - Create Site Design

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.CreateSiteDesign
```

### Request Body [VERIFIED]

```json
{
  "info": {
    "Title": "Customer Project Site",
    "Description": "Site template for customer projects",
    "SiteScriptIds": ["7647d3d6-1046-41fe-b9cd-db9be4b57a5f"],
    "WebTemplate": "64",
    "PreviewImageUrl": "https://contoso.sharepoint.com/SiteAssets/preview.png",
    "PreviewImageAltText": "Customer project preview",
    "IsDefault": false
  }
}
```

### Response JSON [VERIFIED]

```json
{
  "Id": "614f9b28-3e85-4ec9-a961-5971ea086cca",
  "Title": "Customer Project Site",
  "Description": "Site template for customer projects",
  "SiteScriptIds": ["7647d3d6-1046-41fe-b9cd-db9be4b57a5f"],
  "WebTemplate": "64",
  "IsDefault": false,
  "Version": 1
}
```

## 9. GetSiteDesigns - Get All Site Designs

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteDesigns
```

## 10. GetSiteDesignMetadata - Get Design by ID

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GetSiteDesignMetadata
```

### Request Body

```json
{
  "id": "614f9b28-3e85-4ec9-a961-5971ea086cca"
}
```

## 11. UpdateSiteDesign - Update Site Design

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.UpdateSiteDesign
```

### Request Body

```json
{
  "updateInfo": {
    "Id": "614f9b28-3e85-4ec9-a961-5971ea086cca",
    "Title": "Updated Design Title",
    "Description": "Updated description",
    "SiteScriptIds": ["7647d3d6-1046-41fe-b9cd-db9be4b57a5f", "another-script-id"],
    "PreviewImageUrl": "https://contoso.sharepoint.com/SiteAssets/new-preview.png",
    "Version": 2
  }
}
```

## 12. DeleteSiteDesign - Delete Site Design

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.DeleteSiteDesign
```

### Request Body

```json
{
  "id": "614f9b28-3e85-4ec9-a961-5971ea086cca"
}
```

## 13. ApplySiteDesign - Apply to Site

### Description [VERIFIED]

Applies a site design to an existing site collection.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.ApplySiteDesign
```

### Request Body

```json
{
  "siteDesignId": "614f9b28-3e85-4ec9-a961-5971ea086cca",
  "webUrl": "https://contoso.sharepoint.com/sites/TargetSite"
}
```

### Response JSON

```json
{
  "value": [
    {
      "Outcome": "Success",
      "OutcomeText": null,
      "Title": "Create list Customer Tracking"
    },
    {
      "Outcome": "Success",
      "OutcomeText": null,
      "Title": "Apply theme Corporate Theme"
    }
  ]
}
```

## 14. GrantSiteDesignRights - Grant Access

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.GrantSiteDesignRights
```

### Request Body

```json
{
  "id": "614f9b28-3e85-4ec9-a961-5971ea086cca",
  "principalNames": ["user@contoso.com", "group@contoso.com"],
  "grantedRights": "1"
}
```

## 15. RevokeSiteDesignRights - Revoke Access

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.RevokeSiteDesignRights
```

### Request Body

```json
{
  "id": "614f9b28-3e85-4ec9-a961-5971ea086cca",
  "principalNames": ["user@contoso.com"]
}
```

## Common Site Script Actions [VERIFIED]

- **createSPList** - Create list
- **addSPField** - Add field to list
- **deleteSPField** - Delete field
- **addSPView** - Add list view
- **removeSPView** - Remove view
- **setSPFieldCustomFormatter** - Set column formatting
- **applyTheme** - Apply theme
- **setSiteLogo** - Set site logo
- **addNavLink** - Add navigation link
- **removeNavLink** - Remove navigation link
- **triggerFlow** - Trigger Power Automate flow
- **installSolution** - Install SPFx solution
- **associateExtension** - Associate SPFx extension
- **joinHubSite** - Join hub site
- **setSiteExternalSharingCapability** - Set sharing

## Error Responses

- **400** - Invalid script JSON or parameters
- **401** - Unauthorized
- **403** - Insufficient permissions
- **404** - Script or design not found

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso-admin.sharepoint.com" -Interactive

# Site Scripts
$script = Add-PnPSiteScript -Title "Customer Script" -Content $jsonContent
Get-PnPSiteScript
Get-PnPSiteScript -Identity $scriptId
Set-PnPSiteScript -Identity $scriptId -Title "Updated Title"
Remove-PnPSiteScript -Identity $scriptId

# Site Designs
$design = Add-PnPSiteDesign -Title "Customer Design" -SiteScriptIds $script.Id -WebTemplate TeamSite
Get-PnPSiteDesign
Invoke-PnPSiteDesign -Identity $design.Id -WebUrl "https://contoso.sharepoint.com/sites/target"
Remove-PnPSiteDesign -Identity $design.Id
```

## Sources

- **SPAPI-DESIGN-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/declarative-customization/site-design-rest-api
- **SPAPI-DESIGN-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/declarative-customization/site-design-overview

## Document History

**[2026-01-28 21:05]**
- Initial creation with 15 endpoints
- Documented site script JSON structure
- Added common script actions reference
