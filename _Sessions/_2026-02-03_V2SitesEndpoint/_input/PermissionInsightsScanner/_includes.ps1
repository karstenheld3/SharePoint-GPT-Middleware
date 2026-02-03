$env:PNPLEGACYMESSAGE='false'

# writes timestamp and following text to the host: ============================================== START: SCRIPT TITLE ==============================================
Function Write-ScriptHeader($scriptTitle) {
    $global:__ScriptStartDate = Get-Date
    Write-Host (Get-Date -UFormat '+%Y-%m-%d %H:%M:%S')
    Write-Host "$("=" * (52 - ($scriptTitle.Length + 0.5) / 2)) START: $($scriptTitle.ToUpper()) $("=" * (52 - ($scriptTitle.Length +0.5) / 2))"
    if ($ExecutionContext.SessionState.LanguageMode -ne "FullLanguage") { Write-Host "WARNING: PowerShell runs scripts with '$($ExecutionContext.SessionState.LanguageMode)'!" }
}
# writes timestamp and following text to the host: ============================================== END: SCRIPT TITLE ================================================
Function Write-ScriptFooter($scriptTitle) {
    $timeSpan = New-TimeSpan -Start $global:__ScriptStartDate -End (Get-Date)
    if ($timeSpan.Days -gt 0) { $timeText = "$($timeSpan.Days) days $($timeSpan.Hours) hours $($timeSpan.Minutes) mins $($timeSpan.Seconds) secs" }
    elseif ($timeSpan.Hours -gt 0) { $timeText = "$($timeSpan.Hours) hours $($timeSpan.Minutes) mins $($timeSpan.Seconds) secs" }
    elseif ($timeSpan.Minutes -gt 0) { $timeText = "$($timeSpan.Minutes) mins $($timeSpan.Seconds) secs" }
    elseif ($timeSpan.Seconds -gt 0) { $timeText = "$($timeSpan.Seconds) secs" }
    if ($timeText.Length -eq 0){ $timeText = "$($timeSpan.Milliseconds) millisecs"}

    Write-Host "$("=" * (53 - ($scriptTitle.Length + 0.5) / 2)) END: $($scriptTitle.ToUpper()) $("=" * (53 - ($scriptTitle.Length +0.5) / 2))"
    Write-Host "$(Get-Date -UFormat '+%Y-%m-%d %H:%M:%S') ($($timeText))"
}

# tries to read credentials from C:\users\[LOGGED_IN_USER]\AppData\Local\a7.txt
# You can also create a7.txt in command line: "PASSWORD_HERE" | ConvertTo-SecureString -AsPlainText -Force | ConvertFrom-SecureString | Out-File "$($env:LOCALAPPDATA)\a7.txt"
function Get-A7CredentialsOfCurrentUser([bool]$verifyPassword = $true) {
    # Check if the logged user is either A1, A2, or A6 and get A7 username. Append 'a7' if normal user.
    $u = $env:username.ToLower()
    if($u.startsWith("a1") -or $u.startsWith("a2") -or $u.startsWith("a6")){ $a7username = "a7" + $u.Substring(2) }
    elseif($u.startsWith("a01")){ $a7username = "a7" + $u.Substring(3) }
    else{$a7username = "a7" + $u}
    $a7username = $a7username + "@eur.corp.vattenfall.com"
    # password file is stored as secure string as C:\users\[LOGGED_IN_USER]\AppData\Local\a7.txt
    return (GetOrCreateCredentialsOfUserFromFile -username $a7username -passwordFilename (Join-Path $env:LOCALAPPDATA "a7.txt") -verifyPassword $verifyPassword)
}

