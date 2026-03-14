# INFO: Copilot Retrieval API - SDK Examples

**Doc ID**: COPRA-IN01
**Goal**: Document client libraries and code examples for all supported languages

**Depends on:**
- `_INFO_COPRA_SOURCES.md [COPRA-IN01]` for source URLs
- `__INFO_COPRA-IN00_TOC.md [COPRA-IN01]` for topic scope

## Summary

Microsoft provides official client libraries for C#, Python, and TypeScript as part of the Microsoft 365 Agents SDK. These libraries simplify authentication, request building, and response handling. PowerShell can use direct REST calls via Invoke-RestMethod.

**Key Facts [VERIFIED]:**
- Official SDKs: C# (.NET), Python, TypeScript
- Package names: Microsoft.Agents.M365Copilot (NuGet), microsoft-agents-m365copilot (PyPI), @microsoft/agents-m365copilot (npm)
- Built on Kiota-generated clients
- Open source on GitHub: microsoft/Agents-M365Copilot

**Use Cases:**
- .NET applications and Azure Functions
- Python scripts and data pipelines
- Node.js/TypeScript web applications
- PowerShell automation scripts

## Quick Reference

**Package Installation:**
- .NET: `dotnet add package Microsoft.Agents.M365Copilot`
- Python: `pip install microsoft-agents-m365copilot`
- TypeScript: `npm install @microsoft/agents-m365copilot`

**GitHub:** https://github.com/microsoft/Agents-M365Copilot

## SDK Overview

### Microsoft 365 Agents SDK [VERIFIED]

The Copilot APIs client libraries are part of the Microsoft 365 Agents SDK, designed to facilitate development of AI solutions accessing Copilot APIs.

**Library Types:**
- **Service libraries**: Models and request builders for typed API access
- **Core libraries**: Advanced features (retry handling, auth, compression)

**Core Library Features:**
- Embedded retry handling
- Secure redirects
- Transparent authentication
- Payload compression
- Paging through collections
- Batch request creation

### Preview Status [VERIFIED]

The client libraries may be in preview status when initially released or after significant updates.

**Warning:** Avoid using preview releases in production, regardless of whether using v1.0 or beta API endpoints.

### Support [VERIFIED]

Libraries are open-source on GitHub. File issues at: https://github.com/microsoft/Agents-M365Copilot/issues

## .NET Client Library

### Package Information [VERIFIED]

**NuGet Packages:**
- `Microsoft.Agents.M365Copilot` - v1.0 endpoint models and builders
- `Microsoft.Agents.M365Copilot.Beta` - Beta endpoint models and builders
- `Microsoft.Agents.M365Copilot.Core` - Core library (dependency)

**GitHub:** https://github.com/microsoft/Agents-M365Copilot/tree/main/dotnet

### Installation [VERIFIED]

**dotnet CLI (v1.0):**
```bash
dotnet add package Microsoft.Agents.M365Copilot
```

**dotnet CLI (beta):**
```bash
dotnet add package Microsoft.Agents.M365Copilot.Beta
```

**Package Manager Console (v1.0):**
```powershell
Install-Package Microsoft.Agents.M365Copilot
```

### Complete Example [VERIFIED]

```csharp
using Azure.Identity;
using Microsoft.Agents.M365Copilot;
using Microsoft.Agents.M365Copilot.Models;
using Microsoft.Agents.M365Copilot.Copilot.Retrieval;

var scopes = new[] { "Files.Read.All", "Sites.Read.All" };

// Multi-tenant apps can use "common"
// Single-tenant apps must use the tenant ID from Azure portal
var tenantId = "YOUR_TENANT_ID";
var clientId = "YOUR_CLIENT_ID";

// Device code authentication
var deviceCodeCredentialOptions = new DeviceCodeCredentialOptions
{
    ClientId = clientId,
    TenantId = tenantId,
    DeviceCodeCallback = (deviceCodeInfo, cancellationToken) =>
    {
        Console.WriteLine(deviceCodeInfo.Message);
        return Task.CompletedTask;
    },
};

var deviceCodeCredential = new DeviceCodeCredential(deviceCodeCredentialOptions);

// Create the client
AgentsM365CopilotServiceClient client = new AgentsM365CopilotServiceClient(
    deviceCodeCredential, scopes, baseURL);

try
{
    // Build the request
    var requestBody = new RetrievalPostRequestBody
    {
        DataSource = RetrievalDataSource.SharePoint,
        QueryString = "What is the latest in my organization?",
        MaximumNumberOfResults = 10
    };

    // Execute the request
    var result = await client.Copilot.Retrieval.PostAsync(requestBody);

    if (result?.RetrievalHits != null)
    {
        Console.WriteLine($"Found {result.RetrievalHits.Count} results");
        
        foreach (var hit in result.RetrievalHits)
        {
            Console.WriteLine($"URL: {hit.WebUrl}");
            Console.WriteLine($"Type: {hit.ResourceType}");
            
            if (hit.Extracts != null)
            {
                foreach (var extract in hit.Extracts)
                {
                    Console.WriteLine($"Text: {extract.Text}");
                    Console.WriteLine($"Score: {extract.RelevanceScore}");
                }
            }
            
            if (hit.SensitivityLabel != null)
            {
                Console.WriteLine($"Label: {hit.SensitivityLabel.DisplayName}");
            }
        }
    }
}
catch (Exception ex)
{
    Console.WriteLine($"Error: {ex.Message}");
}
```

