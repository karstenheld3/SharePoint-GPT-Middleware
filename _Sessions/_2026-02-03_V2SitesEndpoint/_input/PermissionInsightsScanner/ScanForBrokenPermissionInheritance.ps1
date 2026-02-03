Add-Type -AssemblyName System.Web
#################### START: LOAD INCLUDE AND GET CREDENTIALS ####################
# if you set $global:dontClearScreen = $true outside of this script it will not clear the screen (intended for appending to previous outputs)
if ($global:dontClearScreen -eq $null) {cls}; Remove-Variable * -ErrorAction SilentlyContinue;[system.gc]::Collect()
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
# read password file from C:\users\[LOGGED_IN_USER]\AppData\Local\[ACCOUNT].txt or create new one and create credentials
# You can also create [ACCOUNT].txt in command line: "PASSWORD_HERE" | ConvertTo-SecureString -AsPlainText -Force | ConvertFrom-SecureString | Out-File "$($env:LOCALAPPDATA)\[ACCOUNT].txt"
$spoCredentials = Get-CredentialsOfUser -username "a7afe51@eur.corp.vattenfall.com"
$azureCredentials = Get-CredentialsOfUser -username "a7afe51@eur.corp.vattenfall.com"
#################### END: LOAD INCLUDE AND GET CREDENTIALS ######################

$scriptTitle = "Scan for broken permission inheritance"
######################### START: VARIABLES TO BE CHANGED BY USER #########################
$resumeAfterInterruption = $false
$loadLibrariesFromSubsites = $true # if site url is given, it will load libraries from the site and all subsites
# LOGGING AND SAVING
$writeEveryXLines = 100
$logEveryXFiles = 50
$fieldsToLoad = @("SharedWithUsers","SharedWithDetails") # if empty, will add all found custom list fields
$doNotResolveTheseGroups = @("Everyone except external users","all VF users","all VF externals","all VF internals")
$ignoreAccounts = @("SHAREPOINT\system","app@sharepoint","c:0!.s|windows")
$ignorePermissionLevels = @("Limited Access")
$ignoreSharePointGroups = $false
$maxGroupNestinglevel = 5
$outputColumns = @("LoginName","DisplayName","Email","PermissionLevel","SharedDateTime","SharedByDisplayName","SharedByLoginName","ViaGroup","ViaGroupId","ViaGroupType","AssignmentType","NestingLevel","ParentGroup")
######################### END: VARIABLES TO BE CHANGED BY USER ###########################

$builtInLists = @("Access Requests", "App Packages", "appdata", "appfiles", "Apps in Testing", "AuditLogs", "Cache Profiles", "Composed Looks", "Content and Structure Reports", "Content type publishing error log", "Converted Forms", "Device Channels", "Documents", "Form Templates", "fpdatasources", "Get started with Apps for Office and SharePoint", "List Template Gallery", "Long Running Operation Status", "Maintenance Log Library", "Master Docs", "Master Page Gallery", "MicroFeed", "NintexFormXml", "Notification List", "Project Policy Item List", "Quick Deploy Items", "Relationships List", "Reporting Metadata", "Reporting Templates", "Reusable Content", "Search Config List", "Site Assets", "Site Collection Documents", "Site Collection Images", "Site Pages", "Solution Gallery", "Style Library", "Suggested Content Browser Locations", "TaxonomyHiddenList", "Theme Gallery", "Translation Packages", "Translation Status", "User Information List", "Variation Labels", "Web Part Gallery", "wfpub", "wfsvc", "Workflow History", "Workflow Tasks")
$ignoreFields = @("_CheckinComment","_CommentCount","_ComplianceFlags","_ComplianceTag","_ComplianceTagUserId","_ComplianceTagWrittenTime","_CopySource","_DisplayName","_dlc_DocId","_dlc_DocIdUrl","_ExtendedDescription","_IsRecord","_LikeCount","_ModerationComments","_ModerationStatus","_UIVersionString","Author","AppAuthor","AppEditor","CheckoutUser","ComplianceAssetId","ContentType","Created","DocIcon","Edit","Editor","FileSizeDisplay","FileLeafRef","FolderChildCount","ID","ItemChildCount","Language","LinkTitle","LinkFilename","LinkFilenameNoMenu","MediaServiceAutoTags","MediaServiceOCR","MediaServiceKeyPoints","Modified","ParentVersionString","PublishingStartDate","PublishingExpirationDate","ParentLeafName","SharedWithUsers","SharedWithDetails","Tag","Title")
$ignorePermissionLevelsHash = @{}; $ignorePermissionLevels | ForEach-Object { $ignorePermissionLevelsHash[$_] ="" }

Write-ScriptHeader $scriptTitle

