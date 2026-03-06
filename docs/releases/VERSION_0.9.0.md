# SharePoint-GPT-Middleware Version 0.9.0

**Release Date:** March 2026

## Overview

This middleware provides OpenAI proxy endpoints, crawling SharePoint files into OpenAI vector stores, vector search based query functionality, and inventory management for vector stores.

## What's New in 0.9.0

### Enhanced SharePoint List Crawling

- **Full Field Data Capture** - List crawling now captures all column data instead of just ID, Title, and Modified
- **Smart Field Type Conversion** - Automatic conversion of SharePoint field types (Choice, Lookup, User, DateTime, Currency, URL, MultiChoice, etc.) to human-readable text
- **Dual Export Formats** - Lists exported as both CSV (for analysis) and Markdown (for embedding)
- **Field Ordering** - Consistent field ordering: ID, Title, alphabetical fields, Created, Modified

### V2 Sites Enhancements

- **Site Selftest** - New endpoint to validate site connectivity and permissions with streaming results
- **Security Scan Selftest** - New endpoint with 11 automated tests for scanner validation

### V2 Security Scanner Improvements

- **Configurable Scanner Settings** - JSON-based configuration for scan behavior
- **Subsite Scan Parity** - Subsites now scanned with same depth as root site
- **Group Resolution Fixes** - Improved handling of SharePoint groups and nested groups
- **Improved Logging** - Step/iteration markers with proper indentation for SSE output

### V2 Reports Viewer (`/v2/reports/view`)

- **Split-Panel UI** - File tree on left, content viewer on right
- **CSV Table Display** - Render CSV files as formatted HTML tables
- **In-Browser Viewing** - View report contents without downloading
- **Download Support** - Download individual files or complete archives

### SSE Streaming Improvements

- **Browser Buffering Fix** - Fixed SSE events being buffered in browser until endpoint completion
- **stream_with_flush() Wrapper** - New wrapper function ensures real-time event delivery
- **Consistent Pattern** - All streaming endpoints now use unified streaming pattern

### V2 Endpoint Fixes

- **Navigation Consistency** - All V2 routers now have consistent navigation links
- **Job UI Alignment** - Crawler jobs match /v2/jobs appearance (bold status, force delete)
- **Query Links** - Direct query links from domain rows
- **Clickable Vector Store IDs** - Navigate to OpenAI console from domain view
- **Selftest Cleanup** - Auto-delete sub-jobs created during crawler selftest

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
- Query links for direct vector store search
- UI, HTML, and JSON output formats

**Sites Management** (`/v2/sites`)
- Full CRUD operations for SharePoint sites
- **Site Selftest** - Validate connectivity and permissions
- **Security Scan** - Scan sites for permission issues (individual permissions, shared with everyone)
- **Security Scan Selftest** - Automated scanner validation (11 tests)
- UI, HTML, and JSON output formats

**SharePoint Crawler** (`/v2/crawler`)
- **Crawl** - Discover and list SharePoint files
- **Download** - Download files from SharePoint
- **Process** - Extract and prepare content for embedding
- **Embed** - Upload content to OpenAI vector stores
- **Selftest** - Validate crawler configuration
- **Enhanced List Export** - Full field data capture with smart type conversion

**Jobs Monitoring** (`/v2/jobs`)
- Job status monitoring
- Job control (pause, resume, cancel)
- Job results retrieval
- UI, HTML, and JSON output formats

**Report Archives** (`/v2/reports`)
- Crawl report storage and retrieval
- **Report Viewer** - Split-panel UI for browsing report contents
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

## Breaking Changes

None in this release.

## Migration Notes

No migration required from 0.8.0. All changes are backward compatible.

## Known Issues

- **SharePoint SDK Limitation** - M365/Security groups nested inside SharePoint groups are not resolved to individual members during security scans (SDK limitation)
- **SharePoint $skip** - SharePoint REST API does not support `$skip` for list item pagination; use `$skiptoken` or `odata.nextLink` instead
