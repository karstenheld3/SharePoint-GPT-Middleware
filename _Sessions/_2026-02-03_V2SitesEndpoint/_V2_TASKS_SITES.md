# V2 Sites Router Tasks

**Doc ID**: SITE-TK01
**Goal**: Partitioned task list for implementing the V2 sites router.

**Depends on:**
- `_V2_IMPL_SITES.md [SITE-IP01]` for implementation steps

## Tasks

### Phase 1: Configuration

- [ ] **TK-01**: Add constants to `hardcoded_config.py`
  - File: `src/hardcoded_config.py`
  - Add: `PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER`, `SITE_JSON`
  - Done when: Constants added and file saves without error

### Phase 2: Core Implementation

- [ ] **TK-02**: Create `sites.py` with imports and configuration
  - File: `src/routers_v2/sites.py`
  - Add: Imports, router config, set_config function
  - Done when: File created with basic structure

- [ ] **TK-03**: Implement SiteConfig dataclass and helper functions
  - File: `src/routers_v2/sites.py`
  - Add: SiteConfig, load_site, load_all_sites, save_site_to_file, delete_site_folder, rename_site, validate_site_config, site_config_to_dict, normalize_site_url
  - Done when: All functions implemented

- [ ] **TK-04**: Implement router-specific JavaScript
  - File: `src/routers_v2/sites.py`
  - Add: get_router_specific_js() with New/Edit forms, showNotImplemented
  - Done when: JavaScript functions complete

- [ ] **TK-05**: Implement List endpoint (GET /sites)
  - File: `src/routers_v2/sites.py`
  - Add: sites_root() with docs, json, html, ui formats
  - Done when: Endpoint returns correct format for each param

- [ ] **TK-06**: Implement Get endpoint (GET /sites/get)
  - File: `src/routers_v2/sites.py`
  - Add: sites_get() with docs, json, html formats
  - Done when: Returns site data or 404

- [ ] **TK-07**: Implement Create endpoint (POST /sites/create)
  - File: `src/routers_v2/sites.py`
  - Add: sites_create_docs(), sites_create()
  - Done when: Creates site folder and site.json

- [ ] **TK-08**: Implement Update endpoint (PUT /sites/update)
  - File: `src/routers_v2/sites.py`
  - Add: sites_update_docs(), sites_update() with rename support
  - Done when: Updates site, handles ID change

- [ ] **TK-09**: Implement Delete endpoint (DELETE/GET /sites/delete)
  - File: `src/routers_v2/sites.py`
  - Add: sites_delete_docs(), sites_delete()
  - Done when: Deletes folder, returns deleted data

- [ ] **TK-10**: Implement Selftest endpoint (GET /sites/selftest)
  - File: `src/routers_v2/sites.py`
  - Add: sites_selftest() streaming endpoint
  - Done when: All CRUD operations tested

### Phase 3: Integration

- [ ] **TK-11**: Register router in app.py
  - File: `src/app.py`
  - Add: Import sites_v2, include_router, UI links
  - Done when: Router accessible at /v2/sites

- [ ] **TK-12**: Update navigation in domains.py
  - File: `src/routers_v2/domains.py`
  - Add: Sites link to main_page_nav_html
  - Done when: Navigation includes Sites link

### Phase 4: Testing

- [ ] **TK-13**: Manual test all endpoints
  - Test: Create, Get, Update, Rename, Delete
  - Done when: All operations work correctly

- [ ] **TK-14**: Run selftest via browser
  - Test: GET /v2/sites/selftest?format=stream
  - Done when: All tests pass

- [ ] **TK-15**: Test UI in browser
  - Test: New Site, Edit Site, Delete Site, Scan buttons
  - Done when: UI works correctly

## Document History

**[2026-02-03 09:40]**
- Initial tasks list created

