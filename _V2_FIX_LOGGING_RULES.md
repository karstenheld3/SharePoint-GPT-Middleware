# V2 Logging Rules Compliance Fix Plan

**Goal**: Verify and fix all V2 routers files against the logging rules specified in `.windsurf/rules/python-rules.md` (lines 291-451).

**Target files**: All files in `/src/routers_v2/*.py`

## Table of Contents

1. [Logging Rules Summary](#logging-rules-summary)
2. [Files Analyzed](#files-analyzed)
3. [Violations by Rule](#violations-by-rule)
4. [Violations by File](#violations-by-file)
5. [Detailed Fix Plan](#detailed-fix-plan)
6. [TODO Checklist](#todo-checklist)

## Logging Rules Summary

**Reference**: `_NEW_PYTHON_RULES.md` Section "Logging Rules (LG)"

**GLOB-LG-01**: Sub-Action Indentation - Indent sub-actions with 2 spaces
**GLOB-LG-02**: Log Before Action - Log the action description before executing it
**GLOB-LG-03**: Status Keywords - `OK`, `ERROR`, `FAIL`, `WARNING` on separate indented line
**GLOB-LG-04**: Quote Paths and IDs - Surround with single quotes `'...'`
**GLOB-LG-05**: Iteration Format - Prefix with `[ x / n ]`
**GLOB-LG-06**: Retry Format - Use `( x / n )` inline
**GLOB-LG-07**: Numbers First - State numbers first in results (exception: activity verbs)
**GLOB-LG-08**: Property Format - Use `property_name='value'` format
**GLOB-LG-09**: UNKNOWN Constant - Use `or UNKNOWN` pattern for missing values
**GLOB-LG-10**: Nested Function Indentation - +2 spaces per nesting level
**GLOB-LG-11**: Error Concatenation - Use ` -> ` before exception
**GLOB-LG-12**: Identifier Parentheses - Wrap additional IDs in parentheses `(ID=xxx)`

**Rules with violations found**: GLOB-LG-03, GLOB-LG-07, GLOB-LG-08, GLOB-LG-09, GLOB-LG-10, GLOB-LG-11, GLOB-LG-12
**Rules already compliant**: GLOB-LG-01, GLOB-LG-02, GLOB-LG-04, GLOB-LG-05, GLOB-LG-06

## Files Analyzed

| File | Lines | Has Logging | Status |
|------|-------|-------------|--------|
| common_crawler_functions_v2.py | 474 | Yes | Has violations |
| common_embed_functions_v2.py | 233 | Yes | Has violations |
| common_job_functions_v2.py | 532 | Yes | Has violations |
| common_logging_functions_v2.py | 184 | Yes | Compliant (defines logging) |
| common_map_file_functions_v2.py | 294 | No | N/A |
| common_openai_functions_v2.py | 783 | Yes | Has violations |
| common_report_functions_v2.py | 230 | Yes | Has violations |
| common_sharepoint_functions_v2.py | 406 | Yes | Has UNKNOWN defined, some violations |
| common_ui_functions_v2.py | 1181 | No | N/A (UI only) |
| crawler.py | 646 | Yes | Has violations |
| demorouter1.py | ~200 | Yes | Has violations |
| demorouter2.py | ~200 | Yes | Has violations |
| domains.py | 1127 | Yes | Minor violations |
| jobs.py | 1407 | Yes | Minor violations |
| reports.py | 712 | Yes | Minor violations |

## Violations by Rule

### GLOB-LG-07: Numbers First

**Rule**: State numbers first in logs. Honor singular/plural.
**Exception**: When starting activities, the activity verb should go first.

**BAD**: `Retrieved 1 items so far...` / `Total files retrieved: 2`
**GOOD**: `1 item retrieved so far...` / `2 total files retrieved.`
**EXCEPTION**: `Retrieving 1 item from 'https://...'...` (activity verb first - OK)

**Violations Found**:

1. `common_crawler_functions_v2.py:140`
   - BEFORE: `Found 3 domain folder(s)`
   - AFTER:  `3 domain folders found.`

2. `common_crawler_functions_v2.py:153`
   - BEFORE: `Successfully loaded 3 domain(s)`
   - AFTER:  `3 domains loaded.`

3. `common_report_functions_v2.py:155`
   - BEFORE: `Found 5 report(s).`
   - AFTER:  `5 reports found.`

4. `common_openai_functions_v2.py:676`
   - BEFORE: `File deletion complete: 8 deleted, 2 failed`
   - AFTER:  `8 deleted, 2 failed.`

5. `crawler.py:115`
   - BEFORE: `Change detection: added=5, changed=3, removed=1, unchanged=10`
   - AFTER:  `5 added, 3 changed, 1 removed, 10 unchanged.`

6. `reports.py:659`
   - BEFORE: `Cancelled after creating 3 report(s).`
   - AFTER:  `3 reports created before cancel.`

7. `reports.py:689`, `demorouter1.py:1903`, `demorouter2.py:1131`
   - BEFORE: `Completed: 5 created, 1 failed.`
   - AFTER:  `5 created, 1 failed.`

8. `crawler.py:153`
   - BEFORE: `Download complete: 10 downloaded, 5 skipped, 1 errors`
   - AFTER:  `10 downloaded, 5 skipped, 1 error.`

9. `crawler.py:290`
   - BEFORE: `Embed complete: 8 embedded, 2 failed`
   - AFTER:  `8 embedded, 2 failed.`

10. `crawler.py:388`
    - BEFORE: `Crawl completed: 15 files embedded`
    - AFTER:  `15 files embedded.`

### GLOB-LG-08: Property Format

**Rule**: Use `property_name='value'` format for IDs, paths, names.

**BAD**: `Loading domain AiSearchTest01 from: E:\dev\...`
**GOOD**: `Loading domain 'AiSearchTest01' from 'E:\dev\...'...`

**Violations Found**:

1. `common_crawler_functions_v2.py:130`
   - BEFORE: `Scanning domains path: E:\data\domains`
   - AFTER:  `Scanning domains path='E:\data\domains'...`

2. `common_crawler_functions_v2.py:135`
   - BEFORE: `Created domains folder: E:\data\domains`
   - AFTER:  `Created domains folder path='E:\data\domains'.`

3. `common_crawler_functions_v2.py:209`
   - BEFORE: `Saving domain to: E:\data\domains\DOMAIN01\domain.json`
   - AFTER:  `Saving domain to 'E:\data\domains\DOMAIN01\domain.json'...`

4. `common_crawler_functions_v2.py:218`
   - BEFORE: `Domain saved successfully: DOMAIN01`
   - AFTER:  `Domain domain_id='DOMAIN01' saved.`

5. `common_crawler_functions_v2.py:243`
   - BEFORE: `Deleting domain folder: E:\data\domains\DOMAIN01`
   - AFTER:  `Deleting domain folder path='E:\data\domains\DOMAIN01'...`

### GLOB-LG-12: Additional Info in Parentheses

**Rule**: Use parentheses for additional/secondary information. Primary identifiers can be inline.

**Primary ID inline (correct)**: `Deleted file ID=file_xyz789`
**Additional info in parentheses (correct)**: `Library: 'Documents' (ID=045229b3...)`
**BAD**: `Deleted file (ID='file_xyz789').` (over-parenthesizing primary ID)

**Violations Found**:

1. `common_sharepoint_functions_v2.py:166`
   - BEFORE: `Library: 'Documents' ID=045229b3-57de-49ce-b36a-00c3ec0f4fd4`
   - AFTER:  `Library: 'Documents' (ID=045229b3-57de-49ce-b36a-00c3ec0f4fd4)`

2. `common_sharepoint_functions_v2.py:240`
   - BEFORE: `WARNING: File '/sites/demo/doc.pdf' ID=123 - failed to parse date '2024-01-15'. ValueError: ...`
   - AFTER:  `WARNING: File '/sites/demo/doc.pdf' (ID=123) - failed to parse date '2024-01-15' -> ValueError: ...`

3. `common_sharepoint_functions_v2.py:262`
   - BEFORE: `WARNING: File '/sites/demo/doc.pdf' ID=123 - failed to process. KeyError: ...`
   - AFTER:  `WARNING: File '/sites/demo/doc.pdf' (ID=123) - failed to process -> KeyError: ...`

4. `demorouter1.py:1857`, `demorouter2.py:1090`
   - BEFORE: `Creating 5 demo items (batch ID='abc123', delay=300ms each)...`
   - AFTER:  `Creating 5 demo items (batch_id='abc123', delay=300ms each)...`

### GLOB-LG-09: UNKNOWN Constant

**Rule**: Define `UNKNOWN = '[UNKNOWN]'` and use `or UNKNOWN` pattern.

**Status**:
- `common_sharepoint_functions_v2.py:16` - Defines `UNKNOWN = '[UNKNOWN]'` ✓
- Other files do NOT define UNKNOWN and use various fallback patterns

**Violations Found**:

1. `common_openai_functions_v2.py` - No UNKNOWN constant defined, uses empty strings and `or ''` patterns

2. `common_crawler_functions_v2.py` - No UNKNOWN constant, uses various fallbacks

3. `common_embed_functions_v2.py` - No UNKNOWN constant

4. `common_report_functions_v2.py` - No UNKNOWN constant

5. `crawler.py` - No UNKNOWN constant

6. `domains.py` - No UNKNOWN constant

7. `jobs.py` - No UNKNOWN constant

8. `reports.py` - No UNKNOWN constant

### GLOB-LG-10: Nested Function Indentation

**Rule**: Each nesting level adds 2 spaces (depth 1 = 2 spaces, depth 2 = 4 spaces).

**Violations Found**:

1. `common_openai_functions_v2.py:671` - `[ {i+1} / {len(file_ids)} ] Deleted file ID={file_id}`
   - Missing 2-space prefix for sub-action

2. `common_openai_functions_v2.py:674` - `[ {i+1} / {len(file_ids)} ] WARNING: Failed to delete file ID={file_id}: {str(e)}`
   - Missing 2-space prefix, WARNING should be on separate indented line

3. Most files use `log_function_output` which doesn't auto-indent sub-actions

### GLOB-LG-03: Status Keywords

**Rule**: Use uppercase `OK`, `ERROR`, `FAIL`, `WARNING`. Put on separate indented line.s.

**BAD**: `Success.` / `Download complete` / `failed to process file`
**GOOD**: `  OK.` / `  ERROR: Connection timeout. -> Exception`

**Violations Found**:

1. `common_embed_functions_v2.py:188`
   - BEFORE: `ERROR: Upload failed: Connection timeout`
   - AFTER:  `  ERROR: Upload failed -> ConnectionError: Connection timeout`

2. `common_embed_functions_v2.py:196`
   - BEFORE: `ERROR: Add to vector store failed: Rate limit exceeded`
   - AFTER:  `  ERROR: Add to vector store failed -> RateLimitError: Rate limit exceeded`

3. `common_embed_functions_v2.py:220`
   - BEFORE: `WARNING: Could not remove from vector store: File not found`
   - AFTER:  `  WARNING: Could not remove from vector store -> NotFoundError: File not found`

4. `common_embed_functions_v2.py:226`
   - BEFORE: `WARNING: Could not delete file: Permission denied`
   - AFTER:  `  WARNING: Could not delete file -> PermissionError: Permission denied`

5. `common_crawler_functions_v2.py:73`
   - BEFORE: `ERROR: Domain configuration not found: 'E:\data\...'`
   - AFTER:  `  ERROR: Domain configuration not found path='E:\data\...'`

6. `common_crawler_functions_v2.py:105`, `111`
   - BEFORE: `ERROR: Missing required field in domain.json: name`
   - AFTER:  `  ERROR: Missing required field in domain.json -> KeyError: 'name'`

7. `common_sharepoint_functions_v2.py:240`
   - BEFORE: `WARNING: File '/sites/demo/doc.pdf' ID=123 - failed to parse date '2024-01-15'. ValueError: ...`
   - AFTER:  `  WARNING: File '/sites/demo/doc.pdf' (ID=123) - failed to parse date '2024-01-15' -> ValueError: ...`

8. `common_sharepoint_functions_v2.py:262`
   - BEFORE: `WARNING: File '/sites/demo/doc.pdf' ID=123 - failed to process. KeyError: ...`
   - AFTER:  `  WARNING: File '/sites/demo/doc.pdf' (ID=123) - failed to process -> KeyError: ...`

9. `common_sharepoint_functions_v2.py:271`
   - BEFORE: `ERROR: Library 'Documents' - failed to retrieve files. ClientError: ...`
   - AFTER:  `  ERROR: Library 'Documents' - failed to retrieve files -> ClientError: ...`

10. `common_sharepoint_functions_v2.py:334`
    - BEFORE: `ERROR: List 'Tasks' - failed to get items. ClientError: ...`
    - AFTER:  `  ERROR: List 'Tasks' - failed to get items -> ClientError: ...`

11. `common_sharepoint_functions_v2.py:378`
    - BEFORE: `ERROR: Site pages '/SitePages' - Library not found`
    - AFTER:  `  ERROR: Site pages sharepoint_url_part='/SitePages' - Library not found`

12. `common_report_functions_v2.py:142-151`
    - BEFORE: `WARNING: Skipping 'E:\reports\bad.zip': missing report.json`
    - AFTER:  `  WARNING: Skipping path='E:\reports\bad.zip' - missing report.json`

13. `common_report_functions_v2.py:212`
    - BEFORE: `ERROR: Failed to delete report 'crawls/2024-01-15_demo': PermissionError: ...`
    - AFTER:  `  ERROR: Failed to delete report report_id='crawls/2024-01-15_demo' -> PermissionError: ...`

14. `common_openai_functions_v2.py:674`
    - BEFORE: `[ 3 / 10 ] WARNING: Failed to delete file ID=file_xyz: NotFoundError: ...`
    - AFTER:  `  [ 3 / 10 ] WARNING: Failed to delete file ID='file_xyz' -> NotFoundError: ...`

15. `common_openai_functions_v2.py:685`
    - BEFORE: `ERROR: Failed to delete vector store: NotFoundError: ...`
    - AFTER:  `  ERROR: Failed to delete vector store -> NotFoundError: ...`

16. `crawler.py:102`, `140`, `155`, `258`, `274`
    - BEFORE: `ERROR: Library not found`
    - AFTER:  `  ERROR: Library not found`

17. `reports.py:702`
    - BEFORE: `ERROR: ValueError: Invalid report type`
    - AFTER:  `  ERROR: Create demo report failed -> ValueError: Invalid report type`

### GLOB-LG-11: Error Concatenation

**Rule**: Use ` -> ` without dot before exception.

**BAD**: `Error: Could not download file. {e}`
**GOOD**: `ERROR: Could not download file -> {e}`

**Violations Found**:

1. `common_sharepoint_functions_v2.py:240`
   - BEFORE: `failed to parse date '2024-01-15'. ValueError: invalid format`
   - AFTER:  `failed to parse date '2024-01-15' -> ValueError: invalid format`

2. `common_sharepoint_functions_v2.py:262`
   - BEFORE: `failed to process. KeyError: 'Id'`
   - AFTER:  `failed to process -> KeyError: 'Id'`

3. `common_sharepoint_functions_v2.py:271`
   - BEFORE: `failed to retrieve files. ClientError: 403 Forbidden`
   - AFTER:  `failed to retrieve files -> ClientError: 403 Forbidden`

4. `common_sharepoint_functions_v2.py:334`
   - BEFORE: `failed to get items. ClientError: List not found`
   - AFTER:  `failed to get items -> ClientError: List not found`

5. `common_openai_functions_v2.py:674`
   - BEFORE: `Failed to delete file ID=file_xyz: NotFoundError: File not found`
   - AFTER:  `Failed to delete file ID='file_xyz' -> NotFoundError: File not found`

6. `common_report_functions_v2.py:171`
   - BEFORE: `Failed to read report metadata for 'crawls/demo': BadZipFile: ...`
   - AFTER:  `Failed to read report metadata for 'crawls/demo' -> BadZipFile: ...`

7. `common_report_functions_v2.py:187`
   - BEFORE: `Failed to read file 'data.csv' from report 'crawls/demo': KeyError: ...`
   - AFTER:  `Failed to read file 'data.csv' from report 'crawls/demo' -> KeyError: ...`

8. `common_report_functions_v2.py:212`
   - BEFORE: `Failed to delete report 'crawls/demo': PermissionError: Access denied`
   - AFTER:  `Failed to delete report 'crawls/demo' -> PermissionError: Access denied`

9. `reports.py:702`
   - BEFORE: `ERROR: ValueError: Invalid report type`
   - AFTER:  `  ERROR: Create demo report failed -> ValueError: Invalid report type`

10. `jobs.py:1381`
    - BEFORE: `ERROR: KeyError: 'job_id'`
    - AFTER:  `  ERROR: Selftest failed -> KeyError: 'job_id'`

11. `domains.py:1111`
    - BEFORE: `ERROR: ValueError: Invalid domain config`
    - AFTER:  `  ERROR: Selftest failed -> ValueError: Invalid domain config`

12. `demorouter1.py:1768`, `demorouter1.py:1916`
    - BEFORE: `ERROR: TypeError: 'NoneType' object is not subscriptable`
    - AFTER:  `  ERROR: Operation failed -> TypeError: 'NoneType' object is not subscriptable`

13. `demorouter2.py:1008`, `demorouter2.py:1144`
    - BEFORE: `ERROR: KeyError: 'item_id'`
    - AFTER:  `  ERROR: Operation failed -> KeyError: 'item_id'`

14. `crawler.py:102`, `crawler.py:140`, `crawler.py:155`, `crawler.py:391`
    - BEFORE: `ERROR: Library not found`
    - AFTER:  `  ERROR: Library not found`
    - Note: Some of these already use proper format, others need ` -> ` added

15. `common_report_functions_v2.py:151`
    - BEFORE: `WARNING: Skipping 'path.zip': Exception message`
    - AFTER:  `  WARNING: Skipping path='path.zip' -> Exception message`

## Violations by File

### common_crawler_functions_v2.py
- **GLOB-LG-07**: Lines 140, 153 - Numbers not first, uses `(s)` pattern
- **GLOB-LG-08**: Lines 130, 135, 209, 218, 243 - Missing quotes or uses colon
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-03**: Lines 73, 105, 111 - ERROR on same line, missing indent

### common_embed_functions_v2.py
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-03**: Lines 188, 196, 220, 226 - Missing 2-space indent at start

### common_job_functions_v2.py
- **GLOB-LG-09**: No UNKNOWN constant defined
- Minor formatting issues

### common_openai_functions_v2.py
- **GLOB-LG-07**: Line 676 - Numbers not first (result summary)
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-10**: Line 671 - Missing sub-action indent
- **GLOB-LG-03**: Line 674 - WARNING should be on separate line
- **GLOB-LG-11**: Line 674 - Uses `:` instead of ` -> `

### common_report_functions_v2.py
- **GLOB-LG-07**: Line 155 - Uses `(s)` pattern
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-03**: Lines 142-151, 212 - Indentation issues
- **GLOB-LG-11**: Lines 171, 187, 212 - Uses `:` instead of ` -> `

### common_sharepoint_functions_v2.py
- **GLOB-LG-09**: UNKNOWN defined ✓ but not used consistently everywhere
- **GLOB-LG-03**: Lines 240, 262, 271, 334, 378 - Various format issues
- **GLOB-LG-11**: Lines 240, 262, 271, 334 - Uses `.` instead of ` -> `
- **GLOB-LG-12**: Lines 166, 240, 262 - Missing parentheses around ID

### crawler.py
- **GLOB-LG-07**: Lines 115, 153, 290, 388 - Numbers not first (result summaries)
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-03**: Lines 102, 140, 155, 274, 391 - Missing indent, format issues
- **GLOB-LG-11**: Lines 155, 391 - Uses `:` instead of ` -> `

### domains.py
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-11**: Line 1111 - Uses `:` instead of ` -> `

### jobs.py
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-11**: Line 1381 - Uses `:` instead of ` -> `

### reports.py
- **GLOB-LG-07**: Lines 659, 689 - Numbers not first (result summaries)
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-11**: Line 702 - Uses `:` instead of ` -> `

### demorouter1.py
- **GLOB-LG-07**: Lines 1903 - Numbers not first
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-11**: Lines 1221, 1768, 1897, 1916 - Uses `:` instead of ` -> `
- **GLOB-LG-12**: Line 1857 - Missing parentheses around batch ID

### demorouter2.py
- **GLOB-LG-07**: Lines 1131 - Numbers not first
- **GLOB-LG-09**: No UNKNOWN constant defined
- **GLOB-LG-11**: Lines 648, 1008, 1126, 1144 - Uses `:` instead of ` -> `
- **GLOB-LG-12**: Line 1090 - Missing parentheses around batch ID

## Detailed Fix Plan

### Phase 1: Add UNKNOWN constant (GLOB-LG-09)

Define `UNKNOWN` in `common_logging_functions_v2.py` and import it where needed:

```python
# In common_logging_functions_v2.py (add after imports)
UNKNOWN = '[UNKNOWN]'
```

```python
# In files that need it (update import statement)
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN
```

Files to update:
1. common_logging_functions_v2.py - Define `UNKNOWN = '[UNKNOWN]'`
2. common_sharepoint_functions_v2.py - Remove local UNKNOWN, import from logger
3. common_crawler_functions_v2.py - Import UNKNOWN
4. common_embed_functions_v2.py - Import UNKNOWN
5. common_job_functions_v2.py - Import UNKNOWN
6. common_openai_functions_v2.py - Import UNKNOWN
7. common_report_functions_v2.py - Import UNKNOWN
8. crawler.py - Import UNKNOWN
9. domains.py - Import UNKNOWN
10. jobs.py - Import UNKNOWN (if needed)
11. reports.py - Import UNKNOWN (if needed)

### Phase 2: Fix Numbers First pattern (GLOB-LG-07)

**Pattern to apply**:
- BAD: `Found {count} items`
- GOOD: `{count} item(s) found.` with proper singular/plural

**Specific fixes**:

1. `common_crawler_functions_v2.py:140`:
   - FROM: `f"Found {len(domain_folders)} domain folder(s)"`
   - TO: `f"{len(domain_folders)} domain folder{'' if len(domain_folders) == 1 else 's'} found."`

2. `common_crawler_functions_v2.py:153`:
   - FROM: `f"Successfully loaded {len(domains_list)} domain(s)"`
   - TO: `f"{len(domains_list)} domain{'' if len(domains_list) == 1 else 's'} loaded."`

3. `common_sharepoint_functions_v2.py:175`:
   - FROM: `f"{len(items)} item{'' if len(items) == 1 else 's'} retrieved so far..."`
   - KEEP (already numbers first)

4. `common_openai_functions_v2.py:662`:
   - FROM: `f"Deleting {len(file_ids)} files from global storage..."`
   - TO: `f"{len(file_ids)} file{'' if len(file_ids) == 1 else 's'} to delete from global storage..."`

5. `common_report_functions_v2.py:155`:
   - FROM: `f"Found {len(reports)}" + (" report." if len(reports) == 1 else " reports.")`
   - TO: `f"{len(reports)} report{'' if len(reports) == 1 else 's'} found."`

6. `crawler.py:298`:
   - FROM: `f"Crawling {len(sources)} source(s)"`
   - TO: `f"{len(sources)} source{'' if len(sources) == 1 else 's'} to crawl."`

### Phase 3: Fix Property Quoting (GLOB-LG-08)

**Pattern to apply**:
- Use `property_name='value'` format
- No colons after prepositions like "from", "to", "at"

**Specific fixes**:

1. `common_crawler_functions_v2.py:130`:
   - FROM: `f"Scanning domains path: {domains_path}"`
   - TO: `f"Scanning domains path='{domains_path}'..."`

2. `common_crawler_functions_v2.py:135`:
   - FROM: `f"Created domains folder: {domains_path}"`
   - TO: `f"Created domains folder path='{domains_path}'."`

3. `common_crawler_functions_v2.py:209`:
   - FROM: `f"Saving domain to: {domain_json_path}"`
   - TO: `f"Saving domain to '{domain_json_path}'..."`

4. `common_crawler_functions_v2.py:218`:
   - FROM: `f"Domain saved successfully: {domain_config.domain_id}"`
   - TO: `f"Domain domain_id='{domain_config.domain_id}' saved."`

5. `common_crawler_functions_v2.py:243`:
   - FROM: `f"Deleting domain folder: {domain_folder}"`
   - TO: `f"Deleting domain folder path='{domain_folder}'..."`

6. `common_openai_functions_v2.py:671`:
   - FROM: `f"Deleted file ID={file_id}"`
   - TO: `f"Deleted file ID='{file_id}'."`

7. `common_openai_functions_v2.py:702`:
   - FROM: `f"File {file_id} removed from vector store {vector_store_id}"`
   - TO: `f"File ID='{file_id}' removed from vector store ID='{vector_store_id}'."`

### Phase 4: Fix Error Concatenation (GLOB-LG-11)

**Pattern to apply**:
- FROM: `ERROR: Description: {exception}` or `ERROR: Description. {exception}`
- TO: `ERROR: Description -> {exception}`

**Specific fixes**:

1. `common_sharepoint_functions_v2.py:240`:
   - FROM: `failed to parse date '{modified}'. {date_error}`
   - TO: `failed to parse date '{modified}' -> {date_error}`

2. `common_sharepoint_functions_v2.py:262`:
   - FROM: `failed to process. {item_error}`
   - TO: `failed to process -> {item_error}`

3. `common_sharepoint_functions_v2.py:271`:
   - FROM: `failed to retrieve files. {str(e)}`
   - TO: `failed to retrieve files -> {str(e)}`

4. `common_sharepoint_functions_v2.py:334`:
   - FROM: `failed to get items. {str(e)}`
   - TO: `failed to get items -> {str(e)}`

5. `common_openai_functions_v2.py:674`:
   - FROM: `Failed to delete file ID={file_id}: {str(e)}`
   - TO: `Failed to delete file ID='{file_id}' -> {str(e)}`

6. `common_report_functions_v2.py:171`:
   - FROM: `Failed to read report metadata for '{report_id}': {e}`
   - TO: `Failed to read report metadata for '{report_id}' -> {e}`

7. `common_report_functions_v2.py:187`:
   - FROM: `Failed to read file '{file_path}' from report '{report_id}': {e}`
   - TO: `Failed to read file '{file_path}' from report '{report_id}' -> {e}`

8. `common_report_functions_v2.py:212`:
   - FROM: `Failed to delete report '{report_id}': {e}`
   - TO: `Failed to delete report '{report_id}' -> {e}`

### Phase 5: Fix Status Keyword Indentation (LR-05)

**Pattern to apply**:
- Status keywords should be on separate indented lines (2 spaces)
- Currently many ERROR/WARNING logs are inline without proper indentation

**Note**: Many logs use `log_function_output()` which already handles some indentation. The main fixes needed are:

1. Ensure ERROR/WARNING logs start with 2-space indent when they're sub-actions
2. Use proper ` -> ` format before exceptions

## TODO Checklist

### Phase 1: Add UNKNOWN Constant
- [ ] common_logging_functions_v2.py - Define `UNKNOWN = '[UNKNOWN]'` after imports
- [ ] common_sharepoint_functions_v2.py - Remove local UNKNOWN, import from logger
- [ ] common_crawler_functions_v2.py - Import UNKNOWN from logger
- [ ] common_embed_functions_v2.py - Import UNKNOWN from logger
- [ ] common_job_functions_v2.py - Import UNKNOWN from logger
- [ ] common_openai_functions_v2.py - Import UNKNOWN from logger
- [ ] common_report_functions_v2.py - Import UNKNOWN from logger
- [ ] crawler.py - Import UNKNOWN from logger
- [ ] domains.py - Import UNKNOWN from logger
- [ ] jobs.py - Import UNKNOWN from logger (if needed)
- [ ] reports.py - Import UNKNOWN from logger (if needed)

### Phase 2: Fix Numbers First Pattern
- [ ] common_crawler_functions_v2.py:140 - Fix "Found X domain folder(s)"
- [ ] common_crawler_functions_v2.py:153 - Fix "Successfully loaded X domain(s)"
- [ ] common_openai_functions_v2.py:676 - Fix "File deletion complete: X deleted..."
- [ ] common_report_functions_v2.py:155 - Fix "Found X report(s)"
- [ ] crawler.py:115 - Fix "Change detection: added=X..."
- [ ] crawler.py:153 - Fix "Download complete: X downloaded..."
- [ ] crawler.py:290 - Fix "Embed complete: X embedded..."
- [ ] crawler.py:388 - Fix "Crawl completed: X files embedded"
- [ ] reports.py:659 - Fix "Cancelled after creating X report(s)"
- [ ] reports.py:689 - Fix "Completed: X created, Y failed"
- [ ] demorouter1.py:1903 - Fix "Completed: X created, Y failed"
- [ ] demorouter2.py:1131 - Fix "Completed: X created, Y failed"

### Phase 3: Fix Property Quoting
- [ ] common_crawler_functions_v2.py:130 - Fix "Scanning domains path:"
- [ ] common_crawler_functions_v2.py:135 - Fix "Created domains folder:"
- [ ] common_crawler_functions_v2.py:209 - Fix "Saving domain to:"
- [ ] common_crawler_functions_v2.py:218 - Fix "Domain saved successfully:"
- [ ] common_crawler_functions_v2.py:243 - Fix "Deleting domain folder:"

### Phase 4: Fix Error Concatenation (use ` -> ` before exceptions)
- [ ] common_sharepoint_functions_v2.py:240 - Change `. {date_error}` to ` -> {date_error}`
- [ ] common_sharepoint_functions_v2.py:262 - Change `. {item_error}` to ` -> {item_error}`
- [ ] common_sharepoint_functions_v2.py:271 - Change `. {str(e)}` to ` -> {str(e)}`
- [ ] common_sharepoint_functions_v2.py:334 - Change `. {str(e)}` to ` -> {str(e)}`
- [ ] common_openai_functions_v2.py:674 - Change `: {str(e)}` to ` -> {str(e)}`
- [ ] common_report_functions_v2.py:151 - Change `: {e}` to ` -> {e}`
- [ ] common_report_functions_v2.py:171 - Change `: {e}` to ` -> {e}`
- [ ] common_report_functions_v2.py:187 - Change `: {e}` to ` -> {e}`
- [ ] common_report_functions_v2.py:212 - Change `: {e}` to ` -> {e}`
- [ ] reports.py:702 - Fix `ERROR: {type}: {str}` to `ERROR: ... -> {type}: {str}`
- [ ] jobs.py:1381 - Fix `ERROR: {type}: {str}` to `ERROR: ... -> {type}: {str}`
- [ ] domains.py:1111 - Fix `ERROR: {type}: {str}` to `ERROR: ... -> {type}: {str}`
- [ ] demorouter1.py:1768 - Fix `ERROR: {type}: {str}` to `ERROR: ... -> {type}: {str}`
- [ ] demorouter1.py:1916 - Fix `ERROR: {type}: {str}` to `ERROR: ... -> {type}: {str}`
- [ ] demorouter2.py:1008 - Fix `ERROR: {type}: {str}` to `ERROR: ... -> {type}: {str}`
- [ ] demorouter2.py:1144 - Fix `ERROR: {type}: {str}` to `ERROR: ... -> {type}: {str}`
- [ ] crawler.py:155 - Fix error format
- [ ] crawler.py:391 - Fix error format

### Phase 5: Fix Status Keyword Indentation
- [ ] common_embed_functions_v2.py:188 - Add 2-space prefix
- [ ] common_embed_functions_v2.py:196 - Add 2-space prefix
- [ ] common_embed_functions_v2.py:220 - Add 2-space prefix
- [ ] common_embed_functions_v2.py:226 - Add 2-space prefix
- [ ] common_crawler_functions_v2.py - Review all ERROR logs for proper indentation
- [ ] common_openai_functions_v2.py:674 - Fix WARNING format and position
- [ ] common_report_functions_v2.py - Review all WARNING logs
- [ ] crawler.py:102, 140, 274 - Review ERROR logs for proper indentation

### Phase 6: Fix Identifier Parentheses (GLOB-LG-12)
- [ ] common_sharepoint_functions_v2.py:166 - Add parentheses around ID
- [ ] common_sharepoint_functions_v2.py:240 - Add parentheses around ID (also fix in Phase 4)
- [ ] common_sharepoint_functions_v2.py:262 - Add parentheses around ID (also fix in Phase 4)
- [ ] demorouter1.py:1857 - Fix batch ID format
- [ ] demorouter2.py:1090 - Fix batch ID format

### Final Verification
- [ ] Run application and verify logs are formatted correctly
- [ ] Search for remaining `(s)` patterns in log strings
- [ ] Search for remaining `: {` patterns before exceptions
- [ ] Search for remaining `. {` patterns before exceptions
- [ ] Search for remaining `ID=` patterns without parentheses
- [ ] Verify all files define UNKNOWN constant

## Spec Changes

| Date | Change |
|------|--------|
| 2024-12-29 | Initial analysis and fix plan created |
