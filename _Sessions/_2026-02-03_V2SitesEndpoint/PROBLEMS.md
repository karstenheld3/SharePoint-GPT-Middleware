# Session Problems

**Doc ID**: 2026-02-03_V2SitesEndpoint-PROBLEMS

## Open

### SITE-PR-001: Define site.json schema

- **Status**: Open
- **Priority**: High
- **Description**: Define the complete schema for site.json including all fields
- **Fields identified**:
  - `name` - Site display name (required)
  - `site_url` - SharePoint site URL (required, trailing slash stripped)
  - `file_scan_result` - Result of file scan operation (read-only)
  - `security_scan_result` - Result of security scan operation (read-only)
- **Note**: `site_id` derived from folder name, not stored in JSON

### SITE-PR-002: Integrate sites router into app.py

- **Status**: Open
- **Priority**: High
- **Description**: Determine how to register the new sites router in the FastAPI application

### SITE-PR-003: Add sites folder to hardcoded_config.py

- **Status**: Open
- **Priority**: Medium
- **Description**: Add PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER constant

### SITE-PR-004: Implement placeholder scan buttons

- **Status**: Open
- **Priority**: Low
- **Description**: [File Scan] and [Security Scan] buttons should be grey/disabled placeholders for now

## Resolved

(None yet)

## Deferred

(None yet)

