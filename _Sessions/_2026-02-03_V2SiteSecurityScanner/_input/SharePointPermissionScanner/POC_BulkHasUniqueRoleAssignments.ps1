# POC: Bulk HasUniqueRoleAssignments via REST API
# Task: PSCP-TK-001
# Goal: Retrieve all items with HasUniqueRoleAssignments in single paginated REST query
# Expected: Much faster than per-item Get-PnPProperty calls

param(
    [string]$SiteUrl = "https://whizzyapps.sharepoint.com/sites/AiSearchTest01",
    [string]$ListTitle = "Documents",
    [string]$ClientId = "95fb77ad-0605-4eed-ae6c-3707006603ab"
)

# Connect to SharePoint
Write-Host "Connecting to $SiteUrl..." -ForegroundColor Cyan
Connect-PnPOnline -Url $SiteUrl -Interactive -ClientId $ClientId

# Measure execution time
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# Get all items with HasUniqueRoleAssignments using REST API
Write-Host "Fetching items from list '$ListTitle' via REST API..." -ForegroundColor Cyan

$allItems = [System.Collections.ArrayList]@()
$nextUrl = "/_api/web/lists/getbytitle('$ListTitle')/items?`$select=ID,FileRef,FileLeafRef,FSObjType,HasUniqueRoleAssignments&`$top=5000"
$pageCount = 0

while ($nextUrl) {
    $pageCount++
    Write-Host "  Fetching page $pageCount..." -ForegroundColor Gray
    
    try {
        $response = Invoke-PnPSPRestMethod -Url $nextUrl
        $allItems.AddRange($response.value) | Out-Null
        
        # Handle pagination
        if ($response.'odata.nextLink') {
            # Extract relative URL from full URL
            $fullNextUrl = $response.'odata.nextLink'
            $nextUrl = $fullNextUrl.Substring($fullNextUrl.IndexOf("/_api"))
        } else {
            $nextUrl = $null
        }
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
        break
    }
}

$stopwatch.Stop()

# Filter items with broken inheritance
$brokenItems = $allItems | Where-Object { $_.HasUniqueRoleAssignments -eq $true }

# Summary
Write-Host ""
Write-Host "========== RESULTS ==========" -ForegroundColor Green
Write-Host "Total items retrieved: $($allItems.Count)"
Write-Host "Items with broken inheritance: $($brokenItems.Count)"
Write-Host "Pages fetched: $pageCount"
Write-Host "Execution time: $($stopwatch.Elapsed.TotalSeconds) seconds"
Write-Host "=============================" -ForegroundColor Green

# Show first 10 broken items
if ($brokenItems.Count -gt 0) {
    Write-Host ""
    Write-Host "First 10 items with broken inheritance:" -ForegroundColor Yellow
    $brokenItems | Select-Object -First 10 | ForEach-Object {
        $type = if ($_.FSObjType -eq 1) { "Folder" } else { "File" }
        Write-Host "  [$type] ID: $($_.ID) - $($_.FileLeafRef)"
    }
}

# Return results for comparison
return @{
    TotalCount = $allItems.Count
    BrokenCount = $brokenItems.Count
    ExecutionSeconds = $stopwatch.Elapsed.TotalSeconds
    AllItems = $allItems
    BrokenItems = $brokenItems
}
