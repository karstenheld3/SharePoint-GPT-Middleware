# INFO: SharePoint Permission Scanner PowerShell Optimization Assessment

**Doc ID**: PSCP-IN02
**Goal**: Assess performance optimization strategies for SharePointPermissionScanner.ps1 using PnP PowerShell
**Timeline**: Created 2026-02-19
**Requires**: PnP.PowerShell 2.4.0+ (batching features)

## Summary

- **Primary bottleneck**: Per-item `Get-PnPProperty -Property HasUniqueRoleAssignments` calls (line 759) - causes 1 HTTP request per item [VERIFIED]
- **Best optimization**: Use REST API with `$select=ID,HasUniqueRoleAssignments` to retrieve all items with flag in single paginated query - **8 seconds for 1,600 items vs minutes with per-item calls** [VERIFIED from source, actual performance may vary]
- **PnP batching limitation**: `Get-PnPProperty` does NOT support `-Batch` parameter - batching only works for write operations [VERIFIED]
- **Alternative**: Use `Invoke-PnPSPRestMethod` with `$batch` endpoint for multiple GET requests in single HTTP call [ASSUMED - needs POC validation for item-level queries]
- **Parallel processing**: PowerShell 7's `ForEach-Object -Parallel` can help but has known PnP runspace issues - **NOT RECOMMENDED without validation** [ASSUMED]
- **Microsoft Graph limitation**: Does NOT return `HasUniqueRoleAssignments` property [VERIFIED]

## Table of Contents

1. Current Script Analysis
2. Optimization Strategies
3. Implementation Recommendations
4. Performance Estimates
5. Code Examples
6. Sources
7. Next Steps
8. Document History

## 1. Current Script Analysis

### 1.1 Script Overview

The `SharePointPermissionScanner.ps1` (921 lines) scans SharePoint sites for permissions and produces CSV reports.

**Processing flow:**
```
For each job (site URL):
├─> Connect to site
├─> Load subsites with HasUniqueRoleAssignments
├─> Step 4: Export groups, group members, site permissions
│   ├─> Get-PnPGroup (site groups)
│   ├─> Load-CSOMProperties (role assignments batch)
│   └─> Resolve Azure AD groups recursively
└─> Step 5: Scan items for broken permission inheritance
    ├─> Get-PnPList with HasUniqueRoleAssignments
    ├─> Get-PnPListItem -PageSize 4995 (all items)
    └─> FOR EACH ITEM: Get-PnPProperty -Property HasUniqueRoleAssignments  <-- BOTTLENECK
        └─> If broken: Load-CSOMProperties for RoleAssignments
```

### 1.2 Identified Bottlenecks

**BOTTLENECK 1: Per-item HasUniqueRoleAssignments check** (line 759)
```powershell
Get-PnPProperty -ClientObject $item -Property HasUniqueRoleAssignments | Out-Null
```
- Called for EVERY item in EVERY list
- Each call = 1 HTTP round-trip (~100-200ms)
- 10,000 items = 10,000 requests = ~20+ minutes

**BOTTLENECK 2: Per-item RoleAssignments loading** (line 805)
```powershell
Load-CSOMProperties -parentObject $item -collectionObject $item.RoleAssignments ...
```
- Only called for items with broken inheritance (much smaller set)
- Still 1 request per broken item

**BOTTLENECK 3: Recursive Azure AD group resolution** (lines 271-386)
```powershell
function getAzureGroupMembers() { ... Get-PnPAzureADGroupMember ... }
```
- Recursive calls for nested groups
- Limited by `$maxGroupNestinglevel = 5`
- Cached per session, mitigates repeated calls

### 1.3 Current Optimizations Already in Place

- `Load-CSOMProperties` function (line 247-316 in `_includes.ps1`) - batches CSOM property loading
- Caching: `$global:azureGroupMemberCache`, `$global:sharePointGroupMemberCache`
- Paging: `Get-PnPListItem -PageSize 4995`
- Batch file writing: `$writeEveryXLines = 100`

## 2. Optimization Strategies

### 2.1 Strategy 1: REST API for Bulk HasUniqueRoleAssignments [RECOMMENDED]