$inputFile = "PermissionInsightsScanner-In.csv" # input file
$inputFile = Join-Path $PSScriptRoot "$($inputFile)" # append path where this script is located

$outputFile2 = "Output2.csv" # file with same name as this script, just with '-In.csv' at the end
$outputFile2 = Join-Path $PSScriptRoot "$($outputFile2)" # append path where this script is located
$outputFile2Header = "Url"
if(Test-Path $outputFile2) { Remove-Item -Path $outputFile2 }

$outputFileTemplate = (Get-Item $MyInvocation.MyCommand.Definition).Basename + "-Out-[NUMBER].csv" # file with same name as this script, just with '-Out.csv' at the end
$outputFileTemplate = Join-Path $PSScriptRoot "$($outputFileTemplate)" # append path where this script is located
$outputFileHeaderTemplate = "ItemId,ItemType,ItemUrl"
$outputFileHeader ="" # will be created later depending on which fields were found in the library

$summaryFile = (Get-Item $MyInvocation.MyCommand.Definition).Basename + "-Summary.csv" # file with same name as this script, just with '-Summary.csv' at the end
$summaryFile = Join-Path $PSScriptRoot "$($summaryFile)" # append path where this script is located
$summaryFileHeader = "Job,LastLib,LastItem,Type,ItemsScanned,BrokenPermissions,Url"
$userDisplayNameCache = @{}

function WriteFiles() {
    if ($outputlines.Count -gt 0){ 
        Write-Host "  Writing $($outputlines.Count) lines to '$outputFile'..." -ForegroundColor Cyan
        if (!(Test-Path $outputFile)) { [System.IO.File]::WriteAllLines($outputFile, @($outputFileHeader), (New-Object System.Text.UTF8Encoding $False)) }
        [System.IO.File]::AppendAllLines([string]$outputFile, [string[]]$outputlines, (New-Object System.Text.UTF8Encoding $False))
        $outputlines.Clear()
    }
    Write-Host "  Writing '$summaryFile'..." -ForegroundColor Cyan
    if (!(Test-Path $summaryFile)) { [System.IO.File]::WriteAllLines($summaryFile, @($summaryFileHeader), (New-Object System.Text.UTF8Encoding $False)) }

    $url2 = CSV-Escape-Text -value $url
    
    # "Job,LastLib,LastItem,Type,Item,Folders,Url"
    $line = "$(([string]($jobIndex+1)).PadLeft(3))" # job
    $line += ",$(([string]($listIndex+1)).PadLeft(3))" # last library
    $line += ",$(([string]($itemIndex+1)).PadLeft(7))" # last item
    $line += ",$($urlType.PadRight(7," "))" # type
    $line += ",$(([string]$numberOfItems).PadRight(7," "))" # number of items scanned
    $line += ",$(([string]$numberOfBrokenPermissionInheritances).PadRight(7," "))" # number of broken permissions
    $line += ",$url2"

    $summaryLines =  [System.IO.File]::ReadAllLines($summaryFile, (New-Object System.Text.UTF8Encoding $False))
    $found = $false
    # search for line of current job and overwrite it if found
    for($lineIndex=0;$lineIndex -lt $summaryLines.Count;$lineIndex++){
        $currentLine = [string]$summaryLines[$lineIndex]
        if ( ($currentLine.Length -gt 0) -and !($currentLine.StartsWith($summaryFileHeader)) ) {
            try { $jobIndexOfCurrentLine = [int]($currentLine.Split(",")[0]) - 1 }
            catch { continue }
            if ($jobIndex -eq $jobIndexOfCurrentLine) {
                # overwrite line
                $summaryLines[$lineIndex] = $line
                $found = $true
            }
        }
    }
    # if not found, add new line
    if (!$found){ $summaryLines+=$line }
    [System.IO.File]::WriteAllLines([string]$summaryFile, [string[]]$summaryLines, (New-Object System.Text.UTF8Encoding $False))

    Write-Host "  SUMMARY: $numberOfItems scanned." -ForegroundColor Cyan

    # trigger garbage collection to avoid high memory growth
    [system.gc]::Collect()
}