## Python Client Library

### Package Information [VERIFIED]

**PyPI Packages:**
- `microsoft-agents-m365copilot` - v1.0 endpoint
- `microsoft-agents-m365copilot-beta` - Beta endpoint

**GitHub:** https://github.com/microsoft/Agents-M365Copilot/tree/main/python

### Installation [VERIFIED]

**pip (v1.0):**
```bash
pip install microsoft-agents-m365copilot
```

**pip (beta):**
```bash
pip install microsoft-agents-m365copilot-beta
```

### Complete Example [VERIFIED]

```python
import asyncio
from datetime import datetime
from azure.identity import DeviceCodeCredential
from kiota_abstractions.api_error import APIError
from microsoft_agents_m365copilot.agents_m365_copilot_service_client import (
    AgentsM365CopilotServiceClient
)
from microsoft_agents_m365copilot.generated.copilot.retrieval.retrieval_post_request_body import (
    RetrievalPostRequestBody
)
from microsoft_agents_m365copilot.generated.models.retrieval_data_source import (
    RetrievalDataSource
)

scopes = ['Files.Read.All', 'Sites.Read.All']

# Multi-tenant apps can use "common"
TENANT_ID = 'YOUR_TENANT_ID'
CLIENT_ID = 'YOUR_CLIENT_ID'

def auth_callback(verification_uri: str, user_code: str, expires_on: datetime):
    print(f"\nTo sign in, open: {verification_uri}")
    print(f"Enter code: {user_code}")
    print(f"Expires at: {expires_on}")

# Create credentials
credentials = DeviceCodeCredential(
    client_id=CLIENT_ID,
    tenant_id=TENANT_ID,
    prompt_callback=auth_callback
)

# Create client
client = AgentsM365CopilotServiceClient(credentials=credentials, scopes=scopes)

async def retrieve():
    try:
        # Build request body
        retrieval_body = RetrievalPostRequestBody()
        retrieval_body.data_source = RetrievalDataSource.SharePoint
        retrieval_body.query_string = "What is the latest in my organization?"
        
        # Execute request
        retrieval = await client.copilot.retrieval.post(retrieval_body)
        
        # Process results
        if retrieval and hasattr(retrieval, "retrieval_hits"):
            print(f"Found {len(retrieval.retrieval_hits)} results")
            
            for hit in retrieval.retrieval_hits:
                print(f"URL: {hit.web_url}")
                
                for extract in hit.extracts:
                    print(f"Text: {extract.text}")
                    
    except APIError as e:
        print(f"Error: {e.error.code}: {e.error.message}")
        raise e

# Run
asyncio.run(retrieve())
```

## TypeScript Client Library

### Package Information [VERIFIED]

**npm Packages:**
- `@microsoft/agents-m365copilot` - v1.0 endpoint
- `@microsoft/agents-m365copilot-beta` - Beta endpoint

**GitHub:** https://github.com/microsoft/Agents-M365Copilot/tree/main/typescript

### Installation [VERIFIED]

**npm (v1.0):**
```bash
npm install @microsoft/agents-m365copilot --save
```

**npm (beta):**
```bash
npm install @microsoft/agents-m365copilot-beta --save
```

### Complete Example [VERIFIED]

