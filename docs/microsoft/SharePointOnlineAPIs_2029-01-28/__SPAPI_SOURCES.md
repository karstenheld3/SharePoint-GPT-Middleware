# INFO: SharePoint API Sources - Pre-Flight Research

**Doc ID**: SPAPI-SOURCES
**Goal**: Comprehensive inventory of all available online sources for SharePoint API documentation
**Timeline**: Created 2026-01-28, 2 updates

## Summary (Copy/Paste Ready)

**Primary Sources (Microsoft Learn):** 35+ official documentation pages
**Community Sources:** 5+ (Patterns and Practices (PnP), GitHub, blogs)
**Portable Document Format (PDF)/Guides:** Limited - no official PDF reference found

**Key Documentation Hubs:**
- SharePoint Representational State Transfer (REST) API: `learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/`
- Microsoft Graph: `learn.microsoft.com/en-us/graph/api/resources/sharepoint`
- PnP Community: `pnp.github.io/`

## Table of Contents

- Microsoft Learn - SharePoint REST API
- Microsoft Learn - Microsoft Graph SharePoint
- Microsoft Learn - Specialized APIs
- Microsoft Learn - Permissions
- Community and Open Source
- Third-Party Resources
- Not Found / Limited Coverage

## Microsoft Learn - SharePoint REST API

### Core Documentation

- **REST Service Overview** - Architecture, HTTP methods, URL construction
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/get-to-know-the-sharepoint-rest-service
- **Basic Create, Read, Update, Delete (CRUD) Operations** - CRUD examples
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/complete-basic-operations-using-sharepoint-rest-endpoints
- **Endpoint Uniform Resource Identifier (URI) Structure** - URI syntax, entry points, parameters
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/determine-sharepoint-rest-service-endpoint-uris
- **Data Structure Navigation** - Site hierarchy, context info
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/navigate-the-sharepoint-data-structure-represented-in-the-rest-service
- **Open Data Protocol (OData) Query Operations** - $select, $filter, $expand, $orderby
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/use-odata-query-operations-in-sharepoint-rest-requests
- **Batch Requests** - $batch OData operations
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/make-batch-requests-with-the-rest-apis

### Entity-Specific Documentation

- **Lists and List Items** - CRUD for lists, items, attachments
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-lists-and-list-items-with-rest
- **Folders and Files** - File upload/download, folder operations
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/working-with-folders-and-files-with-rest
- **Custom Permissions** - Role assignments, breaking inheritance
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/set-custom-permissions-on-a-list-by-using-the-rest-interface

### Legacy Reference (SharePoint 2013 era, still applicable)

- **Users, Groups, Roles** - User, Group, RoleAssignment, RoleDefinition resources
  - https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-rest-reference/dn531432(v=office.15)
- **User Profiles** - PeopleManager, ProfileLoader, UserProfile resources
  - https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-rest-reference/dn790354(v=office.15)

## Microsoft Learn - Microsoft Graph SharePoint

### Core Graph Documentation

- **SharePoint Sites Overview** - Site, List, ListItem resources
  - https://learn.microsoft.com/en-us/graph/api/resources/sharepoint?view=graph-rest-1.0
- **SharePoint API Concepts** - Integration patterns, capabilities
  - https://learn.microsoft.com/en-us/graph/sharepoint-concept-overview
- **REST v2 (Graph via SP)** - /_api/v2.0/ endpoints mapping
  - https://learn.microsoft.com/en-us/sharepoint/dev/apis/sharepoint-rest-graph

### Graph Entity Documentation

- **Get Site** - Site retrieval, addressing
  - https://learn.microsoft.com/en-us/graph/api/site-get?view=graph-rest-1.0
- **Get List** - List retrieval
  - https://learn.microsoft.com/en-us/graph/api/list-get?view=graph-rest-1.0
- **List Items** - Item enumeration, filtering
  - https://learn.microsoft.com/en-us/graph/api/listitem-list?view=graph-rest-1.0
- **Create Item** - Item creation
  - https://learn.microsoft.com/en-us/graph/api/listitem-create?view=graph-rest-1.0
- **Get Drive** - Document library as drive
  - https://learn.microsoft.com/en-us/graph/api/drive-get?view=graph-rest-1.0