**Problem**: `Get-PnPListItem -Fields "HasUniqueRoleAssignments"` does NOT load the property value.

**Solution**: Use SharePoint REST API directly:
```
/_api/web/lists/getbytitle('Documents')/items?$select=ID,FileRef,FileLeafRef,FSObjType,HasUniqueRoleAssignments&$top=5000
```

**Performance**: 1,600 items in 8 seconds vs minutes with per-item calls [VERIFIED from source]

**Limitation**: Cannot use `$filter` on `HasUniqueRoleAssignments` - must filter in PowerShell after retrieval.

### 2.2 Strategy 2: PnP PowerShell Batching

**What works with batching:**
- `Add-PnPListItem -Batch`
- `Set-PnPListItem -Batch`
- `Remove-PnPListItem -Batch`
- `Invoke-PnPSPRestMethod -Batch`

**What does NOT work with batching:**
- `Get-PnPProperty` - NO `-Batch` parameter
- `Get-PnPListItem` - retrieval only, no batching support

**Batch mechanics:**
- Batches split into chunks of 100 requests (SharePoint REST)
- Batches split into chunks of 20 requests (Microsoft Graph)
- Use `New-PnPBatch` + `Invoke-PnPBatch`

### 2.3 Strategy 3: REST API $batch Endpoint

The SharePoint REST API supports OData `$batch` for combining multiple requests:
```
POST https://tenant.sharepoint.com/_api/$batch
Content-Type: multipart/mixed; boundary=batch_guid
```

**Benefits:**
- Combine multiple GET requests into single HTTP call
- Reduces network round-trips
- Can batch up to ~100 requests per call

**Implementation via PnP:**
```powershell
$batch = New-PnPBatch -RetainRequests
Invoke-PnPSPRestMethod -Method Get -Url "...items(1)?`$select=HasUniqueRoleAssignments" -Batch $batch
Invoke-PnPSPRestMethod -Method Get -Url "...items(2)?`$select=HasUniqueRoleAssignments" -Batch $batch
# ... add more
$response = Invoke-PnPBatch $batch -Details
```

### 2.4 Strategy 4: Parallel Processing (PowerShell 7) [USE WITH CAUTION]

**WARNING**: PnP PowerShell has documented runspace issues (GitHub #3240). Commands may hang when run from `ForEach-Object -Parallel`. Validate thoroughly before using.

**ForEach-Object -Parallel** (PowerShell 7+):
```powershell
$items | ForEach-Object -Parallel {
    # Process items in parallel runspaces
} -ThrottleLimit 10
```

**Considerations:**
- Each runspace needs its own SharePoint connection (`Connect-PnPOnline` per runspace)
- Risk of triggering SharePoint throttling (HTTP 429/503)
- Default ThrottleLimit is 5; increase cautiously
- Context objects (CSOM) are not thread-safe
- **Known issue**: PnP commands may hang indefinitely in alternate runspaces

**Alternative: Start-ThreadJob**
- Lower overhead than Start-Job
- Queued execution respects ThrottleLimit

### 2.5 Strategy 5: Microsoft Graph Delta Queries

**Limitation**: Microsoft Graph does NOT expose `HasUniqueRoleAssignments` property.

**What Graph CAN do:**
- `/groups/{id}/transitiveMembers` - resolve nested Azure AD groups efficiently
- Delta queries for change tracking (not applicable to permission scanning)

### 2.6 Strategy 6: CAML Query Optimization

**Limitation**: CAML cannot filter on `HasUniqueRoleAssignments`.

**What works:**
```xml
<View>
  <ViewFields>
    <FieldRef Name='ID'/>
    <FieldRef Name='FileRef'/>
    <FieldRef Name='HasUniqueRoleAssignments'/>
  </ViewFields>
  <RowLimit>5000</RowLimit>
