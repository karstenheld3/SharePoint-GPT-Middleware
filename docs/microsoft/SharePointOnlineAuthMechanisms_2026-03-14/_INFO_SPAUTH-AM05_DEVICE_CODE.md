<DevSystem MarkdownTablesAllowed=true />

# INFO: Device Code Flow Authentication

**Doc ID**: SPAUTH-AM05
**Goal**: Detailed guide for device code authentication in FastAPI Azure Web Apps
**Version Scope**: Azure Identity 1.x, MSAL Python 1.x, Microsoft Entra ID (2026)

**Depends on:**
- `__AUTH_MECHANISMS_SOURCES.md [SPAUTH-SOURCES]` for source references

## 1. Intended Scenario and Recommended Use

### When to Use Device Code Flow

Device code flow is for **browserless** or **input-constrained** environments:

- **CLI tools** - Command-line applications without GUI
- **SSH sessions** - Remote terminal access
- **IoT devices** - Smart devices with limited input
- **Headless servers** - Servers without display
- **TV/Console apps** - Limited keyboard input

### User Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ Device Code Flow                                                 │
│                                                                  │
│  CLI/App displays:                                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ To sign in, visit: https://microsoft.com/devicelogin       │  │
│  │ Enter code: ABCD-EFGH                                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│  User opens browser on ANY device (phone, laptop, etc.)          │
│  Visits URL, enters code, logs in                                │
│                          │                                       │
│                          ▼                                       │
│  App polls Microsoft until login complete                        │
│  Receives tokens                                                 │
└──────────────────────────────────────────────────────────────────┘
```

### When NOT to Use

- **Web applications** - Use interactive browser or authorization code
- **Background services** - Use app-only credentials
- **User has browser on same device** - Use interactive browser instead
- **Automated pipelines** - No user to enter code

### Recommendation Level

| Scenario | Recommendation |
|----------|----------------|
| CLI tools | **RECOMMENDED** |
| SSH sessions | **RECOMMENDED** |
| IoT devices | **RECOMMENDED** |
| Web apps | NOT RECOMMENDED |
| Automated jobs | NOT SUPPORTED |

## 2. How to Use in FastAPI Azure Web App

### Architecture Overview

Device code is typically used for CLI tools, not web apps. However, a FastAPI app might provide a CLI companion or admin tool.

```
┌─────────────────────────────────────────────────────────────────┐
│ Terminal / SSH Session                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CLI Tool (Python)                                           │ │
│ │                                                             │ │
│ │  $ python cli.py login                                      │ │
│ │  To sign in, visit: https://microsoft.com/devicelogin       │ │
│ │  Enter code: ABCD-EFGH                                      │ │
│ │                                                             │ │
│ │  [Polling for authentication...]                            │ │
│ │  ✓ Logged in as user@contoso.com                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ User opens phone/laptop browser:                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ https://microsoft.com/devicelogin                           │ │
│ │ Enter code: [ABCD-EFGH]                                     │ │
│ │ [Sign in with Microsoft account]                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### CLI Tool Implementation

```python
# cli/sharepoint_cli.py
import os
import json
import click
from azure.identity import DeviceCodeCredential
from office365.sharepoint.client_context import ClientContext

TOKEN_CACHE_FILE = os.path.expanduser("~/.sharepoint_cli_tokens.json")

class SharePointCLI:
    def __init__(self):
        self._tenant_id = os.environ.get("AZURE_TENANT_ID")
        self._client_id = os.environ.get("AZURE_CLIENT_ID")
        self._sharepoint_url = os.environ.get("SHAREPOINT_URL")
        self._credential = None
        self._token = None
    
    def login(self):
        """Initiate device code login."""
        def prompt_callback(verification_uri, user_code, expires_on):
            print(f"\n{'='*60}")
            print(f"To sign in, visit: {verification_uri}")
            print(f"Enter code: {user_code}")
            print(f"Code expires: {expires_on}")
            print(f"{'='*60}\n")
        
        self._credential = DeviceCodeCredential(
            client_id=self._client_id,
            tenant_id=self._tenant_id,
            prompt_callback=prompt_callback
        )
        
        # Trigger authentication
        print("Waiting for authentication...")
        token = self._credential.get_token(f"{self._sharepoint_url}/.default")
        
        # Cache token
        self._save_token(token)
        print(f"✓ Successfully authenticated!")
        return token
    
    def _save_token(self, token):
        """Save token to file (for demo - use secure storage in production)."""
        with open(TOKEN_CACHE_FILE, "w") as f:
            json.dump({
                "token": token.token,
                "expires_on": token.expires_on
            }, f)
    
    def _load_token(self):
        """Load cached token."""
        if os.path.exists(TOKEN_CACHE_FILE):
            with open(TOKEN_CACHE_FILE) as f:
                return json.load(f)
        return None
    
    def get_context(self, site_url: str) -> ClientContext:
        """Get SharePoint context using cached token."""
        cached = self._load_token()
        if not cached:
            raise click.ClickException("Not logged in. Run 'login' first.")
        
        return ClientContext(site_url).with_access_token(lambda: cached["token"])


@click.group()
def cli():
    """SharePoint CLI Tool"""
    pass

@cli.command()
def login():
    """Login to SharePoint using device code."""
    sp = SharePointCLI()
    sp.login()

@cli.command()
@click.argument("site_name")
def list_items(site_name: str):
    """List items in a SharePoint site."""
    sp = SharePointCLI()
    site_url = f"{os.environ['SHAREPOINT_URL']}/sites/{site_name}"
    
    ctx = sp.get_context(site_url)
    lists = ctx.web.lists.get().execute_query()
    
    for lst in lists:
        click.echo(f"  - {lst.title}")

if __name__ == "__main__":
    cli()
```