if (!$resumeAfterInterruption){
    [System.IO.File]::WriteAllLines($summaryFile, @($summaryFileHeader), (New-Object System.Text.UTF8Encoding $False))
    $existingOutputFiles = $outputFileTemplate.Replace("[NUMBER]","*")
    Remove-Item $existingOutputFiles
} else {
    $resumeAndInitializeValues = $true
    if (!(Test-Path $summaryFile)) { Write-Host "WARNING: Cannot resume because '$summaryFile' not found." -ForegroundColor yellow }
    else {
        $summaryFileLines = Import-CSV $summaryFile -Encoding UTF8
        if (($summaryFileLines | Measure-Object).Count -lt 1){ Write-Host "WARNING: Cannot resume because '$summaryFile' contains no job data." -ForegroundColor yellow }
        else {
            # read numbers and sizes from last job in summary file
            $lastJob = $summaryFileLines[-1]
            $resumeAtJobIndex=0;$resumeAtListIndex=0;$resumeAtItemIndex=0
            
            if ($lastJob.Job -ne $null) {
                if($lastJob.Type.Trim() -ne "ERROR") { $resumeAtJobIndex = $lastJob.Job - 1 } else { $resumeAtJobIndex = $lastJob.Job }
            }            
            if ( ($lastJob.Type.Trim() -ne "ERROR") -and ($lastJob.LastLib -ne $null) -and ($lastJob.LastItem -ne $null) -and ($lastJob.Files -ne $null) ) {
                $resumeAtListIndex = $lastJob.LastLib - 1
                $resumeAtItemIndex = $lastJob.LastItem - 1
                $numberOfBrokenPermissionInheritances = $lastJob.BrokenPermissions
                $numberOfItems = $lastJob.ItemsScanned
                $resumeAndInitializeValues = $false
            }            
        }
    }
}

Write-Host "Reading '$inputFile'..."
if (!(Test-Path $inputFile)) {throw "The input file does not exist: '$inputFile'" }
$inputCsv = Import-CSV $inputFile -Encoding UTF8
$jobCount = ($inputCsv | Measure-Object).Count

Write-Host "Connecting to Azure Active Directory..."
Connect-AzureAD -Credential $azureCredentials | out-null

# run over all rows in CSV