# reads credentials of currently logged in user "abc12" from file or asks user for password and stores it into a file
function Get-CredentialsOfCurrentUser([bool]$verifyPassword = $true) {
    $u = $env:username.ToLower()
    $username = $u + "@eur.corp.vattenfall.com"
    # password file is stored as secure string as C:\users\[LOGGED_IN_USER]\AppData\Local\user.txt
    return (GetOrCreateCredentialsOfUserFromFile -username $username -passwordFilename (Join-Path $env:LOCALAPPDATA "user.txt") -verifyPassword $verifyPassword)
}
# reads credentials of user like "abcd@vattenfall.onmicrosoft.com" from file or asks user for password and stores it into a file
function Get-CredentialsOfUser([string]$username, [bool]$verifyPassword = $true) {
    if ($username.IndexOf("@") -eq -1){ throw "The username '$username' does not contain an '@' character! Please use 'xyz@company.com' instead of 'xyz' or 'DOMAIN\xyz'." }
    $filename = $username.Split("@")[0]
    # password file is stored as secure string as C:\users\[LOGGED_IN_USER]\AppData\Local\[username].txt
    return (GetOrCreateCredentialsOfUserFromFile -username $username -passwordFilename (Join-Path $env:LOCALAPPDATA "$filename.txt") -verifyPassword $verifyPassword)
}

# tries to read credentials file from C:\users\[LOGGED_IN_USER]\AppData\Local\s7.txt or creates new one
Function Get-S7CredentialsOfAdminUser([bool]$verifyPassword = $true) {
    return (GetOrCreateCredentialsOfUserFromFile -username "s7spoadm@eur.corp.vattenfall.com" -passwordFilename (Join-Path $env:LOCALAPPDATA "s7.txt") -verifyPassword $verifyPassword)
}

# Prevents text values from accidentially being converted to dates or numbers when loading into Excel or PowerBI. Do not use for dates or numbers!
# Escapes text value with doublequotes if it contains newlines, commas or double quotes or looks like date, number, or Excel formula (starts with '+', '-', '=')
function CSV-Escape-Text ($value) {
    $retVal = [string]$value    
    if ($retVal -match '^([+\-=\/]*[\.\d\s\/\:]*|.*[\,\"\n].*|[\n]*)$') { $retVal = '"' + $retVal.Replace('"','""') + '"'}
    return $retVal
}