- **List Drives** - All drives in site
  - https://learn.microsoft.com/en-us/graph/api/drive-list?view=graph-rest-1.0
- **Content Types** - Site content types
  - https://learn.microsoft.com/en-us/graph/api/site-list-contenttypes?view=graph-rest-1.0

### Graph Permissions

- **Permissions Reference** - All Graph permissions including Sites.*
  - https://learn.microsoft.com/en-us/graph/permissions-reference
- **Selected Permissions** - Sites.Selected, granular access
  - https://learn.microsoft.com/en-us/graph/permissions-selected-overview

## Microsoft Learn - Specialized APIs

### Search API

- **Search REST API** - /_api/search/query endpoints
  - https://learn.microsoft.com/en-us/sharepoint/dev/general-development/sharepoint-search-rest-api-overview
- **KQL Syntax** - Keyword Query Language reference
  - https://learn.microsoft.com/en-us/sharepoint/dev/general-development/keyword-query-language-kql-syntax-reference
- **Building Search Queries** - Query construction patterns
  - https://learn.microsoft.com/en-us/sharepoint/dev/general-development/building-search-queries-in-sharepoint

### Social and User Profiles

- **Following API** - SocialRestFollowingManager
  - https://learn.microsoft.com/en-us/sharepoint/dev/general-development/following-people-and-content-rest-api-reference-for-sharepoint
- **Social Feed API** - SocialRestFeedManager
  - https://learn.microsoft.com/en-us/sharepoint/dev/general-development/social-feed-rest-api-reference-for-sharepoint
- **User Profiles Overview** - Profile APIs comparison
  - https://learn.microsoft.com/en-us/sharepoint/dev/general-development/work-with-user-profiles-in-sharepoint
- **Follow Content** - Documents, sites, tags
  - https://learn.microsoft.com/en-us/sharepoint/dev/general-development/how-to-follow-documents-sites-and-tags-by-using-the-rest-service-in-sharepoint-2

### Webhooks

- **Webhooks Overview** - Subscription model, notifications
  - https://learn.microsoft.com/en-us/sharepoint/dev/apis/webhooks/overview-sharepoint-webhooks
- **Getting Started** - Step-by-step tutorial
  - https://learn.microsoft.com/en-us/sharepoint/dev/apis/webhooks/get-started-webhooks
- **Create Subscription** - List webhook creation
  - https://learn.microsoft.com/en-us/sharepoint/dev/apis/webhooks/lists/create-subscription
- **Reference Implementation** - PnP sample code
  - https://learn.microsoft.com/en-us/sharepoint/dev/apis/webhooks/webhooks-reference-implementation

### Site Designs and Provisioning

- **Site Design REST API** - Site templates, scripts
  - https://learn.microsoft.com/en-us/sharepoint/dev/declarative-customization/site-design-rest-api
- **Site Design Overview** - Template concepts
  - https://learn.microsoft.com/en-us/sharepoint/dev/declarative-customization/site-design-overview
- **Site Creation REST** - Modern site provisioning
  - https://learn.microsoft.com/en-us/sharepoint/dev/apis/site-creation-rest
- **Modern Site Provisioning** - Programmatic creation
  - https://learn.microsoft.com/en-us/sharepoint/dev/solution-guidance/modern-experience-customizations-provisioning-sites
- **Remote Provisioning** - PnP provisioning patterns
  - https://learn.microsoft.com/en-us/sharepoint/dev/solution-guidance/pnp-remote-provisioning

### Change Tracking

- **Change Log Query** - GetChanges, ChangeQuery, ChangeToken
  - https://learn.microsoft.com/en-us/sharepoint/dev/solution-guidance/query-sharepoint-change-log-with-changequery-and-changetoken

### Navigation

- **Portal Navigation** - Navigation solutions
  - https://learn.microsoft.com/en-us/sharepoint/dev/solution-guidance/portal-navigation

## Microsoft Learn - SharePoint Framework (SPFx)

- **SPFx Overview** - Framework capabilities
  - https://learn.microsoft.com/en-us/sharepoint/dev/spfx/sharepoint-framework-overview
