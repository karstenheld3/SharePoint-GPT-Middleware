#################### START: LOAD INCLUDE AND GET CREDENTIALS ####################
# if you set $global:dontClearScreen = $true outside of this script it will not clear the screen (intended for appending to previous outputs)
if ($global:dontClearScreen -eq $null) {cls}; #Remove-Variable * -ErrorAction SilentlyContinue
# returns the full path of a file to be found; first searches in given path and then in any parent path up to the root; returns "" if not found
function SearchFileInFolderOrAnyParentFolder([string]$path, [string]$filename) {
    $testfilename = (Join-Path $path $filename)
    do {$found = (Test-Path $testfilename); if(!$found){ $path = (Split-Path -Path $path -Parent); $testfilename = (Join-Path $path $filename) } }
    while (!$found -and ($testfilename.Length -gt $filename.Length + 3)) # stop if we reach 'C:\[filename]'
    if($found) { return $testfilename } else { return "" }
}
# load include file
$includeFile1 = (SearchFileInFolderOrAnyParentFolder -path $PSScriptRoot -filename "_includes.ps1")
if ($includeFile1 -eq ""){Write-Host "ERROR: Include file not found! Put '_includes.ps1' in script or parent folder" -ForegroundColor Red; exit}
. $includeFile1

# Define tasks array
$tasks = @(
    @{ siteURL = "https://vattenfall.sharepoint.com/sites/HouseofIT";listName = "SPoC BIO List";outputSubFolder = "HOIT"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/HouseofIT";listName = "List of Acronyms - House of IT";outputSubFolder = "HOIT"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/HouseofIT";listName = "Roles in VIT";outputSubFolder = "HOIT"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/HouseofIT";listName = "Security training catalog";outputSubFolder = "HOIT"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/HouseofIT";listName = "SPoC BIO List";outputSubFolder = "HOIT"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/HouseofIT";listName = "VIT Health & Safety contacts per country";outputSubFolder = "HOIT"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/HouseofIT";listName = "VIT Health & Safety contacts per country";outputSubFolder = "HOIT"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/HouseofIT";listName = "YISPS MOC Roles and responsibilities";outputSubFolder = "HOIT"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/NMS-VMS";listName = "VMS Publication and Republication list";outputSubFolder = "VMS"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/NMS-VMS";listName = "Selected Controls for VMS Follow Up";outputSubFolder = "VMS"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/NMS-SMS";listName = "Glossary";outputSubFolder = "SMS"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/NMS-SMS";listName = "Group SMS legal framework";outputSubFolder = "SMS"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/NMS-SMS";listName = "Security Organisation";outputSubFolder = "SMS"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/spst";listName = "CarBrands";outputSubFolder = "MYSITE"}
    ,@{ siteURL = "https://vattenfall.sharepoint.com/sites/spst";listName = "CarModels";outputSubFolder = "MYSITE"}
)

$autoDetectFieldsToExport = $true # $true = $fieldsToExport will not be used; $false = all fields except $fieldsToIgnore will be exported
$fieldsToExport = @("Confidential Class","Description","Document Type","LiveLink ID","Nickname","Title","Created","Editor","Modified")
$removeLineBreaksFromFieldValues = $true # $true: all linebreaks will be removed from exported field values, making it easier to import the CSV fo Excel
$useFieldDisplayNames = $true # $true: use field display names (can vary across SharePoint display languages) instead of internal names


$fieldsToIgnore = @("Author","Created","Editor","Comment","Modified","_ColorTag","_CommentCount","_ComplianceFlags","_ComplianceTag","_ComplianceTagUserId","_ComplianceTagWrittenTime","_CopySource","_DisplayName",
"_dlc_DocId","_dlc_DocIdUrl","_IsRecord","_LikeCount","_ModerationStatus","_UIVersionString","AppAuthor","AppEditor","Attachments","CheckoutUser",
"ComplianceAssetId","ContentType","DocIcon","Edit","FileSizeDisplay","FolderChildCount","ItemChildCount","LinkTitle","LinkFilename","LinkFilenameNoMenu",
"MediaServiceAutoTags","MediaServiceLocation","MediaServiceOCR","ParentVersionString","SharedWithDetails","SharedWithUsers")
$hideEmptyFields = $false # if $autoDetectFieldsToExport = $true then $true = analyze which fields contain values and only export fields where we have at least 1 row with a value

$scriptTitle = "Export list items to CSV"
Write-ScriptHeader $scriptTitle

# Process each task
foreach ($task in $tasks) {
    $siteURL = $task.siteURL
    $listName = $task.listName
    $outputSubFolder = $task.outputSubFolder
    $outputFolder = Join-Path $PSScriptRoot $outputSubFolder
    if (!(Test-Path $outputFolder)) { New-Item -ItemType Directory -Path $outputFolder | Out-Null }

    Write-Host "Processing task for list '$listName' with output to '$outputFileCsv'" -ForegroundColor Yellow

    if (!$siteURL.Contains("https://") -or !$siteURL.Contains("/sites/")) { 
        Write-Host "  ERROR: URL must start with 'https://' and contain '/sites/'!" -ForegroundColor red
        continue
    }
    $tenantUrl = $siteURL.Substring(0,$siteURL.IndexOf("/","https://".Length))

    Write-Host "Connecting to '$($siteURL)'..."
    $env:ENTRAID_APP_ID = "1b1f528e-1f33-4f14-b7b0-8e31cf987588"

    # Connect to SharePoint
    Connect-PnPOnline -Url $siteURL -Interactive
    $list = Get-PnPList -Identity $listName
    $listUrlName = Split-Path -Path $list.RootFolder.ServerRelativeUrl -Leaf
    $isDocumentLibrary = ($list.BaseTemplate -eq 101)
    $outputFileCsv = Join-Path $outputFolder "$listUrlName.csv"
    $outputFileMd = Join-Path $outputFolder "$listUrlName.md"

    $fieldNames = [System.Collections.ArrayList]@()
    if ($autoDetectFieldsToExport) {
        $fields = (Get-PnPField -List $listName | Where-Object { ($_.Hidden -eq $false) -and ($_.AutoIndexed -eq $false) -and (!$fieldsToIgnore.Contains($_.StaticName)) })
        # add fields to arraylist
        foreach($field in $fields){$fieldNames.Add($field.InternalName) | Out-Null}
        $fieldNames = ($fieldNames | Sort-Object)
    } else { foreach($field in $fieldsToExport) { $fieldNames.Add($field) | out-null } }

    Write-Host "Getting all list items of '$listName'..."
    $items = Get-PnPListItem -List $list -PageSize 4995 -Fields $fieldNames

    if ($autoDetectFieldsToExport -and $hideEmptyFields) {
        Write-Host "Identifying fields that contain values..."
        $usedFieldsHashmap = @{}
        foreach($fieldName in $fieldNames){
            $hasValues = $false
            foreach($item in $items){
                if ($null -ne $item.FieldValues[$fieldName]) { $hasValues = $true; break }
            }
            if ($hasValues){ $usedFieldsHashmap.Add($fieldName,1) | out-null }
        }
        $usedFields = [System.Collections.ArrayList]@()
        # add all used field names to sorted array
        foreach($usedField in $usedFieldsHashmap.GetEnumerator() | Sort-Object Name ) { $usedFields.Add($usedField.Name) | out-null }
        $fieldNames = $usedFields
    }

    # add ID and document library fieldsat first positions
    $tempArray = [System.Collections.ArrayList]@()
    foreach($fieldName in $fieldNames){ if ($fieldName -ne "ID" ) {$tempArray.Add($fieldName) | Out-Null } }
    $fieldNames = $tempArray
    if ($isDocumentLibrary) {  $fieldNames = @("ID","Url","ItemType") + $fieldNames}
    else { $fieldNames = @("ID") + $fieldNames}

    # initialize output csv contents
    if ($useFieldDisplayNames){
        $fieldDisplayNames = [System.Collections.ArrayList]@()
        # search for field in $fields and collect field display names
        foreach($fieldName in $fieldNames){
            $field = $fields | Where-Object { $_.InternalName -eq $fieldName }
            if ($null -ne $field) { $fieldDisplayName = $field.Title } else { $fieldDisplayName = $fieldName }
            $fieldDisplayNames.Add($fieldDisplayName) | Out-Null
        }
        $header = ($fieldDisplayNames -join ",")
    } else {
        $header = ($fieldNames -join ",")
    }

    $outputCsv = [System.Collections.ArrayList]@()
    $outputCsv.Add($header) | out-null
    $outputMd = [System.Collections.ArrayList]@()
    $outputMd.Add("## $listName") | out-null

    # run over items
    foreach($item in $items){
        $values = [System.Collections.ArrayList]@()
        if ($null -eq $item.FieldValues.Title) {
            $title = $item.FieldValues.Title
        } else {
            $title = "Item $($item.ID)"
        }
        $outputMd.Add("`n### ""$listName"" - $title ") | out-null
        foreach($fieldName in $fieldNames){

            switch ($fieldName){
                "Url" {
                    $fileRelativeUrl = $item["FileRef"]
                    $originalValue = $tenantUrl + $fileRelativeUrl
                }
                "ItemType"{
                    switch($item["FSObjType"]){
                        0 { $originalValue = "File"}
                        1 { $originalValue = "Folder"}
                    }
                }
                default {
                    $originalValue = $item.FieldValues[$fieldName]
                }
            }
            
            if ($null -ne $originalValue) {$value = ConvertSharePointFieldToTextOrValueType -value $originalValue}
            else { $value = $originalValue}
            if ($null -ne $value){
                if ($value.GetType().Name -eq "String"){
                    if ($removeLineBreaksFromFieldValues){ $value = $value.Replace("`r","").Replace("`n","") }
                    $value  = CSV-Escape-Text -value $value # csv escape value
                } else {
                    $value = $value.ToString()
                }
            }
            $values.Add($value) | out-null
        }
        $csvLine = $values -join ","
        $outputCsv.Add($csvLine) | out-null
        for ($i = 0; $i -lt $values.Count; $i++) {
            if ( ($fieldDisplayNames[$i] -eq "ID") -or ($null -eq $values[$i]) -or ($values[$i] -eq "")) { continue }
            $mdLine = "**$($fieldDisplayNames[$i])**: $($values[$i])"
            $outputMd.Add($mdLine) | out-null
        }
    }

    Write-Host "Output written to '$outputFileCsv'." -ForegroundColor green 
    [System.IO.File]::WriteAllLines($outputFileCsv, $outputCsv, (New-Object System.Text.UTF8Encoding $False))
    Write-Host "Output written to '$outputFileMd'." -ForegroundColor green 
    [System.IO.File]::WriteAllLines($outputFileMd, $outputMd, (New-Object System.Text.UTF8Encoding $False))
}

Write-ScriptFooter $scriptTitle
