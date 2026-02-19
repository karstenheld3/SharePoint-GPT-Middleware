# POC: Batched RoleAssignments via REST API
# Task: PSCP-TK-002
# Goal: Retrieve RoleAssignments for multiple items in single batch request
# Expected: Validate if Invoke-PnPSPRestMethod -Batch works for GET requests

param(
    [string]$SiteUrl = "https://whizzyapps.sharepoint.com/sites/AiSearchTest01",
    [string]$ListTitle = "Documents",
    [string]$ClientId = "95fb77ad-0605-4eed-ae6c-3707006603ab",
    [int]$BatchSize = 20,
    [int[]]$TestItemIds = @()  # If empty, will use first N items with broken permissions
)

# Connect to SharePoint
Write-Host "Connecting to $SiteUrl..." -ForegroundColor Cyan
Connect-PnPOnline -Url $SiteUrl -Interactive -ClientId $ClientId

# If no test item IDs provided, get items with broken permissions first
if ($TestItemIds.Count -eq 0) {
    Write-Host "Finding items with broken permissions..." -ForegroundColor Cyan
    $response = Invoke-PnPSPRestMethod -Url "/_api/web/lists/getbytitle('$ListTitle')/items?`$select=ID,FileRef,HasUniqueRoleAssignments&`$top=100"
    $brokenItems = $response.value | Where-Object { $_.HasUniqueRoleAssignments -eq $true }
    
    if ($brokenItems.Count -eq 0) {
        Write-Host "No items with broken permissions found. Testing with first $BatchSize items instead." -ForegroundColor Yellow
        $TestItemIds = $response.value | Select-Object -First $BatchSize | ForEach-Object { $_.ID }
    } else {
        $TestItemIds = $brokenItems | Select-Object -First $BatchSize | ForEach-Object { $_.ID }
        Write-Host "Found $($brokenItems.Count) items with broken permissions. Testing with first $($TestItemIds.Count)." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Testing batch GET requests for $($TestItemIds.Count) items..." -ForegroundColor Cyan
Write-Host "Item IDs: $($TestItemIds -join ', ')" -ForegroundColor Gray

# METHOD 1: Test Invoke-PnPSPRestMethod with -Batch parameter
Write-Host ""
Write-Host "========== METHOD 1: PnP Batch ==========" -ForegroundColor Yellow

$stopwatch1 = [System.Diagnostics.Stopwatch]::StartNew()
$batchResults = @{}
$batchSuccess = $false

try {
    $batch = New-PnPBatch -RetainRequests
    
    foreach ($itemId in $TestItemIds) {
        $url = "/_api/web/lists/getbytitle('$ListTitle')/items($itemId)/roleassignments?`$expand=Member,RoleDefinitionBindings"
        Invoke-PnPSPRestMethod -Method Get -Url $url -Batch $batch
    }
    
    $responses = Invoke-PnPBatch $batch -Details
    $stopwatch1.Stop()
    
    Write-Host "Batch executed successfully!" -ForegroundColor Green
    Write-Host "Responses received: $($responses.Count)"
    Write-Host "Execution time: $($stopwatch1.Elapsed.TotalSeconds) seconds"
    
    # Process responses
    for ($i = 0; $i -lt $TestItemIds.Count; $i++) {
        $itemId = $TestItemIds[$i]
        if ($i -lt $responses.Count) {
            $resp = $responses[$i]
            if ($resp.HttpStatusCode -eq 200) {
                $batchResults[$itemId] = $resp.Response.value
                Write-Host "  Item $itemId : $($resp.Response.value.Count) role assignments" -ForegroundColor Gray
            } else {
                Write-Host "  Item $itemId : HTTP $($resp.HttpStatusCode)" -ForegroundColor Red
            }
        }
    }
    $batchSuccess = $true
    
} catch {
    $stopwatch1.Stop()
    Write-Host "ERROR: Batch method failed!" -ForegroundColor Red
    Write-Host $_ -ForegroundColor Red
    Write-Host ""
    Write-Host "This confirms GET batching may not work as expected." -ForegroundColor Yellow
}

# METHOD 2: Compare with per-item requests (baseline)
Write-Host ""
Write-Host "========== METHOD 2: Per-Item (Baseline) ==========" -ForegroundColor Yellow

$stopwatch2 = [System.Diagnostics.Stopwatch]::StartNew()
$perItemResults = @{}

foreach ($itemId in $TestItemIds) {
    try {
        $url = "/_api/web/lists/getbytitle('$ListTitle')/items($itemId)/roleassignments?`$expand=Member,RoleDefinitionBindings"
        $response = Invoke-PnPSPRestMethod -Url $url
        $perItemResults[$itemId] = $response.value
        Write-Host "  Item $itemId : $($response.value.Count) role assignments" -ForegroundColor Gray
    } catch {
        Write-Host "  Item $itemId : ERROR - $_" -ForegroundColor Red
    }
}

$stopwatch2.Stop()
Write-Host "Per-item execution time: $($stopwatch2.Elapsed.TotalSeconds) seconds"

# Summary
Write-Host ""
Write-Host "========== SUMMARY ==========" -ForegroundColor Green
Write-Host "Items tested: $($TestItemIds.Count)"
Write-Host ""
Write-Host "Method 1 (PnP Batch):"
if ($batchSuccess) {
    Write-Host "  Status: SUCCESS" -ForegroundColor Green
    Write-Host "  Time: $($stopwatch1.Elapsed.TotalSeconds) seconds"
    Write-Host "  Results: $($batchResults.Count) items"
} else {
    Write-Host "  Status: FAILED" -ForegroundColor Red
    Write-Host "  Recommendation: Skip Phase 3, use per-item approach"
}
Write-Host ""
Write-Host "Method 2 (Per-Item):"
Write-Host "  Time: $($stopwatch2.Elapsed.TotalSeconds) seconds"
Write-Host "  Results: $($perItemResults.Count) items"

if ($batchSuccess -and $stopwatch1.Elapsed.TotalSeconds -lt $stopwatch2.Elapsed.TotalSeconds) {
    $speedup = [math]::Round($stopwatch2.Elapsed.TotalSeconds / $stopwatch1.Elapsed.TotalSeconds, 1)
    Write-Host ""
    Write-Host "CONCLUSION: Batching is ${speedup}x faster!" -ForegroundColor Green
} elseif ($batchSuccess) {
    Write-Host ""
    Write-Host "CONCLUSION: Batching works but is not faster for this sample size." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "CONCLUSION: GET batching does NOT work. Skip Phase 3 of optimization." -ForegroundColor Red
}

Write-Host "==============================" -ForegroundColor Green

# Return results for comparison
return @{
    BatchSuccess = $batchSuccess
    BatchTimeSeconds = $stopwatch1.Elapsed.TotalSeconds
    PerItemTimeSeconds = $stopwatch2.Elapsed.TotalSeconds
    BatchResults = $batchResults
    PerItemResults = $perItemResults
    ItemsTested = $TestItemIds.Count
}