### FastAPI Admin Endpoint with Device Code

```python
# app/admin/device_auth.py
from fastapi import APIRouter, BackgroundTasks
from azure.identity import DeviceCodeCredential
import asyncio

router = APIRouter(prefix="/admin")

# Store pending auth sessions
pending_auths = {}

@router.post("/auth/device-code/start")
async def start_device_auth(session_id: str):
    """Start device code authentication."""
    
    device_code_info = {}
    
    def prompt_callback(verification_uri, user_code, expires_on):
        device_code_info["verification_uri"] = verification_uri
        device_code_info["user_code"] = user_code
        device_code_info["expires_on"] = str(expires_on)
    
    credential = DeviceCodeCredential(
        client_id=os.environ["AZURE_CLIENT_ID"],
        tenant_id=os.environ["AZURE_TENANT_ID"],
        prompt_callback=prompt_callback
    )
    
    pending_auths[session_id] = {
        "credential": credential,
        "status": "pending",
        "device_code_info": device_code_info
    }
    
    return device_code_info

@router.get("/auth/device-code/poll/{session_id}")
async def poll_device_auth(session_id: str):
    """Poll for authentication completion."""
    if session_id not in pending_auths:
        return {"status": "not_found"}
    
    auth = pending_auths[session_id]
    
    if auth["status"] == "completed":
        return {"status": "completed", "user": auth.get("user")}
    
    try:
        # Try to get token (will succeed once user completes auth)
        token = auth["credential"].get_token(
            "https://graph.microsoft.com/.default"
        )
        auth["status"] = "completed"
        auth["token"] = token.token
        return {"status": "completed"}
    except Exception as e:
        if "authorization_pending" in str(e).lower():
            return {"status": "pending"}
        return {"status": "error", "message": str(e)}
```

### Environment Variables

```bash
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_CLIENT_ID=abcdefab-1234-5678-abcd-abcdefabcdef
SHAREPOINT_URL=https://contoso.sharepoint.com
```

## 3. Prerequisites

### Azure AD App Registration

1. **Create App Registration**
   - Azure Portal > Microsoft Entra ID > App registrations > New registration
   - Name: "SharePoint CLI"
   - Supported account types: Single tenant
   - Redirect URI: Not needed for device code

2. **Enable Public Client**
   - App registration > Authentication
   - Under "Advanced settings":
     - Enable "Allow public client flows": **Yes**
   - Save

3. **Configure API Permissions (Delegated)**
   - App registration > API permissions > Add a permission
   - Microsoft Graph or SharePoint (delegated, not application)
   - Common permissions:
     - `User.Read` - Sign in and read profile
     - `Sites.Read.All` - Read SharePoint sites
   - Grant admin consent (optional - users can self-consent)

### No Client Secret Needed

Device code flow uses a **public client** - no client secret is required or used.

## 4. Dependencies and Maintenance Problems

### Required Packages

```txt
# requirements.txt
azure-identity>=1.15.0
msal>=1.26.0
click>=8.0.0  # For CLI tools
Office365-REST-Python-Client>=2.5.0
```

### Maintenance Concerns

| Issue                             | Impact                     | Mitigation                                          |
|-----------------------------------|----------------------------|-----------------------------------------------------|
| Code expiration (15 minutes)      | User must restart flow     | Display countdown, clear messaging                  |
| Polling too fast                  | Throttled by server        | Use recommended interval (5 seconds)                |
| User confusion                    | Authentication fails       | Clear instructions in prompt                        |
| Token storage                     | Security risk              | Use secure storage or do not persist                |

### Polling Best Practices

```python
# Device code polling is handled by the SDK, but be aware:
# - Default interval: 5 seconds
# - Don't poll faster or you'll get "slow_down" error
# - Code expires after ~15 minutes
```

## 5. Code Examples

### Basic Device Code Flow