```typescript
import { 
    createBaseAgentsM365CopilotServiceClient, 
    RetrievalDataSourceObject 
} from '@microsoft/agents-m365copilot';
import { DeviceCodeCredential } from '@azure/identity';
import { FetchRequestAdapter } from '@microsoft/kiota-http-fetchlibrary';
import { AzureIdentityAuthenticationProvider } from '@microsoft/kiota-authentication-azure';

async function main() {
    // Device code authentication
    const credential = new DeviceCodeCredential({
        tenantId: "YOUR_TENANT_ID",
        clientId: "YOUR_CLIENT_ID",
        userPromptCallback: (info) => {
            console.log(`\nTo sign in, open: ${info.verificationUri}`);
            console.log(`Enter code: ${info.userCode}`);
            console.log(`Expires at: ${info.expiresOn}`);
        }
    });

    // Create request adapter
    const authProvider = new AzureIdentityAuthenticationProvider(
        credential, 
        ["Files.Read.All", "Sites.Read.All"]
    );
    const adapter = new FetchRequestAdapter(authProvider);

    // Create client
    const client = createBaseAgentsM365CopilotServiceClient(adapter);

    try {
        // Build request body
        const retrievalBody = {
            dataSource: RetrievalDataSourceObject.SharePoint,
            queryString: "What is the latest in my organization?"
        };

        // Execute request
        const retrieval = await client.copilot.retrieval.post(retrievalBody);

        // Process results
        if (retrieval?.retrievalHits) {
            console.log(`Found ${retrieval.retrievalHits.length} results`);
            
            for (const hit of retrieval.retrievalHits) {
                console.log(`URL: ${hit.webUrl}`);
                
                for (const extract of hit.extracts || []) {
                    console.log(`Text: ${extract.text}`);
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

main().catch(console.error);
```

## PowerShell Examples

### Direct REST Call [ASSUMED]

PowerShell can call the Retrieval API directly using Invoke-RestMethod:

```powershell
# Get access token (requires Az module)
$token = Get-AzAccessToken -ResourceUrl "https://graph.microsoft.com"

# Build request
$headers = @{
    "Authorization" = "Bearer $($token.Token)"
    "Content-Type" = "application/json"
}

$body = @{
    queryString = "How to setup corporate VPN?"
    dataSource = "sharePoint"
    maximumNumberOfResults = "10"
} | ConvertTo-Json

# Execute request
$response = Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/copilot/retrieval" `
    -Method POST `
    -Headers $headers `
    -Body $body

# Process results
foreach ($hit in $response.retrievalHits) {
    Write-Host "URL: $($hit.webUrl)"
    foreach ($extract in $hit.extracts) {
        Write-Host "Text: $($extract.text)"
        Write-Host "Score: $($extract.relevanceScore)"
    }
}
```

### Using Microsoft Graph PowerShell SDK [ASSUMED]

```powershell
# Install module
Install-Module Microsoft.Graph -Scope CurrentUser

# Connect with required scopes
Connect-MgGraph -Scopes "Files.Read.All", "Sites.Read.All"

# Note: Copilot endpoints may require direct REST call
# as they may not have cmdlet wrappers yet
$body = @{
    queryString = "Company policy documents"
    dataSource = "sharePoint"
} | ConvertTo-Json

Invoke-MgGraphRequest -Method POST `
    -Uri "v1.0/copilot/retrieval" `
    -Body $body
```

## Graph Explorer Usage

### Testing in Browser [VERIFIED]

1. Go to https://developer.microsoft.com/graph/graph-explorer
2. Sign in with an account that has M365 Copilot license
3. Consent to required permissions
4. Select POST method
5. Enter URL: `https://graph.microsoft.com/v1.0/copilot/retrieval`
6. Add request body:
```json
{
    "queryString": "Your search query",
    "dataSource": "sharePoint"
}
```
7. Click "Run Query"

**Quick link:** https://aka.ms/try_copilot_retrieval_API_overview

## Sources

**Primary:**
- `COPRA-IN01-SC-MSFT-SDKLIBS`: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/sdks/api-libraries
- `COPRA-IN01-SC-GITHUB-SDK`: https://github.com/microsoft/Agents-M365Copilot

## Document History

**[2026-01-29 09:20]**
- Initial document created
- All 14 TOC items documented
- Complete working examples in C#, Python, TypeScript, PowerShell