- **Build Web Part** - Hello World tutorial
  - https://learn.microsoft.com/en-us/sharepoint/dev/spfx/web-parts/get-started/build-a-hello-world-web-part
- **Extensions Overview** - Application customizers, field customizers
  - https://learn.microsoft.com/en-us/sharepoint/dev/spfx/extensions/overview-extensions
- **Tools and Libraries** - Development toolchain
  - https://learn.microsoft.com/en-us/sharepoint/dev/spfx/tools-and-libraries
- **PnPjs with SPFx** - Library integration
  - https://learn.microsoft.com/en-us/sharepoint/dev/spfx/web-parts/guidance/use-sp-pnp-js-with-spfx-web-parts

## Microsoft Learn - API Index

- **API Index** - Cross-reference Client-Side Object Model (CSOM), JavaScript Object Model (JSOM), REST endpoints
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/sharepoint-net-server-csom-jsom-and-rest-api-index

## Community and Open Source

### PnP (Patterns and Practices)

- **PnP PowerShell** - 700+ cmdlets for Microsoft 365 (M365)
  - https://pnp.github.io/powershell/
- **PnP PowerShell (MS Learn)** - Official documentation
  - https://learn.microsoft.com/en-us/powershell/sharepoint/sharepoint-pnp/sharepoint-pnp-cmdlets
- **PnP PowerShell GitHub** - Source, issues, releases
  - https://github.com/pnp/powershell
- **PnPjs** - Fluent JavaScript API
  - https://pnp.github.io/pnpjs/
- **PnPjs GitHub** - Source, getting started
  - https://github.com/pnp/pnpjs

## Third-Party Resources

- **SharePoint REST Tutorial** - 135-page PDF guide (third-party)
  - https://www.enjoysharepoint.com/sharepoint-rest-api/
- **SharePoint API Guide** - REST API overview and examples
  - https://hevodata.com/learn/sharepoint-api/
- **SharePoint API Guide** - API collection overview
  - https://www.merge.dev/blog/sharepoint-api
- **Stack Overflow Discussion** - Community discussion on API completeness
  - https://stackoverflow.com/questions/52980482/is-there-a-complete-list-of-sharepoint-online-rest-api-from-official-docs

## Not Found / Limited Coverage

### Areas with Limited Official Documentation

- **Complete endpoint reference** - No single comprehensive list of all REST endpoints exists
- **PDF/offline documentation** - Microsoft does not provide downloadable PDF API reference
- **Taxonomy/Term Store REST API** - Limited direct REST support, primarily CSOM/JSOM
- **Views REST API** - Basic support, full reference not documented
- **Recycle Bin REST API** - Community Q&A only, no official reference page
- **Attachments REST API** - Covered briefly in list items documentation

### Deprecated/Retiring

- **CSOM/JSOM** - Deprecated Nov 2023, retired Apr 2026
  - https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/sharepoint-net-server-csom-jsom-and-rest-api-index
- **Old PnP PowerShell** - Archived, use pnp/powershell instead
  - https://github.com/pnp/PnP-PowerShell

## Source Statistics

**Microsoft Learn Pages Found:** 45+
**GitHub Repositories:** 3
**Third-Party Sources:** 4
**Stack Overflow Discussions:** 1
**PDF Downloads Available:** 1 (third-party, 135 pages)

## Recommendations for Deep Research

1. **Start with core docs**: get-to-know-the-sharepoint-rest-service, complete-basic-operations
2. **Entity-specific**: working-with-lists, working-with-folders-and-files
3. **Graph integration**: sharepoint-rest-graph for v2.0 mapping
4. **Permissions**: permissions-selected-overview for granular access
5. **Community tools**: PnPjs and PnP PowerShell for practical examples

## Document History

**[2026-01-28 18:21]**
- Changed: Converted all Markdown tables to list format per core-conventions

**[2026-01-28 15:50]**
- Fixed: Expanded acronyms on first use (PnP, PDF, REST, CRUD, URI, OData, CSOM, JSOM, M365)
- Verified: Document structure against INFO template

**[2026-01-28 15:00]**
- Initial pre-flight research completed
- Catalogued 45+ Microsoft Learn pages
- Documented community resources (PnP)
- Identified gaps (no complete endpoint list, no PDF reference)
