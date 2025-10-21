# SharePoint-GPT-Middleware

Middleware App Registration App ID: `MMMMMMM-MMMM-MMMM-MMMM-MMMMMMMMMMMM`

Frontend App Registration App ID: `FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF`

## How to secure the Azure App Service

### Step 1: Enable Middleware Authentication

#### Step 1.1 Enable Authentication

Go to your Azure resouce group > [AZURE_APP_SERVICE_NAME] > Settings > Authentication > Add identity provider (click)

- Identity provider: **Microsoft**
- Choose a tenant for your application and its users: **Workforce configuration (current tenant)**
- App registration type: **Create new app registration**
- Name: **[MIDDLEWARE_APP_REGISTRATION_NAME]**
  You should use a human readable name that makes sense to admins who might not know about your application. By default, it's **[AZURE_APP_SERVICE_NAME]**
- Client secret expiration: **Choose from 3 to 24 months**
- Supported account types: **Current tenant - Single tenant**
- Client application requirement: **Allow requests from specific client applications**
- Identity requirement: **Allow requests from any identity**
- Tenant requirement: **Allow requests only from the issuer tenant**
- Restrict access: **Require authentication**
- Unauthenticated requests: **HTTP 302 Found redirect: recommended for websites**
- Token store: **Yes**

From App Service > Settings > Authentication > note the App (client) ID as **[MIDDLEWARE_APP_ID]** (`MMMMMMM-MMMM-MMMM-MMMM-MMMMMMMMMMMM`).

#### Step 1.2 Duplicate "Allowed token audiences" entry as GUID-only

Then go to [AZURE_APP_SERVICE_NAME] > Settings > Authentication > Under Identity provider > Microsoft > in Edit column > click edit symbol

- Allowed token audiences: Duplicate existing entry without `api://` 
  - From the first entry `api://MMMMMMM-MMMM-MMMM-MMMM-MMMMMMMMMMMM`, copy only the GUID (`MMMMMMM-MMMM-MMMM-MMMM-MMMMMMMMMMMM`)
  - Paste it into the second list entry field under the first entry
  - Why? If you access the middleware from Python using a Service Principal (App ID / Client ID + Client Secret) or Managed Identity, your `aud` claim in the token will be ONLY  be `[GUID]`   (without api://). To allow access, **the app service MUST have listed the plain GUID under 'Allowed token audiences'**.

#### Step 1.3 Create Middleware app role (for Application permissions)

Go to Azure > Microsoft Entra ID > App registrations > "All applications" (first tab in window)  > search for [MIDDLEWARE_APP_REGISTRATION_NAME] > click > App roles > Creat app role (click)

- Display name: **FullControl**
- Allowed member types: **Both (Users/Groups + Applications)**
- Value: **Middleware.FullControl**
- Description: **Applications and users that have full access to all endpoints and admin pages.**
- Do you want to enable this app role?: **Yes**

#### Step 1.4 Retrict Access to 

### Step 2: Create Frontend Application Registration

#### Step 2.1 Create App ID / Client ID

Go to Azure > Microsoft Entra ID > App registrations > New registration (click)

- Name: **[FRONTEND_APP_REGISTRATION_NAME]**
- Redirect URI (optional): **No setting, leave empty**

From the "Overview" screen, note the Application (client) ID as **[FRONTEND_APP_ID]** (`FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF`).

#### Step 2.2 Create Client Secret

Then go to [FRONTEND_APP_REGISTRATION_NAME] > Manage > Certificates & secrets > New client secret (click)

- Description: **Secret01**
- Expires: **Choose from 3 to 24 months**
- Click **Add**

#### Step 2.3 Create API Permissions

Go to [FRONTEND_APP_REGISTRATION_NAME] > Manage > API permissions > Add permission (click)

- "Microsoft APIs" tab > Microsoft Graph >  Delegated > In the list, check
  - OpenId permissions > **openid**
  - OpenId permissions > **profile**
  - Click **Add permissions**

Click again on Add permission (click) >  "APIs my organization uses" tab > search for [MIDDLEWARE_APP_REGISTRATION_NAME] > click

- Click "**Application permissions**"
- Check "**Middleware.FullControl**"
- Click **Add permissions**
- In the "API permissions" view, click "**Grant admin consent**"

### Step 3: Give Frontend Application access to Middleware

Go to your Azure resouce group > [AZURE_APP_SERVICE_NAME] > Settings > Authentication > Under Identity provider > Microsoft > in Edit column > click edit symbol

- Allowed client applications > click edit symbol > paste **[FRONTEND_APP_ID]** (`FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF`) > OK
- 