function ConvertSharePointFieldToTextOrValueType (){
    param(
        [Parameter(Mandatory=$true)]$value,
        [Parameter(Mandatory=$false)][bool]$includeLinkDescriptions = $false
    )
    if ($value -eq $null){ $retVal = $value }
    else{
        # value is object
        switch ( $value.GetType().ToString() ){
            { $_ -in "Microsoft.SharePoint.Client.FieldUserValue","Microsoft.SharePoint.Client.FieldLookupValue" } {
                $retVal = $value.LookupValue
            }
            "Microsoft.SharePoint.Client.FieldUserValue[]" {
                $subValues = [System.Collections.ArrayList]@()
                foreach ($val in $value) {
                    $subValues.Add($val.Email + "|" + $val.LookupId + "|" + $val.LookupValue) | Out-Null
                }
                $retVal = $subValues -join ";"
                }
<            "Microsoft.SharePoint.Client.FieldUrlValue" {
                $retVal = $value.Url
                if ($includeLinkDescriptions) { $retVal += ("|" + $value.Description) }
            }
            "Microsoft.SharePoint.Client.Taxonomy.TaxonomyFieldValue" { $retVal = $value.Label }
            "Microsoft.SharePoint.Client.Taxonomy.TaxonomyFieldValueCollection" {
                $subValues = [System.Collections.ArrayList]@()
                foreach ($val in $value) { $subValues.Add($val.Label) | Out-Null }
                $retVal = $subValues -join "|"
            }
            "System.DateTime" {
                # convert to local timezone / dailight saving; datetimes are delivered in UTC+0 timezone
                $itemLocalDate = [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId($value, (Get-TimeZone).Id)
                # convert to ISO-like format that can be read by Excel
                $retVal = $itemLocalDate.ToString("yyyy-MM-dd HH:mm:ss")
            }                
            "System.String" { $retVal = $value }
			"System.String[]" { $retVal = $value -join "|" }
            default {
                # convert only objects types to string; do not convert value types
                if (!$value.GetType().IsValueType) { $retVal = $value.ToString() }
                elseif ($value -is [array]) { $retVal = $value -join "|" }
                else { $retVal = $value }
            }
        }                        
    }
    return $retVal
}

# Converts file size in bytes to "??? B" or "??? KB" or "??? MB" or "??? GB"
function Get-DisplayFileSize ([long]$fileSize){
    if($fileSize -lt 1000) { $displaySize = "$([string]$fileSize) B "}
    elseif($fileSize -lt 1000000) {$displaySize = "$([string][int]($fileSize / 1024)) KB"}
    elseif($fileSize -lt 1000000000) {$displaySize = "$([string][int]($fileSize / 1048576)) MB"}
    elseif($fileSize -lt 1000000000000) {$displaySize = "$([string][int]($fileSize / 1073741824)) GB"}
    elseif($fileSize -lt 1000000000000000) {$displaySize = "$([string][int]($fileSize / 1099511627776)) TB"}
    # right-align sizes so that we can better detect large files
    $displaySize = ($displaySize.PadLeft(6," "))
    return $displaySize
}

# ask user to press key to continue or show dialog if Powershell ISE is running
# returns "OK" or "Cancel" when displaying a dialog or the pressed key if running from console
function Pause ($message)
{
    if ($psISE) {
        Add-Type -AssemblyName System.Windows.Forms;
        return [System.Windows.Forms.MessageBox]::Show("$message","PowerShell Message","OKCancel")
    } else { Write-Host "$message" -ForegroundColor black -BackgroundColor Yellow; return $host.ui.RawUI.ReadKey("NoEcho,IncludeKeyDown").character }
}

# https://www.powershellmagazine.com/2013/02/15/pstip-validating-active-directory-user-credentials/
# https://docs.microsoft.com/en-us/archive/blogs/dsheehan/confirmingvalidating-powershell-get-credential-input-before-use
# tests credentials without triggering failed log on attempts
function Test-Credential ([System.Management.Automation.PSCredential]$credential)  {
    Add-Type -AssemblyName System.DirectoryServices.AccountManagement
    $username = $credential.GetNetworkCredential().UserName
    $username
    $ct = [System.DirectoryServices.AccountManagement.ContextType]::Domain
    $pc = New-Object System.DirectoryServices.AccountManagement.PrincipalContext $ct,$env:USERDOMAIN
    $result = $pc.ValidateCredentials($username,$credential.GetNetworkCredential().Password,[System.DirectoryServices.AccountManagement.ContextOptions]::Negotiate)
    return $result
}


# tries to read credentials from file; if file does not exist or credentials are not correct it will ask for a password and store it securely in that file.
# if $verifyPassword = $false, it will not test if the password is correct (use this for @???.onmicrosoft.com and other accounts that can't be verified by the current Active Directory)
function GetOrCreateCredentialsOfUserFromFile([string]$username, [string]$passwordFilename, [bool]$verifyPassword = $true){
    $internalVerifyPasswordFlag = $true # external parameter can be overwritten here
    # password file 1) must be created on same machine 2) must be used with same logged in user
    $mustWriteToFile = $false
    $error = 0 # 0 = file found, 1 = file not found, 2 = incorrect credential, 3 = password expired
    $credentialTest = $null
    if (Test-Path $passwordFilename) {
        # file exists, load and test credentials
        $credentials = new-object System.Management.Automation.PSCredential ($username), (Get-Content $passwordFilename | ConvertTo-SecureString)
        if ($verifyPassword -and $internalVerifyPasswordFlag) { $credentialTest = (Test-Credential -credential $credentials) } else {$credentialTest = $true }
        if ($credentialTest -eq $false) { $error = 3 }
    } else { $error = 1 }
    do {
        if ($error -gt 0) {
            switch($error) {
                1 { $message = "Password file not found! Enter password for user $($username.Split("@")[0])" }
                2 { $message = "Incorrect password! Enter password for user $($username.Split("@")[0])" }
                3 { $message = "Password in password file incorrect or expired! Enter password for user $($username.Split("@")[0])" }
            }
            $credentials = new-object system.management.automation.pscredential ($username), (read-host -assecurestring -prompt $message)            
            if ($verifyPassword -and $internalVerifyPasswordFlag) { $credentialTest = (Test-Credential -credential $credentials) } else {$credentialTest = $true }
            if ($credentialTest -eq $false) { $error = 2 } else { $mustWriteToFile = $true }
        }
    } while ( $credentialTest -eq $false )
    if ($mustWriteToFile) {
        $credentials.Password | ConvertFrom-SecureString | Set-Content $passwordFilename
        Write-Host "Password OK. File written to '$($passwordFilename)'." -ForegroundColor Green
    }
    return $credentials
}

function Get-PnPVersion {
    $items = Get-Module SharePointPnPPowerShell* -ListAvailable | Sort-Object Version -Descending
    if ($items -eq $null) { $items = Get-Module PnP.PowerShell -ListAvailable | Sort-Object Version -Descending }
    # make sure all return types create valid array: $null, single item, array of items
    if($items -eq $null) { $items = @() } elseif($items.GetType().toString() -ne "System.Object[]") { $items = @($items) }
    $modules = @(); $items | ForEach-Object { $modules += $_.Name + " " + $_.Version +": " + (Split-Path $_.Path)}
    $modules | ForEach-Object { Write-Host $modules }
}

function Get-SPOVersion {
    $items = Get-Module Microsoft.Online.SharePoint.PowerShell* -ListAvailable | Sort-Object Version -Descending
    if ($items -eq $null) { $items = Get-Module PnP.PowerShell -ListAvailable | Sort-Object Version -Descending }
    # make sure all return types create valid array: $null, single item, array of items
    if($items -eq $null) { $items = @() } elseif($items.GetType().toString() -ne "System.Object[]") { $items = @($items) }
    $modules = @(); $items | ForEach-Object { $modules += $_.Name + " " + $_.Version +": " + (Split-Path $_.Path)}
    $modules | ForEach-Object { Write-Host $modules }
}

# https://stackoverflow.com/questions/45470999/powershell-try-catch-and-retry
# use like this: Retry-Command -ScriptBlock { # do something } -MaxRetries 2 -WaitMilliseconds 500
function Retry-Command {
    [CmdletBinding()]
    Param(
        [Parameter(Position=0, Mandatory=$true)] [scriptblock]$ScriptBlock,
        [Parameter(Position=1, Mandatory=$false)] [int]$MaxRetries = 5,
        [Parameter(Position=2, Mandatory=$false)] [int]$WaitMilliseconds = 100
    )
    Begin { $cnt = 0 }
    Process {
        do {
            $cnt++
            try {
                # If you want messages from the ScriptBlock
                # Invoke-Command -Command $ScriptBlock
                # Otherwise use this command which won't display underlying script messages
                $ScriptBlock.Invoke()
                return
            } catch {
                Write-Error $_.Exception.InnerException.Message -ErrorAction Continue
                Start-Sleep -Milliseconds $WaitMilliseconds
            }
        } while ($cnt -lt $MaxRetries)

        # Throw an error after $Maximum unsuccessful invocations. Doesn't need
        # a condition, since the function returns upon successful invocation.
        throw 'Execution failed.'
    }
}


# https://www.sharepointpals.com/post/lambda-expression-in-sharepoint-csom-powershell/
 <#
 .Synopsis
     Facilitates the loading of specific properties of a Microsoft.SharePoint.Client.ClientObject object or Microsoft.SharePoint.Client.ClientObjectCollection object.
 .DESCRIPTION
     Replicates what you would do with a lambda expression in C#. 
     For example, "ctx.Load(list, l => list.Title, l => list.Id)" becomes
     "Load-CSOMProperties -object $list -propertyNames @('Title', 'Id')".
 .EXAMPLE
     Load-CSOMProperties -parentObject $web -collectionObject $web.Fields -propertyNames @("InternalName", "Id") -parentPropertyName "Fields" -executeQuery
     $web.Fields | select InternalName, Id
 .EXAMPLE
    Load-CSOMProperties -object $web -propertyNames @("Title", "Url", "AllProperties") -executeQuery
    $web | select Title, Url, AllProperties
 #>
 
 function global:Load-CSOMProperties {
     [CmdletBinding(DefaultParameterSetName='ClientObject')]
     param (
         # The Microsoft.SharePoint.Client.ClientObject to populate.
         [Parameter(Mandatory = $true, ValueFromPipeline = $true, Position = 0, ParameterSetName = "ClientObject")] [Microsoft.SharePoint.Client.ClientObject] $object,
         # The Microsoft.SharePoint.Client.ClientObject that contains the collection object.
         [Parameter(Mandatory = $true, ValueFromPipeline = $true, Position = 0, ParameterSetName = "ClientObjectCollection")] [Microsoft.SharePoint.Client.ClientObject] $parentObject,
         # The Microsoft.SharePoint.Client.ClientObjectCollection to populate.
         [Parameter(Mandatory = $true, ValueFromPipeline = $true, Position = 1, ParameterSetName = "ClientObjectCollection")] [Microsoft.SharePoint.Client.ClientObjectCollection] $collectionObject,
         # The object properties to populate
         [Parameter(Mandatory = $true, Position = 1, ParameterSetName = "ClientObject")] [Parameter(Mandatory = $true, Position = 2, ParameterSetName = "ClientObjectCollection")] [string[]] $propertyNames,
         # The parent object's property name corresponding to the collection object to retrieve (this is required to build the correct lamda expression).
         [Parameter(Mandatory = $true, Position = 3, ParameterSetName = "ClientObjectCollection")] [string] $parentPropertyName,
         # If specified, execute the ClientContext.ExecuteQuery() method.
         [Parameter(Mandatory = $false, Position = 4)] [switch] $executeQuery
     )
 
     begin { }
     process {
         if ($PsCmdlet.ParameterSetName -eq "ClientObject") {
             $type = $object.GetType()
         } else {
             $type = $collectionObject.GetType() 
             if ($collectionObject -is [Microsoft.SharePoint.Client.ClientObjectCollection]) { $type = $collectionObject.GetType().BaseType.GenericTypeArguments[0] }
         }
 
         $exprType = [System.Linq.Expressions.Expression]
         $parameterExprType = [System.Linq.Expressions.ParameterExpression].MakeArrayType()
         $lambdaMethod = $exprType.GetMethods() | ? { $_.Name -eq "Lambda" -and $_.IsGenericMethod -and $_.GetParameters().Length -eq 2 -and $_.GetParameters()[1].ParameterType -eq $parameterExprType }
         $lambdaMethodGeneric = Invoke-Expression "`$lambdaMethod.MakeGenericMethod([System.Func``2[$($type.FullName),System.Object]])"
         $expressions = @()
 
         foreach ($propertyName in $propertyNames) {
             $param1 = [System.Linq.Expressions.Expression]::Parameter($type, "p")
             try { $name1 = [System.Linq.Expressions.Expression]::Property($param1, $propertyName) }
             catch { Write-Error "Instance property '$propertyName' is not defined for type $type"; return }
             $body1 = [System.Linq.Expressions.Expression]::Convert($name1, [System.Object])
             $expression1 = $lambdaMethodGeneric.Invoke($null, [System.Object[]] @($body1, [System.Linq.Expressions.ParameterExpression[]] @($param1)))
              
             # avoid the following error:
             # An error occurred while enumerating through a collection: The collection has not been initialized. It has not been requested or the request has not been executed. It may need to be explicitly requested..
             try {  if ($collectionObject -ne $null) { $expression1 = [System.Linq.Expressions.Expression]::Quote($expression1) } } catch { }             
             $expressions += @($expression1)
         }
 
         if ($PsCmdlet.ParameterSetName -eq "ClientObject") {
             $object.Context.Load($object, $expressions)
             if ($executeQuery) { $object.Context.ExecuteQuery() }
         } else {
             $newArrayInitParam1 = Invoke-Expression "[System.Linq.Expressions.Expression``1[System.Func````2[$($type.FullName),System.Object]]]"
             $newArrayInit = [System.Linq.Expressions.Expression]::NewArrayInit($newArrayInitParam1, $expressions)
 
             $collectionParam = [System.Linq.Expressions.Expression]::Parameter($parentObject.GetType(), "cp")
             $collectionProperty = [System.Linq.Expressions.Expression]::Property($collectionParam, $parentPropertyName)
 
             $expressionArray = @($collectionProperty, $newArrayInit)
             $includeMethod = [Microsoft.SharePoint.Client.ClientObjectQueryableExtension].GetMethod("Include")
             $includeMethodGeneric = Invoke-Expression "`$includeMethod.MakeGenericMethod([$($type.FullName)])"
 
             $lambdaMethodGeneric2 = Invoke-Expression "`$lambdaMethod.MakeGenericMethod([System.Func``2[$($parentObject.GetType().FullName),System.Object]])"
             $callMethod = [System.Linq.Expressions.Expression]::Call($null, $includeMethodGeneric, $expressionArray)
             
             $expression2 = $lambdaMethodGeneric2.Invoke($null, @($callMethod, [System.Linq.Expressions.ParameterExpression[]] @($collectionParam)))
 
             $parentObject.Context.Load($parentObject, $expression2)
             if ($executeQuery) { $parentObject.Context.ExecuteQuery() }
         }
     }
     end { }
 }
# SIG # Begin signature block
# MIIOkQYJKoZIhvcNAQcCoIIOgjCCDn4CAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUa4cyWRkTcJ+chPJgrCvPJbMI
# IJGgggvwMIIE6TCCA9GgAwIBAgITdgAYWJCtv6CsGTJF+wABABhYkDANBgkqhkiG
# 9w0BAQsFADBTMRMwEQYKCZImiZPyLGQBGRYDY29tMRowGAYKCZImiZPyLGQBGRYK
# dmF0dGVuZmFsbDEgMB4GA1UEAxMXVmF0dGVuZmFsbCBJc3N1aW5nIENBIDYwHhcN
# MjExMTAxMTQyODM5WhcNMjQxMDMxMTQyODM5WjCBjzELMAkGA1UEBhMCREUxDzAN
# BgNVBAcTBkJlcmxpbjETMBEGA1UEChMKVmF0dGVuZmFsbDEOMAwGA1UECxMFWUlD
# TUMxGjAYBgNVBAMTEUwxNzQgQ29kZSBTaWduaW5nMS4wLAYJKoZIhvcNAQkBFh9C
# b3VkZXdpam4uT2trZW1hQHZhdHRlbmZhbGwuY29tMIIBIjANBgkqhkiG9w0BAQEF
# AAOCAQ8AMIIBCgKCAQEAvMyklT7p+Hc/bRDtWIcREZystPE7XZIL/3bcB1YNGmrx
# LXvqYqcZcbyWBb1gMpy4IU6zceHHajWwJ19numER+v65mjiO0ADyzYim5VQ+gEeD
# 2TKe0tDvcx9tXWOxbnOsT5qvv8D0lvhOATx1I5LkPZV4S2iSUX9o0mjEB7sxdX7S
# X30d9fdHt16AsoMQM9qkErBSjW3ZGeerqZ3H8daJlZM4fiZHsV5QMSsJyVo4d8eA
# oyz3fTjJHBojXf+h6ZSpwfxwaXKLHvDNFx3o+YHGgHCbhPvD4CccElCa2DVytNwG
# YMw9/fKVu51t2CH6yi8VJBK5mCP+qkt6Gk1p9BAOCQIDAQABo4IBdzCCAXMwCwYD
# VR0PBAQDAgeAMD0GCSsGAQQBgjcVBwQwMC4GJisGAQQBgjcVCILBtDmEq618hv2V
# OoGl/hqB88ATHYTW3EyCxrhfAgFkAgEXMB0GA1UdDgQWBBTQIwSo/N06XlWrJ+8e
# oNJo6N8ULDAfBgNVHSMEGDAWgBTLuK2oh9i1lGp/fATJHgoaWqSRoTBTBgNVHR8E
# TDBKMEigRqBEhkJodHRwOi8vcGtpLnZhdHRlbmZhbGwuY29tL2NkcC9WYXR0ZW5m
# YWxsJTIwSXNzdWluZyUyMENBJTIwNigxKS5jcmwwXgYIKwYBBQUHAQEEUjBQME4G
# CCsGAQUFBzAChkJodHRwOi8vcGtpLnZhdHRlbmZhbGwuY29tL2FpYS9WYXR0ZW5m
# YWxsJTIwSXNzdWluZyUyMENBJTIwNigxKS5jcnQwEwYDVR0lBAwwCgYIKwYBBQUH
# AwMwGwYJKwYBBAGCNxUKBA4wDDAKBggrBgEFBQcDAzANBgkqhkiG9w0BAQsFAAOC
# AQEAOdcMFGGo2o/FX6IqUeZUECpinvGDFg06EBa0k3ZvsTWnRme37NK7Uh5wHBrt
# hJyj3rNfjov5FCTgB6pSca1sF1TwgFosUAiMakNdShhx2q8JPJj8fQ6ZI+yRj1Ip
# ajI6B4CmM9B/x7gypL6std0Gv0BlYKgb962tJD2a+hDC1wMIzFGxVAigtf990MPZ
# uYksj8xuHGWLbMFAbrKSdJjDjzxjGzbOv7eY6msS1N3VDg44wRBriRXWbAshWLRD
# T1mNNpY2AOSZ1xWmLUF6N05HRTMNwcse1B0sDHyrAtWYx9cvTvDpm65ihxpVJceO
# QzMlKVFz3FfRR6P337vfrmHMBDCCBv8wggTnoAMCAQICExgAAAAFcXG3/10csdcA
# AAAAAAUwDQYJKoZIhvcNAQELBQAwUzETMBEGCgmSJomT8ixkARkWA2NvbTEaMBgG
# CgmSJomT8ixkARkWCnZhdHRlbmZhbGwxIDAeBgNVBAMTF1ZhdHRlbmZhbGwgUm9v
# dCBDQSAyMDE3MB4XDTE3MDExODEzMjUyMVoXDTI3MDExODEzMzUyMVowUzETMBEG
# CgmSJomT8ixkARkWA2NvbTEaMBgGCgmSJomT8ixkARkWCnZhdHRlbmZhbGwxIDAe
# BgNVBAMTF1ZhdHRlbmZhbGwgSXNzdWluZyBDQSA2MIIBIjANBgkqhkiG9w0BAQEF
# AAOCAQ8AMIIBCgKCAQEAsFuXgkcpbnGm0/qwLIjqiBzXmkz2tLkSra0mlxOUuLWG
# P+EqMNqvgZIieU367iq7dwSw2mWx+Kf7AGnKuMABVURMifPIAjMbeGl0PhVYASxT
# jUAt35pD9T/VimLkD3lhHKtg7ZFi/sIt+N+l93dIfxhIrpE8gmkK8zj0VSUJHoXI
# qWOhgFkDJqf8iz+CpMcmUy/ajK8KK6EcPmhLI2KNnHIvRAS+b2Fp4afA+WzWuK9X
# V6dpIz3+uuA3iaIV4YmFht46SHkWvRhIfxM22LdzO+eHX+aAfPUCuk7uQ/1Jzo/5
# jFqZNPMocDlHRULOqRQ+bbTTQLeHMReATArr0CX5swIDAQABo4ICyjCCAsYwEgYJ
# KwYBBAGCNxUBBAUCAwEAATAjBgkrBgEEAYI3FQIEFgQUvK4e6gy7yE05XvtZcFyX
# k6OknP4wHQYDVR0OBBYEFMu4raiH2LWUan98BMkeChpapJGhMIIBXgYDVR0gBIIB
# VTCCAVEwgakGCysGAQQBgbJSAwEBMIGZMGAGCCsGAQUFBwICMFQeUgBWAGEAdAB0
# AGUAbgBmAGEAbABsACAAQwBlAHIAdABpAGYAaQBjAGEAdABlACAAUAByAGEAYwB0
# AGkAYwBlACAAUwB0AGEAdABlAG0AZQBuAHQwNQYIKwYBBQUHAgEWKWh0dHA6Ly9w
# a2kudmF0dGVuZmFsbC5jb20vY3BzL2luZGV4Lmh0bWwAMGMGCysGAQQBgbJSAwEL
# MFQwUgYIKwYBBQUHAgIwRh5EAFYAYQB0AHQAZQBuAGYAYQBsAGwAIABJAHMAcwB1
# AGkAbgBnACAAQwBBACAANgAgAEkAZABlAG4AdABpAGYAaQBlAHIwPgYEVR0gADA2
# MDQGCCsGAQUFBwICMCgeJgBBAGwAbAAgAEkAcwBzAHUAYQBuAGMAZQAgAFAAbwBs
# AGkAYwB5MBkGCSsGAQQBgjcUAgQMHgoAUwB1AGIAQwBBMAsGA1UdDwQEAwIBhjAS
# BgNVHRMBAf8ECDAGAQH/AgEAMB8GA1UdIwQYMBaAFHUIYDosewsy3W+NMq75UhR0
# VwdPMFAGA1UdHwRJMEcwRaBDoEGGP2h0dHA6Ly9wa2kudmF0dGVuZmFsbC5jb20v
# Y2RwL1ZhdHRlbmZhbGwlMjBSb290JTIwQ0ElMjAyMDE3LmNybDBbBggrBgEFBQcB
# AQRPME0wSwYIKwYBBQUHMAKGP2h0dHA6Ly9wa2kudmF0dGVuZmFsbC5jb20vYWlh
# L1ZhdHRlbmZhbGwlMjBSb290JTIwQ0ElMjAyMDE3LmNydDANBgkqhkiG9w0BAQsF
# AAOCAgEAECJ9NZ9odfur6P7hiehi3zPdu779FFHZVqVIjYjfA5aexOzTQSAyFjcj
# gPO6WQvhEBiNtqNKKuT+Jkxsh1XMQMoxQpkQhYyETBWjsdC4F47cf6ERfjMuo/Zx
# 4cn74FKxIjiY+AjvZNtFQDV3edf3Ld4moS651JrTQ4fsYQ5wCZUeq1KCUZ+lg669
# iOqhZWYCG1ewUvKR3WuTWCDhLf5pNQULpk5GlmQiqetQiLWIYBPmVfTmdRwHQ/zz
# td2aW7gk/VdMcqy/RMrj+6+D1wza9LRlJ3Mn7fXyEYrN8bqf79irxa/TSxIpZNXe
# u9pdgaeW5jSsYcBNhZev4IWpC8EHUfZ+A8gZrpL230UCK+afzrho5/VO/v9ZnANc
# 4Y3hrrvclQJW92MmsaNuAp4aM3cojKl7e+WadQlhqpddCS0c68AZOJEEdppwbljp
# rxY+hNJwou2ZIUzwopDz3uGWEZjWlxZSkBau9Xf8QRyDHGbuHuEvDV6UWanWb+K4
# 6WMZbfYPbp1qmP/loY/4io2osjF5SAeiRFQmXaQpNPWqK0m8g2gIA5LJb7cs5IwU
# FKBFhK3phJbgMFYVg2Ec4ZzLd8BYNU2vR5Qwe9AbRTU2+68OQcmxY2QYZj6xj6yn
# gMjyLCTXl7kju8YPKb0tN7rg880AKQflIIM/6l2dEC1+5ncOrHAxggILMIICBwIB
# ATBqMFMxEzARBgoJkiaJk/IsZAEZFgNjb20xGjAYBgoJkiaJk/IsZAEZFgp2YXR0
# ZW5mYWxsMSAwHgYDVQQDExdWYXR0ZW5mYWxsIElzc3VpbmcgQ0EgNgITdgAYWJCt
# v6CsGTJF+wABABhYkDAJBgUrDgMCGgUAoHgwGAYKKwYBBAGCNwIBDDEKMAigAoAA
# oQKAADAZBgkqhkiG9w0BCQMxDAYKKwYBBAGCNwIBBDAcBgorBgEEAYI3AgELMQ4w
# DAYKKwYBBAGCNwIBFTAjBgkqhkiG9w0BCQQxFgQUUXkGeEsg1uvbYLwyIPzlQEGu
# qjwwDQYJKoZIhvcNAQEBBQAEggEAQX4y+/cWPlBxO9oJeVzueza1MUc4Sev9Vfvm
# J3lJ6lKBzAlLSsHVPPAVwwhrINM40S1mQn4aB2HmKEK2It670tbls9HJXpk2xlq8
# RLaPpyd6xR5WRviYTFLk6/PQnoBAQUUXzFlOfjrabAbEHMXNVXtfEKZVGeXORQXZ
# F/qaH3ft4g9S4hkOOaZEvrq8gCHOzCRCG36apNiwd2BHrUgy6en38jRqHP5KgLrP
# a7buCW5kW/4GjFn8X3S0heQUDaVov9hKhTCDlS8aiv5eW5YJv+EKoLL7/dqAkOE0
# 2pAqV13oO5AxQlX/CzFPCoixqDQOtZPeKVS+o8OmuKHkgQ1zJw==
# SIG # End signature block