```python
from azure.identity import DeviceCodeCredential

def prompt_callback(verification_uri, user_code, expires_on):
    print(f"Visit: {verification_uri}")
    print(f"Enter code: {user_code}")

credential = DeviceCodeCredential(
    client_id="your-client-id",
    tenant_id="your-tenant-id",
    prompt_callback=prompt_callback
)

# This blocks until user completes auth
token = credential.get_token("https://graph.microsoft.com/.default")
print(f"Token acquired!")
```

### With MSAL (More Control)

```python
from msal import PublicClientApplication
import time

app = PublicClientApplication(
    client_id="your-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id"
)

# Initiate device code flow
flow = app.initiate_device_flow(
    scopes=["https://contoso.sharepoint.com/.default"]
)

if "error" in flow:
    print(f"Error: {flow['error_description']}")
    exit(1)

print(flow["message"])  # Contains URL and code

# Poll for completion
result = None
while result is None:
    result = app.acquire_token_by_device_flow(flow)
    
    if "error" in result:
        if result["error"] == "authorization_pending":
            time.sleep(flow.get("interval", 5))
            result = None
        else:
            print(f"Error: {result['error_description']}")
            break

if result and "access_token" in result:
    print(f"Authenticated as: {result.get('id_token_claims', {}).get('name')}")
```

### With Token Caching

```python
from msal import PublicClientApplication, SerializableTokenCache
import os

cache_file = os.path.expanduser("~/.my_token_cache.json")

# Load cache
cache = SerializableTokenCache()
if os.path.exists(cache_file):
    cache.deserialize(open(cache_file).read())

app = PublicClientApplication(
    client_id="your-client-id",
    authority="https://login.microsoftonline.com/your-tenant-id",
    token_cache=cache
)

# Try silent first
accounts = app.get_accounts()
result = None

if accounts:
    result = app.acquire_token_silent(
        scopes=["https://contoso.sharepoint.com/.default"],
        account=accounts[0]
    )

# Device code if silent fails
if not result:
    flow = app.initiate_device_flow(scopes=["..."])
    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)

# Save cache
if cache.has_state_changed:
    with open(cache_file, "w") as f:
        f.write(cache.serialize())
```

### Async Version

```python
import asyncio
from azure.identity.aio import DeviceCodeCredential

async def authenticate():
    def prompt_callback(verification_uri, user_code, expires_on):
        print(f"Visit: {verification_uri}")
        print(f"Enter code: {user_code}")
    
    credential = DeviceCodeCredential(
        client_id="your-client-id",
        tenant_id="your-tenant-id",
        prompt_callback=prompt_callback
    )
    
    token = await credential.get_token("https://graph.microsoft.com/.default")
    await credential.close()
    return token

token = asyncio.run(authenticate())
```

## 6. Gotchas and Quirks

### Code Expiration

Device codes expire after ~15 minutes. Always display the expiration time:

```python
def prompt_callback(verification_uri, user_code, expires_on):
    print(f"Code expires at: {expires_on}")
    print(f"You have ~15 minutes to complete authentication")
```

### "Allow public client flows" Must Be Enabled

If disabled, you'll get an error:

```
AADSTS7000218: The request body must contain the following parameter:
'client_assertion' or 'client_secret'.
```

**Fix:** App registration > Authentication > Allow public client flows: Yes

### User Code Format

Codes are typically formatted as `XXXX-XXXX`. Display them clearly:

```python
def prompt_callback(verification_uri, user_code, expires_on):
    print(f"\n┌{'─'*50}┐")
    print(f"│ Visit: {verification_uri:<40} │")
    print(f"│ Code:  {user_code:<40} │")
    print(f"└{'─'*50}┘\n")
```

### Polling Errors

```python
# "authorization_pending" - normal, keep polling
# "slow_down" - increase polling interval
# "expired_token" - code expired, start over
# "access_denied" - user declined consent
```

### MFA Still Applies

Device code flow still requires MFA if the user's policy mandates it. The user completes MFA in the browser.

### Token Scope

```python
# Wrong - use .default for client credentials style
credential.get_token("User.Read")  # May fail

# Correct
credential.get_token("https://graph.microsoft.com/.default")
# Or specific scopes for delegated
credential.get_token("https://graph.microsoft.com/User.Read")
```

### Don't Store Tokens Insecurely

```python
# BAD - plain text file
with open("tokens.json", "w") as f:
    json.dump({"token": token.token}, f)

# BETTER - use OS keychain
import keyring
keyring.set_password("myapp", "access_token", token.token)
```

## Sources

**Primary:**
- SPAUTH-SC-MSFT-DEVICECODE: Device code flow documentation
- SPAUTH-SC-MSFT-MSALPYTHON: MSAL for Python
- SPAUTH-SC-MSFT-AZIDREADME: Azure Identity client library

## Document History

**[2026-03-14 17:20]**
- Initial document created
- CLI tool implementation documented
- Polling and error handling patterns included