</View>
```

**Issue**: Encounters list view threshold errors for lists >5000 items when using CAML query.

## 3. Implementation Recommendations

### 3.1 Priority 1: Replace Per-Item HasUniqueRoleAssignments Check [CRITICAL]

**Current code (line 759):**
```powershell
Get-PnPProperty -ClientObject $item -Property HasUniqueRoleAssignments | Out-Null
```

**Recommended replacement:**
```powershell
# Get all items with HasUniqueRoleAssignments in single REST call
$allItems = @()
$nextUrl = "/_api/web/lists/getbytitle('$($list.Title)')/items?`$select=ID,FileRef,FileLeafRef,FSObjType,HasUniqueRoleAssignments&`$top=5000"

while ($nextUrl) {
    $response = Invoke-PnPSPRestMethod -Url $nextUrl
    $allItems += $response.value
    $nextUrl = $response.'odata.nextLink'
}

# Filter broken inheritance items in PowerShell
$brokenItems = $allItems | Where-Object { $_.HasUniqueRoleAssignments -eq $true }
```

**Expected improvement:** 10x-100x faster for item enumeration phase. [ASSUMED - validate with POC]

**Note on refactoring**: REST API returns PSCustomObjects, not CSOM `ListItem` objects. Processing logic that uses CSOM properties (e.g., `$item.RoleAssignments`) must be rewritten to use REST response structure.

### 3.2 Priority 2: Batch RoleAssignments Loading [HIGH]

**Current code (line 805):**
```powershell
Load-CSOMProperties -parentObject $item -collectionObject $item.RoleAssignments ...
```

**Option A: Use REST API batching** [NEEDS VALIDATION]

**Note**: `Invoke-PnPSPRestMethod -Batch` with GET requests is documented in PnP Example 7, but not extensively tested for item-level permission queries. Create POC to validate before production use.

```powershell
$batch = New-PnPBatch -RetainRequests
foreach ($item in $brokenItems) {
    $url = "/_api/web/lists/getbytitle('$listTitle')/items($($item.ID))/roleassignments?`$expand=Member,RoleDefinitionBindings"
    Invoke-PnPSPRestMethod -Method Get -Url $url -Batch $batch
}
$responses = Invoke-PnPBatch $batch -Details
```

**Expected improvement:** 100 items per HTTP request instead of 1. [ASSUMED]

### 3.3 Priority 3: Use Graph transitiveMembers for Azure AD Groups [MEDIUM]

**Current code (line 341):**
```powershell
$members = Get-PnPAzureADGroupMember -Identity $viaGroupId
```

**Recommended for Security Groups:**
```powershell
# Single call returns ALL nested members (flat)
$members = Get-PnPAzureADGroupMember -Identity $groupId -Transitive
```

**Note:** M365 Groups cannot have nested groups, use regular `/members` for those.

### 3.4 Priority 4: Add Throttling Protection [MEDIUM]

**Reactive approach (basic)**: Handle 429/503 with retry-after.

**Proactive approach (recommended)**: Monitor RateLimit headers to avoid throttling entirely. Microsoft documentation shows proactive handling achieves higher sustained throughput than reactive retry.

**RateLimit Headers to Monitor:**
- `RateLimit-Limit` - Maximum resource units allowed
- `RateLimit-Remaining` - Resource units remaining in window
- `RateLimit-Reset` - Seconds until limit resets

**Reference**: Microsoft's RateLimit demo application at https://github.com/OneDrive/samples/tree/master/scenarios/throttling-ratelimit-handling

```powershell
function Invoke-WithRetry {
    param([ScriptBlock]$ScriptBlock, [int]$MaxRetries = 5)
    $retryCount = 0
    while ($retryCount -lt $MaxRetries) {
        try {
            return & $ScriptBlock
        } catch {
            if ($_.Exception.Response.StatusCode -eq 429 -or 
                $_.Exception.Response.StatusCode -eq 503) {
                $retryAfter = $_.Exception.Response.Headers["Retry-After"]
                if (-not $retryAfter) { $retryAfter = [math]::Pow(2, $retryCount) }
                Write-Host "Throttled. Waiting $retryAfter seconds..."
                Start-Sleep -Seconds $retryAfter
                $retryCount++
            } else { throw }
        }
    }
}
```

## 4. Performance Estimates

### 4.1 Current Performance (Per-Item Calls) [ESTIMATED]

- 1,000 items: ~2-3 minutes
- 10,000 items: ~20-30 minutes
- 100,000 items: ~3-5 hours

### 4.2 Optimized Performance (Bulk REST + Batching) [ASSUMED - NEEDS POC VALIDATION]

- 1,000 items: ~10-15 seconds
- 10,000 items: ~1-2 minutes
- 100,000 items: ~10-15 minutes

**Improvement factor:** 10x-20x faster

**Note**: These estimates are extrapolated from single blog post benchmark (1,600 items in 8 seconds). Actual performance depends on SharePoint tenant configuration, network latency, item complexity, and throttling behavior. Validate with POC before committing to approach.

### 4.3 Breakdown by Operation

**Item enumeration with HasUniqueRoleAssignments:**
- Current: 100-200ms per item
- Optimized: ~1 second per 5000 items (1 REST call)

**RoleAssignments loading for broken items:**
- Current: 100-200ms per item
- Optimized: ~2 seconds per 100 items (1 batch)

**Azure AD group resolution:**
- Already cached, minimal improvement available
- Could use Graph transitiveMembers for Security Groups

## 5. Code Examples

### 5.1 Bulk HasUniqueRoleAssignments Check

```powershell
function Get-ItemsWithUniquePermissions {
    param(
        [Parameter(Mandatory=$true)][string]$ListTitle,
        [Parameter(Mandatory=$true)][string]$SiteUrl
    )
    
    $allItems = [System.Collections.ArrayList]@()
    $nextUrl = "/_api/web/lists/getbytitle('$ListTitle')/items?`$select=ID,FileRef,FileLeafRef,FSObjType,HasUniqueRoleAssignments&`$top=5000"
    
    # NOTE: For folder-specific scans with >5000 items, add $filter on FileRef prefix
    # or use FolderServerRelativeUrl equivalent in REST query
    
    while ($nextUrl) {
        try {
            $response = Invoke-PnPSPRestMethod -Url $nextUrl
            $allItems.AddRange($response.value) | Out-Null
            
            # Handle pagination
            if ($response.'odata.nextLink') {
                $nextUrl = $response.'odata.nextLink'.Replace($SiteUrl, "")
            } else {
                $nextUrl = $null
            }
        } catch {
            Write-Host "Error: $_" -ForegroundColor Red
            break
        }
    }
    
    # Filter items with broken inheritance
    $brokenItems = $allItems | Where-Object { $_.HasUniqueRoleAssignments -eq $true }
    
    return @{
        AllItems = $allItems
        BrokenItems = $brokenItems
        TotalCount = $allItems.Count
        BrokenCount = $brokenItems.Count
    }
}
```

### 5.2 Batched RoleAssignments Loading

```powershell
function Get-BatchedRoleAssignments {
    param(
        [Parameter(Mandatory=$true)][array]$Items,
        [Parameter(Mandatory=$true)][string]$ListTitle,
        [int]$BatchSize = 100
    )
    
    $results = @{}
    $itemBatches = @()
    
    # Split items into batches of $BatchSize
    for ($i = 0; $i -lt $Items.Count; $i += $BatchSize) {
        $itemBatches += ,($Items[$i..[math]::Min($i + $BatchSize - 1, $Items.Count - 1)])
    }
    
    foreach ($batchItems in $itemBatches) {
        $batch = New-PnPBatch -RetainRequests
        
        foreach ($item in $batchItems) {
            $url = "/_api/web/lists/getbytitle('$ListTitle')/items($($item.ID))/roleassignments?`$expand=Member,RoleDefinitionBindings"
            Invoke-PnPSPRestMethod -Method Get -Url $url -Batch $batch
        }
        
        $responses = Invoke-PnPBatch $batch -Details
        
        # Process responses
        for ($j = 0; $j -lt $batchItems.Count; $j++) {
            $itemId = $batchItems[$j].ID
            if ($responses[$j].HttpStatusCode -eq 200) {
                $results[$itemId] = $responses[$j].Response.value
            }
        }
    }
    
    return $results
}
```

### 5.3 Optimized Main Scanning Loop

```powershell
# Replace lines 737-896 with optimized version
if ($scanIndividualItems) {
    # OPTIMIZATION: Get all items with HasUniqueRoleAssignments in bulk
    Write-Host "    Loading items with bulk REST query..."
    $itemData = Get-ItemsWithUniquePermissions -ListTitle $list.Title -SiteUrl $siteUrl
    
    Write-Host "    $($itemData.TotalCount) items found, $($itemData.BrokenCount) with broken permissions."
    
    if ($itemData.BrokenCount -gt 0) {
        # OPTIMIZATION: Batch load role assignments for all broken items
        Write-Host "    Loading role assignments in batches..."
        $roleAssignmentsMap = Get-BatchedRoleAssignments -Items $itemData.BrokenItems -ListTitle $list.Title
        
        # Process broken items
        foreach ($item in $itemData.BrokenItems) {
            $roleAssignments = $roleAssignmentsMap[$item.ID]
            # ... process role assignments (existing logic) ...
        }
    }
}
```

## 6. Sources

**Primary Sources:**

- `PSCP-IN02-SC-RESH-HURA`: https://reshmeeauckloo.com/posts/powershell-get-hasuniqueroleassignments/ - REST API for HasUniqueRoleAssignments is 10x+ faster than PnP cmdlets [VERIFIED]
- `PSCP-IN02-SC-PNPG-BTCH`: https://pnp.github.io/powershell/articles/batching.html - PnP batching reduces requests from 600 to 6 for 100 items [VERIFIED]
- `PSCP-IN02-SC-DWIK-BTCH`: https://deepwiki.com/pnp/powershell/2.3-batch-processing - Batch architecture, chunking at 100 requests [VERIFIED]
- `PSCP-IN02-SC-MSFT-BTCH`: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/make-batch-requests-with-the-rest-apis - SharePoint REST $batch endpoint documentation [VERIFIED]
- `PSCP-IN02-SC-MSFT-THRT`: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/how-to-avoid-getting-throttled-or-blocked-in-sharepoint-online - Throttling guidance, retry-after headers [VERIFIED]
- `PSCP-IN02-SC-PNPG-GLST`: https://pnp.github.io/powershell/cmdlets/Get-PnPListItem.html - PageSize, ScriptBlock parameters [VERIFIED]
- `PSCP-IN02-SC-PNPG-REST`: https://pnp.github.io/powershell/cmdlets/Invoke-PnPSPRestMethod.html - REST method with batch support [VERIFIED]

**Secondary Sources (Code Analysis):**

- `PSCP-IN02-SC-SCAN-MAIN`: `SharePointPermissionScanner.ps1` - Line 759 bottleneck identified [VERIFIED]
- `PSCP-IN02-SC-SCAN-INCL`: `_includes.ps1` - Load-CSOMProperties function analyzed [VERIFIED]

## 7. Next Steps

1. **Create POC script** to validate REST API bulk query approach
2. **Validate GET batching** - Test `Invoke-PnPSPRestMethod -Batch` with GET requests for RoleAssignments
3. **Benchmark** current vs optimized performance on test site
4. **Implement Strategy 1** (bulk HasUniqueRoleAssignments) first
5. **Implement Strategy 2** (batched RoleAssignments) second - after validating batching works
6. **Test throttling behavior** with larger sites
7. **Update production script** after validation

**Do NOT implement parallel processing (Strategy 4) until PnP runspace issues are resolved.**

## 8. Document History

**[2026-02-19 15:00]**
- Applied Devil's Advocate review findings
- Added PnP.PowerShell version requirement (2.4.0+)
- Added `[ASSUMED]` labels to unverified performance estimates
- Added warning about parallel processing runspace issues
- Enhanced throttling section with RateLimit header guidance
- Added notes about CSOM-to-REST refactoring requirements
- Added POC validation steps to Next Steps

**[2026-02-19 14:45]**
- Initial research document created
- Analyzed SharePointPermissionScanner.ps1 (921 lines)
- Identified primary bottleneck: per-item HasUniqueRoleAssignments calls
- Researched 6 optimization strategies
- Documented REST API bulk query approach as best solution
- Added code examples for implementation
