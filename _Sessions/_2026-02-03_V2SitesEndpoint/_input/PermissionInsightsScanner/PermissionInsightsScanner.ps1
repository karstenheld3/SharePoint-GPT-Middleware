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
$spoCredentials = Get-CredentialsOfUser -username "karsten.held@whizzyapps.com" -verifyPassword $false
$azureCredentials = $spoCredentials
#################### END: LOAD INCLUDE AND GET CREDENTIALS ######################

$scriptTitle = "Permission Insights Scanner"

# What it does: Export permissions of SharePoint site / subsite / library / folder defined in input file as CSV files into output folder per url (also called 'job').
# Output files:
#    '01_SiteContents.csv'
#    '02_SiteGroups.csv'
#    '03_SiteGroupMembers.csv'
#    '04_SitePermissions.csv'
#    '05_IndividualPermissionItems.csv'
#    '06_IndividualPermissionItemAccess.csv'
# How it works:
# 1. Read input file with jobs (csv with just one column 'Url'; supported url types: SITE, SUBSITE, LIBRARY, or FOLDER)
# 2. If $resumeAfterInterruption = $true, load summary file and try to resume at last interruption
# 3. Identify url type (SITE, SUBSITE, LIBRARY, FOLDER, ERROR). Site collection urls with many subsites can be stored in $siteUrlsWithManySubsites to speed up type detection.
# 4. If url type is SITE or SUBSITE and $loadSubsites = $true, load all subsites in addition to parent site
# 5. Run over site (or site + subsites) and export into separate files in job folder: 1) site contents, 2) site groups, 2) site group members, 4) site permissions
# 6. If url type is LIBRARY or FOLDER, load all list items, scan for broken permissions and write in job folder: 5) broken permission inheritances
# 7: If url type is SITE or SUBSITE, load all lists of site (or site + subsites) except those defined in $builtInLists, scan for broken permissions and write in job folder: 5) broken permission inheritances

######################### START: VARIABLES TO BE CHANGED BY USER #########################
# LOGGING AND SAVING
$writeEveryXLines = 100
$logEveryXFiles = 50
# these built-in or custom Azure AD groups should not be resolved (because either the can't be resolved or they contain too many members)
$doNotResolveTheseGroups = @("Everyone except external users","all VF users","all VF externals","all VF internals")
$ignoreAccounts = @("SHAREPOINT\system","app@sharepoint","c:0!.s|windows")
$ignorePermissionLevels = @("Limited Access")
$omitSharePointGroupsInBrokenPermissionsFile = $false # if $true, will omit users who have access via SharePoint groups (owners, members, visitors, custom group members).
$loadSubsites = $true
$maxGroupNestinglevel = 5
$siteUrlsWithManySubsites = @("https://vattenfall.sharepoint.com/sites/projects","https://vattenfall.sharepoint.com/sites/departments","https://vattenfall.sharepoint.com/sites/communities")
$loadBuiltInListIfNameMatches = @("Documents","Site Pages")
# https://learn.microsoft.com/en-us/openspecs/sharepoint_protocols/ms-wssts/8bf797af-288c-4a1d-a14b-cf5394e636cf
$loadListIfTemplateMatches = @{100 = "LIST"; 101 = "LIBRARY"; 119 = "SITEPAGES"}
$useAzureActiveDirectoryPowerShellModule = $true
$dateFormat = "yyyy-MM-ddTHH:mm:ss"
######################### END: VARIABLES TO BE CHANGED BY USER ###########################

######################### START: VARIABLES TO BE CHANGED BY DEVELOPER ####################
$permissionLevelSeparator = ", "
$builtInLists = @("Access Requests", "App Packages", "appdata", "appfiles", "Apps in Testing", "AuditLogs", "Cache Profiles", "Composed Looks", "Content and Structure Reports", "Content type publishing error log", "Converted Forms", "Device Channels", "Documents", "Form Templates", "fpdatasources", "Get started with Apps for Office and SharePoint", "List Template Gallery", "Long Running Operation Status", "Maintenance Log Library", "Master Docs", "Master Page Gallery", "MicroFeed", "NintexFormXml", "Notification List", "Project Policy Item List", "Quick Deploy Items", "Relationships List", "Reporting Metadata", "Reporting Templates", "Reusable Content", "Search Config List", "Site Assets", "Site Collection Documents", "Site Collection Images", "Site Pages", "Solution Gallery", "Style Library", "Suggested Content Browser Locations", "TaxonomyHiddenList", "Theme Gallery", "Translation Packages", "Translation Status", "User Information List", "Variation Labels", "Web Part Gallery", "wfpub", "wfsvc", "Workflow History", "Workflow Tasks")

$inputFile = (Get-Item $MyInvocation.MyCommand.Definition).Basename + "-In.csv" # file with same name as this script, just with '-In.csv' at the end
$inputFile = Join-Path $PSScriptRoot "$($inputFile)" # append path where this script is located

$outputFolderTemplate = Join-Path $PSScriptRoot "[JOB_NUMBER] [SITE_URL_PART]"

$outputFilename1SiteContents = "01_SiteContents.csv"
$outputColumns1SiteContents = @("Id","Type","Title","Url")
function newSiteContentsRow($id,$type,$title,$url){ return "$id,$($type),$(CSV-Escape-Text -value $title),$(CSV-Escape-Text -value $url)" }

$outputFilename2SiteGroups = "02_SiteGroups.csv"
$outputColumns2SiteGroups = @("Id","Role","Title","PermissionLevel","Owner")
function newSiteGroupsRow($id,$role,$title,$permmissionLevel,$owner){ return "$($id),$($role),$(CSV-Escape-Text -value $title),$(CSV-Escape-Text -value $permmissionLevel),$($owner)" }

$outputFilename3SiteUsers = "03_SiteUsers.csv"
$outputColumns3SiteUsers = @("Id","LoginName","DisplayName","Email","PermissionLevel","ViaGroup","ViaGroupId","ViaGroupType","AssignmentType","NestingLevel","ParentGroup")
function newSiteUserRow($id,$loginName,$displayName,$email,$permissionLevel,$viaGroup,$viaGroupId,$viaGroupType,$assignmentType,$nestingLevel,$parentGroup){ return "$($id),$($loginName),$(CSV-Escape-Text -value $displayName),$($email),$(CSV-Escape-Text -value $permissionLevel),$(CSV-Escape-Text -value $viaGroup),$($viaGroupId),$($viaGroupType),$($assignmentType),$($nestingLevel),$(CSV-Escape-Text -value $parentGroup)" }

$outputFilename4IndividualPermissionItems = "04_IndividualPermissionItems.csv"
$outputColumns4IndividualPermissionItems = @("Id","Type","Title","Url")
function newIndividualPermissionItemRow($id,$type,$title,$url){ return "$($id),$($type),$($title),$(CSV-Escape-Text -value $url)" }

