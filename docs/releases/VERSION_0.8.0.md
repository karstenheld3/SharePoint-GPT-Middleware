# SharePoint-GPT-Middleware Version 0.8.0

**Release Date:** February 2026

## Overview

This middleware provides OpenAI proxy endpoints, crawling SharePoint files into OpenAI vector stores, vector search based query functionality, and inventory management for vector stores.

## Features

### OpenAI Integration

- **OpenAI Proxy** (`/openai`) - Proxy endpoints for OpenAI API calls
- **Azure OpenAI Support** - Key authentication, managed identity, and service principal authentication
- **Standard OpenAI Support** - Direct API key authentication

### SharePoint Search

- `/describe` - SharePoint Search description (JSON)
- `/describe2` - SharePoint Search description (HTML, JSON)
- `/query` - SharePoint Search query (JSON)
- `/query2` - SharePoint Search query (HTML, JSON)

### V1 API Endpoints

**Inventory Management** (`/v1/inventory`)
- `/v1/inventory/vectorstores` - Vector stores inventory (HTML, JSON, UI)
- `/v1/inventory/files` - Files inventory (HTML, JSON)
- `/v1/inventory/assistants` - Assistants inventory (HTML, JSON)

**Domains** (`/v1/domains`)
- List, create, update, delete knowledge domains

**Crawler** (`/v1/crawler`)
- Local storage management
- Update maps
- Log file retrieval

### V2 API Endpoints

**Knowledge Domains** (`/v2/domains`)
- Full CRUD operations for knowledge domains
- Domain self-test functionality
- UI, HTML, and JSON output formats

**Sites Management** (`/v2/sites`)
- Full CRUD operations for SharePoint sites
- **Security Scan** - Scan sites for permission issues (individual permissions, shared with everyone)
- UI, HTML, and JSON output formats

**SharePoint Crawler** (`/v2/crawler`)
- **Crawl** - Discover and list SharePoint files
- **Download** - Download files from SharePoint
- **Process** - Extract and prepare content for embedding
- **Embed** - Upload content to OpenAI vector stores
- **Selftest** - Validate crawler configuration

**Jobs Monitoring** (`/v2/jobs`)
- Job status monitoring
- Job control (pause, resume, cancel)
- Job results retrieval
- UI, HTML, and JSON output formats

**Report Archives** (`/v2/reports`)
- Crawl report storage and retrieval
- Report viewing and downloading
- Report management (delete)
- UI, HTML, and JSON output formats

## Authentication Methods

| Method | Configuration |
|--------|---------------|
| Azure OpenAI Key | `AZURE_OPENAI_USE_KEY_AUTHENTICATION=true` |
| Azure Managed Identity | `AZURE_OPENAI_USE_MANAGED_IDENTITY=true` + `AZURE_MANAGED_IDENTITY_CLIENT_ID` |
| Azure Service Principal | `AZURE_TENANT_ID` + `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` |
| Standard OpenAI | `OPENAI_SERVICE_TYPE=openai` + `OPENAI_API_KEY` |

## System Endpoints

- `/alive` - Health check
- `/docs` - API documentation (Swagger UI)
- `/openapi.json` - OpenAPI specification
- `/openaiproxyselftest` - OpenAI proxy self-test