for ($jobIndex=0; $jobIndex -lt $jobCount; $jobIndex++) {
    if ($resumeAfterInterruption -and $jobIndex -lt $resumeAtJobIndex) { continue }    
    $inputLine = $inputCsv[$jobIndex]
    $url = [string]$inputLine.Url

    $outputFileNumber = ([string]($jobIndex+1)).PadLeft(3,"0")
    # build output file name and header
    $outputFile = $outputFileTemplate.Replace("[NUMBER]",$outputFileNumber)
    $outputFileHeader = $outputFileHeaderTemplate +","+ ($outputColumns -join ",")
    $outputLines = [System.Collections.ArrayList]@()
    $numberOfBrokenPermissionInheritances=0
    $groupMemberCache = @{}

    # skip empty url, otherwise decode % encoded characters if necessary and remove trailing '/'
    if($url.Length -eq 0) { continue }
    else {
        if ($url.Contains("%")){ $url = [string][System.Web.HttpUtility]::UrlDecode($url)}
        $url = $url.TrimEnd("/")
    }
    Write-Host "Job [ $($jobIndex+1) / $jobCount ] '$url'..."

    # Step 1: Detect Url type
    # ----------------- START: Extract $urlType [SITE|SUBSITE|LIBRARY|FOLDER|ERROR], $siteUrl and $libraryName -----------------

    # example url: 'https://vattenfall.sharepoint.com/sites/spst/111/222/Shared Documents/SharedFolder' where '111' and '222' would be subsites
    if (!$url.Contains("https://") -or !$url.Contains("/sites/")) { Write-Host "  ERROR: URL must start with 'https://' and contain '/sites/'!" -ForegroundColor red; continue }
    $libraryName = ""; $folderRelativeUrl = ""; $urlType = "" # 'SITE' or 'SUBSITE' or 'LIBRARY' or 'FOLDER'    
    $tenantUrl = $url.Substring(0,$url.IndexOf("/","https://".Length))
    $indexOfNextSlash = $url.IndexOf("/",$url.IndexOf("/sites/")+"/sites/".Length)
    if ($indexOfNextSlash -lt 0) { $urlType = "SITE"; $siteUrl = $url }
    else {
        $siteUrl = $url.Substring(0,$indexOfNextSlash)
        # example $folderRelativeUrl: '/sites/spst/111/222/Shared Documents/SharedFolder'
        $folderRelativeUrl = $url.Substring($url.IndexOf("/sites/"))
    }
    Write-Host "  Connecting to '$siteUrl'..."
    try { Connect-PnPOnline -Url $siteUrl –Credential $spoCredentials; $siteExists = $true }
    catch{
        if ( (([string]$_).IndexOf("(404)") -gt 1) -or (([string]$_).IndexOf("(401)") -gt 1) ) { $siteExists = $false }
        Write-Host "  ERROR: $_" -ForegroundColor red
    }
    if ($siteExists -eq $false){ $urlType="ERROR"}
    elseif ($urlType -eq ""){
        try {
            $folder = Get-PnPFolder $folderRelativeUrl -Includes ParentFolder -ErrorAction Stop
            $lastServerRelativeUrl = $folder.ServerRelativeUrl
            # for libraries in site collections the parent folder will be the site
            if ($siteUrl.ToLower().EndsWith($folder.ParentFolder.ServerRelativeUrl.TrimEnd("/").ToLower())){
                $urlType  = "LIBRARY"
                $libraryName = $folderRelativeUrl.Split("/")[-1]
                # reconstruct site or subsite url from $lastServerRelativeUrl by leaving out last split item
                $siteUrl = $tenantUrl + ($folderRelativeUrl.Split("/")[-1000..-2] -join "/")
            } else {
                try {                
                    # load next parent folder until 'File Not Found' exception is thrown (we arrived at the library level)
                    $stop = $false
                    while ( -not $stop ) {
                        $folder = Get-PnPFolder $folder.ParentFolder.ServerRelativeUrl -Includes ParentFolder -ErrorAction Stop
                        $lastServerRelativeUrl = $folder.ServerRelativeUrl
                        # example: /sites/[SITE]/[LIBRARY]/[FOLDER]
                        if ($lastServerRelativeUrl.Split("/").Count -eq 5){ $stop = $true }
                    } 
                } catch {}
                $urlType  = "FOLDER"
                # example $lastServerRelativeUrl: '/sites/spst/111/222/Shared Documents/SharedFolder'
                # extract second last item from split array
                $libraryName = $lastServerRelativeUrl.Split("/")[-2]
                # reconstruct site or subsite url from $lastServerRelativeUrl by leaving out last 2 split items
                $siteUrl = $tenantUrl + ($lastServerRelativeUrl.Split("/")[-1000..-3] -join "/")
            }
        } catch {
            if (([string]$_).IndexOf("has not been initialized") -gt 1){ $urlType  = "ERROR"; continue}
            # subsite or library
            $subSites = Get-PnPSubWeb -Recurse
            $subSite = $subSites | Where-Object { $_.ServerRelativeUrl.ToLower() -eq $folderRelativeUrl.ToLower() }
            if($subSite -ne $null){
                $urlType  = "SUBSITE"
                $siteUrl = $tenantUrl + $folderRelativeUrl
            } else {
                # either library or invalid url
                if ($folderRelativeUrl.Split("/").Count -gt 3 ){
                    # assume it's a library in subsite and try to connect to subsite (3 = number of slashes if site is site collection)
                    $siteUrl = $tenantUrl + ($folderRelativeUrl.Split("/")[-1000..-2] -join "/")
                    try { Connect-PnPOnline -Url $siteUrl –Credential $spoCredentials }
                    catch{ if ( (([string]$_).IndexOf("(404)") -gt 1) -or (([string]$_).IndexOf("(401)") -gt 1) ) { $urlType="ERROR"; $siteExists = $false } }
                }
                try { 
                    $library = (Get-PnPList -ErrorAction Stop | Where-Object {($_.BaseTemplate -eq 101) -and ($_.Hidden -eq $false) -and `
                        ($_.DefaultViewUrl.Substring(0, $_.DefaultViewUrl.IndexOf("/Forms")).ToLower() -eq $folderRelativeUrl.ToLower()) })
                } catch {$library = $null }
                if ($library -ne $null){
                    $urlType  = "LIBRARY"
                    $libraryName = $folderRelativeUrl.Split("/")[-1]
                    # reconstruct site or subsite url from $lastServerRelativeUrl by leaving out last split item
                    $siteUrl = $tenantUrl + ($folderRelativeUrl.Split("/")[-1000..-2] -join "/")
                } else { $urlType  = "ERROR" }
            }
        }
    }

    # ------------------ END: Extract $urlType [SITE|SUBSITE|LIBRARY|FOLDER|ERROR], $siteUrl and $libraryName ------------------

    # Step 2: load all lists
    $lists = @()
    switch ($urlType){
        { $_ -in "SITE","SUBSITE" } {
            Write-Host "  Loading all libraries of site '$siteUrl'..."
            # connect if it's a subsite, otherwise it's already connected
            if ($urlType -eq "SUBSITE") { Connect-PnPOnline -Url $subSite.Url -Credential $spoCredentials }
            $lists = (Get-PnPList | Where-Object {($_.BaseTemplate -eq 101) -and ($_.Hidden -eq $false) -and ($_.Title -eq "Documents" -or !$builtInLists.Contains($_.Title)) })
            # make sure all return types create valid array: $null, single item, array of items
            if($lists -eq $null) { $lists = @() }
            elseif($lists.GetType().toString() -ne "System.Object[]") { $lists = @($lists) }
            if ($loadLibrariesFromSubsites){
                $subSites = Get-PnPSubWeb -Recurse
                foreach($subSite in $subSites){
                    Connect-PnPOnline -Url $subSite.Url -Credential $spoCredentials
                    $subSiteLists = (Get-PnPList | Where-Object {($_.BaseTemplate -eq 101) -and ($_.Hidden -eq $false) -and ($_.Title -eq "Documents" -or !$builtInLists.Contains($_.Title)) })
                    if($subSiteLists -eq $null) { $subSiteLists = @() }
                    elseif($subSiteLists.GetType().toString() -ne "System.Object[]") { $subSiteLists = @($subSiteLists) }
                    $lists += $subSiteLists
                }
            }
        }
        { $_ -in "LIBRARY","FOLDER" } {
            Write-Host "  Loading library '$libraryName' of site '$siteUrl'..."
            Connect-PnPOnline -Url $siteUrl -Credential $spoCredentials
            $list = Get-PnPList -Identity $libraryName
            $lists = @($list)
        }
    }
    # Write-Host "  Found libraries: $($lists.Count)"

    # Step 3 run over all libraries and load all files per library

    if ( !$resumeAfterInterruption -or ($resumeAfterInterruption -and $resumeAndInitializeValues) ) { $numberOfItems = 0 }

    for ($listIndex=0; $listIndex -lt $lists.Count; $listIndex++) {
        $filesWritten = $false

        if ($resumeAfterInterruption -and ($jobIndex -eq $resumeAtJobIndex) -and ($listIndex -lt $resumeAtListIndex) ) { continue }

        $list = $lists[$listIndex]
        $listName = $list.Title
        $listRelativeUrl = $list.DefaultViewUrl.Substring(0,$list.DefaultViewUrl.IndexOf('/Forms'))
        Write-Host "  Scanning library $($listIndex+1) of $($lists.Count): '$listRelativeUrl'..."
        $siteUrl = $tenantUrl + $list.ParentWebUrl
        # if we have only 1 list and the type is LIBRARY or FOLDER we do not need to connect again
        if ( ! ($lists.Count -eq 1 -and ($urlType -in "LIBRARY","FOLDER")) ){            
            Connect-PnPOnline -Url $siteUrl -Credential $spoCredentials
        }
        $fields = @()
        $listFields = (Get-PnPField -List $listName | Where-Object { ($_.Hidden -eq $false) -and ($_.AutoIndexed -eq $false) })
        # add additional fields 
        foreach($field in $listFields) {
            if ($fieldsToLoad.Count -gt 0) {
                if ($fieldsToLoad.Contains($field.StaticName)) { $fields += $field.StaticName }
            } else {
                if (!$ignoreFields.Contains($field.StaticName)) { $fields += $field.StaticName }                
            }
        }

        # get all items in list and sort by full filename
        $items = Get-PnPListItem -List $listName -PageSize 4995 -Fields $fields | Sort-Object -Property @{Expression = {$_["FileRef"]}; Descending = $False}
        if($items -eq $null) { $items = @() } elseif($items.GetType().toString() -ne "System.Object[]") { $items = @($items) }
        $allItems = [System.Collections.ArrayList]@()
        # add files to be scanned
        foreach($item in $items){
            # if url type is folder, ignore files that are not below folder
            if ( ($urlType -eq "FOLDER") -and ( ! ([string]$item["FileRef"]).StartsWith($folderRelativeUrl,"CurrentCultureIgnoreCase") ) ) { continue }
            $allItems.Add($item) | out-null
        }

        # Step 4: Run over items and search for items with broken permission inheritance

        # add all site users to user display name cache (needed to output display names for users who shared items)
        Get-PnPUser | ForEach-Object {
            if ( $_.LoginName.Contains("@") ){
                $loginName = $_.LoginName.Split("|")[2]
                if (!$userDisplayNameCache.ContainsKey($loginName)){ $userDisplayNameCache[$loginName] = $_.Title }
            }
        }

        $itemCount =0
        $filesWritten = $false
        for ($itemIndex=0; $itemIndex -lt $allItems.Count; $itemIndex++) {
           
            if ($resumeAfterInterruption -and ($jobIndex -eq $resumeAtJobIndex) -and ($listIndex -eq $resumeAtListIndex) -and ($itemIndex -le $resumeAtItemIndex) ) { continue }

            $numberOfItems++
            $item = $allItems[$itemIndex]
            $itemId = $item.Id
            $fileRelativeUrl = $item["FileRef"]
            $fileUrl = CSV-Escape-Text -value ($tenantUrl + $fileRelativeUrl)
            $isFolder = ($item.FieldValues["FSObjType"] -eq 1)
            # get individual users who have access to this file
            $sharedWithUsersArray = $item.FieldValues["SharedWithUsers"]
            if ($sharedWithUsersArray -eq $null) { continue }
            $numberOfBrokenPermissionInheritances++

            Write-Host "  Getting permissions for '$fileUrl'..."
            # get details of sharing
            $sharedWithDetailsHashmap = @{}
            if ( ($item.FieldValues["SharedWithDetails"] -ne $null) -and (([string]$item.FieldValues["SharedWithDetails"]).Length -gt 0) ){
                $sharedWithDetailsObject = ConvertFrom-Json -InputObject $item.FieldValues["SharedWithDetails"]
                $sharedWithDetailsObject.PSObject.Properties | ForEach-Object {
                    $loginName = ([string]$_.Name).Split("|")[2]
                    $dateTime = $_.Value.DateTime
                    $sharedByLoginName = $_.Value.LoginName
                    $sharedWithDetailsHashmap[$loginName] = @{"LoginName" = $loginName; "SharedDateTime" = $dateTime; "SharedByLoginName" = $sharedByLoginName}
                }
            }

            # get individual permissions (called role assignments), and load fields 'RoleDefinitionBindings' and 'Member' for each role assignment
            # replaces the following lines:
            # Get-PnPProperty -ClientObject $item -Property RoleAssignments | out-null
            # foreach ( $roleAssignment in $item.RoleAssignments ) { Get-PnPProperty -ClientObject $roleAssignment -Property RoleDefinitionBindings, Member }
            Load-CSOMProperties -parentObject $item -collectionObject $item.RoleAssignments -propertyNames @("RoleDefinitionBindings", "Member") -parentPropertyName "RoleAssignments" -executeQuery
            
            # build existing permissions hashmap: key = group or login name, value = Hashmap with properties "PermissionLevel", "ViaGroup", "ViaGroupId"
            $sharingData = @{}
            $sharingData2 = [System.Collections.ArrayList]@()
            # sort role assignments by display name (group or account)
            $roleAssignments = $item.RoleAssignments | Sort-Object -Property { $_.Member.Title }
            foreach ( $roleAssignment in $roleAssignments ) {                
                $loginName = ""; $permissionLevel = ""; $viaGroup = ""; $viaGroupId = ""
                $permissionLevels = @();                
                # collect permission levels but do not add ignored permission levels
                $roleAssignment.RoleDefinitionBindings | ForEach-Object {                    
                    if (!$ignorePermissionLevelsHash.Contains($_.Name)) { $permissionLevels +=  $_.Name }
                }
                $permissionLevel = ($permissionLevels -join ", ")
                # if no permission levels were collected after removing all ignored permission levels, ignore this role assignment
                if ($permissionLevels.Count -eq 0) { continue }
                $principalType = $roleAssignment.Member.PrincipalType
                switch ($principalType) {
                    "User" {
                        $loginName = $roleAssignment.Member.LoginName.Split("|")[2]
                        $displayName = $roleAssignment.Member.Title
                        $email = $roleAssignment.Member.Email
                        $details = @{}

                        # if the login name contains ignored account name, ignore account
                        $ignoreAccount = ($ignoreAccounts | where { ([string]$loginName).Contains($_)}).Count -gt 0
                        if ($ignoreAccount) { continue }

                        if ($sharedWithDetailsHashmap.ContainsKey($loginName)){ $details = $sharedWithDetailsHashmap[$loginName] }
                        # add sharing user display name from cache
                        if ( ($details.SharedByLoginName -ne $null) -and ($userDisplayNameCache.Contains($details.SharedByLoginName)) ) {
                            $details["SharedByDisplayName"] = $userDisplayNameCache[$details.SharedByLoginName]
                        }
                        $sharingDataObject = @{"LoginName" = $loginName; "DisplayName" = $displayName; "Email" = $email; "PermissionLevel" = $permissionLevel; "SharedDateTime" = $details.SharedDateTime; "SharedByDisplayName" = $details.SharedByDisplayName; "SharedByLoginName" = $details.SharedByLoginName; "ViaGroup" = ""; "ViaGroupId" = ""; "AssignmentType" ="Direct"; "ParentGroup" = ""}
                        $sharingData[$loginName] = $sharingDataObject
                        $sharingData2.Add($sharingDataObject) | Out-Null
                    }
                    # if group is SharePoint or Azure Security Group
                    { $_ -in "SharePointGroup", "SecurityGroup" } {
                        $groupStack = @()
                        $nestingLevel = 0

                        # put group into group stack but ignore SharePoint groups if $ignoreSharePointGroups = $true
                        if ( ($principalType -eq "SharePointGroup") -and (!$ignoreSharePointGroups) ) {
                            $groupStack += @{"Id" = $roleAssignment.Member.Id; "Name" = $roleAssignment.Member.LoginName; "Type" = $principalType; "NestingLevel" = $nestingLevel }
                        } elseif ($principalType -eq "SecurityGroup") {
                            $groupStack += @{"Id" = $roleAssignment.Member.LoginName.Split("|")[2]; "Name" = $roleAssignment.Member.Title; "Type" = $principalType; "NestingLevel" = $nestingLevel }
                        }

                        while ( ($groupStack.Count -gt 0) -and ( $nestingLevel -le $maxGroupNestinglevel) ) {
                            $currentGroup = $groupStack[-1]
                            $groupNestingLevel = $currentGroup.NestingLevel
                            $viaGroupId = $currentGroup.Id
                            $viaGroup = $currentGroup.Name
                            $groupType = $currentGroup.Type

                            # remove current group from stack
                            if ($groupStack.Count -gt 1) { $groupStack = $groupStack[0..($groupStack.Count-2)] } else { $groupStack = @() }

                            # if group should not be resolved, add unresolved group to sharingData 
                            $doNotResolveGroup = ($doNotResolveTheseGroups | where { $viaGroup.Contains($_)}).Count -gt 0
                            if ($doNotResolveGroup) {
                                $sharingDataObject = @{"LoginName" = ""; "DisplayName" = "All members of '$viaGroup'"; "Email" = ""; "PermissionLevel" = $permissionLevel; "SharedDateTime" = ""; "SharedByDisplayName" = ""; "SharedByLoginName" = ""; "ViaGroup" = $viaGroup; "ViaGroupId" = $viaGroupId; "AssignmentType" = $groupType; ; "NestingLevel" = $groupNestingLevel+1; ; "ParentGroup" = ""}
                                $sharingData[$loginName] = $sharingDataObject
                                $sharingData2.Add($sharingDataObject) | out-null
                                continue
                            }

                            Write-Host "    Getting members of group '$viaGroup' [NestingLevel $groupNestingLevel]..."
                            switch ($groupType) {
                                "SharePointGroup" {
                                    # get members and store in cache if not already done
                                    if (!$groupMemberCache.ContainsKey($viaGroupId)){
                                        try { $members = Get-PnPGroupMember -Group $viaGroup -ErrorAction Stop}
                                        catch { Write-Host "ERROR: Get-PnPGroupMember -Group $viaGroup" -ForegroundColor white -BackgroundColor red; Write-Host $_}
                                        if($members -eq $null) { $members = @() } elseif($members.GetType().toString() -ne "System.Object[]") { $members = @($members) }
                                        # sort members by 'Title' (group or account display name)
                                        if($members.Count -gt 0) { $members = $members | Sort-Object -Property "Title" }
                                        $groupMemberCache[$viaGroupId] = $members
                                    }
                                    foreach ($groupMember in $groupMemberCache[$viaGroupId]) {
                                        # if the login name contains ignored account name, ignore the group member
                                        $ignoreAccount = ($ignoreAccounts | where { ([string]$groupMember.LoginName).Contains($_)}).Count -gt 0
                                        if ($ignoreAccount) { continue }
                                        if ($groupMember.LoginName.Contains("|")){
                                            $loginName = [string]$groupMember.LoginName.Split("|")[2]
                                        } else {
                                            $loginName = [string]$groupMember.LoginName
                                        }
                                        # if login name contains '@' or '\' or '/' it can't be a group and we assume it's an account
                                        $isAccount = ( $loginName.Contains("@") -or $loginName.Contains("\") -or $loginName.Contains("/") )
                                        $displayName = $groupMember.Title
                                        # if group is azure group, add to group stack, else add member
                                        if ($isAccount){
                                            # add user to output
                                            $email = $groupMember.Email
                                            $sharingDataObject = @{"LoginName" = $loginName; "DisplayName" = $displayName; "Email" = $email; "PermissionLevel" = $permissionLevel; "SharedDateTime" = ""; "SharedByDisplayName" = ""; "SharedByLoginName" = ""; "ViaGroup" = $viaGroup; "ViaGroupId" = $viaGroupId; "AssignmentType" = $groupType; ; "NestingLevel" = $groupNestingLevel+1; ; "ParentGroup" = ""}
                                            $sharingData[$loginName] = $sharingDataObject
                                            $sharingData2.Add($sharingDataObject) | Out-Null
                                        } else {
                                            # add group to group stack
                                            $currentGroup["SharingDetails"] = @{} # add empty sharing details object
                                            $groupStack += @{"Id" = $loginName; "Name" = $displayName; "Type" = "SecurityGroup"; "NestingLevel" = $groupNestingLevel+1; "ParentGroup" = $currentGroup}                                            
                                        }
                                    }
                                }
                                "SecurityGroup" {
                                    if (!$groupMemberCache.ContainsKey($viaGroupId)){
                                        
                                        # if group id contains '@' or '\' or '/' it can't be a group and we assume it's an account
                                        $isAccount = ( $viaGroupId.Contains("@") -or $viaGroupId.Contains("\") -or $viaGroupId.Contains("/") )

                                        if (!$isAccount) {
                                            try { $members = (Get-AzureADGroup -ObjectId $viaGroupId | Get-AzureADGroupMember -All $true) }
                                            catch { Write-Host "ERROR: Get-AzureADGroup -ObjectId $viaGroup" -ForegroundColor white -BackgroundColor red; Write-Host $_ }
                                            if($members -eq $null) { $members = @() } elseif($members.GetType().toString() -ne "System.Object[]") { $members = @($members) }
                                            # sort members by 'DisplayName' (group or account)
                                            if($members.Count -gt 0) { $members = $members | Sort-Object -Property "DisplayName" }
                                            $groupMemberCache[$viaGroupId] = $members
                                        }
                                    }
                                    $details = @{}
                                    # if group is nested group, take sharing details from parent group (stored in group when group is put on stack), otherwise get sharing details from cache
                                    if ($groupNestingLevel -gt 0) {
                                        $details = $currentGroup.ParentGroup.SharingDetails
                                    } elseif ($sharedWithDetailsHashmap.ContainsKey($viaGroupId)) {
                                        $details = $sharedWithDetailsHashmap[$viaGroupId]
                                    }
                                    foreach($groupMember in $groupMemberCache[$viaGroupId]) {
                                        if ($groupMember.ObjectType -eq "Group"){
                                            $currentGroup["SharingDetails"] = $details # pass details to next nested group as parent group
                                            $groupStack += @{"Id" = $groupMember.ObjectId; "Name" = $groupMember.DisplayName; "Type" = "SecurityGroup"; "NestingLevel" = $groupNestingLevel+1; "ParentGroup" = $currentGroup }
                                        } else {
                                            $loginName = $groupMember.UserPrincipalName
                                            $displayName = $groupMember.DisplayName
                                            $email = $groupMember.Mail
                                            # add sharing user display name from cache
                                            if ( ($details.SharedByLoginName -ne $null) -and ($userDisplayNameCache.Contains($details.SharedByLoginName)) ) {
                                                $details["SharedByDisplayName"] = $userDisplayNameCache[$details.SharedByLoginName]
                                            }
                                            if ($currentGroup.ParentGroup -ne $null){ $parentGroupName = $currentGroup.ParentGroup.Name } else { $parentGroupName = "" }
                                            $sharingDataObject = @{"LoginName" = $loginName; "DisplayName" = $displayName; "Email" = $email; "PermissionLevel" = $permissionLevel; "SharedDateTime" = $details.SharedDateTime; "SharedByDisplayName" = $details.SharedByDisplayName; "SharedByLoginName" = $details.SharedByLoginName; "ViaGroup" = $viaGroup; "ViaGroupId" = $viaGroupId; "AssignmentType" = $groupType; "NestingLevel" = $groupNestingLevel+1; "ParentGroup" = $parentGroupName}
                                            $sharingData[$loginName] = $sharingDataObject
                                            $sharingData2.Add($sharingDataObject) | Out-Null
                                        }
                                    }
                                }
                            }
                            # calculate nesting level of stack
                            $nestingLevel = 0
                            foreach ($group in $groupStack) { if( $group.NestingLevel -gt $nestingLevel ){ $nestingLevel = $group.NestingLevel } }
                        }
                    }
                }
            }
            
            # run over all persons who have access
            foreach($data in $sharingData2 ) {                
                $loginName = $data.LoginName
                $permissionLevel = $data.PermissionLevel
                # "ItemId,ItemType,ItemUrl,..."
                if ($isFolder){ $itemType = "FOLDER" } else  { $itemType = "FILE" }

                $line = "$itemId,$itemType,$fileUrl"
                foreach($field in $outputColumns){
                    $value = $data[$field]
                    if ($value -eq $null){ $value = ""}
                    else { $value = ConvertSharePointFieldToTextOrValueType -value $value }
                    $line += ("," + (CSV-Escape-Text -value $value))
                }
                # add outputline
                $outputLines.Add($line) | out-null
            }

            # write output files
            if( !$filesWritten -and ($outputLines.Count -ge $writeEveryXLines) ){ WriteFiles; }
        } # for loop that runs over files
        
        if(!$filesWritten){ WriteFiles; $filesWritten=$true }

    } # for loop that runs over lists
    
    # after we have resumed a job, values need to be initialized (reset to zero)
    if($resumeAfterInterruption){ $resumeAndInitializeValues = $true }

    if(!$filesWritten){ WriteFiles; $filesWritten=$true }
    
} # loop over rows in input csv

Write-ScriptFooter $scriptTitle