$outputFilename5IndividualPermissionItemAccess = "05_IndividualPermissionItemAccess.csv"
$outputColumns5IndividualPermissionItemAccess = @("Id","Type","Url","LoginName","DisplayName","Email","PermissionLevel","SharedDateTime","SharedByDisplayName","SharedByLoginName","ViaGroup","ViaGroupId","ViaGroupType","AssignmentType","NestingLevel","ParentGroup")
function newIndividualPermissionItemAccessRow($id,$type,$url,$loginName,$displayName,$email,$permissionLevel,$sharedDateTime,$sharedByDisplayName,$sharedByLoginName,$viaGroup,$viaGroupId,$viaGroupType,$assignmentType,$nestingLevel,$parentGroup){
    if ($sharedDateTime -eq $null){ $sharedDateTimeString = "" }
    elseif ($sharedDateTime.GetType().Name -eq "DateTime") {
        $localDate = [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId($sharedDateTime, (Get-TimeZone).Id)
        $sharedDateTimeString = $localDate.ToString($dateFormat)
    } else { $sharedDateTimeString = "" }
    return "$($id),$($type),$(CSV-Escape-Text -value $url),$($loginName),$(CSV-Escape-Text -value $displayName),$($email),$(CSV-Escape-Text -value $permissionLevel),$($sharedDateTimeString),$( CSV-Escape-Text -value $sharedByDisplayName),$($sharedByLoginName),$( CSV-Escape-Text -value $viaGroup),$($viaGroupId),$($viaGroupType),$($assignmentType),$($nestingLevel),$(CSV-Escape-Text -value $parentGroup)"
}

$summaryFile = (Get-Item $MyInvocation.MyCommand.Definition).Basename + "-Summary.csv" # file with same name as this script, just with '-Summary.csv' at the end
$summaryFile = Join-Path $PSScriptRoot "$($summaryFile)" # append path where this script is located
$summaryFileColumns = @("Job","LastLib","LastItem","Type","ScannedItems","BrokenPermissions","Url")
######################### END: VARIABLES TO BE CHANGED BY DEVELOPER ######################

function ensureSharePointSiteIsConnected ([string]$siteUrl, $credentials) {
    # make sure site is connected: connect if context is $null or urls do not match
    try { $ctx = Get-PnPContext -ErrorAction SilentlyContinue } catch {}
    if ( ($ctx -eq $null) -or ($ctx.Url.ToLower() -ne $siteUrl.ToLower()) ) { Connect-PnPOnline -Url $siteUrl -Credentials $credentials }
    try { $ctx = Get-PnPContext -ErrorAction SilentlyContinue } catch {}
    if ( ($ctx -eq $null) -or ($ctx.Url.ToLower() -ne $siteUrl.ToLower()) ) { return $false }
    if ($siteUrl -eq "") { return $false } else { return $true }
}

function GetListUrl($list){
    switch ($list.BaseTemplate){
        # 101 = 'Document Library', 119 = 'Wiki Page Library' aka 'Site Pages'
        { $_ -in 101,119 } { $listUrl = $tenantUrl + ($list.DefaultViewUrl.Substring(0,$list.DefaultViewUrl.IndexOf('/Forms'))) }
        default { $listUrl = $tenantUrl + ($list.DefaultViewUrl.Substring(0,$list.DefaultViewUrl.LastIndexOf('/'))) }
    }
    return $listUrl
}

# writes SharePoint group and its members to group / group member file output lines; assumes that working connection to SharePoint site exist
# -recurse gets members of all nested azure groups recursively
# TODO: Add group owner
function addGroupAndGroupMembersToOutputLines() {
    param(
        [Parameter(Mandatory=$true)][Microsoft.SharePoint.Client.Principal]$group,
        [Parameter(Mandatory=$true)]$roleAssignments,
        [Parameter(Mandatory=$true)][System.Collections.ArrayList]$groupOutputLines,
        [Parameter(Mandatory=$true)][System.Collections.ArrayList]$userOutputLines,
        [Parameter(Mandatory=$true)][AllowEmptyString()][string]$role,
        [Parameter(Mandatory=$false)][switch]$recurse = $false
    )
    # collect permission levels of group but do not add ignored permission levels
    $permissionLevels = @();
    foreach ( $roleAssignment in $roleAssignments ) {
        if ($roleAssignment.PrincipalId -eq $group.Id) {
            $roleAssignment.RoleDefinitionBindings | ForEach-Object { if (!$ignorePermissionLevels.Contains($_.Name)) { $permissionLevels +=  $_.Name } }
            break
        }
    }
    $permissionLevel = ($permissionLevels -join $permissionLevelSeparator)
    $groupOutputLines.Add( (newSiteGroupsRow -id $group.Id -role $role -title $group.Title -permmissionLevel $permissionLevel -owner "") ) | Out-Null
    if ($recurse){ $groupMembers = getSharePointGroupMembers -group $group -recurse }
    else {$groupMembers = getSharePointGroupMembers -group $group }
    # make sure all return types create valid array: $null, single item, array of items
    if($groupMembers -eq $null) { $groupMembers = @() } elseif($groupMembers.GetType().toString() -ne "System.Object[]") { $groupMembers = @($groupMembers) }

    foreach($m in $groupMembers){
        $userOutputLines.Add( (newSiteUserRow -id $m["Id"] -loginName $m["LoginName"] -displayName $m["DisplayName"] -email $m["Email"] -permissionLevel $permissionLevel -viaGroup $m["ViaGroup"] -viaGroupId $m["ViaGroupId"] -viaGroupType $m["ViaGroupType"] -assignmentType "Group" -nestingLevel $m["NestingLevel"] -parentGroup $m["ParentGroup"]) ) | out-null
    }
}

# returns SharePoint group members as arraylist of hashmaps; assumes that working connection to SharePoint site exist
# key: user login name or azure group id; value: hashmap with 'LoginName', 'DisplayName', 'Email', 'ViaGroup', 'ViaGroupId','GroupType','ParentGroup', 'NestingLevel'
# -recurse gets members of all nested azure groups recursively
function getSharePointGroupMembers(){
    param(
        [Parameter(Mandatory=$true)][Microsoft.SharePoint.Client.Principal]$group,
        [Parameter(Mandatory=$false)][switch]$recurse = $false
    )
    $groupMembers = [System.Collections.ArrayList]@()    
    # if cache contains group id, then return group members from cache
    if ($global:sharePointGroupMemberCache.ContainsKey($group.Id)) {
        $groupMembers = $global:sharePointGroupMemberCache[$group.Id]
        return $groupMembers
    }

    try {
        $members = Get-PnPGroupMember -Group $group -ErrorAction Stop
        if($members -eq $null) { $members = @() } elseif($members.GetType().toString() -ne "System.Object[]") { $members = @($members) }
    } catch { Write-Host "ERROR: Get-PnPGroupMember -Group $viaGroup" -f  white -b red; Write-Host $_}
    # sort members by 'Title' (group or account display name)
    if($members.Count -gt 1) { $members = $members | Sort-Object -Property "Title" }
    foreach($member in $members){
        if ($ignoreAccounts.Contains($member.LoginName)){ continue }
        switch ($member.PrincipalType){
            "User" {
                $loginName = $member.LoginName.Split("|")[2]
                if ($ignoreAccounts.Contains($loginName)){ continue }
                $groupMembers.Add( @{"Id"=$member.Id; "LoginName"=$loginName; "DisplayName"=$member.Title; "Email"=$member.Email; "ViaGroup" = $group.Title; "ViaGroupId" = $group.Id; "ViaGroupType"="SharePointGroup"; "NestingLevel"=1; "ParentGroup"=""} ) | out-null
                # add display name to cache so we can later retrieve it when an item has been shared by this user
                if(!$global:userDisplayNameCache.ContainsKey($loginName)){ $global:userDisplayNameCache[$loginName] = $member.Title }
            }
            "SecurityGroup" {
                # M365 group example: $member.LoginName = 'c:0o.c|federateddirectoryclaimprovider|0319638f-ac31-4d7a-bfbf-7658f770c619_o'
                $groupId = [string]($member.LoginName.Split("|")[2])
                # if not groupId not available, add as user and continue
                if ($groupId -eq ""){
                    $groupMembers.Add( @{"Id"=$member.Id; "LoginName"=$loginName; "DisplayName"=$member.Title; "Email"=$member.Email; "ViaGroup" = $group.Title; "ViaGroupId" = $group.Id; "ViaGroupType"="SharePointGroup"; "NestingLevel"=1; "ParentGroup"=""} ) | out-null
                    continue
                }                
                # identify group type and strip trailing '_o' from groupId for M365 groups
                # TODO: find better way to identify M365 groups as sometimes the '_o' suffix is missing when group is M365 group
                if ($groupId.EndsWith("_o")){ $groupType = "M365Group"; $groupId = $groupId.TrimEnd("_o")}
                else { $groupType = "SecurityGroup"}

                if ($recurse) {
                    $azureGroupMembers = (getAzureGroupMembers -groupId $groupId -groupType $groupType -nestingLevel 1 -parentGroup $group.Title -recurse)
                    if($azureGroupMembers -eq $null) { $azureGroupMembers = @() } elseif($azureGroupMembers.GetType().toString() -ne "System.Object[]") { $azureGroupMembers = @($azureGroupMembers) }
                    if ($azureGroupMembers.count -gt 0) { $groupMembers.AddRange($azureGroupMembers) | Out-Null }
                } else {
                    # load group properties from azure to avoid outdated group names (SharePoint keeps old group name if group is being renamed)
                    try {
                        if ($useAzureActiveDirectoryPowerShellModule){ $azureGroup = Get-AzureADGroup -ObjectId $groupId }
                        else { $azureGroup = Get-PnPAzureADGroup -Identity  $groupId }
                        # keep it compatible with AAD and PnP PowerShell module (AAD = group.Mail; PnP = group.UserPrincipalName)
                        if ($azureGroup.Mail -ne $null) { $email = [string]$azureGroup.Mail } else { $mail = $azureGroup.UserPrincipalName }
                        $groupMembers.Add( @{"Id"=$member.Id; "LoginName"=$groupId; "DisplayName"=$azureGroup.DisplayName; "Email"=$email; "ViaGroup" = ""; "ViaGroupId" = ""; "ViaGroupType"=$groupType; "NestingLevel"=1; "ParentGroup"=$group.Title} ) | out-null
                    } catch {
                        if ($useAzureActiveDirectoryPowerShellModule) { Write-Host "ERROR: Get-AzureADGroup -ObjectId $groupId" -f white -b red; Write-Host $_ }
                        else { Write-Host "ERROR: Get-PnPAzureADGroup -Identity $groupId" -f white -b red; Write-Host $_ }                        
                        $groupMembers.Add( @{"Id"=$member.Id; "LoginName"=$groupId; "DisplayName"=$member.Title; "Email"=$member.Email; "ViaGroup" = ""; "ViaGroupId" = ""; "ViaGroupType"=$groupType; "NestingLevel"=1; "ParentGroup"=$group.Title} ) | out-null
                    }                    
                }
            }
        }
    }
    # store group members in cache
    $global:sharePointGroupMemberCache[$group.Id] = $groupMembers
    return $groupMembers
}

# returns Azure group members as arraylist of hashmaps; assumes that $global:azureGroupMemberCache hashmap exists
# key: user login name or azure group id; value: hashmap with 'LoginName', 'DisplayName', 'Email' 
# -recurse gets members of all nested azure groups recursively
function getAzureGroupMembers(){
    param(
        [Parameter(Mandatory=$true)][string]$groupId,
        [Parameter(Mandatory=$true)][string]$groupType,
        [Parameter(Mandatory=$false)][long]$nestingLevel=0,
        [Parameter(Mandatory=$false)][string]$parentGroup="",
        [Parameter(Mandatory=$false)][switch]$recurse = $false
    )
    $groupMembers = [System.Collections.ArrayList]@()

    # if cache contains group id, then return group members from cache
    if ($global:azureGroupMemberCache.ContainsKey($groupId)) {
        $groupMembers = $global:azureGroupMemberCache[$groupId]
        return $groupMembers
    }
    if ( $useAzureActiveDirectoryPowerShellModule){
        try { $azureGroup = Get-AzureADGroup -ObjectId $groupId }
        catch { Write-Host "ERROR: Get-AzureADGroup -ObjectId $groupId" -f white -b red; Write-Host $_; return $groupMembers }
    } else {
        try { $azureGroup = Get-PnPAzureADGroup -Identity $groupId }
        catch { Write-Host "ERROR: Get-PnPAzureADGroup -Identity $groupId" -f white -b red; Write-Host $_; return $groupMembers }
    }


    if ($recurse){
        # add first group to group stack
        $groupStack = @( @{"GroupId"=$groupId; "DisplayName"= $azureGroup.DisplayName; "ViaGroupType"=$groupType; "NestingLevel" = $nestingLevel} )

        while ( ($groupStack.Count -gt 0) -and ( $nestingLevel -le $maxGroupNestinglevel) ) {
            $currentGroup = $groupStack[-1]
            $groupNestingLevel = $currentGroup.NestingLevel
            $viaGroupId = $currentGroup.GroupId
            $viaGroup = $currentGroup.DisplayName
            $groupType = $currentGroup.GroupType

            # remove current group from stack
            if ($groupStack.Count -gt 1) { $groupStack = $groupStack[0..($groupStack.Count-2)] } else { $groupStack = @() }

            # if group should not be resolved, add unresolved group to group members
            if ($doNotResolveTheseGroups.Contains($viaGroup)) {
                # increase nesting level by 1, except for first group in group stack (the group passed into this function)
                if ($viaGroupId -eq $groupStack[0].GroupId) { $tempNestingLevel = $groupNestingLevel } else { $tempNestingLevel = $groupNestingLevel+1 }
                $groupMembers.Add( @{"LoginName" = ""; "DisplayName" = $viaGroup; "Email" = ""; "ViaGroup" = $viaGroup; "ViaGroupId" = $viaGroupId; "ViaGroupType" = $groupType; "NestingLevel" = $tempNestingLevel; "ParentGroup" = $parentGroup} ) | Out-Null
                continue
            }
            Write-Host "    Getting members of group '$viaGroup' [NestingLevel $groupNestingLevel]..."
            if ($viaGroup -eq ""){
                $debug = "EMPTY GROUP"
            }
            # if group id contains '@' or '\' or '/' it can't be a group and we assume it's an account
            $isAccount = ( $viaGroupId.Contains("@") -or $viaGroupId.Contains("\") -or $viaGroupId.Contains("/") )
            if (!$isAccount) {                    
                $groupType = "SecurityGroup"
                if ( $useAzureActiveDirectoryPowerShellModule){
                    try { $members = Get-AzureADGroupMember -ObjectId $viaGroupId -All $true }
                    catch { Write-Host "ERROR: Get-AzureADGroup -ObjectId $viaGroupId" -f white -b red; Write-Host $_ }
                } else {
                    try { $members = Get-PnPAzureADGroupMember -Identity $viaGroupId }
                    catch { Write-Host "ERROR: Get-PnPAzureADGroupMember -Identity $viaGroupId" -f white -b red; Write-Host $_ }
                }
                if($members -eq $null) { $members = @() } elseif($members.GetType().toString() -ne "System.Object[]") { $members = @($members) }
                # sort members by 'DisplayName' (group or account)
                if($members.Count -gt 1) { $members = $members | Sort-Object -Property "DisplayName" }                
            }
            $groupsToBeAddedToGroupStack = @()
            foreach($groupMember in $members) {
                $displayName = $groupMember.DisplayName
                # keep it compatible with AAD and PnP PowerShell module (AAD = group.ObjectType; PnP = group.Type)
                if ($groupMember.ObjectType -ne $null) { $objectType = $groupMember.ObjectType } else { $objectType = $groupMember.Type }
                if ($groupMember.ObjectId -ne $null) { $objectId = $groupMember.ObjectId } else { $objectId = $groupMember.UserPrincipalName }
                if ($groupMember.Mail -ne $null) { $email = [string]$groupMember.Mail } else { $mail = $groupMember.UserPrincipalName }

                if ($currentGroup.ParentGroup -eq $null) { $parentGroupName = $parentGroup }
                elseif ($currentGroup.ParentGroup.GetType().Name -eq "String") { $parentGroupName = $currentGroup.ParentGroup }
                else { $parentGroupName = $currentGroup.ParentGroup.DisplayName }
                if ( ($objectType -eq "Group") ) {
                    if ($recurse) {
                        # if recurse, add group to group stack
                        $groupsToBeAddedToGroupStack += @{"GroupId" = $objectId; "DisplayName" = $displayName; "GroupType" = "SecurityGroup"; "NestingLevel" = $groupNestingLevel+1; "ParentGroup" = $currentGroup }
                    } else {
                        # otherwise add group to members
                        $groupMembers.Add( @{"LoginName" = ""; "DisplayName" = $displayName; "Email" = $email; "ViaGroup" = $viaGroup; "ViaGroupId" = $viaGroupId; "ViaGroupType" = $groupType; "NestingLevel" = $groupNestingLevel+1; "ParentGroup" = $parentGroupName} ) | Out-Null                        
                    }
                } else {
                    # add user to group to members
                    $loginName = $groupMember.UserPrincipalName
                    $groupMembers.Add( @{"LoginName" = $loginName; "DisplayName" = $displayName; "Email" = $email; "ViaGroup" = $viaGroup; "ViaGroupId" = $viaGroupId; "ViaGroupType" = $groupType; "NestingLevel" = $groupNestingLevel+1; "ParentGroup" = $parentGroupName} ) | Out-Null
                }
            }
            # add groups to group stack, but in reverse order so that the last group on the stack has the displayName that comes first
            if ($groupsToBeAddedToGroupStack.Count -gt 0){
                if ($groupsToBeAddedToGroupStack.Count -gt 1){
                    $groupsToBeAddedToGroupStack = ($groupsToBeAddedToGroupStack | Sort-Object -Property @{Expression={ $_.DisplayName }} -Descending)
                }
                $groupStack += $groupsToBeAddedToGroupStack
            }
            # calculate nesting level of stack
            $nestingLevel = 0
            foreach ($group in $groupStack) { if( $group.NestingLevel -gt $nestingLevel ){ $nestingLevel = $group.NestingLevel } }
        }
    } else {
        # if not recurse, add group members
        $groupMembers.Add( @{"LoginName"=$groupId; "DisplayName"=$azureGroup.DisplayName; "Email"=([string]$azureGroup.Mail); "ViaGroup" = ""; "ViaGroupId" = ""; "ViaGroupType"=$groupType; "NestingLevel"=$nestingLevel; "ParentGroup"=$parentGroup} ) | out-null
    }
    $global:azureGroupMemberCache[$groupId] = $groupMembers
    return $groupMembers
}

function appendToFile($file,$lines){
    if ($lines.Count -gt 0){
        [System.IO.File]::AppendAllLines([string]$file, [string[]]$lines, (New-Object System.Text.UTF8Encoding $False))
        Write-Host "    $($lines.Count) lines written to: '$file'" -f Cyan
    }
}

Write-ScriptHeader $scriptTitle

Write-Host "Reading '$inputFile'..."
if (!(Test-Path $inputFile)) {Write-Host "The input file does not exist: '$inputFile'" -f white -b red; exit }

$inputCsv = Import-CSV $inputFile -Encoding UTF8
# make sure all return types create valid array: $null, single item, array of items
if($inputCsv -eq $null) { $inputCsv = @() } elseif($inputCsv.GetType().toString() -ne "System.Object[]") { $inputCsv = @($inputCsv) }
$jobCount = $inputCsv.Count

Write-Host "$($jobCount) jobs found." -f white -b DarkCyan
if ($jobCount -eq 0) { exit }

# key: Azure group id; value: collection of azure member objects
# example keys: '99fa011b-d502-4544-875b-eda3b3fcc65b', '48a9c754-d32c-45c5-a7b2-cb1dbd1d48c9'
# will NOT be cleared after each job
$global:azureGroupMemberCache = @{} 

# key: SharePoint group id; value: array of group member hashmaps
# example keys: 13, 15, 5
# example value: @( @{"DisplayName" = "Karsten Held (YICMC) ext"; ...}, @{"DisplayName" = "John Doe (YINDD)"; ...} )
# will be cleared after each job
$global:sharePointGroupMemberCache = @{}

# key: user login name; value: user display name
# example keys: abc@company.com, afe51@eur.corp.vattenfall.com
# example values: "ABC", "Karsten Held (YICMC) ext"
# will be cleared after each job
$global:userDisplayNameCache = @{}

# key: group id (principal id); value: SharePoint group object
# example keys: 5, 6, 12
# will be cleared after each job
$global:sharePointGroupCache = @{}


# delete all existing output folders by searching for all folders that match the output folder limit
$existingOutputFolders = $outputFolderTemplate.Replace("[JOB_NUMBER]","????").Replace("[SITE_URL_PART]","*")
Remove-Item $existingOutputFolders -Force -Recurse

if ($useAzureActiveDirectoryPowerShellModule){
    Write-Host "Connecting to Azure Active Directory..."
    Connect-AzureAD -Credential $azureCredentials | out-null
}

# run over all rows in CSV
for ($jobIndex=0; $jobIndex -lt $jobCount; $jobIndex++) {
    $global:sharePointGroupMemberCache = @{}
    $global:userDisplayNameCache = @{}
    $global:sharePointGroupCache = @{}

    $inputLine = $inputCsv[$jobIndex]
    $url = [string]$inputLine.Url
    Write-Host "Job [ $($jobIndex+1) / $($jobCount) ] '$($url)'"
    # skip non-urls
    if (!$url.ToLower().StartsWith("https://") -or !$url.Contains("/sites/")) { Write-Host "  ERROR: URL must start with 'https://' and contain '/sites/'!" -f white -b red; continue }
    else {
        # decode urls with % encoding and remove trailing '/'
        if ($url.Contains("%")){ $url = [string][System.Web.HttpUtility]::UrlDecode($url)}
        $url = $url.TrimEnd("/")
    }
    $outputFolderSiteUrlPart = $url.Substring($url.ToLower().IndexOf("sites/")+6).Replace("/"," - ")
    # create output folder
    $outputJobNumber = ([string]($jobIndex+1)).PadLeft(4,"0")
    $outputFolder = $outputFolderTemplate.Replace("[JOB_NUMBER]",$outputJobNumber).Replace("[SITE_URL_PART]",$outputFolderSiteUrlPart)
    New-Item -Path $outputFolder -ItemType Directory | out-null

# Step 3: Detect url type
# ----------------- START: Extract $urlType [SITE|SUBSITE|LIBRARY|FOLDER|ERROR], $siteUrl and $libraryName -----------------

    # example url: 'https://vattenfall.sharepoint.com/sites/spst/111/222/Shared Documents/SharedFolder' where '111' and '222' would be subsites
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
    try { $result = ensureSharePointSiteIsConnected -siteUrl $siteUrl –credentials $spoCredentials; $siteExists = $result }
    catch{
        Write-Host "  ERROR: $_" -f white -b red
        if ( (([string]$_).IndexOf("(404)") -gt 1) -or (([string]$_).IndexOf("(401)") -gt 1) ) { $siteExists = $false }
        else { $urlType = "ERROR" }
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
                    $stop = $false
                    # example: /sites/[SITE]/[LIBRARY]/[FOLDER]
                    if ($lastServerRelativeUrl.Split("/").Count -le 5){ $stop = $true }
                    # load next parent folder until 'File Not Found' exception is thrown (we arrived at the library level)
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
            # url is subsite or library

            # first check if we know this site collection url to contain only subsites
            $isKnownSubSiteUrl = $false
            foreach($knownSubSiteUrl in $knownSubSiteUrls){
                if ($knownSubSiteUrl.TrimEnd("/").tolower() -eq $siteUrl.ToLower()) { $isKnownSubSiteUrl = $true; break }
            }
            if (!$isKnownSubSiteUrl){
                $subSites = Get-PnPSubWeb -Includes HasUniqueRoleAssignments,RoleAssignments -Recurse
                # make sure all return types create valid array: $null, single item, array of items
                if($subSites -eq $null) { $subSites = @() } elseif($subSites.GetType().toString() -ne "System.Object[]") { $subSites = @($subSites) }
                $subSite = $subSites | Where-Object { $_.ServerRelativeUrl.ToLower() -eq $folderRelativeUrl.ToLower() }
            } else {
                $subsite = $true
            }
            if($subSite -ne $null){
                $urlType  = "SUBSITE"
                $siteUrl = $tenantUrl + $folderRelativeUrl
            } else {
                # either library or invalid url
                if ($folderRelativeUrl.Split("/").Count -gt 3 ){
                    # assume it's a library in subsite and try to connect to subsite (3 = number of slashes if site is site collection)
                    $siteUrl = $tenantUrl + ($folderRelativeUrl.Split("/")[-1000..-2] -join "/")
                    try { $result = ensureSharePointSiteIsConnected -siteUrl $siteUrl -credentials $spoCredentials }
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

    if ( $urlType -eq "ERROR" ) { continue }

    $result = ensureSharePointSiteIsConnected -siteUrl $siteUrl -credentials $spoCredentials

    # if $loadSubsites = $true, write found number of subsites to console, otherwise create empty subsites array
    if ( $loadSubsites -and (($urlType -eq "SITE") -or ($urlType -eq "SUBSITE")) )  {
        Write-Host "  Loading subsites..."
        $subSites = Get-PnPSubWeb -Includes HasUniqueRoleAssignments,RoleAssignments -Recurse
        # make sure all return types create valid array: $null, single item, array of items
        if($subSites -eq $null) { $subSites = @() } elseif($subSites.GetType().toString() -ne "System.Object[]") { $subSites = @($subSites) }        
        if ($subSites.Count -gt 0) { Write-Host "  $($subSites.Count) subsites found." -f White -b DarkCyan }
    } else { $subSites = @() }
    $web = Get-PnPWeb -Includes HasUniqueRoleAssignments,RoleAssignments

    $sitesToScan = @($siteUrl)
    if ($subSites.Count -gt 0) { $sitesToScan += $subSites.Url }
    $siteCount = $sitesToScan.Count

    # prepare output files: create files and add header to output lines
    $outputLines1SiteContents = [System.Collections.ArrayList]@()
    $outputLines1SiteContents.Add(($outputColumns1SiteContents -join ",")) | Out-Null
    $outputFile1SiteContents = Join-Path $outputFolder $outputFilename1SiteContents

    $outputLines2SiteGroups = [System.Collections.ArrayList]@()
    $outputLines2SiteGroups.Add(($outputColumns2SiteGroups -join ",")) | Out-Null
    $outputFile2SiteGroups = Join-Path $outputFolder $outputFilename2SiteGroups

    $outputLines3SiteUsers = [System.Collections.ArrayList]@()
    $outputLines3SiteUsers.Add(($outputColumns3SiteUsers -join ",")) | Out-Null
    $outputFile3SiteUsers = Join-Path $outputFolder $outputFilename3SiteUsers

    $outputLines4IndividualPermissionItems = [System.Collections.ArrayList]@()
    $outputLines4IndividualPermissionItems.Add(($outputColumns4IndividualPermissionItems -join ",")) | Out-Null
    $outputFile4IndividualPermissionItems = Join-Path $outputFolder $outputFilename4IndividualPermissionItems

    $outputLines5IndividualPermissionItemAccess = [System.Collections.ArrayList]@()
    $outputLines5IndividualPermissionItemAccess.Add(($outputColumns5IndividualPermissionItemAccess -join ",")) | Out-Null
    $outputFile5IndividualPermissionItemAccess = Join-Path $outputFolder $outputFilename5IndividualPermissionItemAccess

# ------------------ START: Step 4 - Write groups, group members and site users to files ------------------

    # TODO: Add site collection admins (users and groups)

    # avoid writing groups to files multiple times by storing written group ids in this variable
    $sitePrincipalIdsThatHaveBeenWrittenToFile = @{}
    Write-Host "  Loading site groups..."
    # Naming convention:
    # 1) "job site": the site from the input file, can be a site collection or a subsite
    # 2) "current site: the site being currently processed, can be either the job site itself or a subsuite of the job site
    $groups = Get-PnPGroup # collection sorted by group title
    # make sure all return types create valid array: $null, single item, array of items
    if($groups -eq $null) { $groups = @() } elseif($groups.GetType().toString() -ne "System.Object[]") { $groups = @($groups) }
    if ($groups.Count -gt 3){ Write-Host "  $($groups.Count) groups found in site collection." -f White -b DarkCyan }
    # add to cache so we can later get a group by its id
    $groups | ForEach-Object { $global:sharePointGroupCache[$_.Id] = $:_ }

    $jobSiteOwnerGroup = Get-PnPGroup -AssociatedOwnerGroup; $jobSiteMemberGroup = Get-PnPGroup -AssociatedMemberGroup; $jobSiteVisitorGroup = Get-PnPGroup -AssociatedVisitorGroup
    
    # replaces the following lines:
    # foreach ( $roleAssignment in $web.RoleAssignments ) { Get-PnPProperty -ClientObject $roleAssignment -Property RoleDefinitionBindings, Member }
    Load-CSOMProperties -parentObject $web -collectionObject $web.RoleAssignments -propertyNames @("RoleDefinitionBindings", "Member","PrincipalId") -parentPropertyName "RoleAssignments" -executeQuery
    $roleAssignments = $web.RoleAssignments | Sort-Object -Property { $_.Member.Title }
    # make sure all return types create valid array: $null, single item, array of items
    if($roleAssignments -eq $null) { $roleAssignments = @() } elseif($roleAssignments.GetType().toString() -ne "System.Object[]") { $roleAssignments = @($roleAssignments) }
    
    # add all role assignments to cache; key: principal id (number), value = role assignment object
    $siteRoleAssignmentsCache = @{}; $roleAssignments | ForEach-Object { $siteRoleAssignmentsCache[$_.PrincipalId] = $_ }

    # write members of site owners, members, visitors groups at top of file
    if ($jobSiteOwnerGroup -ne $null) {
        addGroupAndGroupMembersToOutputLines -group $jobSiteOwnerGroup -role "SiteOwners" -roleAssignments $roleAssignments -groupOutputLines $outputLines2SiteGroups -userOutputLines $outputLines3SiteUsers -recurse
        $sitePrincipalIdsThatHaveBeenWrittenToFile[$jobSiteOwnerGroup.Id] = ""
    }
    if ($jobSiteMemberGroup -ne $null) {
        addGroupAndGroupMembersToOutputLines -group $jobSiteMemberGroup -role "SiteMembers" -roleAssignments $roleAssignments -groupOutputLines $outputLines2SiteGroups -userOutputLines $outputLines3SiteUsers -recurse
        $sitePrincipalIdsThatHaveBeenWrittenToFile[$jobSiteMemberGroup.Id] = ""
    }
    if ($jobSiteVisitorGroup -ne $null) {
        addGroupAndGroupMembersToOutputLines -group $jobSiteVisitorGroup "SiteVisitors" -roleAssignments $roleAssignments -groupOutputLines $outputLines2SiteGroups -userOutputLines $outputLines3SiteUsers -recurse
        $sitePrincipalIdsThatHaveBeenWrittenToFile[$jobSiteVisitorGroup.Id] = ""
    }

    # run over site collection groups and write only groups that are used by this site or subsite
    foreach ( $group in $groups ) {
        # if group is not owners / members / visitors group
        if (!$sitePrincipalIdsThatHaveBeenWrittenToFile.Contains($group.Id)) {
            # and there is a role assignment in the site or subsite that uses this group
            if ( $siteRoleAssignmentsCache.ContainsKey($group.Id) ) {
                addGroupAndGroupMembersToOutputLines -group $group -role "Custom" -roleAssignments $roleAssignments -groupOutputLines $outputLines2SiteGroups -userOutputLines $outputLines3SiteUsers -recurse
                break
            }
        }
    }

    # write site level users to file
    foreach ($roleAssignment in $roleAssignments) {
        if ($roleAssignment.Member.PrincipalType -eq "User") {
            if ($ignoreAccounts.Contains($roleAssignment.Member.LoginName)){ continue }
            $loginName = $roleAssignment.Member.LoginName.Split("|")[2]
            if ($ignoreAccounts.Contains($loginName)){ continue }
            $displayName = $roleAssignment.Member.Title
            $email = $roleAssignment.Member.Email
            $id = $roleAssignment.PrincipalId
            # collect permission levels but do not add ignored permission levels
            $permissionLevels = @();
            $roleAssignment.RoleDefinitionBindings | ForEach-Object { if (!$ignorePermissionLevels.Contains($_.Name)) { $permissionLevels +=  $_.Name } }
            $permissionLevel = ($permissionLevels -join $permissionLevelSeparator)
            $outputLines3SiteUsers.Add( (newSiteUserRow -id $id -loginName $loginName -displayName $displayName -email $email -permissionLevel $permissionLevels -viaGroup "" -viaGroupId "" -viaGroupType "" -assignmentType "User" -nestingLevel 0 -parentGroup "") ) | Out-Null
            $sitePrincipalIdsThatHaveBeenWrittenToFile[$roleAssignment.PrincipalId] = ""
        }
    }
    # append to output files and reset output lines
    appendToFile -file $outputFile2SiteGroups -lines $outputLines2SiteGroups; $outputLines2SiteGroups = [System.Collections.ArrayList]@()
    appendToFile -file $outputFile3SiteUsers -lines $outputLines3SiteUsers; $outputLines3SiteUsers = [System.Collections.ArrayList]@()

# ------------------ END: Step 4 - Write groups, group members and site users to files ------------------

# ------------------ START: Step 5 - Run over (site or subsite) and contained subsites and write output files ------------------

    for ($siteIndex=0; $siteIndex -lt $siteCount; $siteIndex++) {
        $currentSiteUrl = [string]$sitesToScan[$siteIndex]
        $isSubSite = !($siteUrl.ToLower() -eq $currentSiteUrl.ToLower())

        # make sure current site is connected
        $result = ensureSharePointSiteIsConnected -siteUrl $currentSiteUrl -credentials $spoCredentials
        if ($result = $false){ Write-Host "    ERROR: Could not connect to site '$currentSiteUrl'." -f White -b Red}
        
        if ($isSubSite -eq $true){
            $web = $subSites[$siteIndex-1]
            # add subsite in site contents file
            $outputLines1SiteContents.Add( (newSiteContentsRow -id $web.Id -type "SUBSITE" -title $web.Title -url $web.Url) ) | Out-Null
            # if subsite has broken permission inheritance, add to individual permission items file
            if ($web.HasUniqueRoleAssignments){ $outputLines4IndividualPermissionItems.Add( (newIndividualPermissionItemRow -id $web.Id -type "SUBSITE" -title $web.Title -url $currentSiteUrl) ) | Out-Null }
        }
       
        if ( !$isSubSite ){ Write-Host "  Loading site contents..." }
        else { Write-Host "  Subsite [ $($siteIndex) / $($subSites.Count) ] '$($currentSiteUrl)'..." }

        # do not load lists with base templates not in $loadListIfTemplateMatches
        # do not load hidden lists
        # do not load built-in lists except those in $loadBuiltInListIfNameMatches
        $lists = (Get-PnPList -Includes HasUniqueRoleAssignments,DefaultViewUrl | Where-Object {($loadListIfTemplateMatches.ContainsKey($_.BaseTemplate)) -and ($_.Hidden -eq $false) -and ($loadBuiltInListIfNameMatches.Contains($_.Title) -or !$builtInLists.Contains($_.Title)) })
        # make sure all return types create valid array: $null, single item, array of items
        if($lists -eq $null) { $lists = @() } elseif($lists.GetType().toString() -ne "System.Object[]") { $lists = @($lists) }

        if ($lists.Count -gt 0 ) { Write-Host "    $($lists.Count) lists found." -f White -b DarkCyan }
        foreach ($list in $lists) {
            # map list base template to human readable list type
            $listType = $loadListIfTemplateMatches[$list.BaseTemplate]
            # extract list url from list object
            $listUrl = GetListUrl -list $list
            $listRelativeUrl = $listUrl.Replace($tenantUrl,"")

            Write-Host "    Scanning $($listType.ToLower()) '$listUrl'..."
            # skip this list if this is not the job list 
            if( ($urlType -eq "LIBRARY") -or ($urlType -eq "FOLDER") ) {
                if (!$folderRelativeUrl.StartsWith($listRelativeUrl,"CurrentCultureIgnoreCase")) { continue}
            }

            # add new row for list in site contents file
            $outputLines1SiteContents.Add( (newSiteContentsRow -id $list.Id -type $listType -title $list.Title -url $listUrl) ) | Out-Null
            # if list has broken permission inheritance, add to individual permission items file
            if ($list.HasUniqueRoleAssignments){ $outputLines4IndividualPermissionItems.Add( (newIndividualPermissionItemRow -id $list.Id -type $listType -title $web.Title -url $listUrl ) ) | Out-Null }

            # get all items in list and sort by full filename
            $items = Get-PnPListItem -List $list.Title -PageSize 4995 | Sort-Object -Property @{Expression = {$_["FileRef"]}; Descending = $False}
            if($items -eq $null) { $items = @() } elseif($items.GetType().toString() -ne "System.Object[]") { $items = @($items) }
            if ($urlType -eq "FOLDER"){
                $allItems = [System.Collections.ArrayList]@()
                # add files to be scanned
                foreach($item in $items){
                    # if url type is folder, ignore files that are not below folder
                    if ( -not ([string]$item["FileRef"]).StartsWith($folderRelativeUrl,"CurrentCultureIgnoreCase") ) { continue }
                    $allItems.Add($item) | out-null
                }
            } else { $allItems = $items }

            if ($allItems.Count -gt 10){ Write-Host "    $($allItems.Count) items found." -f White -b DarkCyan }

            # run over all items and check for broken permission inheritance
            foreach ($item in $allItems){
                Get-PnPProperty -ClientObject $item -Property HasUniqueRoleAssignments | Out-Null
                # skip items with permission inheritance
                if (!$item.HasUniqueRoleAssignments) { continue }

                switch ($listType){
                    "LIST" {
                        $itemRelativeUrl = ($list.DefaultViewUrl + "?FilterField1=ID&FilterValue1=$($item.Id)")
                        $itemType = "ITEM"
                        $itemTitle = $item.FieldValues["Title"]
                    } 
                    { $_ -in "LIBRARY","SITEPAGES" } {
                        $itemRelativeUrl = [string]$item["FileRef"]
                        $itemTitle = [string]$item["FileLeafRef"]
                        if ($item.FieldValues["FSObjType"] -eq 1) { $itemType = "FOLDER" } else { $itemType = "FILE" }
                    }
                }

                $itemUrl =  ($tenantUrl + $itemRelativeUrl)

                # add item to individual permission items file
                $outputLines4IndividualPermissionItems.Add( (newIndividualPermissionItemRow -id $item.Id -type $itemType -title $itemTitle -url $itemUrl ) ) | Out-Null


                # get individual users who have access to this file
                $sharedWithUsersArray = $item.FieldValues["SharedWithUsers"]
                # get details of sharing
                $sharedWithDetailsHashmap = @{}
                if ( ($item.FieldValues["SharedWithDetails"] -ne $null) -and (([string]$item.FieldValues["SharedWithDetails"]).Length -gt 0) ){
                    $sharedWithDetailsObject = ConvertFrom-Json -InputObject $item.FieldValues["SharedWithDetails"]
                    $sharedWithDetailsObject.PSObject.Properties | ForEach-Object {
                        $loginName = [string]$_.Name
                        if ($loginName.Contains("|")){ $loginName = $loginName.Split("|")[2] }
                        # get display name of sharing user from cache if available
                        if ($global:userDisplayNameCache.Contains($loginName)) { $sharedByDisplayName = $global:userDisplayNameCache[$loginName] } else { $sharedByDisplayName = "" }
                        $dateTime = $_.Value.DateTime
                        $sharedByLoginName = $_.Value.LoginName
                        $sharedWithDetailsHashmap[$loginName] = @{"LoginName" = $loginName; "SharedDateTime" = $dateTime; "SharedByLoginName" = $sharedByLoginName; "SharedByDisplayName" = $sharedByDisplayName}
                    }
                }
                if ($sharedWithDetailsHashmap.Count -gt 0) {
                    # Write-Host "`$sharedWithDetailsHashmap.Count = $($sharedWithDetailsHashmap.Count)"
                }

                # get individual permissions (called role assignments), and load fields 'RoleDefinitionBindings' and 'Member' for each role assignment
                # replaces the following lines:
                # Get-PnPProperty -ClientObject $item -Property RoleAssignments | out-null
                # foreach ( $roleAssignment in $item.RoleAssignments ) { Get-PnPProperty -ClientObject $roleAssignment -Property RoleDefinitionBindings, Member }
                Load-CSOMProperties -parentObject $item -collectionObject $item.RoleAssignments -propertyNames @("RoleDefinitionBindings", "Member") -parentPropertyName "RoleAssignments" -executeQuery
                # sort role assignments by display name (group or account)
                $roleAssignments = $item.RoleAssignments | Sort-Object -Property { $_.Member.Title }
                foreach ( $roleAssignment in $roleAssignments ) {                
                    $loginName = ""; $permissionLevel = ""; $viaGroup = ""; $viaGroupId = ""
                    # collect permission levels but do not add ignored permission levels
                    $permissionLevels = @();
                    $roleAssignment.RoleDefinitionBindings | ForEach-Object { if (!$ignorePermissionLevels.Contains($_.Name)) { $permissionLevels +=  $_.Name } }
                    $permissionLevel = ($permissionLevels -join $permissionLevelSeparator)
                    if ($permissionLevels.Count -eq 0) { continue }
                    $principalType = $roleAssignment.Member.PrincipalType
                    
                    switch ($principalType) {
                        "User" {
                            # ignore account if in ignore list
                            if ($ignoreAccounts.Contains($roleAssignment.Member.LoginName)){ continue }
                            $loginName = $roleAssignment.Member.LoginName.Split("|")[2]
                            if ($ignoreAccounts.Contains($loginName)){ continue }

                            $displayName = $roleAssignment.Member.Title
                            $email = $roleAssignment.Member.Email
                            if ($sharedWithDetailsHashmap.ContainsKey($loginName)){ $details = $sharedWithDetailsHashmap[$loginName] } else { $details = @{} }
                            # add user to individual permission item access file
                            $outputLines5IndividualPermissionItemAccess.Add( (newIndividualPermissionItemAccessRow -id $item.Id -type $itemType -url $itemUrl -loginName $loginName -displayName $displayName -email $email -permissionLevel $permissionLevel -sharedDateTime $details.SharedDateTime -sharedByDisplayName $details.SharedByDisplayName -sharedByLoginName $details.SharedByLoginName -viaGroup "" -viaGroupId "" -viaGroupType "" -assignmentType "User" -nestingLevel 0 -parentGroup "" ) ) | Out-Null
                        }
                        # if group is SharePoint or Azure Security Group
                        { $_ -in "SharePointGroup", "SecurityGroup" } {
                            if ($principalType -eq "SharePointGroup") {                                
                                $group = $global:sharePointGroupCache[$roleAssignment.Member.Id]
                                $groupType = $principalType
                                $groupMembers = getSharePointGroupMembers -group $group -recurse
                                # make sure all return types create valid array: $null, single item, array of items
                                if($groupMembers -eq $null) { $groupMembers = @() } elseif($groupMembers.GetType().toString() -ne "System.Object[]") { $groupMembers = @($groupMembers) }
                                # if SharePoint group is sharing link, change assignment type to "SharingLink"
                                if ( $roleAssignment.Member.Title.StartsWith("SharingLinks.") -and ($groupMembers.Count -gt 0) ) {
                                    $groupMembers | ForEach-Object { $_["AssignmentType"] = "SharingLink" }
                                }
                            } else {
                                # M365 group example: $member.LoginName = 'c:0o.c|federateddirectoryclaimprovider|0319638f-ac31-4d7a-bfbf-7658f770c619_o'
                                $groupId = [string]($roleAssignment.Member.LoginName.Split("|")[2])
                                $displayName = [string]($roleAssignment.Member.Title)
                                # if not groupId not available, add as user and continue
                                if ($groupId -eq ""){
                                    $loginName = [string]($roleAssignment.Member.LoginName)
                                    $displayName = [string]($roleAssignment.Member.Title)
                                    $email = [string]($roleAssignment.Member.Email)
                                    if ($sharedWithDetailsHashmap.ContainsKey($loginName)){ $details = $sharedWithDetailsHashmap[$loginName] } else { $details = @{} }
                                    # add group to individual permission item access file
                                    $outputLines5IndividualPermissionItemAccess.Add( (newIndividualPermissionItemAccessRow -id $item.Id -type $itemType -url $itemUrl -loginName $loginName -displayName $displayName -email $email -permissionLevel $permissionLevel -sharedDateTime $details.SharedDateTime -sharedByDisplayName $details.SharedByDisplayName -sharedByLoginName $details.SharedByLoginName -viaGroup "" -viaGroupId "" -viaGroupType $principalType -assignmentType "Group" -nestingLevel 0 -parentGroup "" ) ) | Out-Null
                                    continue
                                }
                                # identify group type and strip trailing '_o' from groupId for M365 groups
                                # TODO: find better way to identify M365 groups as sometimes the '_o' suffix is missing when group is M365 group
                                if ($groupId.EndsWith("_o")){ $groupType = "M365Group"; $groupId = $groupId.TrimEnd("_o")}
                                else { $groupType = "SecurityGroup"}
                                $groupMembers = getAzureGroupMembers -groupId $groupId -groupType $groupType -nestingLevel 0 -parentGroup "" -recurse
                                # make sure all return types create valid array: $null, single item, array of items
                                if($groupMembers -eq $null) { $groupMembers = @() } elseif($groupMembers.GetType().toString() -ne "System.Object[]") { $groupMembers = @($groupMembers) }
                            }
                            $groupDisplayName = [string]($roleAssignment.Member.Title)
                            $email = [string]($roleAssignment.Member.Email)
                            # set assignment type to "Group" where no assignment type is set
                            $groupMembers | ForEach-Object { if( ([string]$_["AssignmentType"]) -eq "" ) { $_["AssignmentType"] = "Group" } }
                            foreach ($m in $groupMembers){
                                $loginName = $m["LoginName"]
                                if ($sharedWithDetailsHashmap.ContainsKey($loginName)){ $details = $sharedWithDetailsHashmap[$loginName] } else { $details = @{} }
                                # add group members to individual permission item access file
                                $outputLines5IndividualPermissionItemAccess.Add( (newIndividualPermissionItemAccessRow -id $item.Id -type $itemType -url $itemUrl -loginName $loginName -displayName $m["DisplayName"] -email $m["Email"] -permissionLevel $permissionLevel -sharedDateTime $details.SharedDateTime -sharedByDisplayName $details.SharedByDisplayName -sharedByLoginName $details.SharedByLoginName -viaGroup $m["ViaGroup"] -viaGroupId $m["ViaGroupId"] -viaGroupType $m["ViaGroupType"] -assignmentType $m["AssignmentType"] -nestingLevel $m["NestingLevel"] -parentGroup $m["ParentGroup"] ) ) | Out-Null
                            }

                        }
                    }
                } # loop over role assignments
            } # loop over list items
        } # loop over lists

        # append to output files and reset output lines
        appendToFile -file $outputFile1SiteContents -lines $outputLines1SiteContents; $outputLines1SiteContents = [System.Collections.ArrayList]@()
        appendToFile -file $outputFile2SiteGroups -lines $outputLines2SiteGroups; $outputLines2SiteGroups = [System.Collections.ArrayList]@()
        appendToFile -file $outputFile3SiteUsers -lines $outputLines3SiteUsers; $outputLines3SiteUsers = [System.Collections.ArrayList]@()
        appendToFile -file $outputFile4IndividualPermissionItems -lines $outputLines4IndividualPermissionItems; $outputLines4IndividualPermissionItems = [System.Collections.ArrayList]@()
        appendToFile -file $outputFile5IndividualPermissionItemAccess -lines $outputLines5IndividualPermissionItemAccess; $outputLines5IndividualPermissionItemAccess = [System.Collections.ArrayList]@()

        [system.gc]::Collect() # garbage collect after each site
    } # loop over site and subsites

# ------------------ END: Step 5 - Run over (site or subsite) and contained subsites and write output files ------------------



} # loop over rows in input csv


Write-ScriptFooter $scriptTitle